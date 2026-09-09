from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import DailyPick, Menu, MenuLike


SEOUL = ZoneInfo("Asia/Seoul")
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "menus.json"
IMAGE_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "menu_images.json"

CATEGORY_EMOJI = {
    "KOREAN": "🍚",
    "CHICKEN_SNACK": "🍗",
    "JAPANESE": "🍣",
    "CHINESE": "🥟",
    "WESTERN": "🍝",
    "SOUTHEAST_ASIA": "🍜",
    "INDIAN_MIDDLE_EAST": "🍛",
    "MEXICAN_WORLD": "🌮",
    "LIGHT_HOME": "🍳",
}
RARITY_WEIGHT = {"COMMON": 10, "UNCOMMON": 5, "RARE": 2}
RARITY_TAGLINE = {
    "COMMON": "오늘은 실패 없는 메뉴로.",
    "UNCOMMON": "오늘은 조금 색다르게.",
    "RARE": "이거 먹어본 적 있어요?",
}


def today_seoul() -> date:
    from datetime import datetime

    return datetime.now(SEOUL).date()


def _image_map() -> dict[str, str]:
    if not IMAGE_MAP_PATH.exists():
        return {}
    return json.loads(IMAGE_MAP_PATH.read_text(encoding="utf-8"))


def seed_menus_if_empty(db: Session) -> int:
    if db.scalar(select(func.count(Menu.id))) or 0:
        return 0

    catalog = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    image_map = _image_map()
    inserted = 0
    menu_id = 1
    for rarity, categories in catalog.items():
        for category, names in categories.items():
            for name in names:
                db.add(
                    Menu(
                        id=menu_id,
                        name=name,
                        category=category,
                        sub_category="",
                        rarity=rarity,
                        weight=RARITY_WEIGHT[rarity],
                        emoji=CATEGORY_EMOJI.get(category, "🍽️"),
                        tagline=RARITY_TAGLINE[rarity],
                        image_key=image_map.get(name),
                        enabled=True,
                    )
                )
                menu_id += 1
                inserted += 1
    db.commit()
    return inserted


def sync_menu_images(db: Session) -> int:
    """Keep DB image_key values aligned with the versioned image manifest."""
    image_map = _image_map()
    if not image_map:
        return 0

    changed = 0
    menus = db.scalars(select(Menu).where(Menu.name.in_(list(image_map.keys())))).all()
    for menu in menus:
        image_key = image_map.get(menu.name)
        if menu.image_key != image_key:
            menu.image_key = image_key
            changed += 1

    if changed:
        db.commit()
    return changed


def _stable_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big")
    return value / float(2**64 - 1)


def _pick_rarity(client_id: str, pick_date: date, reroll_index: int) -> str:
    value = _stable_unit(f"rarity|{client_id}|{pick_date.isoformat()}|{reroll_index}")
    if value < 0.60:
        return "COMMON"
    if value < 0.90:
        return "UNCOMMON"
    return "RARE"


def _weighted_menu(menus: list[Menu], seed: str) -> Menu:
    total = sum(max(menu.weight, 1) for menu in menus)
    target = _stable_unit(seed) * total
    cursor = 0.0
    for menu in menus:
        cursor += max(menu.weight, 1)
        if target <= cursor:
            return menu
    return menus[-1]


def _select_menu(db: Session, client_id: str, pick_date: date, reroll_index: int) -> Menu:
    rarity = _pick_rarity(client_id, pick_date, reroll_index)
    previous_ids = set(
        db.scalars(
            select(DailyPick.menu_id).where(
                DailyPick.client_id == client_id,
                DailyPick.pick_date == pick_date,
            )
        ).all()
    )

    menus = db.scalars(
        select(Menu).where(Menu.enabled.is_(True), Menu.rarity == rarity).order_by(Menu.id)
    ).all()
    candidates = [menu for menu in menus if menu.id not in previous_ids]

    if not candidates:
        all_menus = db.scalars(select(Menu).where(Menu.enabled.is_(True)).order_by(Menu.id)).all()
        candidates = [menu for menu in all_menus if menu.id not in previous_ids] or list(all_menus)

    if not candidates:
        raise RuntimeError("No enabled menus are available")

    return _weighted_menu(
        list(candidates),
        f"menu|{client_id}|{pick_date.isoformat()}|{reroll_index}|{rarity}",
    )


def get_or_create_pick(db: Session, client_id: str, reroll_index: int = 0) -> DailyPick:
    pick_date = today_seoul()
    existing = db.scalar(
        select(DailyPick).where(
            DailyPick.client_id == client_id,
            DailyPick.pick_date == pick_date,
            DailyPick.reroll_index == reroll_index,
        )
    )
    if existing:
        return existing

    menu = _select_menu(db, client_id, pick_date, reroll_index)
    pick = DailyPick(
        client_id=client_id,
        pick_date=pick_date,
        reroll_index=reroll_index,
        menu_id=menu.id,
    )
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick


def create_next_reroll(db: Session, client_id: str) -> DailyPick:
    pick_date = today_seoul()
    latest = db.scalar(
        select(func.max(DailyPick.reroll_index)).where(
            DailyPick.client_id == client_id,
            DailyPick.pick_date == pick_date,
        )
    )
    reroll_index = int(latest or 0) + 1
    return get_or_create_pick(db, client_id, reroll_index)


def like_count(db: Session, menu_id: int, liked_date: date | None = None) -> int:
    target_date = liked_date or today_seoul()
    return int(
        db.scalar(
            select(func.count(MenuLike.id)).where(
                MenuLike.menu_id == menu_id,
                MenuLike.liked_date == target_date,
            )
        )
        or 0
    )


def is_liked(db: Session, client_id: str, menu_id: int) -> bool:
    return (
        db.scalar(
            select(MenuLike.id).where(
                MenuLike.client_id == client_id,
                MenuLike.menu_id == menu_id,
                MenuLike.liked_date == today_seoul(),
            )
        )
        is not None
    )


def toggle_like(db: Session, client_id: str, menu_id: int) -> tuple[bool, int]:
    target_date = today_seoul()
    existing = db.scalar(
        select(MenuLike).where(
            MenuLike.client_id == client_id,
            MenuLike.menu_id == menu_id,
            MenuLike.liked_date == target_date,
        )
    )

    if existing:
        db.execute(delete(MenuLike).where(MenuLike.id == existing.id))
        liked = False
    else:
        menu = db.get(Menu, menu_id)
        if menu is None or not menu.enabled:
            raise LookupError("Menu not found")
        db.add(MenuLike(client_id=client_id, menu_id=menu_id, liked_date=target_date))
        liked = True

    db.commit()
    return liked, like_count(db, menu_id, target_date)


def ranking_today(db: Session, limit: int = 10) -> list[tuple[Menu, int]]:
    target_date = today_seoul()
    rows = db.execute(
        select(Menu, func.count(MenuLike.id).label("likes"))
        .join(MenuLike, MenuLike.menu_id == Menu.id)
        .where(MenuLike.liked_date == target_date, Menu.enabled.is_(True))
        .group_by(Menu.id)
        .order_by(func.count(MenuLike.id).desc(), Menu.name.asc())
        .limit(limit)
    ).all()
    return [(menu, int(likes)) for menu, likes in rows]
