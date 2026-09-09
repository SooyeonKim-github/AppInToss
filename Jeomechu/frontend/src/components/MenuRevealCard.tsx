import { MenuIllustration } from "./MenuIllustration";
import type { Menu } from "../types";

const rarityCopy = {
  COMMON: "오늘의 저메추",
  UNCOMMON: "✨ 오늘은 조금 색다르게",
  RARE: "👀 이거 먹어본 적 있어요?",
};

const categoryLabel: Record<string, string> = {
  KOREAN: "한식",
  CHICKEN_SNACK: "치킨 · 분식",
  JAPANESE: "일식",
  CHINESE: "중식",
  WESTERN: "양식",
  SOUTHEAST_ASIA: "동남아",
  INDIAN_MIDDLE_EAST: "인도 · 중동",
  MEXICAN_WORLD: "세계 음식",
  LIGHT_HOME: "간편식 · 집밥",
};

export function MenuRevealCard({ menu }: { menu: Menu }) {
  return (
    <section className={`menu-card rarity-${menu.rarity.toLowerCase()}`}>
      <p className="rarity-copy">{rarityCopy[menu.rarity]}</p>
      <MenuIllustration imageKey={menu.imageKey} emoji={menu.emoji} label={menu.name} />
      <h1>{menu.name}</h1>
      <p className="category">{categoryLabel[menu.category] ?? menu.category}</p>
      <p className="tagline">{menu.tagline}</p>
      {menu.rarity === "RARE" && <span className="rare-chip">RARE MENU ✨</span>}
    </section>
  );
}
