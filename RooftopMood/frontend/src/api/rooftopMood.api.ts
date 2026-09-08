import { apiGet, apiPostForm } from "./client";
import type {
  HomeResponse,
  PhotoUploadResponse,
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
  return apiGet<{ recommendations: Recommendation[] }>(
    "/recommendations/sunset-best",
  );
}

export function uploadCafePhoto(cafeId: number, file: File, userKey?: string) {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<PhotoUploadResponse>(
    `/cafes/${cafeId}/photo`,
    formData,
    userKey ? { "X-User-Key": userKey } : undefined,
  );
}
