import type { UserStats } from '../types/stats';
import { StatsCard } from '../components/StatsCard';
export function DailyResultPage({ score, total, stats, onHome }: { score: number; total: number; stats: UserStats | null; onHome: () => void }) {
  return (
    <main className="screen">
      <div className="mascot">🐿️✨</div>
      <h1>오늘도 완료!</h1>
      <p className="daily-score">{total}문제 중 <strong>{score}개</strong> 맞혔어요.</p>
      {stats && <StatsCard stats={stats} />}
      <button className="primary-button" onClick={onHome}>홈으로</button>
    </main>
  );
}
