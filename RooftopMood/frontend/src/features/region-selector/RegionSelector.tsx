import type { Region } from "../../types";

type Props = {
  regions: Region[];
  selectedRegion: string | null;
  loading: boolean;
  onSelect: (regionCode: string) => void;
};

export function RegionSelector({
  regions,
  selectedRegion,
  loading,
  onSelect,
}: Props) {
  return (
    <section className="section-block reveal">
      <div className="section-heading">
        <h2>어디로 갈까요?</h2>
        <p>선택한 뷰를 볼 수 있는 동네만 보여드려요.</p>
      </div>
      {loading ? (
        <div className="skeleton-line">지역을 찾고 있어요…</div>
      ) : (
        <div className="region-wrap">
          {regions.map((region) => (
            <button
              key={region.code}
              type="button"
              className={`region-chip ${selectedRegion === region.code ? "selected" : ""}`}
              onClick={() => onSelect(region.code)}
            >
              {region.name}
              <span>{region.cafeCount}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
