package com.lifecircle.storage;

import com.lifecircle.common.result.Result;
import org.springframework.core.annotation.Order;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.server.ResponseStatusException;

@Order(-10)
@RestControllerAdvice(assignableTypes = LocalFileController.class)
public class LocalFileExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<Result<Void>> status(ResponseStatusException e) {
        return ResponseEntity.status(e.getStatusCode()).body(Result.fail("FILE_ERROR", e.getReason()));
    }
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Result<Void>> tooLarge(MaxUploadSizeExceededException e) {
        return ResponseEntity.status(413).body(Result.fail("FILE_TOO_LARGE", "File exceeds upload limit"));
    }
}
