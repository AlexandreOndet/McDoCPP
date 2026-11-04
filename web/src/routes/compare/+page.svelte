<script lang="ts">
  import { page } from '$app/state';
  import Food from '$lib/components/Food.svelte';
  import { haversineKm } from '$lib/cpp';
  import { loadNearby } from '$lib/data';
  import { cppCents, km, money } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import type { NearbyDoc } from '$lib/types';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  let key = $state('mcflurry');
  let radius = $state(10);
  let doc = $state<NearbyDoc | null>(null);
  const keys = ['mcflurry', 'fries_md', 'big_mac', 'nuggets_10', 'coffee_sm_md', 'hash_brown'];

  const home = $derived(data.index.stores.find((s) => s.id === (page.url.searchParams.get('store') ?? app.lastStore)) ?? null);
  $effect(() => {
    loadNearby(key).then((d) => (doc = d));
  });
  const rows = $derived.by(() => {
    if (!doc) return [];
    const byId = new Map(data.index.stores.map((s) => [s.id, s]));
    return doc.stores
      .map((p) => ({ ...p, store: byId.get(p.id), d: home ? haversineKm(home.lat, home.lon, p.lat, p.lon) : 0 }))
      .filter((r) => !home || r.d <= radius)
      .sort((a, b) => b.cpp - a.cpp);
  });
</script>

<section class="stub">
  <h1>{app.t('stub.compare')}</h1>
  <p class="muted">{app.t('stub.coming')}</p>
  <div class="controls">
    <select bind:value={key} aria-label={app.t('table.item')}>
      {#each keys as k (k)}<option value={k}>{k}</option>{/each}
    </select>
    {#if home}
      <label>{radius} km <input type="range" min="2" max="50" bind:value={radius} /></label>
    {/if}
  </div>
  {#if doc}
    <h2 class="item"><Food kind={doc.item.kind} size={40} /> {name(doc.item.names, app.locale)}</h2>
    <ol class="list">
      {#each rows as r (r.id)}
        <li>
          <span class="n">{r.store?.name ?? r.id}</span>
          {#if home}<span class="muted">{km(r.d, app.locale)}</span>{/if}
          <span class="cpp display">{cppCents(r.cpp, app.locale)}</span>
          <span class="muted">{money(r.price_cents, app.locale)}</span>
        </li>
      {/each}
    </ol>
  {:else}
    <p class="muted">{app.t('loading')}</p>
  {/if}
</section>

<style>
  .stub {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 0 16px;
  }
  .controls {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
  }
  select {
    min-height: var(--hit);
    padding: 0 14px;
    border-radius: var(--r-pill);
    background: var(--surface);
    border: 1px solid var(--border);
  }
  .item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 24px;
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .list li {
    display: flex;
    gap: 14px;
    align-items: baseline;
    padding: 10px 0;
    border-bottom: var(--dash);
  }
  .n {
    flex: 1;
    font-weight: 700;
  }
  .cpp {
    font-size: 22px;
    color: var(--gold-text);
  }
</style>
