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
@Table(name = "road_segment")
public class RoadSegment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "segment_code", length = 50, nullable = false)
    private String segmentCode;

    @Column(name = "district_id")
    private Long districtId;

    @Column(name = "from_node_id", nullable = false)
    private Long fromNodeId;

    @Column(name = "to_node_id", nullable = false)
    private Long toNodeId;

    @Column(name = "road_name", length = 100)
    private String roadName;

    @Column(name = "road_level", length = 20, nullable = false)
    private String roadLevel;

    @Column(name = "length_m", precision = 10, scale = 2, nullable = false)
    private BigDecimal lengthM;

    @Column(name = "walk_time_s", nullable = false)
    private Integer walkTimeS;

    @Column(name = "is_walkable", length = 1, nullable = false)
    private String isWalkable;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    public RoadSegment() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSegmentCode() {
        return segmentCode;
    }

    public void setSegmentCode(String segmentCode) {
        this.segmentCode = segmentCode;
    }

    public Long getDistrictId() {
        return districtId;
    }

    public void setDistrictId(Long districtId) {
        this.districtId = districtId;
    }

    public Long getFromNodeId() {
        return fromNodeId;
    }

    public void setFromNodeId(Long fromNodeId) {
        this.fromNodeId = fromNodeId;
    }

    public Long getToNodeId() {
        return toNodeId;
    }

    public void setToNodeId(Long toNodeId) {
        this.toNodeId = toNodeId;
    }

    public String getRoadName() {
        return roadName;
    }

    public void setRoadName(String roadName) {
        this.roadName = roadName;
    }

    public String getRoadLevel() {
        return roadLevel;
    }

    public void setRoadLevel(String roadLevel) {
        this.roadLevel = roadLevel;
    }

    public BigDecimal getLengthM() {
        return lengthM;
    }

    public void setLengthM(BigDecimal lengthM) {
        this.lengthM = lengthM;
    }

    public Integer getWalkTimeS() {
        return walkTimeS;
    }

    public void setWalkTimeS(Integer walkTimeS) {
        this.walkTimeS = walkTimeS;
    }

    public String getIsWalkable() {
        return isWalkable;
    }

    public void setIsWalkable(String isWalkable) {
        this.isWalkable = isWalkable;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    @PrePersist
    void prePersist() {
        if (updatedAt == null) {
            updatedAt = Instant.now();
        }
    }

}
