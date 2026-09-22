package com.lifecircle.common.exception;

import com.lifecircle.common.result.ResultCode;

public class BusinessException extends RuntimeException {
    private final String code;

    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
    }

    public BusinessException(ResultCode resultCode) {
        this(resultCode.code(), resultCode.message());
    }

    public String getCode() {
        return code;
    }
}
