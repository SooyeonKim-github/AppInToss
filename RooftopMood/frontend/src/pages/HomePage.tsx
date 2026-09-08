import { useEffect, useState } from "react";
import {
  fetchHome,
  fetchRecommendations,
  fetchRegions,
  fetchSunsetBest,
} from "../api/rooftopMood.api";
import { RecommendationCard } from "../features/recommendation/RecommendationCard";
import { RegionSelector } from "../features/region-selector/RegionSelector";
import { SunsetInfoCard } from "../features/sunset/SunsetInfoCard";
import { ViewSelector } from "../features/view-selector/ViewSelector";
import type {
  HomeResponse,
  Recommendation,
  Region,
  ViewCode,
} from "../types";

export function HomePage() {
  const [home, setHome] = useState<HomeResponse | null>(null);
  const [selectedView, setSelectedView] = useState<ViewCode | null>(null);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [sunsetBestMode, setSunsetBestMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [regionLoading, setRegionLoading] = useState(false);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHome()
      .then(setHome)
      .catch(() => setError("루프탑 정보를 불러오지 못했어요."))
      .finally(() => setLoading(false));
  }, []);

  async function handleViewSelect(view: ViewCode) {
    setSunsetBestMode(false);
    setSelectedView(view);
    setSelectedRegion(null);
    setRecommendations([]);
    setRegionLoading(true);
    try {
      const data = await fetchRegions(view);
      setRegions(data.regions);
    } catch {
      setError("지역 정보를 불러오지 못했어요.");
    } finally {
      setRegionLoading(false);
    }
  }

  async function handleRegionSelect(regionCode: string) {
    if (!selectedView) return;
    setSunsetBestMode(false);
    setSelectedRegion(regionCode);
    setRecommendationLoading(true);
    try {
      const data = await fetchRecommendations(selectedView, regionCode);
      setRecommendations(data.recommendations.slice(0, 5));
      window.setTimeout(() => {
        document
          .getElementById("recommendations")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch {
      setError("추천 카페를 불러오지 못했어요.");
    } finally {
      setRecommendationLoading(false);
    }
  }

  async function handleSunsetBest() {
    setRecommendationLoading(true);
    setSunsetBestMode(true);
    setSelectedView(null);
    setSelectedRegion(null);
    setRegions([]);
    try {
      const data = await fetchSunsetBest();
      setRecommendations(data.recommendations.slice(0, 5));
      window.setTimeout(() => {
        document
          .getElementById("recommendations")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    } catch {
      setError("오늘의 노을 추천을 불러오지 못했어요.");
    } finally {
      setRecommendationLoading(false);
    }
  }

  if (loading) {
    return <main className="app-shell loading-screen">루프탑무드를 준비하고 있어요…</main>;
  }

  if (!home) {
    return <main className="app-shell error-screen">{error ?? "오류가 발생했어요."}</main>;
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="brand-kicker">ROOFTOP MOOD</p>
        <h1>{home.app.name}</h1>
        <p className="hero-description">{home.app.description}</p>
      </header>

      <SunsetInfoCard sunset={home.sunset} />

      <ViewSelector
        views={home.views}
        selectedView={selectedView}
        onSelect={handleViewSelect}
      />

      {selectedView ? (
        <RegionSelector
          regions={regions}
          selectedRegion={selectedRegion}
          loading={regionLoading}
          onSelect={handleRegionSelect}
        />
      ) : null}

      <button className="sunset-best-button" type="button" onClick={handleSunsetBest}>
        <span>🌇</span>
        <div>
          <strong>오늘 노을 보기 제일 좋은 곳</strong>
          <small>서울 전체에서 오늘의 TOP 5를 골라드려요</small>
        </div>
        <span>›</span>
      </button>

      {error ? <p className="inline-error">{error}</p> : null}

      {(recommendationLoading || recommendations.length > 0) && (
        <section id="recommendations" className="recommendations section-block">
          <div className="section-heading recommendation-heading">
            <p className="ranking-kicker">ROOFTOP TOP 5</p>
            <h2>
              {sunsetBestMode
                ? "오늘 노을 추천 TOP 5 🌇"
                : "이 지역 루프탑 추천 TOP 5 🌇"}
            </h2>
            <p>
              {sunsetBestMode
                ? "오늘 날씨와 노을 방향이 잘 맞는 순서예요."
                : "선택한 뷰와 오늘 노을을 함께 보기 좋은 순서예요."}
            </p>
          </div>
          {recommendationLoading ? (
            <div className="skeleton-card">루프탑 TOP 5를 고르고 있어요…</div>
          ) : (
            <div className="recommendation-list">
              {recommendations.map((item, index) => (
                <RecommendationCard key={item.id} item={item} rank={index + 1} />
              ))}
            </div>
          )}
        </section>
      )}

      <footer className="footer-note">서울의 예쁜 루프탑을 하나씩 모으는 중이에요 🌆</footer>
    </main>
  );
}
