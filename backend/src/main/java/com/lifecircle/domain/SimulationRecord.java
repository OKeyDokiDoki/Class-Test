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
@Table(name = "simulation_record")
public class SimulationRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "district_id", nullable = false)
    private Long districtId;

    @Column(name = "category_id", nullable = false)
    private Long categoryId;

    @Column(name = "business_type", length = 100)
    private String businessType;

    @Column(name = "lng", precision = 10, scale = 6)
    private BigDecimal lng;

    @Column(name = "lat", precision = 10, scale = 6)
    private BigDecimal lat;

    @Column(name = "before_coverage", nullable = false)
    private Integer beforeCoverage;

    @Column(name = "after_coverage", nullable = false)
    private Integer afterCoverage;

    @Column(name = "benefited_residents", nullable = false)
    private Integer benefitedResidents;

    @Column(name = "operator", length = 50)
    private String operator;

    @Column(name = "simulated_at", nullable = false)
    private Instant simulatedAt;

    public SimulationRecord() {
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

    public Long getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(Long categoryId) {
        this.categoryId = categoryId;
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

    public Integer getBeforeCoverage() {
        return beforeCoverage;
    }

    public void setBeforeCoverage(Integer beforeCoverage) {
        this.beforeCoverage = beforeCoverage;
    }

    public Integer getAfterCoverage() {
        return afterCoverage;
    }

    public void setAfterCoverage(Integer afterCoverage) {
        this.afterCoverage = afterCoverage;
    }

    public Integer getBenefitedResidents() {
        return benefitedResidents;
    }

    public void setBenefitedResidents(Integer benefitedResidents) {
        this.benefitedResidents = benefitedResidents;
    }

    public String getOperator() {
        return operator;
    }

    public void setOperator(String operator) {
        this.operator = operator;
    }

    public Instant getSimulatedAt() {
        return simulatedAt;
    }

    public void setSimulatedAt(Instant simulatedAt) {
        this.simulatedAt = simulatedAt;
    }

}
