package com.lifecircle.common.utils;

import java.util.List;

public final class CalcUtils {
    private CalcUtils() {
    }

    public static double clamp(double value, double minimum, double maximum) {
        return Math.min(Math.max(value, minimum), maximum);
    }

    public static double normalize(double value, double minimum, double maximum) {
        if (maximum <= minimum) {
            return 0;
        }
        return clamp((value - minimum) / (maximum - minimum) * 100, 0, 100);
    }

    public static double weightedScore(List<WeightedValue> values) {
        if (values == null || values.isEmpty()) {
            return 0;
        }

        double totalWeight = values.stream()
            .filter(value -> value.weight() > 0)
            .mapToDouble(WeightedValue::weight)
            .sum();
        if (totalWeight == 0) {
            return 0;
        }

        double total = values.stream()
            .filter(value -> value.weight() > 0)
            .mapToDouble(value -> clamp(value.value(), 0, 100) * value.weight())
            .sum();
        return Math.round(total / totalWeight * 10) / 10.0;
    }

    public static double demandGap(double demandIndex, double supplyIndex) {
        return clamp(demandIndex - supplyIndex, 0, 100);
    }

    public static double competitionSaturation(int competitorCount, int residentCount) {
        if (competitorCount <= 0 || residentCount <= 0) {
            return 0;
        }
        return Math.round(clamp(competitorCount * 1000.0 / residentCount * 10, 0, 100) * 10) / 10.0;
    }

    public record WeightedValue(double value, double weight) {
    }
}
