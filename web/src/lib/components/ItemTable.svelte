<script lang="ts">
  import type { Shelf } from '$lib/cpp';
  import { cppCents, delta, money, per1k, points } from '$lib/format';
  import { name } from '$lib/i18n';
  import { app } from '$lib/state.svelte';
  import Food from './Food.svelte';

  let { shelves }: { shelves: Shelf[] } = $props();
</script>

<div class="wrap">
  <table>
    <thead>
      <tr>
        <th scope="col">{app.t('table.item')}</th>
        <th scope="col" class="num">{app.t('table.price')}</th>
        <th scope="col" class="num">{app.t('table.cpp')}</th>
        <th scope="col" class="num">{app.t('table.per1k')}</th>
        <th scope="col" class="num">{app.t('table.delta')}</th>
      </tr>
    </thead>
    {#each shelves as shelf (shelf.tier)}
      <tbody class:locked={shelf.locked}>
        <tr class="tier">
          <th scope="rowgroup" colspan="5">
            <span class="display">{points(shelf.tier, app.locale)} {app.t('wallet.pts')}</span>
            {#if shelf.locked}<span class="muted">{app.t('shelf.locked', { n: points(shelf.toUnlock, app.locale) })}</span>{/if}
          </th>
        </tr>
        {#each shelf.items as item (item.key)}
          {@const d = delta(item.delta_vs_national, app.locale)}
          <tr class:best={item === shelf.best} class:unavailable={item.cpp === null}>
            <th scope="row">
              <Food kind={item.kind} size={28} />
              <span>{name(item.names, app.locale)}</span>
              {#if item.breakfast}<span class="badge">{app.t('card.breakfast')}</span>{/if}
            </th>
            <td class="num">{item.price_cents !== null ? money(item.price_cents, app.locale) : app.t('card.unavailable')}</td>
            <td class="num cpp">{item.cpp !== null ? cppCents(item.cpp, app.locale) : ''}</td>
            <td class="num">{item.cpp !== null ? per1k(item.cpp, app.locale) : ''}</td>
            <td class="num" class:up={d.sign > 0} class:down={d.sign < 0}>{d.text}</td>
          </tr>
        {/each}
      </tbody>
    {/each}
  </table>
</div>

<style>
  .wrap {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
  }
  th,
  td {
    padding: 10px 12px;
    text-align: left;
    vertical-align: middle;
    border-bottom: var(--dash);
  }
  thead th {
    color: var(--muted);
    font-weight: 700;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
  }
  .num {
    text-align: right;
    white-space: nowrap;
  }
  tr.tier th {
    padding-top: 22px;
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 14px;
    align-items: baseline;
  }
  tr.tier .display {
    font-size: 24px;
    color: var(--gold-text);
  }
  tbody.locked tr:not(.tier) {
    opacity: 0.55;
  }
  tbody.locked .display {
    color: var(--muted);
  }
  th[scope='row'] {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
  }
  tr.best th[scope='row'] span:first-of-type {
    color: var(--gold-text);
  }
  tr.best .cpp {
    color: var(--gold-text);
    font-weight: 800;
  }
  tr.unavailable {
    color: var(--muted);
  }
  .cpp {
    font-family: var(--display);
    font-weight: 700;
    font-size: 17px;
  }
  .badge {
    padding: 0 8px;
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 12px;
    color: var(--muted);
  }
  .up {
    color: var(--success);
  }
  .down {
    color: var(--warn);
  }
</style>
