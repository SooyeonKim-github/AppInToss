from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import Base, engine, ensure_menu_image_column, get_db, session_scope
from .models import Menu
from .schemas import ClientRequest, LikeResponse, MenuOut, MenuPickResponse, RankingItem
from .services import (
    create_next_reroll,
    get_or_create_pick,
    is_liked,
    like_count,
    ranking_today,
    seed_menus_if_empty,
    sync_menu_images,
    toggle_like,
)
from .settings import settings


def menu_out(menu: Menu) -> MenuOut:
    return MenuOut(
        id=menu.id,
        name=menu.name,
        category=menu.category,
        subCategory=menu.sub_category,
        rarity=menu.rarity,
        emoji=menu.emoji,
        tagline=menu.tagline,
        imageKey=menu.image_key,
    )


def pick_response(db: Session, client_id: str, pick) -> MenuPickResponse:
    return MenuPickResponse(
        menu=menu_out(pick.menu),
        likes=like_count(db, pick.menu_id),
        liked=is_liked(db, client_id, pick.menu_id),
        rerollIndex=pick.reroll_index,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_menu_image_column()
    with session_scope() as db:
        seed_menus_if_empty(db)
        sync_menu_images(db)
    yield


app = FastAPI(
    title="김대리의 저메추 API",
    version="0.3.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    return {
        "ok": True,
        "environment": settings.environment,
        "database": engine.url.get_backend_name(),
    }


@app.get("/api/v1/menu/today", response_model=MenuPickResponse)
def today_menu(
    client_id: str = Query(alias="clientId", min_length=8, max_length=64),
    db: Session = Depends(get_db),
):
    pick = get_or_create_pick(db, client_id, 0)
    return pick_response(db, client_id, pick)


@app.post("/api/v1/menu/reroll", response_model=MenuPickResponse)
def reroll(payload: ClientRequest, db: Session = Depends(get_db)):
    pick = create_next_reroll(db, payload.clientId)
    return pick_response(db, payload.clientId, pick)


@app.post("/api/v1/menu/{menu_id}/like", response_model=LikeResponse)
def like(menu_id: int, payload: ClientRequest, db: Session = Depends(get_db)):
    try:
        liked, likes = toggle_like(db, payload.clientId, menu_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LikeResponse(liked=liked, likes=likes)


@app.get("/api/v1/ranking/today", response_model=list[RankingItem])
def ranking(db: Session = Depends(get_db)):
    rows = ranking_today(db, limit=10)
    return [
        RankingItem(
            rank=index,
            menuId=menu.id,
            name=menu.name,
            emoji=menu.emoji,
            imageKey=menu.image_key,
            likes=likes,
        )
        for index, (menu, likes) in enumerate(rows, start=1)
    ]
