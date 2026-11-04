export type Lang = 'en' | 'fr';
export type Locale = 'en-CA' | 'fr-CA';
export type Names = Record<Lang, string>;

export interface Meta {
  as_of: string;
  catalogue_version: string;
  store_count: number;
  stores_fresh: number;
  alerts: string[];
  tiers: number[];
}

export interface StoreSummary {
  id: string;
  name: string;
  address: string;
  city: string;
  province: string;
  postal: string | null;
  lat: number;
  lon: number;
  best_cpp: number | null;
  best_item_key: string | null;
  as_of: string | null;
}

export interface StoresIndex {
  as_of: string;
  stores: StoreSummary[];
  best_cpp_quantiles: number[];
}

export interface RewardItem {
  key: string;
  tier: number;
  names: Names;
  kind: string;
  breakfast: boolean;
  product_id: number | null;
  price_cents: number | null;
  cpp: number | null;
  value_per_1k: number | null;
  available: boolean;
  national_median_cpp: number | null;
  province_median_cpp: number | null;
  delta_vs_national: number | null;
  delta_vs_province: number | null;
}

export interface StoreDoc {
  as_of: string;
  catalogue_version: string;
  store: Omit<StoreSummary, 'best_cpp' | 'best_item_key' | 'as_of'> & { nsn: string | null };
  items: RewardItem[];
  best_item_key: string | null;
  best_by_tier: Record<string, string | null>;
}

export interface AggregateItem {
  key: string;
  tier: number;
  names: Names;
  kind: string;
  breakfast: boolean;
  n_stores: number;
  median_cpp: number;
  mean_cpp: number;
  p10: number;
  p90: number;
  spread: number;
  value_per_1k: number;
  daily_median: { date: string; median_cpp: number }[];
}

export interface AggregateDoc {
  as_of: string;
  scope: string;
  window_days: number;
  items: AggregateItem[];
}

export interface NearbyDoc {
  as_of: string;
  item: { key: string; tier: number; names: Names; kind: string; breakfast: boolean };
  stores: { id: string; lat: number; lon: number; cpp: number; price_cents: number }[];
}

export interface HistoryDoc {
  as_of: string;
  scope: string;
  item: { key: string; tier: number; names: Names; kind: string; breakfast: boolean };
  series: { month: string; median_cpp: number; mean_cpp: number; p10: number; p90: number; n_stores: number; share_best: number }[];
  catalogue_changes: { version: string; valid_from: string }[];
}

export interface HistoryBestDoc {
  as_of: string;
  scope: string;
  series: { month: string; median_best_cpp: number; mean_best_cpp: number; best_item_mode: string }[];
  catalogue_changes: { version: string; valid_from: string }[];
}
