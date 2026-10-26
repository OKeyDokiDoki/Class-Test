package com.lifecircle.repository;

import com.lifecircle.domain.SiteCandidate;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SiteCandidateRepository extends JpaRepository<SiteCandidate, Long> {
}
