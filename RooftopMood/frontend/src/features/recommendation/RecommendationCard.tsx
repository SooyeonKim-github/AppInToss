import { useEffect, useMemo, useRef, useState } from "react";
import type { Recommendation } from "../../types";

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

  useEffect(() => {
    setLocalImageUrl(item.imageUrl ?? null);
  }, [item.id, item.imageUrl]);

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

  function handlePhotoChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    if (localImageUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(localImageUrl);
    }

    setLocalImageUrl(URL.createObjectURL(file));
  }

  return (
    <article className={`recommendation-card rank-${rank ?? 0}`}>
      <div className="recommendation-image">
        {localImageUrl ? (
          <img src={localImageUrl} alt={`${item.name} 루프탑 뷰`} />
        ) : (
          <div className="photo-empty-state">
            <span className="photo-icon">📷</span>
            <strong>사진이 딱 1장만 등록돼요</strong>
            <p>이 카페의 뷰를 가장 먼저 남겨보세요</p>
            <button
              type="button"
              className="photo-upload-button"
              onClick={() => inputRef.current?.click()}
            >
              사진 올리기
            </button>
            <input
              ref={inputRef}
              className="photo-file-input"
              type="file"
              accept="image/*"
              onChange={handlePhotoChange}
            />
          </div>
        )}
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
