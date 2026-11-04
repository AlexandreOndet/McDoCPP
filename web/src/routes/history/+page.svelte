<script lang="ts">
  import { loadHistory, loadHistoryBest } from '$lib/data';
  import { cppCents } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import type { HistoryBestDoc, HistoryDoc } from '$lib/types';

  let key = $state('big_mac');
  let item = $state<HistoryDoc | null>(null);
  let best = $state<HistoryBestDoc | null>(null);
  const keys = ['big_mac', 'fries_md', 'mcflurry', 'nuggets_10', 'hash_brown', 'coffee_sm_md'];

  $effect(() => {
    loadHistory('national', key).then((d) => (item = d));
  });
  $effect(() => {
    loadHistoryBest('national').then((d) => (best = d));
  });
</script>

<section class="stub">
  <h1>{app.t('stub.history')}</h1>
  <p class="muted">{app.t('stub.coming')}</p>
  <select bind:value={key} aria-label={app.t('table.item')}>
    {#each keys as k (k)}<option value={k}>{k}</option>{/each}
  </select>
  {#if item}
    <h2>{name(item.item.names, app.locale)}</h2>
    {#if item.series.length}
      <p class="muted">{app.t('stub.months', { n: item.series.length })}</p>
      <ul class="list">
        {#each item.series as m (m.month)}
          <li><span class="n">{m.month}</span><span class="cpp display">{cppCents(m.median_cpp, app.locale)}</span><span class="muted">{app.t('stub.n_stores', { n: m.n_stores })}</span></li>
        {/each}
      </ul>
    {:else}
      <p class="muted">{app.t('stub.no_history')}</p>
    {/if}
    <p class="muted small">
      {#each item.catalogue_changes as c (c.version)}<span>catalogue {c.version} from {c.valid_from}</span>{/each}
    </p>
  {/if}
  {#if best?.series.length}
    <h2>{app.t('nav.history')}: best available</h2>
    <ul class="list">
      {#each best.series as m (m.month)}
        <li><span class="n">{m.month}</span><span class="cpp display">{cppCents(m.median_best_cpp, app.locale)}</span><span class="muted">{app.t('stub.best_mode', { item: m.best_item_mode })}</span></li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .stub {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 0 16px;
  }
  select {
    align-self: flex-start;
    min-height: var(--hit);
    padding: 0 14px;
    border-radius: var(--r-pill);
    background: var(--surface);
    border: 1px solid var(--border);
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
  .small {
    font-size: 13px;
  }
</style>
