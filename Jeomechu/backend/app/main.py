from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

load_dotenv()

from .database import Base, engine, get_db, session_scope
from .models import Menu
from .schemas import ClientRequest, LikeResponse, MenuOut, MenuPickResponse, RankingItem
from .services import (
    create_next_reroll,
    get_or_create_pick,
    is_liked,
    like_count,
    ranking_today,
    seed_menus_if_empty,
    toggle_like,
)


def menu_out(menu: Menu) -> MenuOut:
    return MenuOut(
        id=menu.id,
        name=menu.name,
        category=menu.category,
        subCategory=menu.sub_category,
        rarity=menu.rarity,
        emoji=menu.emoji,
        tagline=menu.tagline,
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
    with session_scope() as db:
        seed_menus_if_empty(db)
    yield


app = FastAPI(title="저메추 API", version="0.1.0", lifespan=lifespan)

origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


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
        RankingItem(rank=index, menuId=menu.id, name=menu.name, emoji=menu.emoji, likes=likes)
        for index, (menu, likes) in enumerate(rows, start=1)
    ]
