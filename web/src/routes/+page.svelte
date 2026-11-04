<script lang="ts">
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { page } from '$app/state';
  import Hero from '$lib/components/Hero.svelte';
  import ItemTable from '$lib/components/ItemTable.svelte';
  import Search from '$lib/components/Search.svelte';
  import Shelf from '$lib/components/Shelf.svelte';
  import StalenessBanner from '$lib/components/StalenessBanner.svelte';
  import StoreMap from '$lib/components/StoreMap.svelte';
  import Wallet from '$lib/components/Wallet.svelte';
  import { shelves as buildShelves } from '$lib/cpp';
  import { loadStore } from '$lib/data';
  import { cppCents } from '$lib/format';
  import { app } from '$lib/state.svelte';
  import type { StoreDoc } from '$lib/types';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const picking = $derived(page.url.searchParams.has('pick'));
  const storeId = $derived(picking ? null : (page.url.searchParams.get('store') ?? app.lastStore));
  const tiers = $derived(data.meta.tiers);

  let doc = $state<StoreDoc | null>(null);
  let error = $state<string | null>(null);
  let mapOpen = $state(false);

  $effect(() => {
    const id = storeId;
    if (!id || !data.index.stores.some((s) => s.id === id)) {
      doc = null;
      return;
    }
    let live = true;
    loadStore(id).then(
      (d) => {
        if (!live) return;
        doc = d;
        error = null;
        app.lastStore = id;
        app.save();
      },
      (e: Error) => live && (error = e.message)
    );
    return () => (live = false);
  });

  const shelves = $derived(doc ? buildShelves(doc.items, app.balance, app.allDayOnly, tiers) : []);

  function select(id: string) {
    mapOpen = false;
    const url = new URL(page.url.href);
    url.searchParams.set('store', id);
    url.searchParams.delete('pick');
    goto(resolve(`/?${url.searchParams.toString()}`), { reset: false });
  }

  const nearby = $derived.by(() => {
    if (!doc) return [];
    const { lat, lon } = doc.store;
    return data.index.stores
      .filter((s) => s.id !== doc?.store.id && s.best_cpp !== null)
      .map((s) => ({ s, d: Math.hypot((s.lat - lat) * 111, (s.lon - lon) * 111 * Math.cos((lat * Math.PI) / 180)) }))
      .sort((a, b) => a.d - b.d)
      .slice(0, 3);
  });
</script>

