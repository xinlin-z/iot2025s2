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

import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

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

        // Get all unique cooking styles
        List<String> allCookingStyles = cookingSessions.stream()
            .map(CookingSession::getCookingStyle)
            .filter(style -> style != null && !style.isEmpty())
            .distinct()
            .collect(Collectors.toList());

        // Get all unique ingredients
        List<String> allIngredients = cookingSessions.stream()
            .map(CookingSession::getIngredients)
            .filter(ingredients -> ingredients != null && !ingredients.isEmpty())
            .flatMap(ingredients -> {
                // Remove curly braces and split by comma
                String cleaned = ingredients.replace("{", "").replace("}", "");
                return java.util.Arrays.stream(cleaned.split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty());
            })
            .distinct()
            .sorted()
            .collect(Collectors.toList());

        model.addAttribute("cookingSessions", cookingSessions);
        model.addAttribute("sessionImageUrls", sessionImageUrls);
        model.addAttribute("sessionAllImageUrls", sessionAllImageUrls);
        model.addAttribute("totalSessions", totalSessions);
        model.addAttribute("allCookingStyles", allCookingStyles);
        model.addAttribute("allIngredients", allIngredients);
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
                // Convert Fahrenheit to Celsius
                double celsius = (temp.getValue() - 32) * 5.0 / 9.0;
                data.put("value", celsius);
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
        // Convert Fahrenheit to Celsius
        double celsius = (closestTemp.getValue() - 32) * 5.0 / 9.0;
        result.put("value", celsius);
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