from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from .models import CollectedProduct

BASE_URL = "https://www.oliveyoung.co.kr"
PROMOTION_KEYWORDS = ("올영픽", "단독", "기획", "1+1", "2+1", "증정", "세일", "쿠폰", "오늘드림", "특가")


def _first_text(node: Tag, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            text = found.get_text(" ", strip=True)
            if text:
                return text
    return ""


def _numbers(text: str) -> list[int]:
    return [int(v.replace(",", "")) for v in re.findall(r"\d[\d,]*", text or "")]


def _parse_price(text: str) -> int | None:
    nums = _numbers(text)
    return nums[0] if nums else None


def _parse_review_count(text: str) -> int | None:
    if not text:
        return None
    compact = text.replace(",", "")
    plus = re.search(r"(\d+)\s*\+", compact)
    if plus:
        return int(plus.group(1))
    nums = re.findall(r"\d+", compact)
    return int(nums[-1]) if nums else None


def _parse_rating(text: str) -> float | None:
    for pattern in (r"(?:평점|별점)\s*([0-9]+(?:\.[0-9]+)?)", r"([0-9]+(?:\.[0-9]+)?)\s*점"):
        match = re.search(pattern, text or "")
        if match:
            value = float(match.group(1))
            if 0 <= value <= 10:
                return value
    return None


def _goods_no_from_url(url: str) -> str | None:
    goods_no = parse_qs(urlparse(url).query).get("goodsNo", [None])[0]
    if goods_no:
        return goods_no
    match = re.search(r"goodsNo=([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else None


def _find_product_link(card: Tag) -> Tag | None:
    for selector in ("a.prd_thumb.goodsList", "a.prd_name", ".prd_name a[href*='goodsNo=']", "a[href*='/store/goods/getGoodsDetail.do'][href*='goodsNo=']"):
        found = card.select_one(selector)
        if found and found.get("href"):
            return found
    return None


def _extract_badges(card: Tag) -> list[str]:
    badges: list[str] = []
    for selector in (".prd_flag span", ".prd_flag", ".flag span", ".icon_flag span", ".prd_tag span"):
        for node in card.select(selector):
            text = node.get_text(" ", strip=True)
            if text and text not in badges:
                badges.append(text)
    return badges


def parse_category_html(html: str, source_url: str) -> list[CollectedProduct]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.prd_info")
    if not cards:
        cards = [a.parent for a in soup.select("a[href*='/store/goods/getGoodsDetail.do'][href*='goodsNo=']") if a.parent]

    products: list[CollectedProduct] = []
    seen: set[str] = set()
    for index, card in enumerate(cards, start=1):
        if not isinstance(card, Tag):
            continue
        link = _find_product_link(card)
        if link is None:
            continue
        product_url = urljoin(BASE_URL, str(link.get("href", "")))
        goods_no = _goods_no_from_url(product_url)
        if not goods_no or goods_no in seen:
            continue
        seen.add(goods_no)

        brand = _first_text(card, (".tx_brand", ".prd_name .tx_brand", ".brand"))
        name = _first_text(card, (".tx_name", ".prd_name .tx_name", ".prd_name p", ".prd_name"))
        if brand and name.startswith(brand):
            name = name[len(brand):].strip()
        if not name:
            name = link.get_text(" ", strip=True)

        original_price = _parse_price(_first_text(card, (".tx_org .tx_num", ".prd_price .tx_org", ".price-1")))
        sale_price = _parse_price(_first_text(card, (".tx_cur .tx_num", ".prd_price .tx_cur", ".price-2")))
        if sale_price is None:
            sale_price = original_price
        if original_price is None:
            original_price = sale_price
        discount_rate = None
        if original_price and sale_price is not None:
            discount_rate = round(max(0.0, min(100.0, (original_price - sale_price) / original_price * 100)), 1)

        review_count = _parse_review_count(_first_text(card, (".prd_review_cnt", ".review_count", ".goods_reputation")))
        rating = _parse_rating(_first_text(card, (".prd_point", ".review_point", ".point", ".prd_review_cnt")))
        image_node = card.select_one("img")
        image_url = None
        if image_node:
            image_url = image_node.get("data-original") or image_node.get("data-src") or image_node.get("src")
            if image_url:
                image_url = urljoin(BASE_URL, str(image_url))

        badges = _extract_badges(card)
        combined = " ".join([name, card.get_text(" ", strip=True), *badges])
        products.append(CollectedProduct(
            goods_no=goods_no, brand_name=brand or "UNKNOWN", product_name=name or goods_no,
            product_url=product_url, image_url=image_url, original_price=original_price,
            sale_price=sale_price, discount_rate=discount_rate, review_count=review_count,
            rating=rating, rank=index, is_new_badge=any(t in combined for t in ("신상", "NEW", "뉴 ")),
            is_oliveyoung_pick="올영픽" in combined,
            has_promotion=any(k in combined for k in PROMOTION_KEYWORDS), badges=badges, source_url=source_url,
        ))
    return products
