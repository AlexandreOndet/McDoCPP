<script lang="ts">
  import '../app.css';
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import { page } from '$app/state';
  import Header from '$lib/components/Header.svelte';
  import { app } from '$lib/state.svelte';
  import type { Snippet } from 'svelte';
  import type { LayoutData } from './$types';

  let { data, children }: { data: LayoutData; children: Snippet } = $props();

  const storeId = $derived(page.url.searchParams.get('store') ?? app.lastStore);
  const store = $derived(data.index.stores.find((s) => s.id === storeId) ?? null);

  $effect(() => {
    document.documentElement.lang = app.locale;
  });

  function changeStore() {
    const url = new URL(page.url.href);
    url.searchParams.delete('store');
    url.searchParams.set('pick', '1');
    goto(resolve(`${page.route.id ?? '/'}?${url.searchParams.toString()}`), { reset: false });
  }
</script>

<svelte:head>
  <title>McDoCPP</title>
  <meta name="description" content={app.t('app.tagline')} />
</svelte:head>

<div class="shell">
  <Header storeName={store?.name ?? null} onchange={changeStore} />
  <main>
    {@render children()}
  </main>
  <footer class="muted">
    <p>{app.t('app.disclaimer')}</p>
    <p>{app.t('app.costs')} <span>{app.t('map.tiles')}.</span></p>
  </footer>
</div>

<style>
  .shell {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 32px 56px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }
  main {
    display: flex;
    flex-direction: column;
    gap: 36px;
  }
  footer {
    font-size: 13px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-top: 24px;
    border-top: var(--dash);
  }
  @media (max-width: 760px) {
    .shell {
      padding: 0 0 96px;
      gap: 12px;
    }
    main {
      gap: 20px;
    }
    footer {
      padding: 20px 16px 0;
    }
  }
</style>
