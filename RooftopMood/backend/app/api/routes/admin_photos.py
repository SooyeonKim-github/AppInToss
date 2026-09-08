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


def _signed_url(storage_path: str, expires_in: int = 900) -> str | None:
    if not settings.supabase_url:
        return None
    bucket = settings.supabase_storage_bucket
    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/sign/{bucket}/{storage_path}",
            headers=_headers(),
            json={"expiresIn": expires_in},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    relative_url = response.json().get("signedURL") or response.json().get("signedUrl")
    if not relative_url:
        return None
    if str(relative_url).startswith("http"):
        return str(relative_url)
    return f"{settings.supabase_url.rstrip('/')}/storage/v1{relative_url}"


@router.get("")
def list_photos(
    status: str = Query("PENDING", pattern="^(PENDING|APPROVED)$"),
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
                "select": "id,cafe_id,storage_path,status,created_at,cafes(name,region_name)",
                "status": f"eq.{status}",
                "order": "created_at.desc",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        rows = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Supabase 조회에 실패했어요.") from exc

    for row in rows:
        row["reviewImageUrl"] = _signed_url(row["storage_path"])
    return rows


def _update_status(photo_id: int, status: str) -> dict:
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")

    payload = {
        "status": status,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }

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


def _find_photo(photo_id: int) -> dict:
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers=_headers(),
            params={"select": "id,cafe_id,storage_path", "id": f"eq.{photo_id}", "limit": "1"},
            timeout=10.0,
        )
        response.raise_for_status()
        rows = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Supabase 조회에 실패했어요.") from exc
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
    photo = _find_photo(photo_id)
    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Supabase 서버 설정이 완료되지 않았어요.")

    bucket = settings.supabase_storage_bucket
    try:
        storage_response = httpx.delete(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{photo['storage_path']}",
            headers=_headers(),
            timeout=10.0,
        )
        storage_response.raise_for_status()
        db_response = httpx.delete(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers=_headers(),
            params={"id": f"eq.{photo_id}"},
            timeout=10.0,
        )
        db_response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="사진 거절 처리에 실패했어요.") from exc

    return {
        "photoId": photo_id,
        "cafeId": photo["cafe_id"],
        "status": "REJECTED",
        "message": "사진을 거절하고 업로드 자리를 다시 열었어요.",
    }
