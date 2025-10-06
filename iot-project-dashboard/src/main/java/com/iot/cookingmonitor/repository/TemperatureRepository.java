package com.iot.cookingmonitor.repository;

import com.iot.cookingmonitor.entity.Temperature;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TemperatureRepository extends JpaRepository<Temperature, Long> {
    List<Temperature> findBySessionOrderByDatetimeAsc(Integer session);
}