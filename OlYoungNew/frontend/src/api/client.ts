import { mockProducts } from "../mocks/products";
import type { HomeProduct } from "../types/product";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

export async function getHomeProducts(): Promise<HomeProduct[]> {
  if (!API_BASE_URL) {
    return mockProducts;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/trends/home`);
    if (!response.ok) {
      throw new Error(`home trends request failed: ${response.status}`);
    }
    return (await response.json()) as HomeProduct[];
  } catch (error) {
    console.warn("올영뉴 API 연결에 실패해 Mock 데이터로 실행합니다.", error);
    return mockProducts;
  }
}
