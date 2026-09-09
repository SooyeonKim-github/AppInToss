import { useState } from "react";
import { MenuIllustration } from "./MenuIllustration";
import type { RankingItem } from "../types";

function compact(value: number) {
  return new Intl.NumberFormat("ko-KR", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

export function PopularRanking({ items }: { items: RankingItem[] }) {
  const [atBottom, setAtBottom] = useState(false);
  const hasOverflow = items.length > 4;

  const handleScroll: React.UIEventHandler<HTMLOListElement> = (event) => {
    const target = event.currentTarget;
    const reachedBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 3;
    setAtBottom(reachedBottom);
  };

  if (!items.length) {
    return (
      <section className="ranking-card">
        <div className="section-title"><span>🔥 오늘 인기 저메추</span><small>첫 하트를 기다리는 중</small></div>
      </section>
    );
  }

  return (
    <section className="ranking-card">
      <div className="section-title"><span>🔥 오늘 인기 저메추</span><small>하트 순 · 실시간</small></div>

      <div className="ranking-scroll-shell">
        <ol className="ranking-scroll-list" onScroll={handleScroll}>
          {items.map((item) => (
            <li key={item.menuId}>
              <span className="rank">{item.rank}</span>
              <MenuIllustration imageKey={item.imageKey} emoji={item.emoji} label={item.name} size="rank" />
              <strong>{item.name}</strong>
              <span className="rank-like">❤️ {compact(item.likes)}</span>
            </li>
          ))}
        </ol>

        {hasOverflow && !atBottom && <div className="ranking-fade" aria-hidden="true" />}
      </div>
    </section>
  );
}
