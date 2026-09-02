import type { Candle } from '../types/quiz';

type Props = { candles: Candle[]; showFuture?: boolean };

export function ChartCard({ candles }: Props) {
  if (!candles.length) return <div className="chart-empty">차트 데이터가 없어요.</div>;
  const closes = candles.map((c) => c.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const width = 320;
  const height = 180;
  const pad = 16;
  const span = Math.max(max - min, 1);
  const points = closes.map((value, index) => {
    const x = pad + (index / Math.max(closes.length - 1, 1)) * (width - pad * 2);
    const y = height - pad - ((value - min) / span) * (height - pad * 2);
    return `${x},${y}`;
  }).join(' ');
  return (
    <div className="chart-card" aria-label="주가 차트">
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        <line x1="16" y1="45" x2="304" y2="45" className="grid-line" />
        <line x1="16" y1="90" x2="304" y2="90" className="grid-line" />
        <line x1="16" y1="135" x2="304" y2="135" className="grid-line" />
        <polyline points={points} fill="none" className="price-line" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="chart-caption">종목명과 날짜는 정답 공개 전까지 숨겨져요</div>
    </div>
  );
}
