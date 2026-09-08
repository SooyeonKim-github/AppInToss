import { apiGet } from "./client";
import type {
  HomeResponse,
  Recommendation,
  Region,
  ViewCode,
} from "../types";

export function fetchHome() {
  return apiGet<HomeResponse>("/home");
}

export function fetchRegions(view: ViewCode) {
  return apiGet<{ view: ViewCode; regions: Region[] }>(`/views/${view}/regions`);
}

export function fetchRecommendations(view: ViewCode, region: string) {
  const params = new URLSearchParams({ view, region });
  return apiGet<{ recommendations: Recommendation[] }>(
    `/recommendations?${params.toString()}`,
  );
}

export function fetchSunsetBest() {
  return apiGet<{ recommendation: Recommendation }>(
    "/recommendations/sunset-best",
  );
}
