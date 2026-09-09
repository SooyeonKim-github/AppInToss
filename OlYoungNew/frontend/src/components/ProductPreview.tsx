import type { HomeProduct } from "../types/product";

interface ProductPreviewProps {
  product: HomeProduct;
  inMix: boolean;
  onAddToMix: (productId: number) => void;
}

const statusLabel: Record<HomeProduct["status"], string> = {
  HOT: "지금 가장 빠르게 뜨는 중",
  RISING: "반응이 빠르게 올라오는 중",
  NEW: "막 발견된 신상",
  WATCH: "반응을 지켜보는 신상",
};

export function ProductPreview({ product, inMix, onAddToMix }: ProductPreviewProps) {
  return (
    <section className="product-preview" aria-live="polite">
      <div className="product-preview__topline">
        <span className="product-preview__brand">{product.brandName}</span>
        <span className={`status-dot status-dot--${product.status.toLowerCase()}`}>{statusLabel[product.status]}</span>
      </div>
      <h2>{product.productName}</h2>

      <div className="product-preview__signal-row">
        <div className="reaction-pill">
          <span>🔥 반응지수</span>
          <strong>{product.reactionScore}</strong>
        </div>
        <span className="score-change">▲ {product.scoreChange}</span>
        <span className="launch-age">출시 {product.daysSinceLaunch}일차</span>
      </div>

      <div className="tag-row">
        {product.tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}
      </div>

      <div className="product-preview__actions">
        <button className="secondary-button" type="button">왜 뜨지?</button>
        <button
          className={`primary-button${inMix ? " primary-button--done" : ""}`}
          type="button"
          onClick={() => onAddToMix(product.id)}
          disabled={inMix}
        >
          {inMix ? "조합에 담김 ✓" : "+ 조합해보기"}
        </button>
      </div>
    </section>
  );
}
