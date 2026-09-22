import { DEFAULT_SCORE_MAX, SCORE_LEVELS } from "../constants/score.js";

export function clamp(value, minimum = 0, maximum = DEFAULT_SCORE_MAX) {
  const number = Number(value);
  if (!Number.isFinite(number)) return minimum;
  return Math.min(Math.max(number, minimum), maximum);
}

export function normalizeScore(value, minimum, maximum) {
  if (maximum <= minimum) return 0;
  return clamp(((Number(value) - minimum) / (maximum - minimum)) * DEFAULT_SCORE_MAX);
}

export function calculateWeightedScore(items) {
  if (!Array.isArray(items) || items.length === 0) return 0;

  const validItems = items.filter(
    (item) => Number.isFinite(Number(item.value)) && Number(item.weight ?? 1) > 0
  );
  const totalWeight = validItems.reduce((sum, item) => sum + Number(item.weight ?? 1), 0);
  if (totalWeight === 0) return 0;

  const total = validItems.reduce(
    (sum, item) => sum + clamp(item.value) * Number(item.weight ?? 1),
    0
  );
  return Math.round((total / totalWeight) * 10) / 10;
}

export function getScoreLevel(value) {
  const score = clamp(value);
  if (score >= SCORE_LEVELS.HIGH.min) return SCORE_LEVELS.HIGH.label;
  if (score >= SCORE_LEVELS.MEDIUM.min) return SCORE_LEVELS.MEDIUM.label;
  return SCORE_LEVELS.LOW.label;
}
