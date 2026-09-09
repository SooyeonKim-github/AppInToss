const PALETTES = [
  ["#FFF0E2", "#F7A56A", "#6F9A63"],
  ["#FFF2D8", "#F2B84B", "#D86C4D"],
  ["#EAF5EA", "#7CAD80", "#E07A65"],
  ["#FFE7DD", "#E46B52", "#F0B44B"],
  ["#EDF1F8", "#8499BE", "#E79C75"],
  ["#EEF6DF", "#86A95A", "#E8A34D"],
  ["#FFF0D6", "#D68B45", "#B35C46"],
  ["#FFE7D8", "#E46743", "#72A05D"],
  ["#F7F1E3", "#D6A957", "#82A072"],
] as const;

const GARNISH = ["🌿", "🌶️", "🥬", "🧄", "🍋", "🥚", "🧀", "🍅", "🫛", "🥕"] as const;

interface Props {
  imageKey?: string | null;
  emoji: string;
  label: string;
  size?: "hero" | "rank";
}

function imageIndex(imageKey?: string | null) {
  if (!imageKey?.startsWith("menu-")) return -1;
  const value = Number.parseInt(imageKey.slice(5), 10);
  return Number.isFinite(value) && value >= 0 && value < 296 ? value : -1;
}

export function MenuIllustration({ imageKey, emoji, label, size = "hero" }: Props) {
  const index = imageIndex(imageKey);

  if (index < 0) {
    return (
      <div className={`menu-illustration illustration-${size} illustration-fallback`} role="img" aria-label={label}>
        {emoji}
      </div>
    );
  }

  const [background, accent, garnishColor] = PALETTES[index % PALETTES.length];
  const garnish = GARNISH[(index * 7 + 3) % GARNISH.length];
  const garnishX = 100 + (index * 11) % 16;
  const garnishY = 42 + (index * 13) % 14;
  const foodSize = 62 + (index % 9);

  return (
    <svg
      className={`menu-illustration illustration-${size}`}
      viewBox="0 0 144 144"
      role="img"
      aria-label={`${label} 일러스트`}
    >
      <rect x="4" y="4" width="136" height="136" rx="28" fill={background} />
      <circle cx="28" cy="28" r="5" fill={garnishColor} opacity=".35" />
      <circle cx="116" cy="118" r="4" fill={accent} opacity=".30" />
      <ellipse cx="72" cy="91" rx="52" ry="31" fill="#fffdf8" stroke={accent} strokeWidth="3" />
      <ellipse cx="72" cy="87" rx="40" ry="19" fill={accent} opacity=".10" />
      <text x="72" y="99" textAnchor="middle" fontSize={foodSize}>{emoji}</text>
      <text x={garnishX} y={garnishY} textAnchor="middle" fontSize="19">{garnish}</text>
    </svg>
  );
}
