package com.lifecircle.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class PoiSyncJob {
    private static final Logger log = LoggerFactory.getLogger(PoiSyncJob.class);

    @Scheduled(cron = "0 0 3 1,16 * *")
    public void syncPoiIncrementally() {
        log.info("POI incremental sync placeholder started");
    }
}
