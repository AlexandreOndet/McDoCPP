<script lang="ts">
  import Food from '$lib/components/Food.svelte';
  import { loadAggregate } from '$lib/data';
  import { cppCents, per1k } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import type { AggregateDoc } from '$lib/types';

  let doc = $state<AggregateDoc | null>(null);
  let scope = $state('national');
  $effect(() => {
    loadAggregate(scope).then((d) => (doc = d));
  });
  const scopes = ['national', 'QC', 'ON', 'BC', 'AB', 'MB', 'SK', 'NS', 'NB', 'NL', 'PE'];
</script>

<section class="stub">
  <h1>{app.t('stub.deals')}</h1>
  <p class="muted">{app.t('stub.coming')}</p>
  <div class="scopes">
    {#each scopes as s (s)}
      <button type="button" class="pill" aria-pressed={scope === s} onclick={() => (scope = s)}>{s === 'national' ? 'Canada' : s}</button>
    {/each}
  </div>
  {#if doc}
    <ol class="list">
      {#each doc.items as it (it.key)}
        <li>
          <Food kind={it.kind} size={40} />
          <span class="n">{name(it.names, app.locale)}</span>
          <span class="muted">{it.tier / 1000}k</span>
          <span class="cpp display">{cppCents(it.median_cpp, app.locale)}</span>
          <span class="muted small">{per1k(it.median_cpp, app.locale)} / 1k · {app.t('stub.n_stores', { n: it.n_stores })} · {app.t('stub.spread', { cpp: cppCents(it.spread, app.locale) })}</span>
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
  .scopes {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
  }
  .list li {
    display: grid;
    grid-template-columns: 40px 1fr auto auto;
    gap: 4px 14px;
    align-items: center;
    padding: 10px 0;
    border-bottom: var(--dash);
  }
  .n {
    font-weight: 700;
  }
  .cpp {
    font-size: 22px;
    color: var(--gold-text);
  }
  .small {
    grid-column: 2 / -1;
    font-size: 13px;
  }
</style>
