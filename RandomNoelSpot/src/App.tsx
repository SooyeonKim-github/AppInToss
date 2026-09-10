import { useMemo, useState } from "react";
import { Accuracy, getCurrentLocation } from "@apps-in-toss/web-framework";
import { sunsetSpots, type SpotCategory, type SunsetSpot } from "./spots";
import { rankedScore, sunsetInfo, type Position } from "./sunset";

const filters: { id: "all" | SpotCategory; label: string }[] = [
  { id:"all", label:"✨ 아무 데나 좋아" }, { id:"cafe", label:"☕ 카페에서" },
  { id:"park", label:"🌿 공원에서" }, { id:"bridge", label:"🌉 육교 위에서" },
  { id:"commute", label:"🚇 퇴근길에" }, { id:"walk", label:"🚶 산책하면서" },
];

export function App() {
  const [filter, setFilter] = useState<"all" | SpotCategory>("all");
  const [currentId, setCurrentId] = useState(sunsetSpots[0].id);
  const [busy, setBusy] = useState(false);
  const [savedIds, setSavedIds] = useState<string[]>(() => JSON.parse(localStorage.getItem("random-noel:saved") ?? "[]"));
  const [position, setPosition] = useState<Position>();
  const sun = useMemo(() => sunsetInfo(37.5665, 126.978), []);
  const current = sunsetSpots.find((spot) => spot.id === currentId) ?? sunsetSpots[0];
  const score = rankedScore(current, sun.azimuth, position);

  function poolFor(nextFilter = filter) { return nextFilter === "all" ? sunsetSpots : sunsetSpots.filter((spot) => spot.categories.includes(nextFilter)); }
  function pick(nextFilter = filter) {
    const pool = poolFor(nextFilter); const alternatives = pool.filter((spot) => spot.id !== currentId); const choices = alternatives.length ? alternatives : pool;
    setBusy(true); window.setTimeout(() => { setCurrentId(choices[Math.floor(Math.random()*choices.length)].id); setBusy(false); }, 680);
  }
  function selectFilter(next: "all" | SpotCategory) { setFilter(next); pick(next); }
  function toggleSaved() { setSavedIds((ids) => { const next = ids.includes(current.id) ? ids.filter((id) => id !== current.id) : [...ids,current.id]; localStorage.setItem("random-noel:saved", JSON.stringify(next)); return next; }); }
  async function useMyLocation() {
    try { const result = await getCurrentLocation({ accuracy: Accuracy.Balanced }); setPosition({ latitude: result.coords.latitude, longitude: result.coords.longitude }); }
    catch { navigator.geolocation?.getCurrentPosition(({coords}) => setPosition({ latitude:coords.latitude, longitude:coords.longitude })); }
  }
  const mapUrl = `https://map.kakao.com/link/map/${encodeURIComponent(current.name)},${current.latitude},${current.longitude}`;
  const sunsetMinutes = Number(sun.time.slice(0,2))*60 + Number(sun.time.slice(3));
  const arrivalTotal = Math.max(0, sunsetMinutes - 30);
  const arrival = `${String(Math.floor(arrivalTotal/60)).padStart(2,"0")}:${String(arrivalTotal%60).padStart(2,"0")}`;

  return <main className="app-shell">
    <header className="hero"><div><p>오늘 서울 일몰 <strong>{sun.time}</strong></p><h1>오늘 노을,<br/>어디서 볼까?</h1></div><span className="sun">☀</span></header>
    <section className="filter-section"><div className="section-title"><h2>어떻게 보고 싶어요?</h2><button onClick={useMyLocation}>{position ? "✓ 현재 위치 적용" : "⌖ 내 위치 적용"}</button></div><div className="filters" role="radiogroup">{filters.map((item)=><button key={item.id} className={filter===item.id?"active":""} role="radio" aria-checked={filter===item.id} onClick={()=>selectFilter(item.id)}>{item.label}</button>)}</div></section>
    <section className="card-shell" aria-live="polite">{busy ? <div className="loading"><span>🌇</span><b>노을 자리를 찾는 중…</b><small>해가 지는 방향을 살펴보고 있어요</small></div> : null}
      <article className={`spot-card ${busy?"muted":""}`}><div className={`photo ${current.theme}`}><div className="photo-top"><span>TODAY'S PICK</span><button onClick={toggleSaved} aria-label="저장">{savedIds.includes(current.id)?"♥":"♡"}</button></div><div><small>{current.viewLabel}</small><h2>{current.name}</h2></div></div>
      <div className="card-body"><div className="meta"><span>{current.typeLabel}</span><b>🚇 {current.station} 도보 {current.walkMinutes}분</b></div><p className="guide">“{current.guide}”</p><div className="facts"><div><small>노을 기대도</small><strong>{score}%</strong></div><div><small>추천 도착 시간</small><strong>{arrival}</strong></div></div><p className="address">📍 {current.address}</p><a className="kakao" href={mapUrl} target="_blank" rel="noreferrer"><span><i/>카카오맵에서 위치 보기</span><b>↗</b></a>{current.verification==="candidate"?<p className="candidate">현장 검증 전 후보 스팟이에요. 공개 전 좌표·시야·안전성을 확인합니다.</p>:null}</div></article>
    </section>
    <div className="actions"><button className="save" onClick={toggleSaved}><b>{savedIds.includes(current.id)?"♥ 저장했어요":"♡ 여기 갈래요"}</b><small>나중에 다시 볼게요</small></button><button className="reroll" onClick={()=>pick()} disabled={busy}><b>🎲 다시 뽑기</b><small>다른 곳도 볼래요</small></button></div>
    <footer>멀리 가지 않아도, 서울에는 노을 자리가 있어요.</footer>
  </main>;
}
