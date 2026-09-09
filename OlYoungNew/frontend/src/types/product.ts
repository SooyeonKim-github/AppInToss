export type ProductStatus = "HOT" | "RISING" | "NEW" | "WATCH";

export interface ReactionMetrics {
  reviewVelocity: number;
  rating: number;
  discount: number;
  oliveyoungExposure: number;
  freshness: number;
  earlyReaction: number;
  snsBuzz: number;
}

export interface ProductArtTheme {
  label: string;
  accent: string;
  soft: string;
}

export interface HomeProduct {
  id: number;
  brandName: string;
  productName: string;
  imageUrl?: string;
  reactionScore: number;
  scoreChange: number;
  daysSinceLaunch: number;
  reviewCount: number;
  discountRate: number;
  status: ProductStatus;
  tags: string[];
  benefits: string[];
  metrics: ReactionMetrics;
  art: ProductArtTheme;
}
