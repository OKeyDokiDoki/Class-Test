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

@Entity
@DynamicInsert
@DynamicUpdate
@Table(name = "assessment_facility_stat")
public class AssessmentFacilityStat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "assessment_id", nullable = false)
    private Long assessmentId;

    @Column(name = "category_id", nullable = false)
    private Long categoryId;

    @Column(name = "facility_count", nullable = false)
    private Integer facilityCount;

    @Column(name = "nearest_distance_m", precision = 10, scale = 2)
    private BigDecimal nearestDistanceM;

    @Column(name = "status", length = 20)
    private String status;

    public AssessmentFacilityStat() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getAssessmentId() {
        return assessmentId;
    }

    public void setAssessmentId(Long assessmentId) {
        this.assessmentId = assessmentId;
    }

    public Long getCategoryId() {
        return categoryId;
    }

    public void setCategoryId(Long categoryId) {
        this.categoryId = categoryId;
    }

    public Integer getFacilityCount() {
        return facilityCount;
    }

    public void setFacilityCount(Integer facilityCount) {
        this.facilityCount = facilityCount;
    }

    public BigDecimal getNearestDistanceM() {
        return nearestDistanceM;
    }

    public void setNearestDistanceM(BigDecimal nearestDistanceM) {
        this.nearestDistanceM = nearestDistanceM;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

}
