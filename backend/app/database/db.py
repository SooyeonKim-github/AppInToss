from __future__ import annotations
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "data" / "oreulkka.db"

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db() -> None:
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS predictions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT NOT NULL,
          question_id TEXT NOT NULL,
          prediction TEXT NOT NULL CHECK(prediction IN ('UP','DOWN')),
          is_correct INTEGER NOT NULL,
          virtual_buy INTEGER NOT NULL,
          return_d1 REAL NOT NULL,
          return_d5 REAL NOT NULL,
          return_d10 REAL NOT NULL,
          return_d20 REAL NOT NULL,
          pattern_type TEXT NOT NULL,
          pattern_name TEXT NOT NULL,
          predicted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id, question_id)
        );
        """)
