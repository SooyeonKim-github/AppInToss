import type { Recommendation } from "../../types";

export function RecommendationCard({
  item,
  rank,
}: {
  item: Recommendation;
  rank?: number;
}) {
  const sunset = item.todaySunsetInfo;

  return (
    <article className="recommendation-card">
      <div className="recommendation-image" aria-hidden="true">
        {item.imageUrl ? <img src={item.imageUrl} alt="" /> : <span>🌇</span>}
        {rank ? <span className="rank-badge">TOP {rank}</span> : null}
      </div>
      <div className="recommendation-body">
        <div className="card-title-row">
          <div>
            <p className="region-label">{item.regionName}</p>
            <h3>{item.name}</h3>
          </div>
          <div className="score-pill">{item.score}점</div>
        </div>

        <p className="view-description">{item.viewDescription}</p>

        <div className={`today-sunset ${sunset.visible ? "visible" : "muted"}`}>
          <div className="today-sunset-title">
            <span>🌇 오늘의 노을</span>
            <strong>{sunset.sunsetTime}</strong>
          </div>
          <p>{sunset.message}</p>
          <div className="today-sunset-meta">
            <span>BEST {sunset.bestTime}</span>
            <span>방향 일치 {sunset.alignmentScore}점</span>
          </div>
        </div>

        <div className="tag-row">
          {item.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
        <p className="seat-tip">💡 {item.bestSeatTip}</p>
      </div>
    </article>
  );
}
