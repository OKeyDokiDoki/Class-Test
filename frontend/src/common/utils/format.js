export function formatNumber(value, locale = "zh-CN") {
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString(locale) : "--";
}

export function formatScore(value, maximum = 100) {
  const score = Number(value);
  return Number.isFinite(score) ? `${Math.round(score)} / ${maximum}` : `-- / ${maximum}`;
}

export function formatRentRange(minimum, maximum, unit = "万/年") {
  const min = Number(minimum);
  const max = Number(maximum);
  if (!Number.isFinite(min) || !Number.isFinite(max) || min > max) return "--";
  return `${min}-${max} ${unit}`;
}
