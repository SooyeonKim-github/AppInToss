from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    sub_category: Mapped[str] = mapped_column(String(40), default="")
    rarity: Mapped[str] = mapped_column(String(16), index=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    emoji: Mapped[str] = mapped_column(String(16), default="🍽️")
    tagline: Mapped[str] = mapped_column(String(120), default="오늘 저녁은 이걸로!")
    image_key: Mapped[str | None] = mapped_column(String(120), nullable=True, default=None)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class DailyPick(Base):
    __tablename__ = "daily_picks"
    __table_args__ = (
        UniqueConstraint("client_id", "pick_date", "reroll_index", name="uq_daily_pick_client_date_reroll"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    pick_date: Mapped[date] = mapped_column(Date, index=True)
    reroll_index: Mapped[int] = mapped_column(Integer, default=0)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    menu: Mapped[Menu] = relationship()


class MenuLike(Base):
    __tablename__ = "menu_likes"
    __table_args__ = (
        UniqueConstraint("client_id", "menu_id", "liked_date", name="uq_menu_like_client_menu_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id"), index=True)
    liked_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    menu: Mapped[Menu] = relationship()
