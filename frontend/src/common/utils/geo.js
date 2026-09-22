const EARTH_RADIUS_METERS = 6_371_000;
const DEFAULT_WALKING_SPEED = 1.2;

function toRadians(value) {
  return (value * Math.PI) / 180;
}

export function estimateWalkingRadius(minutes, metersPerSecond = DEFAULT_WALKING_SPEED) {
  const duration = Math.max(0, Number(minutes) || 0);
  const speed = Math.max(0, Number(metersPerSecond) || 0);
  return Math.round(duration * 60 * speed);
}

export function calculateDistanceMeters(origin, destination) {
  if (!origin || !destination) return 0;

  const lat1 = toRadians(Number(origin.latitude));
  const lat2 = toRadians(Number(destination.latitude));
  const deltaLat = lat2 - lat1;
  const deltaLng = toRadians(Number(destination.longitude) - Number(origin.longitude));
  if (![lat1, lat2, deltaLat, deltaLng].every(Number.isFinite)) return 0;

  const haversine =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLng / 2) ** 2;
  return Math.round(2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(haversine)));
}
