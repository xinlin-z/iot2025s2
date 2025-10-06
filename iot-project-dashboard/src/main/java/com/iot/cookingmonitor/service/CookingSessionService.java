package com.iot.cookingmonitor.service;

import com.iot.cookingmonitor.entity.CookingSession;
import com.iot.cookingmonitor.entity.Image2;
import com.iot.cookingmonitor.repository.Image2Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class CookingSessionService {

    @Autowired
    private Image2Repository image2Repository;

    public List<CookingSession> getAllCookingSessions() {
        try {
            // Get all records from the image2 table ordered by session number descending
            List<Image2> image2Records = image2Repository.findAllByOrderBySessionDesc();

            // Convert Image2 entities to CookingSession entities
            return image2Records.stream()
                    .map(Image2::toCookingSession)
                    .collect(Collectors.toList());
        } catch (Exception e) {
            // Log the error and return empty list if database connection fails
            System.err.println("Error fetching data from database: " + e.getMessage());
            e.printStackTrace();
            return List.of(); // Return empty list instead of sample data
        }
    }

    public CookingSession getCookingSessionById(Long id) {
        try {
            return image2Repository.findById(id)
                    .map(Image2::toCookingSession)
                    .orElse(null);
        } catch (Exception e) {
            System.err.println("Error fetching session by ID: " + e.getMessage());
            return null;
        }
    }

    public CookingSession getCookingSessionBySessionNumber(Integer sessionNumber) {
        try {
            return image2Repository.findBySession(sessionNumber)
                    .map(Image2::toCookingSession)
                    .orElse(null);
        } catch (Exception e) {
            System.err.println("Error fetching session by number: " + e.getMessage());
            return null;
        }
    }
}