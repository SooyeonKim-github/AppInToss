from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class CollectedProduct:
    goods_no: str
    brand_name: str
    product_name: str
    product_url: str
    image_url: Optional[str] = None
    original_price: Optional[int] = None
    sale_price: Optional[int] = None
    discount_rate: Optional[float] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    rank: Optional[int] = None
    is_new_badge: bool = False
    is_oliveyoung_pick: bool = False
    has_promotion: bool = False
    badges: list[str] = field(default_factory=list)
    source_url: Optional[str] = None
