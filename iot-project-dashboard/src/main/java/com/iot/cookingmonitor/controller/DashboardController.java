package com.iot.cookingmonitor.controller;

import com.iot.cookingmonitor.entity.CookingSession;
import com.iot.cookingmonitor.entity.Temperature;
import com.iot.cookingmonitor.entity.Motion2;
import com.iot.cookingmonitor.service.CookingSessionService;
import com.iot.cookingmonitor.service.ImageScraperService;
import com.iot.cookingmonitor.repository.TemperatureRepository;
import com.iot.cookingmonitor.repository.Motion2Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.stream.Collectors;
import java.time.format.DateTimeFormatter;
import java.time.YearMonth;

@Controller
@RequestMapping("/dashboard")
public class DashboardController {

    @Autowired
    private CookingSessionService cookingSessionService;

    @Autowired
    private ImageScraperService imageScraperService;

    @Autowired
    private TemperatureRepository temperatureRepository;

    @Autowired
    private Motion2Repository motion2Repository;

    @GetMapping
    public String dashboard(Model model) {
        List<CookingSession> cookingSessions = cookingSessionService.getAllCookingSessions();

        // Get last image for each session
        for (CookingSession session : cookingSessions) {
            List<String> allImageUrls = imageScraperService.getAllImageUrls(session.getSessionNumber());
            if (!allImageUrls.isEmpty()) {
                session.setImageUrl(allImageUrls.get(allImageUrls.size() - 1));
            }
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

        // Sort sessions by date (latest first) for timeline
        List<CookingSession> sortedSessions = cookingSessions.stream()
            .sorted((s1, s2) -> s2.getDateTime().compareTo(s1.getDateTime()))
            .collect(Collectors.toList());

        // Create index map for alternating positions
        Map<CookingSession, Integer> sessionIndexMap = new HashMap<>();
        for (int i = 0; i < sortedSessions.size(); i++) {
            sessionIndexMap.put(sortedSessions.get(i), i);
        }

        // Group sessions by month for timeline (latest first)
        Map<String, List<CookingSession>> sessionsByMonth = sortedSessions.stream()
            .collect(Collectors.groupingBy(
                session -> {
                    YearMonth yearMonth = YearMonth.from(session.getDateTime());
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMM yyyy");
                    return session.getDateTime().format(formatter);
                },
                LinkedHashMap::new,
                Collectors.toList()
            ));

        model.addAttribute("totalSessions", totalSessions);
        model.addAttribute("allCookingStyles", allCookingStyles);
        model.addAttribute("allIngredients", allIngredients);
        model.addAttribute("cookingStyleCounts", cookingStyleCounts);
        model.addAttribute("ingredientCounts", ingredientCounts);
        model.addAttribute("cookingSessions", cookingSessions);
        model.addAttribute("sessionsByMonth", sessionsByMonth);
        model.addAttribute("sessionIndexMap", sessionIndexMap);
        return "dashboard";
    }

    @GetMapping("/session/{sessionNumber}")
    public String sessionDetails(@PathVariable Integer sessionNumber, Model model) {
        CookingSession session = cookingSessionService.getCookingSessionBySessionNumber(sessionNumber);
        if (session != null) {
            model.addAttribute("session", session);
            return "session-details";
        } else {
            return "redirect:/dashboard?error=session-not-found";
        }
    }

    @GetMapping("/api/temperature/{sessionNumber}")
    @ResponseBody
    public List<Map<String, Object>> getTemperatureData(@PathVariable Integer sessionNumber) {
        List<Temperature> temperatures = temperatureRepository.findBySessionOrderByDatetimeAsc(sessionNumber);

        return temperatures.stream()
            .map(temp -> {
                Map<String, Object> data = new HashMap<>();
                data.put("datetime", temp.getDatetime().toString());
                // Temperature is already in Celsius
                data.put("value", temp.getValue());
                return data;
            })
            .collect(Collectors.toList());
    }

    @GetMapping("/api/motion/{sessionNumber}")
    @ResponseBody
    public List<Map<String, Object>> getMotionData(@PathVariable Integer sessionNumber) {
        List<Motion2> motions = motion2Repository.findBySessionOrderByDatetimeAsc(sessionNumber);

        return motions.stream()
            .map(motion -> {
                Map<String, Object> data = new HashMap<>();
                data.put("datetime", motion.getDatetime().toString());
                data.put("value", motion.getValue());
                return data;
            })
            .collect(Collectors.toList());
    }

    @GetMapping("/api/temperature/{sessionNumber}/closest")
    @ResponseBody
    public Map<String, Object> getClosestTemperature(@PathVariable Integer sessionNumber,
                                                       @org.springframework.web.bind.annotation.RequestParam String datetime) {
        List<Temperature> temperatures = temperatureRepository.findBySessionOrderByDatetimeAsc(sessionNumber);

        if (temperatures.isEmpty()) {
            return Map.of("error", "No temperature data available");
        }

        java.time.LocalDateTime targetTime;
        try {
            targetTime = java.time.LocalDateTime.parse(datetime);
        } catch (Exception e) {
            return Map.of("error", "Invalid datetime format");
        }

        Temperature closestTemp = temperatures.get(0);
        long minDifference = Math.abs(java.time.Duration.between(targetTime, closestTemp.getDatetime()).toSeconds());

        for (Temperature temp : temperatures) {
            long difference = Math.abs(java.time.Duration.between(targetTime, temp.getDatetime()).toSeconds());
            if (difference < minDifference) {
                minDifference = difference;
                closestTemp = temp;
            }
        }

        Map<String, Object> result = new HashMap<>();
        result.put("datetime", closestTemp.getDatetime().toString());
        // Temperature is already in Celsius
        result.put("value", closestTemp.getValue());
        result.put("index", temperatures.indexOf(closestTemp));
        return result;
    }

    @GetMapping("/api/motion/{sessionNumber}/closest")
    @ResponseBody
    public Map<String, Object> getClosestMotion(@PathVariable Integer sessionNumber,
                                                  @org.springframework.web.bind.annotation.RequestParam String datetime) {
        List<Motion2> motions = motion2Repository.findBySessionOrderByDatetimeAsc(sessionNumber);

        if (motions.isEmpty()) {
            return Map.of("error", "No motion data available");
        }

        java.time.LocalDateTime targetTime;
        try {
            targetTime = java.time.LocalDateTime.parse(datetime);
        } catch (Exception e) {
            return Map.of("error", "Invalid datetime format");
        }

        Motion2 closestMotion = motions.get(0);
        long minDifference = Math.abs(java.time.Duration.between(targetTime, closestMotion.getDatetime()).toSeconds());

        for (Motion2 motion : motions) {
            long difference = Math.abs(java.time.Duration.between(targetTime, motion.getDatetime()).toSeconds());
            if (difference < minDifference) {
                minDifference = difference;
                closestMotion = motion;
            }
        }

        Map<String, Object> result = new HashMap<>();
        result.put("datetime", closestMotion.getDatetime().toString());
        result.put("value", closestMotion.getValue());
        return result;
    }
}

