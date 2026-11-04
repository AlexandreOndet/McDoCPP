<script lang="ts">
  import type { Shelf } from '$lib/cpp';
  import { cppCents, points } from '$lib/format';
  import { app } from '$lib/state.svelte';
  import ItemCard from './ItemCard.svelte';

  let { shelf }: { shelf: Shelf } = $props();
</script>

<section class="shelf" class:locked={shelf.locked} aria-labelledby={`shelf-${shelf.tier}`} data-testid="shelf" data-tier={shelf.tier} data-locked={shelf.locked}>
  <header class="rail">
    <h2 id={`shelf-${shelf.tier}`} class="display tier"><span>{shelf.tier / 1000}</span><small>k</small></h2>
    <p class="note">
      {#if shelf.locked}
        <strong>{app.t('shelf.locked', { n: points(shelf.toUnlock, app.locale) })}</strong>
      {:else if shelf.best?.cpp != null}
        {app.t('shelf.count', { n: shelf.items.length, cpp: cppCents(shelf.best.cpp, app.locale) })}
      {/if}
    </p>
  </header>
  <ul class="row">
    {#each shelf.items as item (item.key)}
      <li><ItemCard {item} best={item === shelf.best} /></li>
    {/each}
  </ul>
</section>

<style>
  .shelf {
    display: grid;
    grid-template-columns: 150px 1fr;
    gap: 20px;
    padding: 24px 0 28px;
    border-top: var(--dash);
    transition: opacity 250ms;
  }
  .shelf.locked {
    opacity: 0.55;
  }
  .rail {
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-self: start;
    position: sticky;
    top: 16px;
  }
  .tier {
    font-size: 96px;
    line-height: 0.9;
    color: var(--gold-text);
  }
  .locked .tier {
    color: var(--muted);
  }
  .tier small {
    font-size: 40px;
    font-weight: 700;
    margin-left: 2px;
    color: var(--muted);
  }
  .note {
    color: var(--muted);
    font-weight: 600;
    font-size: 14px;
    max-width: 150px;
  }
  .note strong {
    color: var(--text);
  }
  .row {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 16px;
    min-width: 0;
  }
  .row li {
    display: flex;
    min-width: 0;
  }
  .row li > :global(*) {
    flex: 1;
  }

  @media (max-width: 760px) {
    .shelf {
      grid-template-columns: 1fr;
      gap: 12px;
      padding: 18px 0 20px;
    }
    .rail {
      position: static;
      flex-direction: row;
      align-items: baseline;
      gap: 14px;
      padding: 0 16px;
    }
    .tier {
      font-size: 48px;
    }
    .tier small {
      font-size: 22px;
    }
    .note {
      max-width: none;
    }
    .row {
      display: flex;
      flex-direction: column;
      padding: 0 16px;
      gap: 8px;
    }
  }
</style>
