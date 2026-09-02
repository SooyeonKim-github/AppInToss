type Props = { returns: { d1: number; d5: number; d10: number; d20: number } };
const fmt = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
export function ReturnProgress({ returns }: Props) {
  return (
    <div className="returns-grid">
      <div><span>D+1</span><strong>{fmt(returns.d1)}</strong></div>
      <div><span>D+5</span><strong>{fmt(returns.d5)}</strong></div>
      <div><span>D+10</span><strong>{fmt(returns.d10)}</strong></div>
      <div><span>D+20</span><strong>{fmt(returns.d20)}</strong></div>
    </div>
  );
}
