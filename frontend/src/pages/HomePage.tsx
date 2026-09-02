import type { UserStats } from '../types/stats';
import { StatsCard } from '../components/StatsCard';

type Props = { stats: UserStats | null; onStart: () => void };
export function HomePage({ stats, onStart }: Props) {
  return (
    <main className="screen home-screen">
      <div className="mascot">🐿️</div>
      <h1>오를까?</h1>
      <p className="subtitle">입문편 · 차트를 보고 감각을 키워봐요</p>
      <button className="primary-button big" onClick={onStart}>오늘의 차트 5문제</button>
      {stats && stats.totalAttempts > 0 && <StatsCard stats={stats} />}
      <p className="disclaimer">과거 차트를 활용한 게임형 학습이며 투자 권유가 아니에요.</p>
    </main>
  );
}
