from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("OLYOUNG_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("OLYOUNG_DB_PATH", DATA_DIR / "olyoung_new.db"))

OLIVEYOUNG_CATEGORY_ID = os.getenv("OLYOUNG_CATEGORY_ID", "1000001000100140001")
OLIVEYOUNG_SORT = os.getenv("OLYOUNG_SORT", "02")  # 02 = 신상품순
OLIVEYOUNG_ROWS_PER_PAGE = int(os.getenv("OLYOUNG_ROWS_PER_PAGE", "24"))
OLIVEYOUNG_MAX_PAGES = int(os.getenv("OLYOUNG_MAX_PAGES", "3"))
OLIVEYOUNG_REQUEST_INTERVAL_SEC = float(os.getenv("OLYOUNG_REQUEST_INTERVAL_SEC", "1.0"))
OLIVEYOUNG_TIMEOUT_SEC = float(os.getenv("OLYOUNG_TIMEOUT_SEC", "15"))
OLIVEYOUNG_USE_SELENIUM = os.getenv("OLYOUNG_USE_SELENIUM", "0") == "1"

USER_AGENT = os.getenv(
    "OLYOUNG_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)
