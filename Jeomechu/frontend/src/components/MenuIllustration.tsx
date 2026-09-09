import type { CSSProperties } from "react";

const SPRITE_KEYS = [
  "chicken", "samgyeopsal", "jeyuk_bokkeum", "kimchi_jjigae", "sushi", "donkkaseu",
  "maratang", "pasta", "hamburger", "dakgalbi", "sundubu_jjigae", "budae_jjigae",
  "dwaeji_gukbap", "jjimdak", "gamjatang", "bossam", "jokbal", "dakbokkeumtang",
  "jjukkumi_bokkeum", "yukhoe_bibimbap", "ramen", "maze_soba", "gyukatsu", "jjajangmyeon",
  "jjambbong", "tangsuyuk", "pizza", "steak", "risotto", "pho",
] as const;

const SPRITE_URL = `${import.meta.env.BASE_URL}menu-images/menu-sprite.svg`;

interface Props {
  imageKey?: string | null;
  emoji: string;
  label: string;
  size?: "hero" | "rank";
}

export function MenuIllustration({ imageKey, emoji, label, size = "hero" }: Props) {
  const index = imageKey ? SPRITE_KEYS.indexOf(imageKey as (typeof SPRITE_KEYS)[number]) : -1;

  if (index < 0) {
    return (
      <div className={`menu-illustration illustration-${size} illustration-fallback`} role="img" aria-label={label}>
        {emoji}
      </div>
    );
  }

  const column = index % 6;
  const row = Math.floor(index / 6);
  const style = {
    backgroundImage: `url("${SPRITE_URL}")`,
    backgroundPosition: `${column * 20}% ${row * 25}%`,
  } satisfies CSSProperties;

  return (
    <div
      className={`menu-illustration illustration-${size}`}
      style={style}
      role="img"
      aria-label={`${label} 일러스트`}
    />
  );
}
