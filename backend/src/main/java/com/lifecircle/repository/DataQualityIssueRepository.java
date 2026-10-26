package com.lifecircle.repository;

import com.lifecircle.domain.DataQualityIssue;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DataQualityIssueRepository extends JpaRepository<DataQualityIssue, Long> {
}
