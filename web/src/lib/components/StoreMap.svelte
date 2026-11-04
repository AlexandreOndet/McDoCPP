<script lang="ts">
  import { onMount } from 'svelte';
  import type { Map as MlMap, MapMouseEvent, GeoJSONSource, StyleSpecification, LngLatBoundsLike } from 'maplibre-gl';
  import type { FeatureCollection } from 'geojson';
  import { cppCents } from '$lib/format';
  import { app } from '$lib/state.svelte';
  import type { StoreSummary } from '$lib/types';
  import { quantileBin } from '$lib/cpp';

  let {
    stores,
    cuts,
    selected = null,
    onselect
  }: { stores: StoreSummary[]; cuts: number[]; selected?: string | null; onselect: (id: string) => void } = $props();

  // worst → best quantile
  const COLORS = ['#7a5c4e', '#a8805b', '#d4a544', '#f6c443', '#ffe08a'];
  const DARK = 'https://tiles.openfreemap.org/styles/fiord';
  const LIGHT = 'https://tiles.openfreemap.org/styles/positron';

  let el: HTMLDivElement;
  let map: MlMap | undefined;
  let ready = $state(false);

  function geojson(): FeatureCollection {
    return {
      type: 'FeatureCollection',
      features: stores
        .filter((s) => s.best_cpp !== null)
        .map((s) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [s.lon, s.lat] },
          properties: { id: s.id, name: s.name, cpp: s.best_cpp, bin: quantileBin(s.best_cpp as number, cuts) }
        }))
    };
  }

  function warm(m: MlMap) {
    // Pull the base style toward the palette: background/water/land in the app's browns, labels muted.
    const dark = matchMedia('(prefers-color-scheme: dark)').matches;
    for (const layer of m.getStyle().layers) {
      if (layer.type === 'background') m.setPaintProperty(layer.id, 'background-color', dark ? '#1b1310' : '#fff7ea');
      if (layer.type === 'fill' && /water/.test(layer.id)) m.setPaintProperty(layer.id, 'fill-color', dark ? '#120d0b' : '#e9dcc8');
      if (layer.type === 'fill' && /land|park|wood|grass|residential|building/.test(layer.id)) m.setPaintProperty(layer.id, 'fill-color', dark ? '#231a15' : '#f6e9d6');
      if (layer.type === 'line' && /road|street|highway|motorway|bridge|tunnel|path|rail/.test(layer.id)) m.setPaintProperty(layer.id, 'line-color', dark ? '#40312a' : '#e4d3be');
      if (layer.type === 'line' && /boundary|admin/.test(layer.id)) m.setPaintProperty(layer.id, 'line-color', dark ? '#5a4538' : '#c9b5a3');
      if (layer.type === 'symbol') {
        m.setPaintProperty(layer.id, 'text-color', dark ? '#c9b5a3' : '#6b5a4d');
        m.setPaintProperty(layer.id, 'text-halo-color', dark ? '#1b1310' : '#fff7ea');
      }
    }
  }

  onMount(() => {
    let cancelled = false;
    Promise.all([import('maplibre-gl'), import('maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url')]).then(([{ Map, NavigationControl, AttributionControl, setWorkerUrl }, worker]) => {
      if (cancelled) return;
      // Vite bundles the ESM worker; MapLibre's own import.meta.url lookup does not survive the build.
      setWorkerUrl(worker.default);
      const dark = matchMedia('(prefers-color-scheme: dark)').matches;
      const blank = {
        version: 8 as const,
        sources: {},
        layers: [{ id: 'bg', type: 'background' as const, paint: { 'background-color': dark ? '#1b1310' : '#fff7ea' } }]
      };
      map = new Map({ container: el, style: blank, center: [-79.5, 48.5], zoom: 3.4, attributionControl: false });
      map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
      map.addControl(new AttributionControl({ compact: true }), 'bottom-right');
      map.on('load', () => {
        if (!map) return;
        warm(map);
        map.addSource('stores', { type: 'geojson', data: geojson() });
        map.addLayer({
          id: 'stores-ring',
          type: 'circle',
          source: 'stores',
          paint: { 'circle-radius': 15, 'circle-color': 'rgba(246, 196, 67, 0.25)', 'circle-stroke-width': 3, 'circle-stroke-color': '#f6c443' },
          filter: ['==', ['get', 'id'], selected ?? '']
        });
        map.addLayer({
          id: 'stores-dot',
          type: 'circle',
          source: 'stores',
          paint: {
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 3, 5, 10, 9],
            'circle-color': ['to-color', ['at', ['get', 'bin'], ['literal', COLORS]]],
            'circle-stroke-width': 1.5,
            'circle-stroke-color': '#1b1310'
          }
        });
        map.on('click', 'stores-dot', (e: MapMouseEvent) => {
          const f = map?.queryRenderedFeatures(e.point, { layers: ['stores-dot'] })[0];
          if (f?.properties?.id) onselect(String(f.properties.id));
        });
        map.on('mouseenter', 'stores-dot', () => map && (map.getCanvas().style.cursor = 'pointer'));
        map.on('mouseleave', 'stores-dot', () => map && (map.getCanvas().style.cursor = ''));
        ready = true;
        if (!selected) {
          const pts = stores.filter((s) => s.best_cpp !== null);
          if (pts.length > 1) {
            const b: LngLatBoundsLike = [
              [Math.min(...pts.map((s) => s.lon)), Math.min(...pts.map((s) => s.lat))],
              [Math.max(...pts.map((s) => s.lon)), Math.max(...pts.map((s) => s.lat))]
            ];
            map.fitBounds(b, { padding: 48, maxZoom: 7, duration: 0 });
          }
        }
        // Basemap is optional: fetched separately so a failed tile server never removes the store layers.
        fetch(dark ? DARK : LIGHT)
          .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
          .then((style: StyleSpecification) => {
            if (!map) return;
            map.once('style.load', () => map && warm(map));
            map.setStyle(style, {
              transformStyle: (prev, next) => ({
                ...next,
                sources: { ...next.sources, stores: prev?.sources.stores ?? { type: 'geojson', data: geojson() } },
                layers: [...next.layers, ...(prev?.layers.filter((l) => l.id.startsWith('stores-')) ?? [])]
              })
            });
          })
          .catch(() => undefined);
      });
    });
    return () => {
      cancelled = true;
      map?.remove();
      map = undefined;
    };
  });

  $effect(() => {
    if (!ready || !map) return;
    (map.getSource('stores') as GeoJSONSource | undefined)?.setData(geojson());
  });

  $effect(() => {
    if (!ready || !map) return;
    map.setFilter('stores-ring', ['==', ['get', 'id'], selected ?? '']);
    const s = stores.find((x) => x.id === selected);
    if (s) map.easeTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 11), duration: 600 });
  });

  const legend = $derived(COLORS.map((c, i) => ({ c, label: i === 0 ? `< ${cppCents(cuts[0] ?? 0, app.locale)}` : i === COLORS.length - 1 ? `≥ ${cppCents(cuts[cuts.length - 1] ?? 0, app.locale)}` : '' })));
