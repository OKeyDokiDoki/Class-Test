package com.lifecircle.storage;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.util.Map;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.*;

/** Admission is per request, with no lock around file reads. ZIP shares the same budget. */
@Component
public class DownloadCapacity {
    private final int limit;
    private final Semaphore permits;
    private final AtomicInteger active = new AtomicInteger(), peak = new AtomicInteger();
    private final AtomicLong completed = new AtomicLong(), failed = new AtomicLong(), rejected = new AtomicLong();
    public DownloadCapacity(@Value("${storage.download.max-concurrent:32}") int limit) {
        if (limit < 1 || limit > 128) throw new IllegalArgumentException("Download concurrency must be 1-128");
        this.limit = limit; permits = new Semaphore(limit);
    }
    public int limit() { return limit; }
    public Lease acquire() {
        if (!permits.tryAcquire()) { rejected.incrementAndGet(); return null; }
        int count = active.incrementAndGet(); peak.accumulateAndGet(count, Math::max);
        return new Lease();
    }
    public Map<String,Object> snapshot() {
        return Map.of("active", active.get(), "maxConcurrent", limit, "peakActive", peak.get(),
            "completed", completed.get(), "failed", failed.get(), "rejected", rejected.get());
    }
    public final class Lease {
        private final AtomicBoolean released = new AtomicBoolean();
        public void release(boolean success) {
            if (released.compareAndSet(false, true)) {
                if (success) completed.incrementAndGet(); else failed.incrementAndGet();
                active.decrementAndGet(); permits.release();
            }
        }
    }
}
