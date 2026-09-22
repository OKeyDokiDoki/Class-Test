package com.lifecircle.common.result;

public enum ResultCode {
    SUCCESS("0", "成功"),
    PARAM_ERROR("400", "请求参数错误"),
    BUSINESS_ERROR("BIZ_ERROR", "业务处理失败"),
    UNKNOWN_ERROR("500", "系统内部错误");

    private final String code;
    private final String message;

    ResultCode(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public String code() {
        return code;
    }

    public String message() {
        return message;
    }
}
