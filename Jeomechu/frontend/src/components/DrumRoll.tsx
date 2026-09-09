export function DrumRoll() {
  return (
    <section className="drum-roll" aria-live="polite">
      <p className="eyebrow">오늘 당신의 저메추는…</p>
      <div className="drum">🥁</div>
      <strong>두구두구</strong>
      <div className="loading-dots" aria-hidden="true"><span /><span /><span /></div>
    </section>
  );
}
