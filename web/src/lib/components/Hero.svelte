<script lang="ts">
  import { fade } from 'svelte/transition';
  import { bestForBalance, nextTierHint, sortByCpp } from '$lib/cpp';
  import { cppCents, money, per1k, points } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import type { RewardItem } from '$lib/types';
  import Food from './Food.svelte';

  let { items, tiers }: { items: RewardItem[]; tiers: readonly number[] } = $props();

  const best = $derived(bestForBalance(items, app.balance, app.allDayOnly));
  const hint = $derived(nextTierHint(items, app.balance, app.allDayOnly, tiers));
  // Shown greyed when nothing is unlocked yet: the cheapest shelf's best.
  const preview = $derived(best ?? sortByCpp(items.filter((i) => i.tier === tiers[0] && i.cpp !== null))[0] ?? null);
  const shown = $derived(preview);

  const hintText = $derived.by(() => {
    switch (hint.kind) {
      case 'nothing':
        return app.t('hero.nothing', { n: points(hint.need ?? 0, app.locale) });
      case 'wait':
        return app.t('hero.wait', {
          n: points(hint.need ?? 0, app.locale),
          item: hint.item ? name(hint.item.names, app.locale) : '',
          cpp: hint.item?.cpp != null ? cppCents(hint.item.cpp, app.locale) : ''
        });
      case 'cash_in':
        return app.t('hero.cash_in', { tier: points(hint.nextTier ?? 0, app.locale) });
      default:
        return app.t('hero.top');
    }
  });
</script>

<section class="hero" class:locked={!best} aria-live="polite" data-testid="hero">
  {#if shown}
    {#key shown.key}
      <div class="inner" in:fade={{ duration: 200 }}>
        <div class="art" aria-hidden="true"><span class="plate"></span><Food kind={shown.kind} size="100%" /></div>
        <div class="copy">
          <p class="eyebrow">{best ? app.t('hero.label') : app.t('hero.nothing_title')}</p>
          <h1 data-testid="hero-name">{name(shown.names, app.locale)}</h1>
          <p class="price">
            {app.t('hero.price_for', { price: money(shown.price_cents ?? 0, app.locale), pts: points(shown.tier, app.locale) })}
            {#if shown.breakfast}<span class="badge">{app.t('hero.breakfast')}</span>{/if}
          </p>
          <p class="cpp">
            <span class="display big" data-testid="hero-cpp">{cppCents(shown.cpp ?? 0, app.locale)}</span>
            <span class="per">{app.t('hero.per100')}</span>
          </p>
          <p class="per1k">{app.t('hero.per1k', { value: per1k(shown.cpp ?? 0, app.locale) })}</p>
          <p class="hint" data-testid="hero-hint">{hintText}</p>
        </div>
      </div>
    {/key}
  {/if}
</section>

<style>
  .hero {
    position: relative;
    overflow: hidden;
    background: var(--gold);
    color: var(--ink-on-gold);
    border-radius: var(--r-xl);
    min-height: 100%;
  }
  .hero.locked {
    background: var(--surface-2);
    color: var(--text);
  }
  .inner {
    display: grid;
    grid-template-columns: minmax(140px, 36%) 1fr;
    gap: 16px 24px;
    align-items: center;
    padding: 28px;
    min-height: 100%;
  }
  .art {
    position: relative;
    width: 100%;
    aspect-ratio: 1;
    transform: translate(-14%, 4%) scale(1.3);
    transform-origin: center;
  }
  .plate {
    position: absolute;
    inset: 8%;
    border-radius: 50%;
    background: rgba(27, 19, 16, 0.1);
  }
  .locked .plate {
    background: rgba(255, 243, 227, 0.05);
  }
  .art :global(svg) {
    position: relative;
  }
  .locked .art {
    opacity: 0.45;
    filter: saturate(0.6);
  }
  .copy {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
  }
  .eyebrow {
    font-weight: 700;
    color: var(--ink-on-gold-2);
  }
  .locked .eyebrow,
  .locked .price,
  .locked .per,
  .locked .per1k,
  .locked .hint {
    color: var(--muted);
  }
  h1 {
    font-size: clamp(28px, 4vw, 40px);
    overflow-wrap: anywhere;
  }
  .price {
    font-weight: 600;
    color: var(--ink-on-gold-2);
  }
  .badge {
    display: inline-block;
    margin-left: 8px;
    padding: 1px 10px;
    border: 1px solid currentColor;
    border-radius: var(--r-pill);
    font-size: 13px;
  }
  .cpp {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-top: 6px;
    flex-wrap: wrap;
  }
  .big {
    font-size: clamp(48px, 7vw, 72px);
  }
  .per {
    font-weight: 700;
    color: var(--ink-on-gold-2);
  }
  .per1k {
    font-weight: 700;
    color: var(--ink-on-gold-2);
  }
  .hint {
    margin-top: 6px;
    padding-top: 10px;
    border-top: 1px dashed rgba(27, 19, 16, 0.3);
    font-weight: 600;
    color: var(--ink-on-gold-2);
  }
  .locked .hint {
    border-top-color: var(--border);
  }
  @media (max-width: 560px) {
    .inner {
      grid-template-columns: 1fr;
      padding: 22px 20px;
    }
    .plate {
      background: rgba(27, 19, 16, 0.06);
      inset: 14%;
    }
    .art {
      width: 46%;
      transform: none;
      justify-self: end;
      margin-top: -8px;
      margin-bottom: -34%;
      position: relative;
      z-index: 0;
    }
    .copy {
      position: relative;
      z-index: 1;
    }
  }
</style>
