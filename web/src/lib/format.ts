import type { Locale } from './types';

export const STALE_HOURS = 48;

/** cpp is price_cents / points. Shown ×100: cents per 100 pts (= per $1 spent). */
export function cppCents(cpp: number, locale: Locale): string {
  const n = new Intl.NumberFormat(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(cpp * 100);
  return locale === 'fr-CA' ? `${n} ¢` : `${n}¢`;
}

export function money(cents: number, locale: Locale): string {
  return new Intl.NumberFormat(locale, { style: 'currency', currency: 'CAD', currencyDisplay: 'narrowSymbol' }).format(cents / 100);
}

/** Dollar value of 1,000 points. */
export function per1k(cpp: number, locale: Locale): string {
  return money(cpp * 1000, locale);
}

export function points(n: number, locale: Locale): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(n);
}

/** ▲ 3.1 % / ▼ 2.0 %; null → em-dash-free placeholder. */
export function delta(frac: number | null, locale: Locale): { text: string; sign: 1 | 0 | -1 } {
  if (frac === null) return { text: '', sign: 0 };
  const pct = new Intl.NumberFormat(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(Math.abs(frac) * 100);
  const sign: 1 | 0 | -1 = frac > 0.0005 ? 1 : frac < -0.0005 ? -1 : 0;
  const arrow = sign > 0 ? '▲' : sign < 0 ? '▼' : '=';
  return { text: `${arrow} ${pct} %`, sign };
}

export function hoursSince(iso: string, now: Date = new Date()): number {
  return (now.getTime() - new Date(iso).getTime()) / 3_600_000;
}

export function isStale(iso: string, now: Date = new Date()): boolean {
  return hoursSince(iso, now) > STALE_HOURS;
}

/** "today 05:12" | "yesterday 05:12" | "3 days ago"; caller prefixes "seen". */
export function seenAt(iso: string, locale: Locale, now: Date = new Date()): { key: 'today' | 'yesterday' | 'days'; time: string; days: number } {
  const d = new Date(iso);
  const time = new Intl.DateTimeFormat(locale, { hour: '2-digit', minute: '2-digit' }).format(d);
  const dayStart = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((dayStart(now) - dayStart(d)) / 86_400_000);
  return { key: days <= 0 ? 'today' : days === 1 ? 'yesterday' : 'days', time, days };
}

export function km(d: number, locale: Locale): string {
  return d < 1
    ? `${new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(d * 1000)} m`
    : `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(d)} km`;
}
