import type { MenuPickResponse, RankingItem } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
