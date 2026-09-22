package com.lifecircle.common.utils;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CalcUtilsTests {
    @Test
    void calculatesWeightedScore() {
        double score = CalcUtils.weightedScore(List.of(
            new CalcUtils.WeightedValue(80, 2),
            new CalcUtils.WeightedValue(50, 1)
        ));

        assertThat(score).isEqualTo(70);
    }

    @Test
    void calculatesDemandAndCompetition() {
        assertThat(CalcUtils.demandGap(90, 35)).isEqualTo(55);
        assertThat(CalcUtils.competitionSaturation(5, 10_000)).isEqualTo(5);
    }
}
