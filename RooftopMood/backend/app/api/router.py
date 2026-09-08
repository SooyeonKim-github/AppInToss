from fastapi import APIRouter

from app.api.routes import cafes, home, recommendations, views

api_router = APIRouter()
api_router.include_router(home.router)
api_router.include_router(views.router)
api_router.include_router(recommendations.router)
api_router.include_router(cafes.router)
