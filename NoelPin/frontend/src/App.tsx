import { useCallback, useMemo, useRef, useState } from "react";
import { Accuracy, getCurrentLocation } from "@apps-in-toss/web-framework";
import { SunsetMap } from "./SunsetMap";
import { sunsetSpots, type SunsetSpot } from "./spots";

const SUNSET_TIME = "18:48";

export function App() {
  const mapSectionRef = useRef<HTMLElement | null>(null);
  const [selectedSpot, setSelectedSpot] = useState<SunsetSpot | null>(null);
  const [locationMessage, setLocationMessage] = useState("내 주변 기준");
  const [savedIds, setSavedIds] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("noel-pin:saved") ?? "[]");
    } catch {
      return [];
    }
  });

  const nearbySpots = useMemo(() => sunsetSpots.filter((spot) => !spot.transit), []);
  const transitSpot = useMemo(() => sunsetSpots.find((spot) => spot.transit) ?? null, []);
  const heroSpot = nearbySpots[0];

  const handleSelect = useCallback((spot: SunsetSpot) => setSelectedSpot(spot), []);

  async function scrollToMap() {
    mapSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
      await getCurrentLocation({ accuracy: Accuracy.Balanced });
      setLocationMessage("현재 위치 기준");
      return;
    } catch {
      // Local browser preview fallback. Apps-in-Toss uses getCurrentLocation above.
    }

    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      () => setLocationMessage("현재 위치 기준"),
      () => setLocationMessage("내 주변 기준"),
      { enableHighAccuracy: false, timeout: 5000, maximumAge: 300000 },
    );
  }

  function toggleSaved(id: string) {
    setSavedIds((current) => {
      const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
      localStorage.setItem("noel-pin:saved", JSON.stringify(next));
      return next;
    });
  }

  return (
    <main className="app-shell">
      <section className="hero-section">
        <div className="topbar">
          <div className="brand-mark"><span>🌇</span><strong>퇴근길 노을핀</strong></div>
          <button className="icon-button" type="button" aria-label="저장한 노을핀">♡</button>
        </div>

        <div className="hero-copy">
          <p className="eyebrow">오늘 하루도 수고했어요</p>
          <h1>오늘도 고생했어요.<br />집에 가기 전, 노을 보고 갈까요?</h1>
          <div className="sunset-time"><span>🌅</span><strong>오늘 일몰 {SUNSET_TIME}</strong></div>
        </div>

        <button className="primary-button" type="button" onClick={scrollToMap}>
          <span>📍</span> 지금 내 퇴근길 노을 보기
        </button>

        <section className="nearby-preview">
          <div className="section-title-row">
            <div><p className="section-kicker">{locationMessage}</p><h2>지금 내 주변엔</h2></div>
            <span className="distance-chip">도보 {heroSpot.walkMinutes}분</span>
          </div>

          <button className="hero-card" type="button" onClick={() => handleSelect(heroSpot)}>
            <div className="sunset-photo" aria-hidden="true">
              <div className="sun-disc" />
              <div className="skyline"><i /><i /><i /><i /><i /></div>
              <div className="bridge-line" />
            </div>
            <div className="hero-card-body">
              <div className="spot-heading"><strong>{heroSpot.name}</strong><span>›</span></div>
              <div className="tag-row">
                {heroSpot.tags.slice(0, 2).map((tag) => <span key={tag}>#{tag}</span>)}
              </div>
              <p>“{heroSpot.guide}”</p>
            </div>
          </button>

          {transitSpot ? (
            <button className="transit-card" type="button" onClick={() => handleSelect(transitSpot)}>
              <span className="transit-icon">🚇</span>
              <div><strong>지하철 안에서도 노을을 만나요</strong><small>창밖노을 구간 보기</small></div>
              <span>›</span>
            </button>
          ) : null}
        </section>

        <div className="map-peek-label"><span>내 주변 퇴근길 노을핀</span><b>⌄</b></div>
        <button className="map-peek" type="button" onClick={scrollToMap} aria-label="지도로 내려가기">
          <SunsetMap spots={sunsetSpots} selectedId={selectedSpot?.id ?? null} onSelect={handleSelect} compact />
        </button>
      </section>

      <section className="map-section" ref={mapSectionRef}>
        <div className="sticky-map-header">
          <div><p className="section-kicker">퇴근길에 잠깐</p><h2>내 주변 노을핀</h2></div>
          <div className="filter-row"><span className="filter-chip is-active">전체</span><span className="filter-chip">건물사이</span><span className="filter-chip">한강</span><span className="filter-chip">창밖</span></div>
        </div>

        <SunsetMap spots={sunsetSpots} selectedId={selectedSpot?.id ?? null} onSelect={handleSelect} />

        <div className="spot-strip">
          {sunsetSpots.map((spot) => (
            <button key={spot.id} className="mini-spot-card" type="button" onClick={() => handleSelect(spot)}>
              <span className="mini-icon">{spot.transit ? "🚇" : "🌅"}</span>
              <div><strong>{spot.shortName}</strong><small>{spot.transit ? "창밖노을" : `도보 ${spot.walkMinutes}분`}</small></div>
            </button>
          ))}
        </div>
      </section>

      <footer>멀리 가지 않아도, 서울에는 퇴근길 노을 자리가 있어요.</footer>

      {selectedSpot ? (
        <div className="sheet-backdrop" onClick={() => setSelectedSpot(null)}>
          <section className="detail-sheet" onClick={(event) => event.stopPropagation()}>
            <div className="sheet-handle" />
            <div className="sheet-topline">
              <div><p className="section-kicker">{selectedSpot.transit ? "🚇 창밖노을" : "📍 정확한 노을자리"}</p><h2>{selectedSpot.name}</h2></div>
              <button className="close-button" type="button" onClick={() => setSelectedSpot(null)}>×</button>
            </div>
            <div className="tag-row sheet-tags">{selectedSpot.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div>
            <div className="detail-grid">
              <div><small>{selectedSpot.transit ? "어디서 봐요" : "여기 서세요"}</small><strong>{selectedSpot.viewDirection}</strong></div>
              <div><small>언제 가요</small><strong>{selectedSpot.arrivalTip}</strong></div>
            </div>
            <p className="detail-description">{selectedSpot.guide}</p>
            {selectedSpot.transit ? (
              <div className="transit-detail">
                <span>{selectedSpot.transit.line}</span><b>{selectedSpot.transit.section}</b><small>{selectedSpot.transit.windowSide}</small>
              </div>
            ) : null}
            {selectedSpot.verification === "candidate" ? <p className="candidate-note">현장 검증 전 후보 스팟이에요. 실제 서비스 공개 전 좌표·시야·안전성을 확인합니다.</p> : null}
            <div className="sheet-actions">
              <button className="secondary-button" type="button" onClick={() => toggleSaved(selectedSpot.id)}>{savedIds.includes(selectedSpot.id) ? "♥ 저장됨" : "♡ 저장"}</button>
              <button className="primary-button sheet-primary" type="button" onClick={() => setSelectedSpot(null)}>이 자리 기억하기</button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
