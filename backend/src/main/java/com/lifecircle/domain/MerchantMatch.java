package com.lifecircle.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import org.hibernate.annotations.DynamicInsert;
import org.hibernate.annotations.DynamicUpdate;

import java.time.Instant;

@Entity
@DynamicInsert
@DynamicUpdate
@Table(name = "merchant_match")
public class MerchantMatch {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "intent_id", nullable = false)
    private Long intentId;

    @Column(name = "district_id", nullable = false)
    private Long districtId;

    @Column(name = "gap_id")
    private Long gapId;

    @Column(name = "fit_score", nullable = false)
    private Integer fitScore;

    @Column(name = "match_reason", length = 500)
    private String matchReason;

    @Column(name = "status", length = 20, nullable = false)
    private String status;

    @Column(name = "matched_at", nullable = false)
    private Instant matchedAt;

    public MerchantMatch() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getIntentId() {
        return intentId;
    }

    public void setIntentId(Long intentId) {
        this.intentId = intentId;
    }

    public Long getDistrictId() {
        return districtId;
    }

    public void setDistrictId(Long districtId) {
        this.districtId = districtId;
    }

    public Long getGapId() {
        return gapId;
    }

    public void setGapId(Long gapId) {
        this.gapId = gapId;
    }

    public Integer getFitScore() {
        return fitScore;
    }

    public void setFitScore(Integer fitScore) {
        this.fitScore = fitScore;
    }

    public String getMatchReason() {
        return matchReason;
    }

    public void setMatchReason(String matchReason) {
        this.matchReason = matchReason;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Instant getMatchedAt() {
        return matchedAt;
    }

    public void setMatchedAt(Instant matchedAt) {
        this.matchedAt = matchedAt;
    }

}
