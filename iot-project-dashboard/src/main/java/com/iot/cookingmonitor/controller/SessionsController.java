package com.iot.cookingmonitor.controller;

import com.iot.cookingmonitor.entity.CookingSession;
import com.iot.cookingmonitor.service.CookingSessionService;
import com.iot.cookingmonitor.service.ImageScraperService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

@Controller
@RequestMapping("/sessions")
public class SessionsController {

    @Autowired
    private CookingSessionService cookingSessionService;

    @Autowired
    private ImageScraperService imageScraperService;

    @GetMapping
    public String sessions(Model model) {
        List<CookingSession> cookingSessions = cookingSessionService.getAllCookingSessions();

        // Fetch first image URL for each session
        Map<Integer, String> sessionImageUrls = new HashMap<>();
        Map<Integer, List<String>> sessionAllImageUrls = new HashMap<>();

        for (CookingSession session : cookingSessions) {
            String imageUrl = imageScraperService.getFirstImageUrl(session.getSessionNumber());
            List<String> allImageUrls = imageScraperService.getAllImageUrls(session.getSessionNumber());

            sessionImageUrls.put(session.getSessionNumber(), imageUrl);
            sessionAllImageUrls.put(session.getSessionNumber(), allImageUrls);
        }

        // Calculate statistics
        int totalSessions = cookingSessions.size();

        // Count cooking styles
        Map<String, Long> cookingStyleCounts = cookingSessions.stream()
            .map(CookingSession::getCookingStyle)
            .filter(style -> style != null && !style.isEmpty())
            .collect(Collectors.groupingBy(style -> style, Collectors.counting()));

        // Get all unique cooking styles
        List<String> allCookingStyles = cookingStyleCounts.keySet().stream()
            .sorted()
            .collect(Collectors.toList());

        // Count ingredients
        Map<String, Long> ingredientCounts = cookingSessions.stream()
            .map(CookingSession::getIngredients)
            .filter(ingredients -> ingredients != null && !ingredients.isEmpty())
            .flatMap(ingredients -> {
                // Remove curly braces and split by comma
                String cleaned = ingredients.replace("{", "").replace("}", "");
                return java.util.Arrays.stream(cleaned.split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty());
            })
            .collect(Collectors.groupingBy(ingredient -> ingredient, Collectors.counting()));

        // Get all unique ingredients sorted by count (descending)
        List<String> allIngredients = ingredientCounts.entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());

        model.addAttribute("cookingSessions", cookingSessions);
        model.addAttribute("sessionImageUrls", sessionImageUrls);
        model.addAttribute("sessionAllImageUrls", sessionAllImageUrls);
        model.addAttribute("totalSessions", totalSessions);
        model.addAttribute("allCookingStyles", allCookingStyles);
        model.addAttribute("allIngredients", allIngredients);
        model.addAttribute("cookingStyleCounts", cookingStyleCounts);
        model.addAttribute("ingredientCounts", ingredientCounts);
        return "sessions";
    }
}
