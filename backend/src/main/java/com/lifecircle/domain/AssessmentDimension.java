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
@Table(name = "assessment_dimension")
public class AssessmentDimension {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "assessment_id", nullable = false)
    private Long assessmentId;

    @Column(name = "dimension_code", length = 30, nullable = false)
    private String dimensionCode;

    @Column(name = "dimension_name", length = 50, nullable = false)
    private String dimensionName;

    @Column(name = "dimension_score", nullable = false)
    private Integer dimensionScore;

    @Column(name = "weight", precision = 5, scale = 2, nullable = false)
    private BigDecimal weight;

    @Column(name = "facility_count", nullable = false)
    private Integer facilityCount;

    public AssessmentDimension() {
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

    public String getDimensionCode() {
        return dimensionCode;
    }

    public void setDimensionCode(String dimensionCode) {
        this.dimensionCode = dimensionCode;
    }

    public String getDimensionName() {
        return dimensionName;
    }

    public void setDimensionName(String dimensionName) {
        this.dimensionName = dimensionName;
    }

    public Integer getDimensionScore() {
        return dimensionScore;
    }

    public void setDimensionScore(Integer dimensionScore) {
        this.dimensionScore = dimensionScore;
    }

    public BigDecimal getWeight() {
        return weight;
    }

    public void setWeight(BigDecimal weight) {
        this.weight = weight;
    }

    public Integer getFacilityCount() {
        return facilityCount;
    }

    public void setFacilityCount(Integer facilityCount) {
        this.facilityCount = facilityCount;
    }

}