{#if !storeId || (!doc && !error && !data.index.stores.some((s) => s.id === storeId))}
  <!-- Landing: pick a store -->
  <section class="landing">
    <div class="landing-copy">
      <h1>{app.t('landing.title')}</h1>
      <p class="muted">{app.t('landing.subtitle')}</p>
      <Search stores={data.index.stores} onselect={select} id="landing-search" />
    </div>
    <div class="landing-map">
      <StoreMap stores={data.index.stores} cuts={data.index.best_cpp_quantiles} onselect={select} />
    </div>
  </section>
{:else if error}
  <p role="alert" class="card err">{app.t('error.load')}</p>
{:else if doc}
  <div class="sticky-wallet">
    <Wallet {tiers} compact />
  </div>

  <section class="top">
    <div class="wallet-desktop"><Wallet {tiers} /></div>
    <div class="hero-slot"><Hero items={doc.items} {tiers} /></div>
  </section>

  <div class="storeline">
    <h2 class="store-name">{doc.store.name}</h2>
    <span class="muted">{doc.store.address}, {doc.store.city} {doc.store.province}</span>
    <StalenessBanner asOf={doc.as_of} />
    <div class="view" role="group" aria-label="View">
      <button type="button" class="pill" aria-pressed={app.view === 'cards'} onclick={() => ((app.view = 'cards'), app.save())}>{app.t('shelf.view_cards')}</button>
      <button type="button" class="pill" aria-pressed={app.view === 'table'} onclick={() => ((app.view = 'table'), app.save())}>{app.t('shelf.view_table')}</button>
    </div>
  </div>

  {#if app.view === 'table'}
    <ItemTable {shelves} />
  {:else}
    <div class="shelves">
      {#each shelves as shelf (shelf.tier)}
        <Shelf {shelf} />
      {/each}
    </div>
  {/if}

  <section class="nearby card">
    <div class="nearby-copy">
      <h2>{app.t('map.title')}</h2>
      <p class="muted">{app.t('map.subtitle')}</p>
      <ul class="chips">
        {#each nearby as { s, d } (s.id)}
          {@const mine = doc.items[0]?.cpp ?? 0}
          <li>
            <button type="button" class="chip" onclick={() => select(s.id)}>
              <span class="chip-name">{s.name} · {d < 1 ? `${Math.round(d * 1000)} m` : `${d.toFixed(1)} km`}</span>
              <span class="chip-cpp" class:up={(s.best_cpp ?? 0) > mine}>{cppCents(s.best_cpp ?? 0, app.locale)} {(s.best_cpp ?? 0) > mine ? '▲' : (s.best_cpp ?? 0) < mine ? '▼' : ''}</span>
            </button>
          </li>
        {/each}
      </ul>
      <Search stores={data.index.stores} onselect={select} id="nearby-search" />
    </div>
    <div class="nearby-map">
      <StoreMap stores={data.index.stores} cuts={data.index.best_cpp_quantiles} selected={doc.store.id} onselect={select} />
    </div>
  </section>

  <button type="button" class="pill map-fab" onclick={() => (mapOpen = true)}>{app.t('map.open')}</button>
  {#if mapOpen}
    <div class="sheet" role="dialog" aria-modal="true" aria-label={app.t('map.title')}>
      <div class="sheet-head">
        <h2>{app.t('map.title')}</h2>
        <button type="button" class="pill" onclick={() => (mapOpen = false)}>{app.t('map.close')}</button>
      </div>
      <Search stores={data.index.stores} onselect={select} id="sheet-search" />
      <div class="sheet-map">
        <StoreMap stores={data.index.stores} cuts={data.index.best_cpp_quantiles} selected={doc.store.id} onselect={select} />
      </div>
    </div>
  {/if}
{:else}
  <p class="muted">{app.t('loading')}</p>
{/if}

<style>
  .landing {
    display: grid;
    grid-template-columns: minmax(300px, 5fr) 7fr;
    gap: 24px;
    min-height: 520px;
  }
  .landing-copy {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 28px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
  }
  .landing h1 {
    font-size: clamp(32px, 4vw, 48px);
  }
  .landing-map {
    min-height: 420px;
  }

  .top {
    display: grid;
    grid-template-columns: 5fr 7fr;
    gap: 24px;
    align-items: stretch;
  }
  .sticky-wallet {
    display: none;
  }

  .storeline {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 16px;
  }
  .store-name {
    font-size: 24px;
  }
  .view {
    margin-left: auto;
    display: flex;
    gap: 6px;
  }
  .shelves {
    display: flex;
    flex-direction: column;
  }

  .nearby {
    display: grid;
    grid-template-columns: minmax(280px, 2fr) 3fr;
    gap: 24px;
    padding: 28px;
  }
  .nearby-copy {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .nearby h2 {
    font-size: 24px;
  }
  .chips {
    list-style: none;
    margin: 4px 0 8px;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
  .chip {
    display: inline-flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    min-height: var(--hit);
    padding: 10px 16px;
    border-radius: 16px;
    border: 0;
    background: var(--surface-2);
    color: var(--text);
    cursor: pointer;
    text-align: left;
  }
  .chip-name {
    font-weight: 700;
  }
  .chip-cpp {
    font-size: 13px;
    font-weight: 700;
    color: var(--muted);
  }
  .chip-cpp.up {
    color: var(--gold-text);
  }
  .nearby-map {
    min-height: 360px;
  }
  .map-fab,
  .sheet {
    display: none;
  }
  .err {
    padding: 20px;
  }

  @media (max-width: 760px) {
    .landing {
      grid-template-columns: 1fr;
      min-height: 0;
      padding: 0 16px;
    }
    .landing-copy {
      padding: 20px;
    }
    .sticky-wallet {
      display: block;
      position: sticky;
      top: 0;
      z-index: 5;
      background: var(--bg);
    }
    .wallet-desktop {
      display: none;
    }
    .top {
      grid-template-columns: 1fr;
      padding: 0 16px;
    }
    .storeline {
      padding: 0 16px;
    }
    .nearby {
      grid-template-columns: 1fr;
      margin: 0 16px;
      padding: 20px;
    }
    .nearby-map {
      display: none;
    }
    .map-fab {
      display: inline-flex;
      position: fixed;
      left: 50%;
      bottom: 16px;
      transform: translateX(-50%);
      z-index: 6;
      background: var(--gold);
      color: var(--ink-on-gold);
      border-color: var(--gold);
      box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
      padding: 0 24px;
    }
    .sheet {
      display: flex;
      flex-direction: column;
      gap: 12px;
      position: fixed;
      inset: 12vh 0 0 0;
      z-index: 10;
      background: var(--bg);
      border-radius: var(--r-xl) var(--r-xl) 0 0;
      border-top: 1px solid var(--border);
      padding: 16px 16px 0;
    }
    .sheet-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .sheet-head h2 {
      font-size: 22px;
    }
    .sheet-map {
      flex: 1;
      min-height: 0;
      margin: 0 -16px;
    }
    .sheet-map :global(.map) {
      border-radius: 0;
      border: 0;
      height: 100%;
    }
  }
</style>
