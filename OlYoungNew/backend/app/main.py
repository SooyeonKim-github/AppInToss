from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .mock_data import HOME_PRODUCTS
from .services import get_home_products
from .storage import SQLiteStore

app = FastAPI(
    title="OlYoungNew API",
    version="0.2.0",
    description="올영뉴 신상 반응지수·제품·조합 분석 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    store = SQLiteStore()
    return {"status": "ok", "db": str(store.path), "products": store.count_products()}


@app.get("/api/v1/trends/home")
def home_trends() -> list[dict]:
    store = SQLiteStore()
    products = get_home_products(store, limit=15)
    return products or HOME_PRODUCTS


@app.post("/api/v1/mix/analyze")
def analyze_mix(product_ids: list[int]) -> dict:
    return {
        "productIds": product_ids,
        "mixScore": min(92, 72 + len(product_ids) * 5),
        "status": "MOCK_INGREDIENT_ENGINE",
        "message": "product snapshot/reaction DB is live; ingredient engine is next",
    }
