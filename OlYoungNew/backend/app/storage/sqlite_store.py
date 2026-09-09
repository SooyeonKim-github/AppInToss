from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from ..config import DB_PATH
from ..collectors.oliveyoung.models import CollectedProduct

UTC = timezone.utc
SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS products (
    goods_no TEXT PRIMARY KEY, brand_name TEXT NOT NULL, product_name TEXT NOT NULL,
    product_url TEXT NOT NULL, image_url TEXT, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS product_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT, goods_no TEXT NOT NULL, collected_at TEXT NOT NULL,
    rank INTEGER, original_price INTEGER, sale_price INTEGER, discount_rate REAL,
    review_count INTEGER, rating REAL, is_new_badge INTEGER NOT NULL DEFAULT 0,
    is_oliveyoung_pick INTEGER NOT NULL DEFAULT 0, has_promotion INTEGER NOT NULL DEFAULT 0,
    badges_json TEXT NOT NULL DEFAULT '[]', source_url TEXT,
    FOREIGN KEY(goods_no) REFERENCES products(goods_no)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_goods_time ON product_snapshots(goods_no, collected_at DESC);
CREATE TABLE IF NOT EXISTS reaction_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT, goods_no TEXT NOT NULL, calculated_at TEXT NOT NULL,
    score REAL NOT NULL, review_velocity_score REAL NOT NULL, rating_score REAL NOT NULL,
    discount_score REAL NOT NULL, exposure_score REAL NOT NULL, new_badge_score REAL NOT NULL,
    freshness_score REAL NOT NULL, score_change REAL, components_json TEXT NOT NULL,
    FOREIGN KEY(goods_no) REFERENCES products(goods_no)
);
CREATE INDEX IF NOT EXISTS idx_scores_goods_time ON reaction_scores(goods_no, calculated_at DESC);
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT,
    status TEXT NOT NULL, products_found INTEGER NOT NULL DEFAULT 0, error_message TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class SQLiteStore:
    def __init__(self, path: Path | str = DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def start_run(self) -> int:
        with self.connect() as connection:
            cursor = connection.execute("INSERT INTO collection_runs(started_at, status) VALUES (?, ?)", (_now_iso(), "RUNNING"))
            return int(cursor.lastrowid)

    def finish_run(self, run_id: int, *, status: str, products_found: int, error_message: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE collection_runs SET finished_at=?, status=?, products_found=?, error_message=? WHERE id=?", (_now_iso(), status, products_found, error_message, run_id))

    def save_products(self, products: Iterable[CollectedProduct], *, collected_at: str | None = None) -> int:
        timestamp = collected_at or _now_iso()
        count = 0
        with self.connect() as connection:
            for product in products:
                connection.execute(
                    """INSERT INTO products(goods_no, brand_name, product_name, product_url, image_url, first_seen_at, last_seen_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(goods_no) DO UPDATE SET brand_name=excluded.brand_name, product_name=excluded.product_name,
                    product_url=excluded.product_url, image_url=COALESCE(excluded.image_url, products.image_url), last_seen_at=excluded.last_seen_at""",
                    (product.goods_no, product.brand_name, product.product_name, product.product_url, product.image_url, timestamp, timestamp),
                )
                connection.execute(
                    """INSERT INTO product_snapshots(goods_no, collected_at, rank, original_price, sale_price, discount_rate,
                    review_count, rating, is_new_badge, is_oliveyoung_pick, has_promotion, badges_json, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (product.goods_no, timestamp, product.rank, product.original_price, product.sale_price, product.discount_rate,
                     product.review_count, product.rating, int(product.is_new_badge), int(product.is_oliveyoung_pick),
                     int(product.has_promotion), json.dumps(product.badges, ensure_ascii=False), product.source_url),
                )
                count += 1
        return count

    def get_latest_and_previous_snapshots(self, goods_no: str):
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT s.*, p.first_seen_at, p.brand_name, p.product_name, p.product_url, p.image_url
                FROM product_snapshots s JOIN products p ON p.goods_no=s.goods_no
                WHERE s.goods_no=? ORDER BY s.collected_at DESC LIMIT 2""", (goods_no,)
            ).fetchall()
        return (rows[0] if rows else None, rows[1] if len(rows) > 1 else None)

    def list_latest_snapshot_goods(self) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute("SELECT DISTINCT goods_no FROM product_snapshots").fetchall()
        return [str(row["goods_no"]) for row in rows]

    def save_reaction_score(self, goods_no: str, result: dict, *, calculated_at: str | None = None) -> None:
        timestamp = calculated_at or _now_iso()
        with self.connect() as connection:
            previous = connection.execute("SELECT score FROM reaction_scores WHERE goods_no=? ORDER BY calculated_at DESC LIMIT 1", (goods_no,)).fetchone()
            previous_score = float(previous["score"]) if previous else None
            score_change = round(float(result["score"]) - previous_score, 1) if previous_score is not None else 0.0
            connection.execute(
                """INSERT INTO reaction_scores(goods_no, calculated_at, score, review_velocity_score, rating_score,
                discount_score, exposure_score, new_badge_score, freshness_score, score_change, components_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (goods_no, timestamp, result["score"], result["review_velocity"], result["rating"], result["discount"],
                 result["exposure"], result["new_badge"], result["freshness"], score_change,
                 json.dumps(result, ensure_ascii=False)),
            )

    def get_home_products(self, limit: int = 15):
        with self.connect() as connection:
            return connection.execute(
                """WITH latest_snapshot AS (
                    SELECT s.* FROM product_snapshots s JOIN (SELECT goods_no, MAX(collected_at) max_at FROM product_snapshots GROUP BY goods_no) x
                    ON x.goods_no=s.goods_no AND x.max_at=s.collected_at
                ), latest_score AS (
                    SELECT r.* FROM reaction_scores r JOIN (SELECT goods_no, MAX(calculated_at) max_at FROM reaction_scores GROUP BY goods_no) x
                    ON x.goods_no=r.goods_no AND x.max_at=r.calculated_at
                )
                SELECT p.*, s.rank, s.original_price, s.sale_price, s.discount_rate, s.review_count, s.rating,
                s.is_new_badge, s.is_oliveyoung_pick, s.has_promotion, s.badges_json,
                r.score, r.score_change, r.review_velocity_score, r.rating_score, r.discount_score,
                r.exposure_score, r.new_badge_score, r.freshness_score
                FROM products p JOIN latest_snapshot s ON s.goods_no=p.goods_no
                LEFT JOIN latest_score r ON r.goods_no=p.goods_no
                ORDER BY COALESCE(r.score, 0) DESC, s.rank ASC LIMIT ?""", (limit,)
            ).fetchall()

    def count_products(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) cnt FROM products").fetchone()
        return int(row["cnt"]) if row else 0
