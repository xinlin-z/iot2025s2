package com.iot.cookingmonitor.repository;

import com.iot.cookingmonitor.entity.Motion2;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface Motion2Repository extends JpaRepository<Motion2, Long> {
    List<Motion2> findBySessionOrderByDatetimeAsc(Integer session);
}
