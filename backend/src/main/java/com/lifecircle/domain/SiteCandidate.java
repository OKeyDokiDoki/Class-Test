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

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@DynamicInsert
@DynamicUpdate
@Table(name = "site_candidate")
public class SiteCandidate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "district_id", nullable = false)
    private Long districtId;

    @Column(name = "batch_id")
    private Long batchId;

    @Column(name = "candidate_name", length = 100, nullable = false)
    private String candidateName;

    @Column(name = "business_type", length = 100)
    private String businessType;

    @Column(name = "lng", precision = 10, scale = 6)
    private BigDecimal lng;

    @Column(name = "lat", precision = 10, scale = 6)
    private BigDecimal lat;

    @Column(name = "population_index", precision = 10, scale = 2)
    private BigDecimal populationIndex;

    @Column(name = "competitor_count")
    private Integer competitorCount;

    @Column(name = "demand_level", length = 10)
    private String demandLevel;

    @Column(name = "competition_level", length = 10)
    private String competitionLevel;

    @Column(name = "rent_min", precision = 8, scale = 2)
    private BigDecimal rentMin;

    @Column(name = "rent_max", precision = 8, scale = 2)
    private BigDecimal rentMax;

    @Column(name = "site_score")
    private Integer siteScore;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public SiteCandidate() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getDistrictId() {
        return districtId;
    }

    public void setDistrictId(Long districtId) {
        this.districtId = districtId;
    }

    public Long getBatchId() {
        return batchId;
    }

    public void setBatchId(Long batchId) {
        this.batchId = batchId;
    }

    public String getCandidateName() {
        return candidateName;
    }

    public void setCandidateName(String candidateName) {
        this.candidateName = candidateName;
    }

    public String getBusinessType() {
        return businessType;
    }

    public void setBusinessType(String businessType) {
        this.businessType = businessType;
    }

    public BigDecimal getLng() {
        return lng;
    }

    public void setLng(BigDecimal lng) {
        this.lng = lng;
    }

    public BigDecimal getLat() {
        return lat;
    }

    public void setLat(BigDecimal lat) {
        this.lat = lat;
    }

    public BigDecimal getPopulationIndex() {
        return populationIndex;
    }

    public void setPopulationIndex(BigDecimal populationIndex) {
        this.populationIndex = populationIndex;
    }

    public Integer getCompetitorCount() {
        return competitorCount;
    }

    public void setCompetitorCount(Integer competitorCount) {
        this.competitorCount = competitorCount;
    }

    public String getDemandLevel() {
        return demandLevel;
    }

    public void setDemandLevel(String demandLevel) {
        this.demandLevel = demandLevel;
    }

    public String getCompetitionLevel() {
        return competitionLevel;
    }

    public void setCompetitionLevel(String competitionLevel) {
        this.competitionLevel = competitionLevel;
    }

    public BigDecimal getRentMin() {
        return rentMin;
    }

    public void setRentMin(BigDecimal rentMin) {
        this.rentMin = rentMin;
    }

    public BigDecimal getRentMax() {
        return rentMax;
    }

    public void setRentMax(BigDecimal rentMax) {
        this.rentMax = rentMax;
    }

    public Integer getSiteScore() {
        return siteScore;
    }

    public void setSiteScore(Integer siteScore) {
        this.siteScore = siteScore;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    @PrePersist
    void prePersist() {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
    }

}
