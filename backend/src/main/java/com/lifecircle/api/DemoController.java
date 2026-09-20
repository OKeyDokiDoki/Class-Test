package com.lifecircle.api;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class DemoController {
    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "UP", "time", Instant.now(), "mode", "demo");
    }

    @GetMapping("/resident/assessment")
    public Map<String, Object> residentAssessment() {
        return Map.of(
            "score", 82, "label", "青年通勤型", "district", "朝阳社区示范片区",
            "dimensions", List.of(
                Map.of("name", "生鲜购物", "value", 92), Map.of("name", "医疗健康", "value", 68),
                Map.of("name", "亲子教育", "value", 76), Map.of("name", "交通通勤", "value", 89),
                Map.of("name", "夜间服务", "value", 84)),
            "facilities", List.of(
                Map.of("name", "社区生鲜店", "count", 8, "status", "充足"),
                Map.of("name", "社区诊所", "count", 2, "status", "待改善"),
                Map.of("name", "托育机构", "count", 3, "status", "基本满足"),
                Map.of("name", "夜间药店", "count", 4, "status", "充足")),
            "insight", "日常购物与通勤便利，夜间医疗资源相对不足，建议关注东南侧社区卫生服务点。");
    }

    @GetMapping("/merchant/recommendations")
    public Map<String, Object> merchantRecommendations() {
        return Map.of("profile", "稳健型商户", "recommendations", List.of(
            Map.of("name", "东园路口", "score", 91, "demand", "高", "competition", "低", "rent", "6-8 万/年", "type", "早餐与便利店"),
            Map.of("name", "文体中心西侧", "score", 86, "demand", "中高", "competition", "低", "rent", "8-10 万/年", "type", "亲子托育"),
            Map.of("name", "康宁小区南门", "score", 79, "demand", "高", "competition", "中", "rent", "7-9 万/年", "type", "药店与健康服务")));
    }

    @ResponseStatus(HttpStatus.CREATED)
    @PostMapping("/merchant/intents")
    public Map<String, Object> createIntent(@Valid @RequestBody MerchantIntent request) {
        return Map.of("id", System.currentTimeMillis(), "status", "submitted", "merchantName", request.merchantName());
    }

    @GetMapping("/community/overview")
    public Map<String, Object> communityOverview() {
        return Map.of(
            "coverage", 78, "residents", 12680, "intents", 18,
            "gaps", List.of(
                Map.of("area", "东南片区", "issue", "夜间就医距离较远", "level", "高"),
                Map.of("area", "北部新居", "issue", "生鲜网点承载不足", "level", "中"),
                Map.of("area", "文体中心周边", "issue", "托育服务供给不足", "level", "中")),
            "matches", List.of(
                Map.of("merchant", "安心社区药房", "area", "东南片区", "fit", 94),
                Map.of("merchant", "邻家鲜生", "area", "北部新居", "fit", 89),
                Map.of("merchant", "小芽托育", "area", "文体中心周边", "fit", 87)));
    }

    @PostMapping("/community/simulations")
    public Map<String, Object> simulate(@RequestBody Map<String, Object> request) {
        return Map.of("beforeCoverage", 78, "afterCoverage", 86, "benefitedResidents", 2140);
    }

    public record MerchantIntent(@NotBlank String merchantName, @NotBlank String businessType, @NotBlank String contact) {}
}
