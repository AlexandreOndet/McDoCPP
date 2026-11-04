<script lang="ts">
  import { cppCents, delta, money } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import type { RewardItem } from '$lib/types';
  import Food from './Food.svelte';

  let { item, best = false }: { item: RewardItem; best?: boolean } = $props();
  const d = $derived(delta(item.delta_vs_national, app.locale));
</script>

<article class="item" class:best class:unavailable={item.cpp === null} data-testid="item-card" data-key={item.key}>
  {#if best}<span class="tag">{app.t('shelf.best')}</span>{/if}
  <div class="art"><Food kind={item.kind} size={104} /></div>
  <h3>{name(item.names, app.locale)}</h3>
  <p class="meta muted">
    {#if item.price_cents !== null}
      <span>{app.t('card.here', { price: money(item.price_cents, app.locale) })}</span>
    {:else}
      <span>{app.t('card.unavailable')}</span>
    {/if}
    {#if item.breakfast}<span class="badge">{app.t('card.breakfast')}</span>{/if}
  </p>
  <div class="foot">
    {#if item.cpp !== null}
      <span class="cpp display">{cppCents(item.cpp, app.locale)}<small>{app.t('card.per_pt')}</small></span>
      {#if d.text}<span class="delta" class:up={d.sign > 0} class:down={d.sign < 0}>{app.t('card.vs_canada', { delta: d.text })}</span>{/if}
    {:else}
      <span class="cpp display none">–</span>
    {/if}
  </div>
</article>

<style>
  .item {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 18px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    min-width: 0;
  }
  .item.best {
    border-color: var(--gold);
    box-shadow: inset 0 0 0 1px var(--gold);
  }
  .item.unavailable {
    opacity: 0.55;
  }
  .tag {
    position: absolute;
    top: 14px;
    left: 14px;
    padding: 4px 10px;
    border-radius: 12px;
    background: var(--gold);
    color: var(--ink-on-gold);
    font-family: var(--display);
    font-weight: 800;
    font-size: 12px;
  }
  .art {
    align-self: center;
    margin-top: 8px;
  }
  h3 {
    font-family: var(--body);
    font-size: 17px;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: 0;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
  }
  .badge {
    padding: 1px 8px;
    border: 1px solid var(--border);
    border-radius: 10px;
  }
  .foot {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    padding-top: 10px;
    border-top: var(--dash);
    margin-top: auto;
  }
  .cpp {
    font-size: 26px;
    letter-spacing: -0.02em;
  }
  .best .cpp {
    color: var(--gold-text);
  }
  .cpp small {
    font-family: var(--body);
    font-size: 12px;
    font-weight: 500;
    color: var(--muted);
    margin-left: 4px;
    letter-spacing: 0;
  }
  .cpp.none {
    color: var(--muted);
  }
  .delta {
    font-size: 13px;
    font-weight: 700;
    color: var(--muted);
  }
  .delta.up {
    color: var(--success);
  }
  .delta.down {
    color: var(--warn);
  }

  @media (max-width: 760px) {
    .item {
      display: grid;
      grid-template-columns: 60px minmax(0, 1fr) auto;
      grid-template-areas:
        'art name cpp'
        'art meta cpp';
      align-items: center;
      column-gap: 12px;
      row-gap: 2px;
      min-height: 76px;
      padding: 8px 14px 8px 8px;
      border-radius: 16px;
    }
    .tag {
      position: static;
      grid-area: name;
      justify-self: start;
      margin-bottom: 2px;
      display: none;
    }
    .art {
      grid-area: art;
      margin: 0;
    }
    .art :global(svg) {
      width: 60px;
      height: 60px;
    }
    h3 {
      grid-area: name;
      font-size: 15px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .meta {
      grid-area: meta;
      font-size: 12px;
      gap: 6px;
    }
    .foot {
      grid-area: cpp;
      flex-direction: column;
      align-items: flex-end;
      gap: 0;
      padding: 0;
      border: 0;
      margin: 0;
    }
    .cpp {
      font-size: 22px;
    }
    .cpp small {
      display: none;
    }
    .delta {
      font-size: 11px;
    }
  }
</style>
