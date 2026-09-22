import test from "node:test";
import assert from "node:assert/strict";
import { calculateDistanceMeters, estimateWalkingRadius } from "./geo.js";
import { calculateWeightedScore, getScoreLevel, normalizeScore } from "./score.js";
import { validateMerchantIntent } from "./validate.js";

test("calculates weighted scores", () => {
  assert.equal(
    calculateWeightedScore([
      { value: 80, weight: 2 },
      { value: 50, weight: 1 }
    ]),
    70
  );
  assert.equal(normalizeScore(50, 0, 200), 25);
  assert.equal(getScoreLevel(85), "高");
});

test("calculates walking radius and geographic distance", () => {
  assert.equal(estimateWalkingRadius(15), 1080);
  assert.ok(
    calculateDistanceMeters(
      { latitude: 30.657, longitude: 104.066 },
      { latitude: 30.658, longitude: 104.066 }
    ) > 100
  );
});

test("validates merchant intent", () => {
  assert.equal(
    validateMerchantIntent({
      merchantName: "邻里店",
      businessType: "便利店",
      contact: "13800138000"
    }).isValid,
    true
  );
  assert.equal(validateMerchantIntent({}).isValid, false);
});
