package com.iot.cookingmonitor.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "cooking_sessions")
public class CookingSession {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "session_number", nullable = false, unique = true)
    private Integer sessionNumber;

    @Column(name = "date_time", nullable = false)
    private LocalDateTime dateTime;

    @Column(name = "cooking_style", nullable = false)
    private String cookingStyle;

    @Column(name = "ingredients", columnDefinition = "TEXT")
    private String ingredients;

    @Column(name = "dish_description", columnDefinition = "TEXT")
    private String dishDescription;

    @Column(name = "thumbnail_image_path")
    private String thumbnailImagePath;

    @Column(name = "duration_minutes")
    private Integer durationMinutes;

    @Column(name = "temperature_avg")
    private Double temperatureAvg;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Transient
    private String imageUrl;

    // Constructors
    public CookingSession() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public CookingSession(Integer sessionNumber, LocalDateTime dateTime, String cookingStyle,
                         String ingredients, String dishDescription, String thumbnailImagePath) {
        this();
        this.sessionNumber = sessionNumber;
        this.dateTime = dateTime;
        this.cookingStyle = cookingStyle;
        this.ingredients = ingredients;
        this.dishDescription = dishDescription;
        this.thumbnailImagePath = thumbnailImagePath;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Integer getSessionNumber() {
        return sessionNumber;
    }

    public void setSessionNumber(Integer sessionNumber) {
        this.sessionNumber = sessionNumber;
    }

    public LocalDateTime getDateTime() {
        return dateTime;
    }

    public void setDateTime(LocalDateTime dateTime) {
        this.dateTime = dateTime;
    }

    public String getCookingStyle() {
        return cookingStyle;
    }

    public void setCookingStyle(String cookingStyle) {
        this.cookingStyle = cookingStyle;
    }

    public String getIngredients() {
        return ingredients;
    }

    public void setIngredients(String ingredients) {
        this.ingredients = ingredients;
    }

    public String getDishDescription() {
        return dishDescription;
    }

    public void setDishDescription(String dishDescription) {
        this.dishDescription = dishDescription;
    }

    public String getThumbnailImagePath() {
        return thumbnailImagePath;
    }

    public void setThumbnailImagePath(String thumbnailImagePath) {
        this.thumbnailImagePath = thumbnailImagePath;
    }

    public Integer getDurationMinutes() {
        return durationMinutes;
    }

    public void setDurationMinutes(Integer durationMinutes) {
        this.durationMinutes = durationMinutes;
    }

    public Double getTemperatureAvg() {
        return temperatureAvg;
    }

    public void setTemperatureAvg(Double temperatureAvg) {
        this.temperatureAvg = temperatureAvg;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}