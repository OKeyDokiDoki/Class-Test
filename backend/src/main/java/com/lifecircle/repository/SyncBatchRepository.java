package com.lifecircle.repository;

import com.lifecircle.domain.SyncBatch;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SyncBatchRepository extends JpaRepository<SyncBatch, Long> {
}
