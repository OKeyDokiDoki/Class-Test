package com.lifecircle.storage;

import com.lifecircle.common.result.Result;
import org.springframework.core.annotation.Order;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;
import org.springframework.http.converter.HttpMessageNotReadableException;
import java.io.IOException;

@Order(-10)
@RestControllerAdvice(assignableTypes = LocalFileController.class)
public class LocalFileExceptionHandler {
    @ExceptionHandler(ChunkRepairException.class)
    public ResponseEntity<Result<java.util.Map<String,Object>>> repair(ChunkRepairException e) {
        return ResponseEntity.status(e.getStatusCode()).body(new Result<>(e.code(), e.getReason(),
            java.util.Map.of("indexes", e.indexes(), "retryable", true)));
    }
    @ExceptionHandler(org.springframework.core.task.TaskRejectedException.class)
    public ResponseEntity<Result<Void>> busy(org.springframework.core.task.TaskRejectedException e) {
        return ResponseEntity.status(503).header("Retry-After", "2")
            .body(Result.fail("DOWNLOAD_BUSY", "Download workers are busy; retry later"));
    }
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Result<Void>> status(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode()).body(Result.fail("FILE_ERROR", e.getReason()));
    }
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Result<Void>> tooLarge(MaxUploadSizeExceededException e) {
        return ResponseEntity.status(413).body(Result.fail("FILE_TOO_LARGE", "File exceeds upload limit"));
    }
    @ExceptionHandler({MissingServletRequestParameterException.class, MissingServletRequestPartException.class, HttpMessageNotReadableException.class})
    public ResponseEntity<Result<Void>> invalid(Exception e) {
        return ResponseEntity.badRequest().body(Result.fail("FILE_PARAMETER_ERROR", "Check request fields and JSON"));
    }
    @ExceptionHandler(IOException.class)
    public ResponseEntity<Result<Void>> storage(IOException e) {
        return ResponseEntity.status(503).body(Result.fail("STORAGE_UNAVAILABLE", "Storage operation failed; check server logs and connection"));
    }
}
