import en from './i18n/en-CA.json';
import fr from './i18n/fr-CA.json';
import type { Lang, Locale, Names } from './types';

export const MESSAGES: Record<Locale, Record<string, string>> = { 'en-CA': en, 'fr-CA': fr };

export function langOf(locale: Locale): Lang {
  return locale === 'fr-CA' ? 'fr' : 'en';
}

export function translate(locale: Locale, key: string, params: Record<string, string | number> = {}): string {
  const s = MESSAGES[locale][key] ?? MESSAGES['en-CA'][key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k: string) => String(params[k] ?? `{${k}}`));
}

export function name(names: Names, locale: Locale): string {
  return names[langOf(locale)] || names.en;
}

export function detectLocale(): Locale {
  if (typeof navigator === 'undefined') return 'en-CA';
  return navigator.language.toLowerCase().startsWith('fr') ? 'fr-CA' : 'en-CA';
}
