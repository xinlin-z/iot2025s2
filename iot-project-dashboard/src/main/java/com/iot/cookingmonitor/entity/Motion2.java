package com.iot.cookingmonitor.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "motion2")
public class Motion2 {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "session")
    private Integer session;

    @Column(name = "datetime", nullable = false)
    private LocalDateTime datetime;

    @Column(name = "value")
    private Boolean value;

    // Constructors
    public Motion2() {
    }

    public Motion2(Integer session, LocalDateTime datetime, Boolean value) {
        this.session = session;
        this.datetime = datetime;
        this.value = value;
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

    public Boolean getValue() {
        return value;
    }

    public void setValue(Boolean value) {
        this.value = value;
    }
}
