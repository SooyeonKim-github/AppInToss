import { MenuIllustration } from "./MenuIllustration";
import type { RankingItem } from "../types";

function compact(value: number) {
  return new Intl.NumberFormat("ko-KR", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function PopularRanking({ items }: { items: RankingItem[] }) {
  if (!items.length) {
    return (
      <section className="ranking-card">
        <div className="section-title"><span>🔥 오늘 인기 저메추</span><small>첫 하트를 기다리는 중</small></div>
      </section>
    );
  }

  return (
    <section className="ranking-card">
      <div className="section-title"><span>🔥 오늘 인기 저메추</span><small>실시간</small></div>
      <ol>
        {items.slice(0, 3).map((item) => (
          <li key={item.menuId}>
            <span className="rank">{item.rank}</span>
            <MenuIllustration imageKey={item.imageKey} emoji={item.emoji} label={item.name} size="rank" />
            <strong>{item.name}</strong>
            <span className="rank-like">❤️ {compact(item.likes)}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
