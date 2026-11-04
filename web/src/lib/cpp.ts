import type { RewardItem } from './types';

export const TIERS = [2000, 4000, 6000, 10000, 14000] as const;

export interface Shelf {
  tier: number;
  items: RewardItem[]; // sorted by cpp desc, unavailable last
  best: RewardItem | null; // best redeemable (respects allDayOnly)
  locked: boolean;
  toUnlock: number;
}

export interface Hint {
  kind: 'nothing' | 'wait' | 'cash_in' | 'top';
  nextTier?: number;
  need?: number;
  item?: RewardItem;
}

const redeemable = (i: RewardItem, allDayOnly: boolean) => i.cpp !== null && (!allDayOnly || !i.breakfast);

export function sortByCpp(items: RewardItem[]): RewardItem[] {
  return [...items].sort((a, b) => (b.cpp ?? -1) - (a.cpp ?? -1));
}

/** Best redemption the balance can pay for right now. */
export function bestForBalance(items: RewardItem[], balance: number, allDayOnly = false): RewardItem | null {
  const ok = sortByCpp(items.filter((i) => redeemable(i, allDayOnly) && i.tier <= balance));
  return ok[0] ?? null;
}

/** Highest tier the balance reaches, or null. */
export function reachedTier(balance: number, tiers: readonly number[] = TIERS): number | null {
  const r = tiers.filter((t) => t <= balance);
  return r.length ? r[r.length - 1] : null;
}

export function nextTier(balance: number, tiers: readonly number[] = TIERS): number | null {
  return tiers.find((t) => t > balance) ?? null;
}

/** "Wait for the next tier?" hint: compares the current best with the best on the next shelf only. */
export function nextTierHint(items: RewardItem[], balance: number, allDayOnly = false, tiers: readonly number[] = TIERS): Hint {
  const best = bestForBalance(items, balance, allDayOnly);
  const next = nextTier(balance, tiers);
  if (!best) return { kind: 'nothing', nextTier: next ?? undefined, need: next ? next - balance : undefined };
  if (next === null) return { kind: 'top' };
  const nb = sortByCpp(items.filter((i) => i.tier === next && redeemable(i, allDayOnly)))[0];
  if (nb && (nb.cpp ?? 0) > (best.cpp ?? 0)) return { kind: 'wait', nextTier: next, need: next - balance, item: nb };
  return { kind: 'cash_in', nextTier: next };
}

export function shelves(items: RewardItem[], balance: number, allDayOnly = false, tiers: readonly number[] = TIERS): Shelf[] {
  return tiers.map((tier) => {
    const its = sortByCpp(items.filter((i) => i.tier === tier));
    return {
      tier,
      items: its,
      best: its.find((i) => redeemable(i, allDayOnly)) ?? null,
      locked: tier > balance,
      toUnlock: Math.max(0, tier - balance)
    };
  });
}

/** Fill of the tier meter, 0..1, linear in points up to the top tier. */
export function meterFill(balance: number, tiers: readonly number[] = TIERS): number {
  return Math.min(1, Math.max(0, balance / tiers[tiers.length - 1]));
}

/** 0..k bin index for a store's best cpp given k-1 ascending cut points. */
export function quantileBin(value: number, cuts: number[]): number {
  let b = 0;
  for (const c of cuts) if (value >= c) b++;
  return b;
}

export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
