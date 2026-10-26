package com.lifecircle.repository;

import com.lifecircle.domain.SiteScoreItem;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SiteScoreItemRepository extends JpaRepository<SiteScoreItem, Long> {
}
