package com.lifecircle.common.result;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ResultTests {
    @Test
    void createsSuccessResult() {
        Result<String> result = Result.ok("data");

        assertThat(result.code()).isEqualTo("0");
        assertThat(result.message()).isEqualTo("成功");
        assertThat(result.data()).isEqualTo("data");
    }
}
