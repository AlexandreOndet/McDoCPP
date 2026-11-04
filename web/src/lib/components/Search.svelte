<script lang="ts">
  import { haversineKm } from '$lib/cpp';
  import { cppCents, km } from '$lib/format';
  import { app } from '$lib/state.svelte';
  import type { StoreSummary } from '$lib/types';

  let {
    stores,
    onselect,
    id = 'store-search'
  }: { stores: StoreSummary[]; onselect: (id: string) => void; id?: string } = $props();

  let query = $state('');
  let active = $state(-1);
  let here = $state<{ lat: number; lon: number } | null>(null);
  let geoBusy = $state(false);

  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  const results = $derived.by(() => {
    const q = norm(query.trim());
    let list = stores;
    if (q) {
      list = stores.filter((s) => norm(`${s.id} ${s.name} ${s.address} ${s.city} ${s.province} ${s.postal ?? ''}`).includes(q));
    } else if (!here) {
      return [];
    }
    if (here) {
      const h = here;
      list = [...list].sort((a, b) => haversineKm(h.lat, h.lon, a.lat, a.lon) - haversineKm(h.lat, h.lon, b.lat, b.lon));
    }
    return list.slice(0, 8);
  });

  function pick(s: StoreSummary) {
    onselect(s.id);
    query = '';
    active = -1;
  }

  function onKey(e: KeyboardEvent) {
    if (!results.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      active = (active + 1) % results.length;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      active = (active - 1 + results.length) % results.length;
    } else if (e.key === 'Enter' && active >= 0) {
      e.preventDefault();
      pick(results[active]);
    } else if (e.key === 'Escape') {
      query = '';
      active = -1;
    }
  }

  function locate() {
    if (!navigator.geolocation) return;
    geoBusy = true;
    navigator.geolocation.getCurrentPosition(
      (p) => {
        here = { lat: p.coords.latitude, lon: p.coords.longitude };
        geoBusy = false;
      },
      () => (geoBusy = false),
      { maximumAge: 600_000, timeout: 10_000 }
    );
  }
</script>

<div class="search">
  <label for={id} class="visually-hidden">{app.t('search.label')}</label>
  <div class="bar">
    <input
      {id}
      type="search"
      placeholder={app.t('search.placeholder')}
      bind:value={query}
      onkeydown={onKey}
      role="combobox"
      aria-expanded={results.length > 0}
      aria-controls={`${id}-list`}
      aria-autocomplete="list"
      aria-activedescendant={active >= 0 ? `${id}-opt-${active}` : undefined}
      autocomplete="off"
    />
    <button type="button" class="pill" onclick={locate} aria-busy={geoBusy} disabled={geoBusy}>
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
      {app.t('search.use_location')}
    </button>
  </div>
  {#if results.length}
    <ul id={`${id}-list`} role="listbox" class="list" aria-label={here && !query ? app.t('search.nearest') : app.t('search.results', { n: results.length })}>
      {#each results as s, i (s.id)}
        <li
          id={`${id}-opt-${i}`}
          role="option"
          aria-selected={i === active}
          class:active={i === active}
        >
          <button type="button" onclick={() => pick(s)} onmouseenter={() => (active = i)}>
            <span class="name">{s.name}</span>
            <span class="muted addr">{s.address}, {s.city} {s.province}{here ? ` · ${km(haversineKm(here.lat, here.lon, s.lat, s.lon), app.locale)}` : ''}</span>
            {#if s.best_cpp !== null}<span class="cpp">{cppCents(s.best_cpp, app.locale)}</span>{/if}
          </button>
        </li>
      {/each}
    </ul>
  {:else if query.trim()}
    <p class="muted none">{app.t('search.no_results')}</p>
  {/if}
</div>

<style>
  .search {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .bar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  input {
    flex: 1 1 240px;
    min-height: var(--hit);
    padding: 0 18px;
    border-radius: var(--r-pill);
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 16px;
  }
  input::placeholder {
    color: var(--muted);
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 6px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    display: flex;
    flex-direction: column;
  }
  .list li + li {
    border-top: var(--dash);
  }
  .list button {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2px 12px;
    align-items: center;
    text-align: left;
    min-height: var(--hit);
    padding: 10px 14px;
    background: transparent;
    border: 0;
    border-radius: 14px;
    cursor: pointer;
  }
  .list li.active button,
  .list button:hover {
    background: var(--surface-2);
  }
  .name {
    font-weight: 700;
  }
  .addr {
    font-size: 13px;
    grid-column: 1;
  }
  .cpp {
    grid-column: 2;
    grid-row: 1 / span 2;
    font-family: var(--display);
    font-weight: 800;
    color: var(--gold-text);
    font-size: 18px;
  }
  .none {
    padding: 4px 18px;
  }
</style>
