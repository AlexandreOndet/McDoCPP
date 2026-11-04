<script lang="ts">
  import { meterFill, nextTier } from '$lib/cpp';
  import { points } from '$lib/format';
  import { app } from '$lib/state.svelte';

  let { tiers, compact = false }: { tiers: readonly number[]; compact?: boolean } = $props();
  const id = $derived(compact ? 'pts-compact' : 'pts');

  const fill = $derived(meterFill(app.balance, tiers));
  const next = $derived(nextTier(app.balance, tiers));
  const top = $derived(tiers[tiers.length - 1]);

  function onInput(e: Event) {
    const el = e.target as HTMLInputElement;
    const v = parseInt(el.value.replace(/\D/g, '') || '0', 10);
    app.balance = Math.min(999999, Math.max(0, Number.isFinite(v) ? v : 0));
    app.save();
  }
  function onBlur(e: Event) {
    (e.target as HTMLInputElement).value = points(app.balance, app.locale);
  }
</script>

<section class="wallet card" class:compact aria-labelledby={`${id}-label`}>
  <label id={`${id}-label`} for={id} class="label">{app.t('wallet.label')}</label>
  <div class="row">
    <input
      {id}
      class="display pts"
      type="text"
      inputmode="numeric"
      autocomplete="off"
      value={points(app.balance, app.locale)}
      oninput={onInput}
      onblur={onBlur}
      aria-describedby={`${id}-line`}
    />
    <span class="unit display">{app.t('wallet.pts')}</span>
  </div>

  <div class="meter" role="meter" aria-valuemin="0" aria-valuemax={top} aria-valuenow={Math.min(app.balance, top)} aria-label={app.t('wallet.label')}>
    <div class="track"><div class="fill" style:width={`${(fill * 100).toFixed(1)}%`}></div></div>
    <ol class="marks">
      {#each tiers as t (t)}
        <li class:reached={t <= app.balance} style:left={`${(t / top) * 100}%`}>{t / 1000}k</li>
      {/each}
    </ol>
  </div>

  <p id={`${id}-line`} class="muted line">
    {next ? app.t('wallet.next', { n: points(next - app.balance, app.locale) }) : app.t('wallet.all_open')}
    {#if !compact}{app.t('wallet.expiry')}{/if}
  </p>

  <label class="check">
    <input type="checkbox" bind:checked={app.allDayOnly} onchange={() => app.save()} />
    {app.t('wallet.skip_breakfast')}
  </label>
</section>

<style>
  .wallet {
    padding: 28px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .label {
    font-weight: 700;
    color: var(--muted);
  }
  .row {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }
  .pts {
    width: 7ch;
    max-width: 100%;
    background: transparent;
    border: 0;
    border-bottom: 2px solid var(--gold);
    border-radius: 0;
    color: var(--text);
    font-size: 56px;
    padding: 0;
  }
  .unit {
    font-weight: 500;
    font-size: 22px;
    color: var(--muted);
  }
  .meter {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding-bottom: 18px;
  }
  .track {
    position: relative;
    height: 14px;
    border-radius: 7px;
    background: var(--meter-track);
    overflow: hidden;
  }
  .fill {
    position: absolute;
    inset: 0 auto 0 0;
    background: var(--gold);
    border-radius: 7px;
    transition: width 250ms ease-out;
  }
  .marks {
    position: relative;
    list-style: none;
    margin: 0;
    padding: 0;
    height: 18px;
    font-family: var(--display);
    font-weight: 700;
    font-size: 12px;
    color: var(--muted);
  }
  .marks li {
    position: absolute;
    transform: translateX(-100%);
    padding-left: 2px;
  }
  .marks li.reached {
    color: var(--gold-text);
  }
  .check {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-height: var(--hit);
    cursor: pointer;
    font-weight: 600;
  }
  .check input {
    accent-color: var(--gold);
    width: 20px;
    height: 20px;
    margin: 0;
  }

  .compact {
    padding: 12px 16px;
    gap: 8px;
    border-radius: 0 0 var(--r-lg) var(--r-lg);
  }
  .compact .label {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
  }
  .compact .row {
    gap: 8px;
  }
  .compact .pts {
    font-size: 32px;
    width: 6ch;
  }
  .compact .unit {
    font-size: 15px;
  }
  .compact .meter {
    padding-bottom: 10px;
    gap: 4px;
  }
  .compact .track {
    height: 6px;
  }
  .compact .marks {
    height: 14px;
    font-size: 11px;
  }
  .compact .line {
    font-size: 12px;
  }
  .compact .check {
    min-height: 32px;
    font-size: 13px;
  }
  .compact .check input {
    width: 18px;
    height: 18px;
  }
</style>
