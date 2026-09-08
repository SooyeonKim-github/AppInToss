from datetime import datetime, timezone
from secrets import compare_digest

import httpx
from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings

router = APIRouter(prefix="/admin/photos", tags=["admin-photos"])


def _require_admin(admin_key: str | None) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="관리자 API 키가 설정되지 않았어요.")
    if not admin_key or not compare_digest(admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="관리자 인증에 실패했어요.")


def _headers() -> dict[str, str]:
    if not settings.supabase_service_role_key:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }


@router.get("")
def list_photos(
    status: str = Query("PENDING", pattern="^(PENDING|APPROVED|REJECTED)$"),
    admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> list[dict]:
    _require_admin(admin_key)
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")

    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers=_headers(),
            params={
                "select": "id,cafe_id,image_url,status,created_at,cafes(name,region_name)",
                "status": f"eq.{status}",
                "order": "created_at.desc",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Supabase 조회에 실패했어요.") from exc


def _update_status(photo_id: int, status: str) -> dict:
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")

    payload: dict[str, str | None] = {"status": status}
    payload["approved_at"] = (
        datetime.now(timezone.utc).isoformat() if status == "APPROVED" else None
    )

    try:
        response = httpx.patch(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers={**_headers(), "Prefer": "return=representation"},
            params={"id": f"eq.{photo_id}"},
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        rows = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Supabase 수정에 실패했어요.") from exc

    if not rows:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")
    return rows[0]


@router.post("/{photo_id}/approve")
def approve_photo(
    photo_id: int,
    admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(admin_key)
    return _update_status(photo_id, "APPROVED")


@router.post("/{photo_id}/reject")
def reject_photo(
    photo_id: int,
    admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(admin_key)
    return _update_status(photo_id, "REJECTED")
