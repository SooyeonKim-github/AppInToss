import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import type { HomeProduct } from "../types/product";
import { ProductArt } from "./ProductArt";

interface ProductBubbleClusterProps {
  products: HomeProduct[];
  selectedId: number;
  onSelect: (productId: number) => void;
}

interface Point {
  x: number;
  y: number;
}

const layout: Point[] = [
  { x: 0, y: 0 },
  { x: -104, y: -74 },
  { x: 106, y: -78 },
  { x: -126, y: 46 },
  { x: 126, y: 44 },
  { x: -58, y: 128 },
  { x: 60, y: 130 },
  { x: 0, y: -162 },
  { x: -194, y: -42 },
  { x: 194, y: -34 },
  { x: -170, y: 126 },
  { x: 166, y: 132 },
  { x: -82, y: 218 },
  { x: 84, y: 222 },
  { x: 0, y: 286 },
];

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));
const getDiameter = (score: number) => clamp(74 + (score - 68) * 1.24, 72, 112);

export function ProductBubbleCluster({ products, selectedId, onSelect }: ProductBubbleClusterProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const pointerStartRef = useRef<Point | null>(null);
  const offsetStartRef = useRef<Point>({ x: 0, y: 0 });
  const [offset, setOffset] = useState<Point>({ x: 0, y: -24 });
  const [dragging, setDragging] = useState(false);
  const [viewport, setViewport] = useState({ width: 390, height: 430 });

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const update = () => {
      setViewport({ width: element.clientWidth, height: element.clientHeight });
    };
    update();

    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const visibleProducts = useMemo(() => products.slice(0, layout.length), [products]);

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    pointerStartRef.current = { x: event.clientX, y: event.clientY };
    offsetStartRef.current = offset;
    setDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!pointerStartRef.current) return;
    const dx = event.clientX - pointerStartRef.current.x;
    const dy = event.clientY - pointerStartRef.current.y;
    setOffset({
      x: clamp(offsetStartRef.current.x + dx, -150, 150),
      y: clamp(offsetStartRef.current.y + dy, -170, 74),
    });
  };

  const handlePointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    pointerStartRef.current = null;
    setDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };

  const centerX = viewport.width / 2;
  const centerY = viewport.height * 0.43;

  return (
    <div
      ref={containerRef}
      className={`bubble-cluster${dragging ? " bubble-cluster--dragging" : ""}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <div className="bubble-cluster__halo bubble-cluster__halo--one" />
      <div className="bubble-cluster__halo bubble-cluster__halo--two" />

      {visibleProducts.map((product, index) => {
        const point = layout[index];
        const diameter = getDiameter(product.reactionScore);
        const x = centerX + point.x + offset.x;
        const y = centerY + point.y + offset.y;
        const distance = Math.hypot(x - centerX, y - centerY);
        const proximityScale = clamp(1.09 - distance / 920, 0.78, 1.08);
        const selectedScale = product.id === selectedId ? 1.09 : 1;
        const finalScale = proximityScale * selectedScale;
        const isHot = product.reactionScore >= 90;

        const style = {
          width: `${diameter}px`,
          height: `${diameter}px`,
          left: `${x - diameter / 2}px`,
          top: `${y - diameter / 2}px`,
          transform: `scale(${finalScale})`,
          zIndex: Math.round(100 - distance / 10) + (product.id === selectedId ? 50 : 0),
        } satisfies CSSProperties;

        return (
          <button
            type="button"
            key={product.id}
            className={`product-bubble${product.id === selectedId ? " product-bubble--selected" : ""}${isHot ? " product-bubble--hot" : ""}`}
            style={style}
            onClick={() => onSelect(product.id)}
            aria-label={`${product.brandName} ${product.productName}, 반응지수 ${product.reactionScore}`}
          >
            <ProductArt product={product} compact />
            {product.status === "NEW" && <span className="product-bubble__new">NEW</span>}
            {product.reactionScore >= 78 && <span className="product-bubble__score">{product.reactionScore}</span>}
          </button>
        );
      })}

      <div className="bubble-cluster__drag-hint">드래그해서 신상을 둘러보세요</div>
    </div>
  );
}
