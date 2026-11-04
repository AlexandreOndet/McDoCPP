import { describe, expect, it } from 'vitest';
import { bestForBalance, meterFill, nextTier, nextTierHint, quantileBin, reachedTier, shelves } from '../src/lib/cpp';
import type { RewardItem } from '../src/lib/types';

const item = (key: string, tier: number, cpp: number | null, breakfast = false): RewardItem => ({
  key, tier, cpp, breakfast, names: { en: key, fr: key }, kind: 'burger', product_id: 1,
  price_cents: cpp === null ? null : Math.round(cpp * tier), value_per_1k: cpp === null ? null : cpp * 10,
  available: cpp !== null, national_median_cpp: null, province_median_cpp: null, delta_vs_national: null, delta_vs_province: null
});

const items = [
  item('hash_brown', 2000, 0.1295, true), item('coffee', 2000, 0.1095), item('pie', 2000, 0.0995),
  item('fries_md', 4000, 0.1047), item('mcflurry', 4000, 0.1148),
  item('nuggets_6', 6000, 0.1232), item('wrap', 6000, null),
  item('nuggets_10', 10000, 0.1069),
  item('nuggets_10_meal', 14000, 0.1078)
];

describe('bestForBalance', () => {
  it('picks the highest cpp within balance', () => {
    expect(bestForBalance(items, 6000)?.key).toBe('hash_brown');
    expect(bestForBalance(items, 4000)?.key).toBe('hash_brown');
    expect(bestForBalance(items, 1999)).toBeNull();
  });
  it('skips breakfast when asked and ignores unavailable', () => {
    expect(bestForBalance(items, 2000, true)?.key).toBe('coffee');
    expect(bestForBalance(items, 6000, true)?.key).toBe('nuggets_6');
  });
});

describe('nextTierHint', () => {
  it('says nothing unlocked below 2k', () => {
    expect(nextTierHint(items, 500)).toMatchObject({ kind: 'nothing', nextTier: 2000, need: 1500 });
  });
  it('suggests waiting only when the next shelf beats the current best', () => {
    // at 4000 skipping breakfast: best = mcflurry 0.1148; next shelf 6000 has nuggets 0.1232 → wait
    expect(nextTierHint(items, 4000, true)).toMatchObject({ kind: 'wait', nextTier: 6000, need: 2000, item: { key: 'nuggets_6' } });
    // at 6000: best nuggets_6 0.1232; next 10000 best 0.1069 → cash in
    expect(nextTierHint(items, 6000, true)).toMatchObject({ kind: 'cash_in', nextTier: 10000 });
  });
  it('is "top" above the last tier', () => {
    expect(nextTierHint(items, 14000)).toEqual({ kind: 'top' });
  });
});

describe('shelves', () => {
  it('groups, sorts, locks and marks best', () => {
    const s = shelves(items, 5000);
    expect(s.map((x) => x.tier)).toEqual([2000, 4000, 6000, 10000, 14000]);
    expect(s[0].items.map((i) => i.key)).toEqual(['hash_brown', 'coffee', 'pie']);
    expect(s[0].best?.key).toBe('hash_brown');
    expect(shelves(items, 5000, true)[0].best?.key).toBe('coffee');
    expect(s[2]).toMatchObject({ locked: true, toUnlock: 1000 });
    expect(s[2].items.at(-1)?.key).toBe('wrap'); // unavailable last
  });
});

describe('tiers and meter', () => {
  it('reached/next/meter', () => {
    expect(reachedTier(5000)).toBe(4000);
    expect(reachedTier(100)).toBeNull();
    expect(nextTier(14000)).toBeNull();
    expect(meterFill(7000)).toBeCloseTo(0.5);
    expect(meterFill(99999)).toBe(1);
  });
  it('quantileBin', () => {
    expect(quantileBin(0.10, [0.11, 0.12, 0.13, 0.14])).toBe(0);
    expect(quantileBin(0.125, [0.11, 0.12, 0.13, 0.14])).toBe(2);
    expect(quantileBin(0.2, [0.11, 0.12, 0.13, 0.14])).toBe(4);
  });
});
