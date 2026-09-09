import { useEffect, useMemo, useState } from "react";
import { getHomeProducts } from "../api/client";
import { ProductBubbleCluster } from "../components/ProductBubbleCluster";
import { ProductPreview } from "../components/ProductPreview";
import type { HomeProduct } from "../types/product";

interface HomePageProps {
  mixIds: number[];
  onAddToMix: (productId: number) => void;
}

export function HomePage({ mixIds, onAddToMix }: HomePageProps) {
  const [products, setProducts] = useState<HomeProduct[]>([]);
  const [selectedId, setSelectedId] = useState<number>(101);

  useEffect(() => {
    void getHomeProducts().then((items) => {
      setProducts(items);
      if (items.length > 0) setSelectedId(items[0].id);
    });
  }, []);

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === selectedId) ?? products[0],
    [products, selectedId],
  );

  return (
    <main className="home-page page-shell">
      <header className="home-header">
        <div>
          <div className="eyebrow">NEW BEAUTY RADAR</div>
          <h1>올영뉴</h1>
          <p>이번 달 뭐가 새로 나왔지?</p>
        </div>
        <div className="tracking-badge">
          <strong>{products.length || 15}</strong>
          <span>신상 추적 중</span>
        </div>
      </header>

      {products.length === 0 ? (
        <div className="bubble-skeleton" aria-label="신상 불러오는 중"><i /><i /><i /><i /><i /></div>
      ) : (
        <ProductBubbleCluster products={products} selectedId={selectedId} onSelect={setSelectedId} />
      )}

      {selectedProduct && (
        <ProductPreview product={selectedProduct} inMix={mixIds.includes(selectedProduct.id)} onAddToMix={onAddToMix} />
      )}
    </main>
  );
}
