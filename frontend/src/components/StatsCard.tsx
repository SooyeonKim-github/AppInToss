import type { UserStats } from '../types/stats';
const pct = (v: number) => `${v.toFixed(1)}%`;
export function StatsCard({ stats }: { stats: UserStats }) {
  return (
    <section className="stats-card">
      <h2>🐿️ 나의 차트 감각</h2>
      <div className="stats-row"><span>전체 정답률</span><strong>{pct(stats.accuracy)}</strong></div>
      <div className="stats-row"><span>상승 예측</span><strong>{stats.upPredictions}개</strong></div>
      <div className="stats-row highlight"><span>상승으로 고른 차트 D+20 평균</span><strong>{pct(stats.avgReturnD20)}</strong></div>
    </section>
  );
}
