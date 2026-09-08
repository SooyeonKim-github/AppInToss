from __future__ import annotations

from io import BytesIO

import httpx
from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class PhotoUploadError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PhotoService:
    @property
    def _headers(self) -> dict[str, str]:
        key = settings.supabase_service_role_key or ""
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }

    def _require_supabase(self) -> None:
        if not settings.photo_upload_enabled:
            raise PhotoUploadError("현재 사진 업로드가 비활성화되어 있어요.", 503)
        if settings.data_backend.lower() != "supabase":
            raise PhotoUploadError(
                "사진 업로드는 Supabase 운영 모드에서 사용할 수 있어요.",
                503,
            )
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise PhotoUploadError("Supabase 서버 설정이 완료되지 않았어요.", 503)

    def _existing_photo(self, cafe_id: int) -> dict | None:
        assert settings.supabase_url is not None
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers=self._headers,
            params={
                "select": "id,image_url,status",
                "cafe_id": f"eq.{cafe_id}",
                "limit": "1",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    @staticmethod
    async def _read_limited(file: UploadFile) -> bytes:
        data = await file.read(settings.photo_max_bytes + 1)
        if len(data) > settings.photo_max_bytes:
            raise PhotoUploadError("사진은 최대 10MB까지 올릴 수 있어요.", 413)
        if not data:
            raise PhotoUploadError("빈 파일은 올릴 수 없어요.")
        return data

    @staticmethod
    def _to_webp(data: bytes) -> tuple[bytes, int, int]:
        try:
            with Image.open(BytesIO(data)) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail(
                    (settings.photo_max_side_px, settings.photo_max_side_px),
                    Image.Resampling.LANCZOS,
                )
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGB")
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=image.getchannel("A"))
                    image = background

                width, height = image.size
                output = BytesIO()
                image.save(
                    output,
                    format="WEBP",
                    quality=settings.photo_webp_quality,
                    method=6,
                )
                return output.getvalue(), width, height
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise PhotoUploadError("올바른 이미지 파일이 아니에요.") from exc

    def _upload_storage(self, cafe_id: int, data: bytes) -> tuple[str, str]:
        assert settings.supabase_url is not None
        bucket = settings.supabase_storage_bucket
        storage_path = f"{cafe_id}/cover.webp"
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{storage_path}",
            headers={
                **self._headers,
                "Content-Type": "image/webp",
                "x-upsert": "false",
            },
            content=data,
            timeout=20.0,
        )
        if response.status_code in {400, 409}:
            raise PhotoUploadError("방금 다른 분이 먼저 사진을 등록했어요! 🌇", 409)
        response.raise_for_status()
        public_url = (
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
            f"{bucket}/{storage_path}"
        )
        return storage_path, public_url

    def _delete_storage(self, storage_path: str) -> None:
        if not settings.supabase_url:
            return
        bucket = settings.supabase_storage_bucket
        try:
            httpx.delete(
                f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{storage_path}",
                headers=self._headers,
                timeout=10.0,
            )
        except httpx.HTTPError:
            pass

    def _insert_photo(
        self,
        cafe_id: int,
        storage_path: str,
        image_url: str,
        uploaded_by: str | None,
        width: int,
        height: int,
        file_size_bytes: int,
    ) -> dict:
        assert settings.supabase_url is not None
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/rest/v1/cafe_photos",
            headers={
                **self._headers,
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json={
                "cafe_id": cafe_id,
                "image_url": image_url,
                "storage_path": storage_path,
                "uploaded_by": uploaded_by,
                "status": "PENDING",
                "content_type": "image/webp",
                "width": width,
                "height": height,
                "file_size_bytes": file_size_bytes,
            },
            timeout=10.0,
        )
        if response.status_code == 409:
            raise PhotoUploadError("방금 다른 분이 먼저 사진을 등록했어요! 🌇", 409)
        response.raise_for_status()
        rows = response.json()
        return rows[0]

    async def upload(
        self,
        cafe_id: int,
        file: UploadFile,
        uploaded_by: str | None = None,
    ) -> dict:
        self._require_supabase()

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise PhotoUploadError("JPG, PNG, WEBP 사진만 올릴 수 있어요.")

        if self._existing_photo(cafe_id):
            raise PhotoUploadError("이 카페에는 이미 사진이 등록되어 있어요.", 409)

        original = await self._read_limited(file)
        webp, width, height = self._to_webp(original)
        storage_path, image_url = self._upload_storage(cafe_id, webp)

        try:
            row = self._insert_photo(
                cafe_id=cafe_id,
                storage_path=storage_path,
                image_url=image_url,
                uploaded_by=uploaded_by,
                width=width,
                height=height,
                file_size_bytes=len(webp),
            )
        except Exception:
            self._delete_storage(storage_path)
            raise

        return {
            "cafeId": cafe_id,
            "imageUrl": image_url,
            "status": row["status"],
            "message": "사진이 등록됐어요. 확인 후 대표 사진으로 보여드릴게요 🌇",
        }
