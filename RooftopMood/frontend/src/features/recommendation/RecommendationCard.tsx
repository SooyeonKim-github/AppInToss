import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { uploadCafePhoto } from "../../api/rooftopMood.api";
import type { PhotoStatus, Recommendation } from "../../types";
import "./recommendation-card.css";

const RANK_LABELS: Record<number, string> = {
  1: "🥇 1위",
  2: "🥈 2위",
  3: "🥉 3위",
  4: "4위",
  5: "5위",
};

export function RecommendationCard({
  item,
  rank,
}: {
  item: Recommendation;
  rank?: number;
}) {
  const sunset = item.todaySunsetInfo;
  const inputRef = useRef<HTMLInputElement>(null);
  const [localImageUrl, setLocalImageUrl] = useState<string | null>(item.imageUrl ?? null);
  const [photoStatus, setPhotoStatus] = useState<PhotoStatus | null>(item.photoStatus ?? null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  useEffect(() => {
    setLocalImageUrl(item.imageUrl ?? null);
    setPhotoStatus(item.photoStatus ?? null);
    setUploadError(null);
    setUploadMessage(null);
  }, [item.id, item.imageUrl, item.photoStatus]);

  useEffect(() => {
    return () => {
      if (localImageUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(localImageUrl);
      }
    };
  }, [localImageUrl]);

  const kakaoMapUrl = useMemo(
    () =>
      item.kakaoMapUrl ||
      `https://map.kakao.com/link/search/${encodeURIComponent(item.name)}`,
    [item.kakaoMapUrl, item.name],
  );

  const canUpload = (item.canUploadPhoto ?? !item.imageUrl) && photoStatus === null;

  async function handlePhotoChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setUploadError("JPG, PNG, WEBP 사진만 올릴 수 있어요.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("사진은 최대 10MB까지 올릴 수 있어요.");
      return;
    }

    if (localImageUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(localImageUrl);
    }

    const previewUrl = URL.createObjectURL(file);
    setLocalImageUrl(previewUrl);
    setUploading(true);
    setUploadError(null);
    setUploadMessage(null);

    try {
      const result = await uploadCafePhoto(item.id, file);
      setPhotoStatus(result.status);
      setUploadMessage(result.message);
    } catch (error) {
      URL.revokeObjectURL(previewUrl);
      setLocalImageUrl(item.imageUrl ?? null);
      setUploadError(
        error instanceof Error ? error.message : "사진을 올리지 못했어요.",
      );
    } finally {
      setUploading(false);
    }
  }

  function renderPhotoArea() {
    if (localImageUrl) {
      return (
        <>
          <img src={localImageUrl} alt={`${item.name} 루프탑 뷰`} />
          {uploading ? <span className="photo-review-badge">업로드 중…</span> : null}
          {!uploading && photoStatus === "PENDING" ? (
            <span className="photo-review-badge">확인 중</span>
          ) : null}
        </>
      );
    }

    if (photoStatus === "PENDING") {
      return (
        <div className="photo-empty-state photo-pending-state">
          <span className="photo-icon">🌇</span>
          <strong>사진을 확인하고 있어요</strong>
          <p>승인되면 이 자리에 대표 사진으로 보여드릴게요</p>
        </div>
      );
    }

    if (!canUpload) {
      return (
        <div className="photo-empty-state photo-pending-state">
          <span className="photo-icon">📷</span>
          <strong>사진 확인이 필요해요</strong>
          <p>관리자 확인 후 다시 보여드릴게요</p>
        </div>
      );
    }

    return (
      <div className="photo-empty-state">
        <span className="photo-icon">📷</span>
        <strong>사진이 딱 1장만 등록돼요</strong>
        <p>이 카페의 뷰를 가장 먼저 남겨보세요</p>
        <button
          type="button"
          className="photo-upload-button"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          사진 올리기
        </button>
        <input
          ref={inputRef}
          className="photo-file-input"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handlePhotoChange}
        />
        {uploadError ? <p className="photo-upload-error">{uploadError}</p> : null}
      </div>
    );
  }

  return (
    <article className={`recommendation-card rank-${rank ?? 0}`}>
      <div className="recommendation-image">
        {renderPhotoArea()}
        {rank ? <span className="rank-badge">{RANK_LABELS[rank] ?? `${rank}위`}</span> : null}
      </div>

      <div className="recommendation-body">
        <div className="card-title-row">
          <div>
            <p className="region-label">
              {item.tags[0] ? `${item.tags[0]} · ` : ""}
              {item.regionName}
            </p>
            <h3>{item.name}</h3>
          </div>
          <div className="score-pill">노을 궁합 {item.score}점</div>
        </div>

        {uploadMessage ? <p className="photo-upload-message">{uploadMessage}</p> : null}
        <p className="view-description">{item.viewDescription}</p>

        <div className={`today-sunset ${sunset.visible ? "visible" : "muted"}`}>
          <div className="today-sunset-title">
            <span>🌇 오늘의 노을</span>
            <strong>{sunset.positionLabel}</strong>
          </div>
          <p>{sunset.message}</p>
          <div className="today-sunset-meta">
            <span>⏰ BEST {sunset.bestTime}</span>
            <span>일몰 {sunset.sunsetTime}</span>
          </div>
        </div>

        <a
          className="kakao-map-button"
          href={kakaoMapUrl}
          target="_blank"
          rel="noreferrer"
        >
          <span>📍 카카오맵 보기</span>
          <span aria-hidden="true">›</span>
        </a>
      </div>
    </article>
  );
}
