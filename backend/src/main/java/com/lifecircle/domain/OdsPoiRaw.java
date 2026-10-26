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
@Table(name = "ods_poi_raw")
public class OdsPoiRaw {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "batch_id", nullable = false)
    private Long batchId;

    @Column(name = "source", length = 20, nullable = false)
    private String source;

    @Column(name = "source_poi_id", length = 100, nullable = false)
    private String sourcePoiId;

    @Column(name = "poi_name", length = 200)
    private String poiName;

    @Column(name = "lng", precision = 10, scale = 6)
    private BigDecimal lng;

    @Column(name = "lat", precision = 10, scale = 6)
    private BigDecimal lat;

    @Column(name = "category_raw", length = 100)
    private String categoryRaw;

    @Column(name = "address", length = 255)
    private String address;

    @Column(name = "raw_json", nullable = false)
    private String rawJson;

    @Column(name = "load_at", nullable = false)
    private Instant loadAt;

    @Column(name = "process_status", length = 20, nullable = false)
    private String processStatus;

    public OdsPoiRaw() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getBatchId() {
        return batchId;
    }

    public void setBatchId(Long batchId) {
        this.batchId = batchId;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getSourcePoiId() {
        return sourcePoiId;
    }

    public void setSourcePoiId(String sourcePoiId) {
        this.sourcePoiId = sourcePoiId;
    }

    public String getPoiName() {
        return poiName;
    }

    public void setPoiName(String poiName) {
        this.poiName = poiName;
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

    public String getCategoryRaw() {
        return categoryRaw;
    }

    public void setCategoryRaw(String categoryRaw) {
        this.categoryRaw = categoryRaw;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getRawJson() {
        return rawJson;
    }

    public void setRawJson(String rawJson) {
        this.rawJson = rawJson;
    }

    public Instant getLoadAt() {
        return loadAt;
    }

    public void setLoadAt(Instant loadAt) {
        this.loadAt = loadAt;
    }

    public String getProcessStatus() {
        return processStatus;
    }

    public void setProcessStatus(String processStatus) {
        this.processStatus = processStatus;
    }

}
