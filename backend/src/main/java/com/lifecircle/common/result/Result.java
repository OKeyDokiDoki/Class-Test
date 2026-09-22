package com.lifecircle.common.result;

public record Result<T>(String code, String message, T data) {
    public static <T> Result<T> ok(T data) {
        return of(ResultCode.SUCCESS, data);
    }

    public static Result<Void> ok() {
        return of(ResultCode.SUCCESS, null);
    }

    public static <T> Result<T> fail(ResultCode resultCode) {
        return of(resultCode, null);
    }

    public static <T> Result<T> fail(String code, String message) {
        return new Result<>(code, message, null);
    }

    public static <T> Result<T> of(ResultCode resultCode, T data) {
        return new Result<>(resultCode.code(), resultCode.message(), data);
    }
}
