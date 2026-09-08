from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    kakao_rest_api_key: str = os.getenv("KAKAO_REST_API_KEY", "").strip()
    naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "").strip()
    naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    request_timeout_sec: float = float(os.getenv("REQUEST_TIMEOUT_SEC", "10"))
    naver_blog_display: int = int(os.getenv("NAVER_BLOG_DISPLAY", "10"))

    @property
    def has_kakao(self) -> bool:
        return bool(self.kakao_rest_api_key)

    @property
    def has_naver(self) -> bool:
        return bool(self.naver_client_id and self.naver_client_secret)


settings = Settings()
