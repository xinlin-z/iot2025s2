package com.iot.cookingmonitor.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "image2")
public class Image2 {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "session")
    private Integer session;

    @Column(name = "datetime")
    private LocalDateTime datetime;

    @Column(name = "ingredient")
    private String ingredient;

    @Column(name = "style")
    private String style;

    @Column(name = "description")
    private String description;

    // Constructors
    public Image2() {}

    public Image2(Integer session, LocalDateTime datetime, String ingredient, String style, String description) {
        this.session = session;
        this.datetime = datetime;
        this.ingredient = ingredient;
        this.style = style;
        this.description = description;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Integer getSession() {
        return session;
    }

    public void setSession(Integer session) {
        this.session = session;
    }

    public LocalDateTime getDatetime() {
        return datetime;
    }

    public void setDatetime(LocalDateTime datetime) {
        this.datetime = datetime;
    }

    public String getIngredient() {
        return ingredient;
    }

    public void setIngredient(String ingredient) {
        this.ingredient = ingredient;
    }

    public String getStyle() {
        return style;
    }

    public void setStyle(String style) {
        this.style = style;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    // Convert to CookingSession for compatibility with existing UI
    public CookingSession toCookingSession() {
        CookingSession cookingSession = new CookingSession();
        cookingSession.setSessionNumber(this.session);
        cookingSession.setDateTime(this.datetime);
        cookingSession.setCookingStyle(this.style != null ? this.style : "Unknown");
        cookingSession.setIngredients(this.ingredient != null ? this.ingredient : "Not specified");
        cookingSession.setDishDescription(this.description != null ? this.description : "No description");
        cookingSession.setThumbnailImagePath("/images/placeholder-cooking.jpg");
        return cookingSession;
    }
}