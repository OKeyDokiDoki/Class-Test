package com.lifecircle.repository;

import com.lifecircle.domain.PoiChangeLog;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PoiChangeLogRepository extends JpaRepository<PoiChangeLog, Long> {
}
