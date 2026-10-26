package com.lifecircle.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "merchant_intent")
public class MerchantIntent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String merchantName;

    @Column(nullable = false, length = 100)
    private String businessType;

    @Column(nullable = false, length = 100)
    private String contact;

    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    protected MerchantIntent() {
    }

    public MerchantIntent(String merchantName, String businessType, String contact) {
        this.merchantName = merchantName;
        this.businessType = businessType;
        this.contact = contact;
        this.createdAt = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public String getMerchantName() {
        return merchantName;
    }

    public String getBusinessType() {
        return businessType;
    }

    public String getContact() {
        return contact;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
