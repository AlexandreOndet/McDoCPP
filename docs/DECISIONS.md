# Decisions

One line each, newest last.

- 2026-11-03 Storage table A (daily `reward_price_daily` Parquet) over A′ events; A′ derivable later.
- 2026-11-03 cpp stored as `price_cents / points` (design §2); UI shows it ×100 labelled "per 100 pts" with $/1k pts beside it, since the mockup's "¢ /pt" is 100× the §2 value.
- 2026-11-03 `TrayPhone.dc.html` absent from design-ref; phone layout built from the brief's description.
- 2026-11-03 Shelves (cards) by default, table view as a toggle; satisfies design §9's "full table" and the Tray brief.
- 2026-11-03 uv + Python 3.12 for collector; pnpm through corepack for web.
- 2026-11-03 Catalogue tiers for cappuccino, McFlurry, McChicken marked "verify" in YAML; curated, not from an API.
- 2026-11-03 Parser: same product ID at several prices → keep the max; reward items are standalone so conflicts only come from combo components.
- 2026-11-03 Refresh token rotation persisted via the storage backend (`secrets/refresh_token` object) when Secret Manager is not configured.
- 2026-11-03 S3 backend uses boto3 as optional extra `[s3]`; default install stays local-only.
- 2026-11-03 Synthetic fixtures: 40 stores over 10 provinces, per-province multiplier plus per-store jitter, fixed seed, 1 to 2 reward items missing at some stores.
- 2026-11-03 Phone shelves follow `docs/design-ref/mobile/TrayPhone.dc.html`: stacked compact rows (art, name, meta, CPP), not horizontal snap rows; the mockup wins over the brief.
- 2026-11-03 Web data base URL is `VITE_DATA_BASE` (Vite-native) rather than SvelteKit `$env`; default `/data` is the copy made by `make crawl-fixtures`.
- 2026-11-03 SvelteKit 3: `$lib` kept via the (deprecated) `alias` option; `#lib` subpath imports need file extensions on every import. Revisit when the alias is removed.
- 2026-11-03 TypeScript pinned to 5.x: SvelteKit 3's tsconfig loader needs `ts.sys`, absent from the TypeScript 7 JS API.
- 2026-11-03 MapLibre worker bundled by Vite (`?worker&url` + `setWorkerUrl`); the library's own `import.meta.url` lookup 404s after a rolldown build.
- 2026-11-03 Map basemap (OpenFreeMap style) is fetched separately and swapped in with `transformStyle`; store markers render on an inline blank style even if the tile server is down.
- 2026-11-03 Pages are prerendered shells with `ssr = false`; all data loads client-side, so the site is a pure static deploy with `?store=` query routing.
- 2026-11-03 Collector raw snapshot pruning (14 days) is done in code for LocalFS; on R2/GCS it is a bucket lifecycle rule.
- 2026-11-04 Token bootstrap: try Path A (anonymous client_credentials guest token) before any account or capture; mcbroken/hotnspicy run this in production for US+CA. Fall back to magic-link (Path B), then device proxy (Path C).
- 2026-11-04 CA routes through us-prod with the US client id + mcd-marketid: CA; no CA-specific mcd-clientid is public. If the guest mint 403s, recover the CA client id by static APK decompile (not an Akamai bypass).
- 2026-11-04 No public CA loyalty/rewards-catalogue endpoint; DE's loyalty surface is points-balance + offers, not a points-tier to product catalogue. Manual rewards_catalogue.yaml stays the source.
- 2026-11-04 Will not build an Akamai x-acf-sensor-data generator; refresh and magic-link paths do not need it, and defeating bot-detection is out of scope.
- 2026-11-04 Collector must egress from a North-American IP; endpoints region-lock with error 41600 otherwise (confirmed across public repos).
- 2026-11-04 Client credentials live in env (MCD_CLIENT_ID/MCD_CLIENT_SECRET), never in the repo; public US pair is in the McReverse/mcbroken repos.
