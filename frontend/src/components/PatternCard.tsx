import type { ChartFeatureSignal } from '../types/quiz';

type Props = {
  name: string;
  tip: string;
  features?: ChartFeatureSignal[];
  onStart: () => void;
};

const iconFor = (direction: ChartFeatureSignal['direction']) => {
  if (direction === 'BULLISH') return '📈';
  if (direction === 'BEARISH') return '📉';
  return '🔎';
};

export function PatternCard({ name, tip, features = [], onStart }: Props) {
  return (
    <section className="pattern-card">
      <div className="eyebrow">오늘의 차트 읽기</div>
      <h2>{features.length ? '눈여겨볼 점' : name}</h2>
      <div className="pattern-illustration">🔎</div>

      {features.length ? (
        <ul className="feature-reading-list">
          {features.map((feature) => (
            <li key={feature.key}>
              <span>{iconFor(feature.direction)}</span>
              <div>
                <strong>{feature.label}</strong>
                <p>{feature.text}</p>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>{tip}</p>
      )}

      <button className="primary-button" onClick={onStart}>차트 보기</button>
    </section>
  );
}
