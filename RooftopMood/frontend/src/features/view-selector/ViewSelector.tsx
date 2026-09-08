import type { ViewCode, ViewOption } from "../../types";

type Props = {
  views: ViewOption[];
  selectedView: ViewCode | null;
  onSelect: (view: ViewCode) => void;
};

export function ViewSelector({ views, selectedView, onSelect }: Props) {
  return (
    <section className="section-block">
      <div className="section-heading">
        <h2>어떤 뷰가 좋아요?</h2>
        <p>보고 싶은 풍경을 하나 골라주세요.</p>
      </div>
      <div className="view-grid">
        {views.map((view) => {
          const selected = selectedView === view.code;
          return (
            <button
              key={view.code}
              type="button"
              className={`choice-button ${selected ? "selected" : ""}`}
              onClick={() => onSelect(view.code)}
            >
              <span className="choice-emoji">{view.emoji}</span>
              <span>{view.name}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
