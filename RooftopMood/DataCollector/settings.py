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

    # 2026-07 이후 신규 검색 API는 NAVER Developers가 아니라
    # NAVER Cloud Platform > NAVER API HUB에서 발급합니다.
    # 기존 변수명도 fallback으로 읽어 로컬 환경을 깨지 않게 합니다.
    naver_client_id: str = (
        os.getenv("NAVER_API_HUB_CLIENT_ID", "").strip()
        or os.getenv("NAVER_CLIENT_ID", "").strip()
    )
    naver_client_secret: str = (
        os.getenv("NAVER_API_HUB_CLIENT_SECRET", "").strip()
        or os.getenv("NAVER_CLIENT_SECRET", "").strip()
    )
    naver_api_hub_base_url: str = os.getenv(
        "NAVER_API_HUB_BASE_URL",
        "https://naverapihub.apigw.ntruss.com",
    ).strip().rstrip("/")

    request_timeout_sec: float = float(os.getenv("REQUEST_TIMEOUT_SEC", "10"))
    naver_blog_display: int = int(os.getenv("NAVER_BLOG_DISPLAY", "10"))

    # DataCollector 결과를 운영 DB로 publish 할 때만 사용합니다.
    supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    @property
    def has_kakao(self) -> bool:
        return bool(self.kakao_rest_api_key)

    @property
    def has_naver(self) -> bool:
        return bool(self.naver_client_id and self.naver_client_secret)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


settings = Settings()
