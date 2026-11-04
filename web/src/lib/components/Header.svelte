<script lang="ts">
  import { page } from '$app/state';
  import { resolve } from '$app/paths';
  import { app } from '$lib/state.svelte';

  let { storeName = null, onchange }: { storeName?: string | null; onchange?: () => void } = $props();

  function toggleLang() {
    app.locale = app.locale === 'fr-CA' ? 'en-CA' : 'fr-CA';
    app.save();
  }

  const qs = $derived(page.url.searchParams.toString());
  const links = [
    { route: '/', key: 'nav.store' },
    { route: '/deals', key: 'nav.deals' },
    { route: '/compare', key: 'nav.compare' },
    { route: '/history', key: 'nav.history' }
  ] as const;
</script>

<header class="hdr">
  <a href={qs ? resolve(`/?${qs}`) : resolve('/')} class="brand">
    <span class="roundel" aria-hidden="true">¢</span>
    McDoCPP
  </a>
  <p class="tag muted">{app.t('app.tagline')}</p>
  <nav class="nav" aria-label="Sections">
    {#each links as l (l.key)}
      <a href={qs ? resolve(`${l.route}?${qs}`) : resolve(l.route)} class="pill" class:is-active={page.route.id === l.route}>{app.t(l.key)}</a>
    {/each}
  </nav>
  <div class="right">
    {#if storeName}
      <button type="button" class="pill store" onclick={onchange} data-testid="change-store">
        <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold-text)" stroke-width="2.2"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
        <span class="store-name">{storeName}</span>
        <span class="muted">{app.t('search.change')}</span>
      </button>
    {/if}
    <button type="button" class="pill lang" onclick={toggleLang} lang={app.locale === 'fr-CA' ? 'en-CA' : 'fr-CA'} aria-label={app.t('lang.switch')} data-testid="lang">
      {app.t('lang.switch_short')}
    </button>
  </div>
</header>

<style>
  .hdr {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px 24px;
    padding: 18px 0;
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--text);
    font-family: var(--display);
    font-weight: 800;
    font-size: 26px;
    letter-spacing: -0.02em;
  }
  .roundel {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--gold);
    color: #1b1310;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }
  .tag {
    flex: 1 1 260px;
  }
  .nav {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .nav .pill {
    background: transparent;
    border-color: transparent;
    color: var(--muted);
    padding: 0 12px;
  }
  .nav .pill.is-active {
    background: var(--surface);
    border-color: var(--border);
    color: var(--text);
  }
  .right {
    margin-left: auto;
    display: flex;
    gap: 10px;
    align-items: center;
  }
  .store-name {
    max-width: 28ch;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .lang {
    background: transparent;
    color: var(--muted);
    min-width: var(--hit);
  }
  @media (max-width: 760px) {
    .hdr {
      padding: 12px 0;
      gap: 10px 16px;
    }
    .tag {
      display: none;
    }
    .nav {
      order: 3;
      width: 100%;
      overflow-x: auto;
      flex-wrap: nowrap;
      scrollbar-width: none;
    }
    .nav .pill {
      white-space: nowrap;
      flex: none;
    }
    .right {
      margin-left: 0;
      width: 100%;
      order: 2;
    }
    .store {
      flex: 1;
      justify-content: flex-start;
      border-radius: 16px;
    }
    .store-name {
      max-width: none;
      flex: 1;
      text-align: left;
    }
    .store .muted {
      color: var(--gold-text);
      font-size: 13px;
    }
    .lang {
      order: -1;
      position: absolute;
      right: 16px;
      top: 12px;
    }
    .hdr {
      position: relative;
      padding: 12px 16px;
    }
  }
</style>
