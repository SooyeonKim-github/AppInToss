export type MenuRarity = "COMMON" | "UNCOMMON" | "RARE";

export interface Menu {
  id: number;
  name: string;
  category: string;
  subCategory: string;
  rarity: MenuRarity;
  emoji: string;
  tagline: string;
  imageKey?: string | null;
}

export interface MenuPickResponse {
  menu: Menu;
  likes: number;
  liked: boolean;
  rerollIndex: number;
}

export interface RankingItem {
  rank: number;
  menuId: number;
  name: string;
  emoji: string;
  imageKey?: string | null;
  likes: number;
}
