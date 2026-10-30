package com.lifecircle.storage;

import org.springframework.context.annotation.*;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.servlet.config.annotation.*;

@Configuration
public class DownloadWebConfiguration implements WebMvcConfigurer {
    private final DownloadCapacity capacity;
    public DownloadWebConfiguration(DownloadCapacity capacity) { this.capacity = capacity; }
    @Bean public ThreadPoolTaskExecutor fileDownloadExecutor() {
        ThreadPoolTaskExecutor pool = new ThreadPoolTaskExecutor();
        pool.setThreadNamePrefix("file-download-");
        pool.setCorePoolSize(capacity.limit()); pool.setMaxPoolSize(capacity.limit() + 2);
        pool.setQueueCapacity(capacity.limit());
        return pool;
    }
    @Override public void configureAsyncSupport(AsyncSupportConfigurer configurer) {
        configurer.setTaskExecutor(fileDownloadExecutor()).setDefaultTimeout(30L * 60 * 1000);
    }
}
