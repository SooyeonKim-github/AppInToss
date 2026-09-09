import type { HomeProduct } from "../types/product";

interface ProductArtProps {
  product: HomeProduct;
  compact?: boolean;
}

export function ProductArt({ product, compact = false }: ProductArtProps) {
  if (product.imageUrl) {
    return <img className="product-art__image" src={product.imageUrl} alt="" draggable={false} />;
  }

  return (
    <div
      className={`product-art${compact ? " product-art--compact" : ""}`}
      style={{ background: `linear-gradient(145deg, #FFFFFF 5%, ${product.art.soft} 92%)` }}
      aria-hidden="true"
    >
      <div className="product-art__cap" style={{ background: product.art.accent }} />
      <div className="product-art__bottle" style={{ borderColor: `${product.art.accent}66` }}>
        <span style={{ color: product.art.accent }}>{product.art.label}</span>
      </div>
      <div className="product-art__shine" />
    </div>
  );
}
