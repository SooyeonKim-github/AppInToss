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

EMOJI_RULES: list[tuple[tuple[str, ...], str]] = [
    (("치킨", "닭강정", "닭갈비", "찜닭", "닭볶음탕", "닭발", "닭한마리", "닭개장", "닭목살", "가라아게", "치킨난반", "탄두리치킨", "파닭"), "🍗"),
    (("라멘", "우동", "소바", "국수", "쫄면", "막국수", "우육면", "탄탄면", "도삭면", "락사", "똠얌누들", "팟타이", "팟씨유", "야키소바"), "🍜"),
    (("비빔밥", "볶음밥", "덮밥", "계란밥", "오므라이스", "규동", "가츠동", "오야코동", "부타동", "루러우판", "카오팟", "나시고렝", "치킨라이스"), "🍚"),
    (("카레", "커리", "비리야니"), "🍛"),
    (("초밥", "사시미", "생선회", "회덮밥", "물회", "세비체"), "🍣"),
    (("김밥", "삼각김밥"), "🍙"),
    (("만두", "딤섬", "샤오롱바오"), "🥟"),
    (("튀김", "텐동"), "🍤"),
    (("피자",), "🍕"),
    (("버거",), "🍔"),
    (("샌드위치", "반미", "파니니", "토스트"), "🥪"),
    (("파스타", "리조또", "라자냐", "뇨끼"), "🍝"),
    (("떡볶이", "라볶이", "오뎅", "어묵"), "🍢"),
    (("오코노미야키", "파전", "감자전", "부추전", "김치전"), "🥞"),
    (("샐러드", "포케"), "🥗"),
    (("타코", "부리또", "퀘사디아", "나초", "파히타"), "🌮"),
    (("케밥", "팔라펠", "후무스", "샥슈카"), "🧆"),
    (("짜장",), "🍜"),
    (("짬뽕", "마라탕", "마라샹궈", "훠궈", "마라룽샤"), "🌶️"),
    (("탕수육", "꿔바로우", "깐풍기", "유린기"), "🥡"),
    (("돈까스", "규카츠", "멘치카츠", "피쉬앤칩스"), "🍱"),
    (("장어", "고등어", "갈치", "삼치", "생선"), "🐟"),
    (("게장", "꽃게"), "🦀"),
    (("낙지", "주꾸미", "오징어", "아귀", "해물", "타코야키"), "🦑"),
    (("감바스",), "🍤"),
    (("삼겹", "목살", "불고기", "돼지불백", "갈비", "스테이크", "양꼬치", "양갈비", "바비큐", "족발", "보쌈", "동파육"), "🥩"),
    (("오리",), "🦆"),
    (("계란", "에그"), "🍳"),
    (("요거트", "오트밀"), "🥣"),
    (("찌개", "탕", "국", "전골", "나베", "스키야키", "샤브", "백숙", "삼계탕", "부야베스", "검보"), "🍲"),
]


def today_seoul() -> date:
    from datetime import datetime

    return datetime.now(SEOUL).date()


def menu_emoji(name: str, category: str) -> str:
    for keywords, emoji in EMOJI_RULES:
        if any(keyword in name for keyword in keywords):
            return emoji
    return CATEGORY_EMOJI.get(category, "🍽️")


def _catalog() -> dict[str, dict[str, list[str]]]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _catalog_image_map() -> dict[str, str]:
    image_map: dict[str, str] = {}
    index = 0
    for categories in _catalog().values():
        for names in categories.values():
            for name in names:
                image_map[name] = f"menu-{index:03d}"
                index += 1
    return image_map


def seed_menus_if_empty(db: Session) -> int:
    if db.scalar(select(func.count(Menu.id))) or 0:
        return 0

    catalog = _catalog()
    inserted = 0
    menu_id = 1
    image_index = 0
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
                        emoji=menu_emoji(name, category),
                        tagline=RARITY_TAGLINE[rarity],
                        image_key=f"menu-{image_index:03d}",
                        enabled=True,
                    )
                )
                menu_id += 1
                image_index += 1
                inserted += 1
    db.commit()
    return inserted


def sync_menu_images(db: Session) -> int:
    """Give every catalog menu a stable image key and a menu-aware illustration emoji."""
    image_map = _catalog_image_map()
    menus = db.scalars(select(Menu)).all()
    changed = 0

    for menu in menus:
        expected_key = image_map.get(menu.name)
        expected_emoji = menu_emoji(menu.name, menu.category)
        dirty = False

        if expected_key is not None and menu.image_key != expected_key:
            menu.image_key = expected_key
            dirty = True
        if menu.emoji != expected_emoji:
            menu.emoji = expected_emoji
            dirty = True

        if dirty:
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
