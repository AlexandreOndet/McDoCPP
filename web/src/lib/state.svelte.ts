import { browser } from '$app/env';
import { detectLocale, translate } from './i18n';
import type { Locale } from './types';

function persisted<T>(key: string, fallback: T, parse: (s: string) => T): T {
  if (!browser) return fallback;
  const v = localStorage.getItem(key);
  return v === null ? fallback : parse(v);
}

class AppState {
  balance = $state(persisted('mcdocpp.balance', 6000, Number));
  allDayOnly = $state(persisted('mcdocpp.allDayOnly', false, (s) => s === '1'));
  locale = $state<Locale>(persisted('mcdocpp.locale', browser ? detectLocale() : 'en-CA', (s) => (s === 'fr-CA' ? 'fr-CA' : 'en-CA')));
  lastStore = $state<string | null>(persisted('mcdocpp.lastStore', null, (s) => s));
  view = $state<'cards' | 'table'>(persisted('mcdocpp.view', 'cards', (s) => (s === 'table' ? 'table' : 'cards')));

  t = (key: string, params?: Record<string, string | number>) => translate(this.locale, key, params);

  save() {
    if (!browser) return;
    localStorage.setItem('mcdocpp.balance', String(this.balance));
    localStorage.setItem('mcdocpp.allDayOnly', this.allDayOnly ? '1' : '0');
    localStorage.setItem('mcdocpp.locale', this.locale);
    localStorage.setItem('mcdocpp.view', this.view);
    if (this.lastStore) localStorage.setItem('mcdocpp.lastStore', this.lastStore);
  }
}

export const app = new AppState();
