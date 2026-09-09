from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .mock_data import HOME_PRODUCTS

app = FastAPI(
    title="OlYoungNew API",
    version="0.1.0",
    description="올영뉴 신상 반응지수·제품·조합 분석 API 뼈대",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/trends/home")
def home_trends() -> list[dict]:
    """MVP: 실제 수집 파이프라인 연결 전 Mock 응답."""
    return HOME_PRODUCTS


@app.post("/api/v1/mix/analyze")
def analyze_mix(product_ids: list[int]) -> dict:
    """MVP 조합 분석 API contract. 성분 DB 연결 단계에서 실제 로직으로 교체."""
    return {
        "productIds": product_ids,
        "mixScore": min(92, 72 + len(product_ids) * 5),
        "status": "MOCK",
        "message": "ingredient engine is not connected yet",
    }
