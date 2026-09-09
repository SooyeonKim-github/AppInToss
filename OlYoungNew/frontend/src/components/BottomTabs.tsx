export type AppTab = "home" | "new" | "mix";

interface BottomTabsProps {
  current: AppTab;
  mixCount: number;
  onChange: (tab: AppTab) => void;
}

export function BottomTabs({ current, mixCount, onChange }: BottomTabsProps) {
  return (
    <nav className="bottom-tabs" aria-label="주요 메뉴">
      <button className={current === "home" ? "active" : ""} onClick={() => onChange("home")} type="button">
        <span>⌂</span>
        홈
      </button>
      <button className={current === "new" ? "active" : ""} onClick={() => onChange("new")} type="button">
        <span>✦</span>
        신상
      </button>
      <button className={current === "mix" ? "active" : ""} onClick={() => onChange("mix")} type="button">
        <span className="mix-tab-icon">◌{mixCount > 0 && <b>{mixCount}</b>}</span>
        조합
      </button>
    </nav>
  );
}
