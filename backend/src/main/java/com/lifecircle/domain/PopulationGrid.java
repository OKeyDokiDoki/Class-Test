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
import java.time.LocalDate;

@Entity
@DynamicInsert
@DynamicUpdate
@Table(name = "population_grid")
public class PopulationGrid {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "district_id", nullable = false)
    private Long districtId;

    @Column(name = "grid_code", length = 40, nullable = false)
    private String gridCode;

    @Column(name = "grid_level", length = 20, nullable = false)
    private String gridLevel;

    @Column(name = "center_lng", precision = 10, scale = 6, nullable = false)
    private BigDecimal centerLng;

    @Column(name = "center_lat", precision = 10, scale = 6, nullable = false)
    private BigDecimal centerLat;

    @Column(name = "population", nullable = false)
    private Integer population;

    @Column(name = "density", precision = 12, scale = 2)
    private BigDecimal density;

    @Column(name = "data_date", nullable = false)
    private LocalDate dataDate;

    @Column(name = "source", length = 20, nullable = false)
    private String source;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public PopulationGrid() {
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

    public String getGridCode() {
        return gridCode;
    }

    public void setGridCode(String gridCode) {
        this.gridCode = gridCode;
    }

    public String getGridLevel() {
        return gridLevel;
    }

    public void setGridLevel(String gridLevel) {
        this.gridLevel = gridLevel;
    }

    public BigDecimal getCenterLng() {
        return centerLng;
    }

    public void setCenterLng(BigDecimal centerLng) {
        this.centerLng = centerLng;
    }

    public BigDecimal getCenterLat() {
        return centerLat;
    }

    public void setCenterLat(BigDecimal centerLat) {
        this.centerLat = centerLat;
    }

    public Integer getPopulation() {
        return population;
    }

    public void setPopulation(Integer population) {
        this.population = population;
    }

    public BigDecimal getDensity() {
        return density;
    }

    public void setDensity(BigDecimal density) {
        this.density = density;
    }

    public LocalDate getDataDate() {
        return dataDate;
    }

    public void setDataDate(LocalDate dataDate) {
        this.dataDate = dataDate;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
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
