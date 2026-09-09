import { mockProducts } from "../mocks/products";
import { ProductArt } from "../components/ProductArt";

interface NewProductsPageProps {
  mixIds: number[];
  onAddToMix: (productId: number) => void;
}

export function NewProductsPage({ mixIds, onAddToMix }: NewProductsPageProps) {
  return (
    <main className="list-page page-shell">
      <header className="sub-header">
        <div className="eyebrow">SEPTEMBER NEW</div>
        <h1>이번 달 신상</h1>
        <p>검색 없이, 지금 반응 오는 제품부터 둘러보세요.</p>
      </header>

      <div className="quick-filters" aria-label="신상 필터">
        <button type="button" className="active">🔥 급상승</button>
        <button type="button">🆕 최신</button>
        <button type="button">💸 할인</button>
        <button type="button">⭐ 만족도</button>
      </div>

      <section className="product-list">
        {mockProducts.map((product, index) => (
          <article className="feed-card" key={product.id}>
            <div className="feed-card__rank">{String(index + 1).padStart(2, "0")}</div>
            <div className="feed-card__art"><ProductArt product={product} /></div>
            <div className="feed-card__body">
              <span className="feed-card__brand">{product.brandName}</span>
              <h2>{product.productName}</h2>
              <div className="feed-card__score"><strong>🔥 {product.reactionScore}</strong><span>▲ {product.scoreChange}</span></div>
              <div className="tag-row">{product.tags.slice(0, 2).map((tag) => <span key={tag}>{tag}</span>)}</div>
            </div>
            <button
              className="round-add"
              type="button"
              disabled={mixIds.includes(product.id)}
              onClick={() => onAddToMix(product.id)}
              aria-label={`${product.productName} 조합하기`}
            >
              {mixIds.includes(product.id) ? "✓" : "+"}
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
