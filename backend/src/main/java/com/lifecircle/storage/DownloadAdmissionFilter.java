package com.lifecircle.storage;

import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;

/** A lease survives the servlet thread: release only after streaming ends or fails. */
@Component
public class DownloadAdmissionFilter extends OncePerRequestFilter {
    private final DownloadCapacity capacity;
    public DownloadAdmissionFilter(DownloadCapacity capacity) { this.capacity = capacity; }
    @Override protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI().substring(request.getContextPath().length());
        return !(path.matches("/api/files/[^/]+/download") || path.equals("/api/files/batch-download"));
    }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        DownloadCapacity.Lease lease = capacity.acquire();
        if (lease == null) {
            response.setStatus(429); response.setHeader("Retry-After", "2");
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":\"DOWNLOAD_BUSY\",\"message\":\"Download capacity reached; retry later\",\"data\":null}");
            return;
        }
        try { chain.doFilter(request, response); }
        finally {
            if (request.isAsyncStarted()) {
                try {
                    request.getAsyncContext().addListener(new AsyncListener() {
                        public void onComplete(AsyncEvent e) { lease.release(response.getStatus() < 400); }
                        public void onTimeout(AsyncEvent e) { lease.release(false); }
                        public void onError(AsyncEvent e) { lease.release(false); }
                        public void onStartAsync(AsyncEvent e) { e.getAsyncContext().addListener(this); }
                    });
                } catch (IllegalStateException alreadyCompleted) { lease.release(response.getStatus() < 400); }
            } else { lease.release(response.getStatus() < 400); }
        }
    }
}
