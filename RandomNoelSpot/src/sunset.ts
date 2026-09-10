import type { SunsetSpot } from "./spots";

export type Position = { latitude: number; longitude: number };

const toRad = (value: number) => value * Math.PI / 180;
const toDeg = (value: number) => value * 180 / Math.PI;

export function distanceKm(a: Position, b: Position) {
  const earth = 6371;
  const dLat = toRad(b.latitude - a.latitude);
  const dLon = toRad(b.longitude - a.longitude);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.latitude)) * Math.cos(toRad(b.latitude)) * Math.sin(dLon / 2) ** 2;
  return 2 * earth * Math.asin(Math.sqrt(h));
}

export function angularDistance(a: number, b: number) { return Math.abs(((a - b + 180) % 360) - 180); }

export function sunsetInfo(latitude: number, longitude: number, target = new Date()) {
  const start = Date.UTC(target.getFullYear(), 0, 0);
  const day = Math.floor((Date.UTC(target.getFullYear(), target.getMonth(), target.getDate()) - start) / 86400000);
  const gamma = 2 * Math.PI / 365 * (day - 1);
  const eqTime = 229.18 * (0.000075 + 0.001868*Math.cos(gamma) - 0.032077*Math.sin(gamma) - 0.014615*Math.cos(2*gamma) - 0.040849*Math.sin(2*gamma));
  const decl = 0.006918 - 0.399912*Math.cos(gamma) + 0.070257*Math.sin(gamma) - 0.006758*Math.cos(2*gamma) + 0.000907*Math.sin(2*gamma) - 0.002697*Math.cos(3*gamma) + 0.00148*Math.sin(3*gamma);
  const lat = toRad(latitude), zenith = toRad(90.833);
  const cosHa = Math.max(-1, Math.min(1, Math.cos(zenith)/(Math.cos(lat)*Math.cos(decl)) - Math.tan(lat)*Math.tan(decl)));
  const hourAngle = Math.acos(cosHa);
  const utcMinutes = 720 - 4*longitude - eqTime + 4*toDeg(hourAngle);
  const localMinutes = (utcMinutes + 540 + 1440) % 1440;
  const hours = Math.floor(localMinutes / 60), minutes = Math.round(localMinutes % 60);
  const azimuth = (toDeg(Math.atan2(Math.sin(hourAngle), Math.cos(hourAngle)*Math.sin(lat) - Math.tan(decl)*Math.cos(lat))) + 180) % 360;
  return { time: `${String(hours + Math.floor(minutes/60)).padStart(2,"0")}:${String(minutes%60).padStart(2,"0")}`, azimuth };
}

export function rankedScore(spot: SunsetSpot, azimuth: number, user?: Position) {
  const direction = Math.max(0, 1 - angularDistance(spot.viewDirectionDeg, azimuth) / 45) * 12;
  const distance = user ? Math.max(0, 8 - distanceKm(user, spot) * .7) : 4;
  return Math.round(Math.min(99, spot.baseScore * .82 + direction + distance));
}
