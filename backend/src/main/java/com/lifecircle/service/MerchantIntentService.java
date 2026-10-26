package com.lifecircle.service;

import com.lifecircle.domain.MerchantIntent;
import com.lifecircle.repository.MerchantIntentRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class MerchantIntentService {
    private final MerchantIntentRepository repository;

    public MerchantIntentService(MerchantIntentRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public MerchantIntent create(String merchantName, String businessType, String contact) {
        MerchantIntent intent = new MerchantIntent();
        intent.setMerchantName(merchantName);
        intent.setBusinessType(businessType);
        intent.setContact(contact);
        return repository.save(intent);
    }

    @Transactional(readOnly = true)
    public List<MerchantIntent> findAll() {
        return repository.findAll(Sort.by(Sort.Direction.DESC, "createdAt"));
    }
}
