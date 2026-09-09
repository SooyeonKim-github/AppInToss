import { ProductArt } from "../components/ProductArt";
import { mockProducts } from "../mocks/products";

interface MixPageProps {
  mixIds: number[];
  onRemove: (productId: number) => void;
}

export function MixPage({ mixIds, onRemove }: MixPageProps) {
  const products = mockProducts.filter((product) => mixIds.includes(product.id));
  const benefitCount = products.flatMap((product) => product.benefits).reduce<Record<string, number>>((acc, benefit) => {
    acc[benefit] = (acc[benefit] ?? 0) + 1;
    return acc;
  }, {});
  const topBenefits = Object.entries(benefitCount).sort((a, b) => b[1] - a[1]).slice(0, 4);

  return (
    <main className="mix-page page-shell">
      <header className="sub-header">
        <div className="eyebrow">MY BEAUTY MIX</div>
        <h1>내 조합</h1>
        <p>담은 제품의 역할이 겹치는지 한눈에 확인해요.</p>
      </header>

      {products.length === 0 ? (
        <section className="empty-mix">
          <div className="empty-mix__icon">◌</div>
          <h2>아직 담은 신상이 없어요</h2>
          <p>홈에서 마음에 드는 제품을 눌러<br />‘조합해보기’에 담아보세요.</p>
        </section>
      ) : (
        <>
          <section className="mix-strip">
            {products.map((product) => (
              <article key={product.id} className="mix-product">
                <button type="button" onClick={() => onRemove(product.id)} aria-label={`${product.productName} 제거`}>×</button>
                <ProductArt product={product} compact />
                <strong>{product.art.label}</strong>
              </article>
            ))}
          </section>

          <section className="mix-summary-card">
            <div className="mix-score-circle">{Math.min(92, 72 + products.length * 5)}</div>
            <div>
              <span>조합 미리보기</span>
              <h2>{products.length >= 2 ? "밸런스를 분석하고 있어요" : "하나 더 담으면 비교할 수 있어요"}</h2>
              <p>성분 DB 연결 후 중복·주의 조합·추천 루틴까지 확장됩니다.</p>
            </div>
          </section>

          <section className="coverage-card">
            <h2>지금 조합이 채우는 케어</h2>
            {topBenefits.length === 0 ? <p>제품을 더 담아주세요.</p> : topBenefits.map(([benefit, count]) => (
              <div className="coverage-row" key={benefit}>
                <span>{benefit}</span>
                <div><i style={{ width: `${Math.min(100, 38 + count * 28)}%` }} /></div>
                <strong>{count >= 2 ? "강함" : "보통"}</strong>
              </div>
            ))}
          </section>
        </>
      )}
    </main>
  );
}
