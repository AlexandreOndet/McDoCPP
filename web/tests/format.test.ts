import { describe, expect, it } from 'vitest';
import { cppCents, delta, isStale, money, per1k, seenAt } from '../src/lib/format';

describe('format', () => {
  it('cpp as cents per 100 pts and $ per 1k', () => {
    expect(cppCents(0.1245, 'en-CA')).toBe('12.45¢');
    expect(cppCents(0.1245, 'fr-CA').replace(/ /g, ' ')).toBe('12,45 ¢'.replace(' ', ' '));
    expect(per1k(0.1245, 'en-CA')).toBe('$1.25');
    expect(money(479, 'en-CA')).toBe('$4.79');
  });
  it('delta arrows', () => {
    expect(delta(0.031, 'en-CA')).toEqual({ text: '▲ 3.1 %', sign: 1 });
    expect(delta(-0.02, 'en-CA')).toEqual({ text: '▼ 2.0 %', sign: -1 });
    expect(delta(0, 'en-CA').sign).toBe(0);
  });
  it('staleness and seen-at buckets', () => {
    const now = new Date('2026-11-04T12:00:00Z');
    expect(isStale('2026-11-03T05:12:00Z', now)).toBe(false);
    expect(isStale('2026-11-01T05:12:00Z', now)).toBe(true);
    expect(seenAt('2026-11-04T05:12:00Z', 'en-CA', now).key).toBe('today');
    expect(seenAt('2026-11-03T05:12:00Z', 'en-CA', now).key).toBe('yesterday');
    expect(seenAt('2026-11-01T05:12:00Z', 'en-CA', now)).toMatchObject({ key: 'days', days: 3 });
  });
});
