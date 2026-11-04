import type { AggregateDoc, HistoryBestDoc, HistoryDoc, Meta, NearbyDoc, StoreDoc, StoresIndex } from './types';

const base = ((import.meta.env.VITE_DATA_BASE as string | undefined) || '/data').replace(/\/$/, '');

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${base}/${path}`);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

export const loadMeta = () => get<Meta>('meta.json');
export const loadIndex = () => get<StoresIndex>('stores/index.json');
export const loadStore = (id: string) => get<StoreDoc>(`stores/${encodeURIComponent(id)}.json`);
export const loadAggregate = (scope = 'national') => get<AggregateDoc>(`aggregates/${scope}/7d.json`);
export const loadNearby = (key: string) => get<NearbyDoc>(`items/${key}/nearby.json`);
export const loadHistory = (scope: string, key: string) => get<HistoryDoc>(`history/${scope}/${key}.json`);
export const loadHistoryBest = (scope: string) => get<HistoryBestDoc>(`history/${scope}/best.json`);
