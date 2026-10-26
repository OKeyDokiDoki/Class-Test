package com.lifecircle.repository;

import com.lifecircle.domain.SimulationRecord;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SimulationRecordRepository extends JpaRepository<SimulationRecord, Long> {
}
