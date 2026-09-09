import { useEffect, useRef, useState } from "react";
import { loadKakaoMaps } from "./kakaoMaps";
import type { SunsetSpot } from "./spots";

type Props = {
  spots: SunsetSpot[];
  selectedId: string | null;
  onSelect: (spot: SunsetSpot) => void;
  compact?: boolean;
};

export function SunsetMap({ spots, selectedId, onSelect, compact = false }: Props) {
  const mapNodeRef = useRef<HTMLDivElement | null>(null);
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    let disposed = false;
    let map: any;

    loadKakaoMaps()
      .then((kakao) => {
        if (disposed || !mapNodeRef.current) return;
        const center = new kakao.maps.LatLng(37.5197, 126.9782);
        map = new kakao.maps.Map(mapNodeRef.current, {
          center,
          level: compact ? 7 : 6,
        });

        spots.forEach((spot) => {
          const position = new kakao.maps.LatLng(spot.latitude, spot.longitude);
          const marker = new kakao.maps.Marker({ map, position });
          kakao.maps.event.addListener(marker, "click", () => onSelect(spot));
        });
        setMapReady(true);
      })
      .catch(() => setMapReady(false));

    return () => {
      disposed = true;
      map = undefined;
    };
  }, [compact, onSelect, spots]);

  return (
    <div className={compact ? "map-frame map-frame--compact" : "map-frame"}>
      <div ref={mapNodeRef} className={`kakao-map ${mapReady ? "is-ready" : ""}`} />
      {!mapReady ? (
        <div className="fallback-map" aria-label="노을핀 지도 미리보기">
          <div className="river river-a" />
          <div className="river river-b" />
          <div className="road road-a" />
          <div className="road road-b" />
          <span className="map-label map-label--1">용산</span>
          <span className="map-label map-label--2">한강</span>
          {spots.slice(0, compact ? 4 : spots.length).map((spot, index) => (
            <button
              key={spot.id}
              type="button"
              className={`sunset-pin sunset-pin--${index + 1} ${selectedId === spot.id ? "is-selected" : ""}`}
              onClick={() => onSelect(spot)}
              aria-label={`${spot.name} 보기`}
            >
              <span>{spot.transit ? "🚇" : "🌅"}</span>
            </button>
          ))}
          <span className="my-location" aria-label="내 위치">●</span>
        </div>
      ) : null}
      <div className="map-gradient" />
    </div>
  );
}
