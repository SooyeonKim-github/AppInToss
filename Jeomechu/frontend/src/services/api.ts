import type { MenuPickResponse, RankingItem } from "../types";

const configuredApiBase = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE = (configuredApiBase || "http://localhost:8000").replace(/\/+$/, "");

if (import.meta.env.PROD && !configuredApiBase) {
  console.error("VITE_API_BASE_URL is not configured for the production build.");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export function fetchTodayMenu(clientId: string) {
  return request<MenuPickResponse>(`/api/v1/menu/today?clientId=${encodeURIComponent(clientId)}`);
}

export function rerollMenu(clientId: string) {
  return request<MenuPickResponse>("/api/v1/menu/reroll", {
    method: "POST",
    body: JSON.stringify({ clientId }),
  });
}

export function toggleMenuLike(clientId: string, menuId: number) {
  return request<{ liked: boolean; likes: number }>(`/api/v1/menu/${menuId}/like`, {
    method: "POST",
    body: JSON.stringify({ clientId }),
  });
}

export function fetchTodayRanking() {
  return request<RankingItem[]>("/api/v1/ranking/today");
}
