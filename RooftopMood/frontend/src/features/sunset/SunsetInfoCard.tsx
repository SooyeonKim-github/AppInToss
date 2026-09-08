import type { SunsetInfo } from "../../types";

export function SunsetInfoCard({ sunset }: { sunset: SunsetInfo }) {
  const weather = sunset.weather;

  return (
    <section className="sunset-card" aria-label="오늘 서울 일몰 정보">
      <div>
        <p className="eyebrow">오늘 서울 일몰 시간 🌇</p>
        <strong className="sunset-time">{sunset.time}</strong>
      </div>
      <div className="sunset-score-box">
        <span>노을 기대도</span>
        <strong>{sunset.score}점</strong>
      </div>
      <p className="sunset-message">{sunset.message}</p>
      <div className="weather-facts" aria-label="노을 기대도 날씨 근거">
        <span>☁️ 구름 {weather.cloudCover}%</span>
        <span>☔ 강수 {weather.precipitationProbability}%</span>
        <span>👀 시정 {weather.visibilityKm}km</span>
      </div>
      {weather.source === "OPEN_METEO" ? (
        <small className="weather-source">Weather data: Open-Meteo</small>
      ) : null}
    </section>
  );
}
