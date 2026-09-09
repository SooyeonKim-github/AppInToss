from __future__ import annotations

from pydantic import BaseModel, Field


class MenuOut(BaseModel):
    id: int
    name: str
    category: str
    subCategory: str
    rarity: str
    emoji: str
    tagline: str
    imageKey: str | None = None


class MenuPickResponse(BaseModel):
    menu: MenuOut
    likes: int
    liked: bool
    rerollIndex: int


class ClientRequest(BaseModel):
    clientId: str = Field(min_length=8, max_length=64)


class LikeResponse(BaseModel):
    liked: bool
    likes: int


class RankingItem(BaseModel):
    rank: int
    menuId: int
    name: str
    emoji: str
    imageKey: str | None = None
    likes: int
