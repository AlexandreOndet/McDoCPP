# Status (2026-11-03)

Phases 0 to 2 of the roadmap (`docs/mcdocpp-design.md` §11) are implemented. Everything below runs from fixtures with no network and no credentials.

```sh
make setup            # uv sync + pnpm install
make check            # ruff, mypy --strict, pytest (27), eslint, svelte-check, vitest (11)
make crawl-fixtures   # 40 synthetic stores → out/ (JSON + Parquet + raw gz) → web/static/data
make web-build        # static site in web/build, deployable to Cloudflare Pages as-is
make e2e              # Playwright: search → store → balance → hero → locked shelf; table view; change store
make screens          # docs/screens/{desktop,phone,landing,desktop-light}.png
```

## Done

**Phase 0**
- `collector/spike.py`: refresh → fetch one store → parse `GMA_PICKUP` + `en-CA`/`fr-CA` → reward prices and CPP. `--fixture` reads `fixtures/menu_sample.json`; `--save` keeps a live payload.
- `docs/CAPTURE.md`: exactly which headers and fields to capture, and what to note for sizing.

**Phase 1** (`collector/mcdocpp/`)
- `auth.py` token manager (refresh chain, rotation persisted to `secrets/refresh_token` in storage; Secret Manager version pruning is left to the operator, see below).
- `fetcher.py`: ≤1 req/s jittered, randomized order, 401 → refresh once, 403/429/5xx → exponential backoff, abort past 10 % errors after 20 requests.
- `parser.py`: recursive walk, `QUANTITY` add-ons skipped, duplicate ID → max price kept and conflict recorded, hash of the price vector for dedup.
- `catalogue.py` + `rewards_catalogue.yaml`: 23 items, post-2025-09-16 tiers; regex → pinned IDs (`crawl --pin-ids` writes them back); >5 % unresolved → alert in `meta.json`.
- `cpp.py`: highest-priced qualifying variant, null when absent, breakfast flag, per-store and per-tier best.
- `history.py`: Parquet tiers A (`reward_price_daily`), B (`cpp_aggregate_daily`, `best_cpp_daily`), B′ (monthly rollups), DuckDB aggregates with the 48 h freshness filter, 7-day window, p10/p90/spread, share_best. Raw tier D as gz, 14-day prune.
- `publisher.py` + `schemas/*.schema.json`: every §8 file, each validated against its schema before write, each carrying `as_of`.
- `storage.py`: `LocalFS` (default) and `S3Compatible` (R2/GCS via boto3, optional extra).
- `synth.py`: 40 stores, 10 provinces, province multiplier + store jitter, a few missing optional items, a duplicate-ID price conflict every 7th store.
- `Dockerfile` (builds, 2-stage, non-root), `cloudrun-job.yaml`, `scheduler.sh`.

**Phase 2** (`web/`)
- SvelteKit 3 static adapter, Svelte 5, MapLibre 6 with OpenFreeMap tiles restyled to the palette, markers by best-CPP quantile with legend, selected ring, `?store=<id>` URLs, last store remembered.
- U1 search (accent-insensitive, keyboard listbox, geolocation nearest) + map; U2 shelves with best card, locked shelves, delta vs Canada, breakfast badge, table view; U3 wallet with meter, best-for-balance, next-tier hint, breakfast skip; U6 `en-CA`/`fr-CA` string files, item names from data, `lang` attribute follows the locale.
- Dark default, light via `prefers-color-scheme`. Fonts self-hosted via `@fontsource`. Original SVG sprite, 12 food kinds, `<use>`.
- Phone layout per `docs/design-ref/mobile/TrayPhone.dc.html`: sticky compact wallet, hero, stacked rows per shelf, map as a bottom sheet.
- U4/U5/U7 routes (`/deals`, `/compare`, `/history`) read the aggregate, nearby and history JSON and render plain lists.

## Stubbed or thin
- `/deals`, `/compare`, `/history`: data wired, no charts, item pickers are hard-coded key lists. Phase 3.
- History has one day of data in fixtures, so monthly series are one point. The synthetic generator has no multi-day mode.
- `stores.py::discover` parses the DE-market shape of `/exp/v1/restaurant/location`; field names are a guess until a CA capture exists.
- No Cloud Monitoring alert wiring; `meta.json.alerts` and a non-zero exit code are the signals.
- Catalogue tiers for cappuccino, McFlurry and McChicken are marked `verify` in the YAML.
- Light-theme map uses the Positron style with a warm tint; not tuned as carefully as dark.

## Phase 0 exit criteria (§3.7)

| # | Criterion | State |
|---|---|---|
| 1 | CA login + refresh captured; refresh works without `x-acf-sensor-data` | **Needs your token.** `uv run spike.py --store <id>` prints "refresh ok" |
| 2 | 3 stores in 3 provinces match the app and a receipt | **Needs your token** + a receipt photo |
| 3 | Enumerate all CA restaurant IDs (~1,400–1,500) | `mcdocpp discover` written, **needs token + a real response to confirm field names** |
| 4 | Loyalty catalogue endpoint for CA? | **Needs token.** Until then the YAML catalogue is the source |
| 5 | Payload size and rate-limit behaviour | **Needs a live run**; `--save` keeps one payload for sizing |
| 6 | GMA from GCP vs Cloudflare vs residential IP | **Needs a real-IP test**; the Docker image runs the same `crawl` anywhere |

## Token bootstrap (research 2026-11-04, public sources)

The one-time token capture may be unnecessary. Public trackers mint an anonymous **client_credentials** token and read menus with no account. See `docs/CAPTURE.md` Path A. Open question, answerable with one request from a Canadian IP: does the CA price `/menus` endpoint accept a guest token?

Confirmed from public code (mcbroken, hotnspicy, McReverse, CyrilSLi, BuyMeMcDonalds):
- `/login/refresh` does not need the Akamai sensor header; refresh rotates both tokens; access token ~15 min.
- Store sweep is `GET /exp/v1/restaurant/location?distance=&filter=summary&latitude=&longitude=&pageSize=`; fields `nationalStoreNumber`, `address.{addressLine1,cityTown,postalZip}`, `location.{latitude,longitude}`. The `stores.py` parser matches this.
- Endpoints region-lock to North-American IPs (error 41600).

Gaps that still need your own run: whether a guest token works on CA menus, the current CA `mcd-clientid` (US id is the public default; APK decompile recovers a CA-specific one if needed), the `/menus` payload size, and whether a CA rewards-catalogue endpoint exists.

## Operator notes
- Secrets only via env / Secret Manager (`.env.example`). The job writes the rotated refresh token to `secrets/refresh_token` in the bucket; keep Secret Manager at ≤6 versions by hand or a small follow-up.
- R2 lifecycle rule for `raw/` (14 days) is bucket config.
- `web/.env`: `VITE_DATA_BASE` = R2 custom domain for production; omit for the bundled fixture copy.
