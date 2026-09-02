type Props = { name: string; tip: string; onStart: () => void };
export function PatternCard({ name, tip, onStart }: Props) {
  return (
    <section className="pattern-card">
      <div className="eyebrow">오늘의 패턴</div>
      <h2>{name}</h2>
      <div className="pattern-illustration">📈</div>
      <p>{tip}</p>
      <button className="primary-button" onClick={onStart}>연습 시작</button>
    </section>
  );
}