</script>

<div class="map">
  <div class="canvas" bind:this={el} role="region" aria-label={app.t('map.title')}></div>
  <div class="legend" aria-label={app.t('map.legend')}>
    <span class="muted">{app.t('map.legend')}</span>
    <span class="swatches">
      {#each legend as l, i (i)}
        <span class="sw" style:background={l.c} title={l.label}></span>
      {/each}
    </span>
    <span class="ends"><span>{legend[0].label}</span><span>{legend[legend.length - 1].label}</span></span>
  </div>
</div>

<style>
  @import 'maplibre-gl/dist/maplibre-gl.css';

  .map {
    position: relative;
    height: 100%;
    min-height: 320px;
    border-radius: var(--r-xl);
    overflow: hidden;
    border: 1px solid var(--border);
    background: var(--surface);
  }
  .canvas {
    position: absolute;
    inset: 0;
  }
  .legend {
    position: absolute;
    left: 12px;
    bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 12px;
    background: color-mix(in srgb, var(--surface) 88%, transparent);
    border: 1px solid var(--border);
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
  }
  .swatches {
    display: flex;
    gap: 3px;
  }
  .sw {
    width: 22px;
    height: 10px;
    border-radius: 3px;
  }
  .ends {
    display: flex;
    justify-content: space-between;
    color: var(--muted);
    gap: 10px;
  }
  :global(.maplibregl-ctrl-group) {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    box-shadow: none !important;
  }
  :global(.maplibregl-ctrl-group button) {
    width: 44px !important;
    height: 44px !important;
  }
  :global(.maplibregl-ctrl-group button + button) {
    border-top-color: var(--border) !important;
  }
  :global(.maplibregl-ctrl-icon) {
    filter: invert(0.9) sepia(0.3);
  }
  :global(.maplibregl-ctrl-attrib) {
    background: color-mix(in srgb, var(--surface) 80%, transparent) !important;
    color: var(--muted);
    font-size: 11px;
  }
  :global(.maplibregl-ctrl-attrib a) {
    color: var(--muted);
  }
</style>
