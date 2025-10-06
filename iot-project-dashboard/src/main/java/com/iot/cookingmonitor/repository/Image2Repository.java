package com.iot.cookingmonitor.repository;

import com.iot.cookingmonitor.entity.Image2;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface Image2Repository extends JpaRepository<Image2, Long> {

    // Find by session number
    Optional<Image2> findBySession(Integer session);

    // Get all records ordered by datetime descending (most recent first)
    List<Image2> findAllByOrderByDatetimeDesc();

    // Get all records ordered by session number descending
    List<Image2> findAllByOrderBySessionDesc();

    // Custom query to get distinct sessions for dashboard
    @Query("SELECT DISTINCT i FROM Image2 i ORDER BY i.session DESC")
    List<Image2> findDistinctSessions();
}