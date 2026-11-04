<script lang="ts">
  import { isStale, seenAt } from '$lib/format';
  import { app } from '$lib/state.svelte';

  let { asOf }: { asOf: string } = $props();
  const stale = $derived(isStale(asOf));
  const seen = $derived(seenAt(asOf, app.locale));
</script>

{#if stale}
  <div class="stale" role="alert">{app.t('stale.banner', { n: seen.days })}</div>
{:else}
  <span class="seen muted" data-testid="seen-at">
    {seen.key === 'today' ? app.t('store.seen_today', { time: seen.time }) : seen.key === 'yesterday' ? app.t('store.seen_yesterday', { time: seen.time }) : app.t('store.seen_days', { n: seen.days })}
  </span>
{/if}

<style>
  .stale {
    padding: 14px 20px;
    border-radius: var(--r-lg);
    background: var(--warn);
    color: #1b1310;
    font-weight: 700;
    font-size: 16px;
  }
  .seen {
    font-size: 13px;
    font-weight: 600;
  }
</style>
