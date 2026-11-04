# McDoCPP — Design & Architecture Documentation
 
**Status:** Draft v0.2 — 2026-11-04 (v0.1 2026-10-31)
**Owner:** h4dd0ck
**Scope:** Canada only (MyMcDonald's Rewards CA, en-CA / fr-CA)
**See also:** `docs/mcdocpp-hosting-costs.md` (cost scenarios; the S2.5 architecture below is derived from it)
 
---
 
## 1. What McDoCPP is
 
McDoCPP shows, for every McDonald's restaurant in Canada, the **cents-per-point (CPP)** value of each item redeemable with MyMcDonald's Rewards points, using **that restaurant's actual in-store price**.
 
Reward tiers are national (2,000 / 4,000 / 6,000 / 10,000 / 14,000 pts) but menu prices are set per restaurant by franchisees. The same 2,000-pt redemption is therefore worth more at some locations than others, and the "best" redemption changes from store to store. Existing content (Rewards Canada, Milesopedia, etc.) publishes CPP computed from a single city's prices — e.g. Rewards Canada's Sept-2025 "top 5" used pre-tax prices from NW Calgary and explicitly notes prices vary by location. McDoCPP replaces that single-point estimate with per-restaurant, continuously refreshed data.
 
### Core user stories
 
| # | As a user I want to… | Notes |
|---|---|---|
| U1 | Search for or pick a restaurant on a map | Text search (address / city / postal code / store #) + map markers |
| U2 | See every reward item at that restaurant ranked by CPP | **Full list visible**, not just top N. Grouped by tier, sortable |
| U3 | Know the single best redemption for my current points balance | Input: points balance → best item ≤ balance, plus "wait for next tier?" hint |
| U4 | See the best deals **on average across all locations** over the past few days | National / provincial rolling-window aggregates (default 7 days) |
| U5 | Compare nearby restaurants for one item | "Where is the McFlurry redemption worth the most within 10 km?" |
| U6 | Switch language en-CA / fr-CA | Item names come localized from the source; UI strings in both |
| U7 | See how CPP has evolved over months/years | Per-item national/provincial median CPP timeline, "best available CPP" timeline, catalogue changes annotated |
 
### Non-goals (v1)
- Ordering, login to McDonald's on behalf of users, offers/coupons.
- US or other markets.
- Delivery-app pricing as a *source of truth* (see §3).
- Retaining full menu history for non-reward products (see §7 retention).
---
 
## 2. Definitions
 
- **CPP** — `price_cents / points_required`. 1 pt earned per 1¢ spent (100 pts / $1), so CPP > 1.0 means the redemption beats the earn rate. Reported with 4 decimals (e.g. `0.1895`) to match community convention, and also as **$ value per 1,000 pts**.
- **Price basis** — pre-tax, **pickup/in-store channel** (`GMA_PICKUP`), regular menu price (no promos/offers).
- **Reward item** — an entry in the MyMcDonald's Rewards catalogue: `(tier_points, product reference, size constraint, availability window e.g. breakfast-only)`.
- **Snapshot** — one restaurant's full menu+prices at one timestamp.
---
 
## 3. Phase 0 — Price data source investigation
 
This phase gates everything else. Findings so far and the decision tree.
 
### 3.1 Is there a public McDonald's API? — **No**
McDonald's Corp. runs no developer program, publishes no API docs and offers no self-service signup; menu, loyalty and restaurant data flow only through bilateral partner integrations (delivery marketplaces, POS vendors). Confirmed by api-evangelist/apis.io profile (as of 2026-06) and by the absence of any official docs.
 
### 3.2 The McDonald's app backend (GMA) — **Primary candidate**
 
The Global Mobile App (GMA) talks to an undocumented but stable REST backend. It is the **same price feed the app, kiosks and POS use**, so it is the only source that is correct by construction.
 
**Evidence / prior art (Canada-specific):**
[CyrilSLi/mcdonalds-price-tracker](https://github.com/CyrilSLi/mcdonalds-price-tracker) — a Canadian project (datasets for Regina, Saskatoon, Winnipeg area, Brandon, Kitchener-Waterloo, Mississauga…, bilingual UI) that compares menu prices across restaurants. Its `fetch_menu.py` reveals the Canadian endpoints:
 
| Purpose | Endpoint |
|---|---|
| Full menu + prices for a store | `GET https://us-prod.api.mcd.com/ca/gma/api/v1/restaurants/{restaurant_id}/menus` |
| Store details (address, hours, geo) | `GET https://us-prod.api.mcd.com/exp/v1/restaurant/{restaurant_id}?filter=full&storeUniqueIdType=NSN` |
| Token refresh | `POST https://us-prod.api.mcd.com/exp/v1/customer/login/refresh` body `{"refreshToken": ...}` → `response.accessToken` / `response.refreshToken` |
| Nearby stores (seen in DE market lib, same `exp/v1` surface) | `GET …/exp/v1/restaurant/location?distance=&latitude=&longitude=&pageSize=&filter=summary` |
 
Headers (from the German-market lib [Louuke/McReverse](https://github.com/Louuke/McReverse), structure identical across markets): `Authorization: Bearer <accessToken>`, `mcd-clientid: <static app client id>`, `mcd-marketid: CA`, `mcd-uuid: <random UUIDv4>`, plus the usual app UA headers. The initial **login** (`/exp/v1/customer/login`) requires an Akamai Bot Manager `x-acf-sensor-data` header; **refresh does not appear to** (CyrilSLi's script runs refresh with only the captured headers). Practical consequence: bootstrap once by capturing a login from a real device (mitmproxy / Frida, standard pentest tooling), then keep the refresh-token chain alive indefinitely.
 
**Payload shape (from `process_menus.py`):**
```
channelMenus
├── channels
│   ├── GMA_PICKUP   ← price basis for CPP
│   ├── DELIVERY     (McDelivery in-app channel)
│   └── EATIN
│   └── … nested categories → items {ID, price (int cents), type, options[]}
└── localizations
    ├── en-CA {strings[], lookup{productID: [.., .., stringIndex]}}
    └── fr-CA {…}
```
- Prices are **integer cents** (`479` = $4.79).
- `type: "QUANTITY"` entries with `options[[price, …]]` are add-ons (extra sauce, etc.) — irrelevant to rewards but must be skipped correctly.
- Same add-on can have different prices depending on parent item → not a concern for reward items, which are standalone products, but the parser must not assume price uniqueness per ID.
- Localization strings are identical across restaurants in a region (the tracker asserts this), so a single product-ID → name map can be shared.
- **The payload contains strings like `** Delivery DD **`, `** Delivery Uber **`, `** Delivery Skip **`.** This shows that McDonald's Canada maintains **separate per-platform price lists for DoorDash, Uber Eats and SkipTheDishes inside its own menu system** and pushes them to the marketplaces. See §3.3 for why this matters.
**Risks:**
- Undocumented; endpoint or schema may change without notice (track `mcd-clientid` / app version bumps).
- Akamai may be extended to refresh or menu endpoints; mitigation: keep request rate low, rotate `mcd-uuid`, keep a captured sensor-data generator as fallback.
- ToS: scraping the consumer app API is against McDonald's app terms. Treat as a personal/educational project, publish aggregates not raw dumps, honour takedown, no bulk redistribution of the raw menu JSON. (Same posture as McBroken / price-tracker projects, which have run for years.)
### 3.3 Food-delivery APIs — **Rejected as price source, kept as validation signal**
 
The user concern was: "delivery prices aren't accurate, so we'd have to see how they get pricing from McDonald's in the first place." Findings:
 
1. **Delivery apps don't invent the price — McDonald's gives it to them.** Marketplace integrations are bilateral; the merchant sets its own menu prices on Uber Eats / DoorDash (both platforms state this publicly). The GMA payload above proves McDonald's maintains a dedicated per-platform delivery price list (`Delivery DD / Uber / Skip`).
2. **Those lists are systematically higher than in-store.** Business Insider found McDonald's delivery menu prices ~19.6 % above in-store; Self.inc's 2025 100-city study found all-in delivery orders ~69–71 % above in-restaurant cost (fees included). The Canadian app Ritual built a whole feature (MenuIQ) around exposing this gap.
3. **The uplift is not a constant factor** — it varies by item and by platform, so "divide Uber price by 1.2" would yield wrong CPP rankings, especially between tiers.
**Decision:** delivery-app prices are **never** used to compute CPP. If the GMA source dies, fallback order is §3.4, then §3.5 — not Uber Eats. Delivery prices may optionally be stored as a separate `channel` column to (a) show users the pickup-vs-delivery gap and (b) sanity-check GMA data (a store whose Uber price is *lower* than our pickup price signals a stale snapshot).
 
### 3.4 Fallback A — Web/kiosk menu surfaces
`mcdonalds.ca` menu pages show national "representative" pricing only (no store-level prices) → unusable for per-restaurant CPP, but useful as a product catalogue (names, images, categories, nutrition) to join with GMA product IDs.
 
### 3.5 Fallback B — Crowdsourced receipts
Pattern from [vom00/sandwich-index](https://github.com/vom00/sandwich-index): users log the price from a receipt / app screenshot (OCR), each price tagged with source + date, stale entries excluded from comparisons. Low coverage, high noise, but zero dependency on McDonald's infra. Keep as a v2 "report a price" feature that overlays on GMA data rather than as a primary source.
 
### 3.6 Other prior art reviewed
- `zivreich/McIndex` — country-level Big-Mac-index style tracker; useful UI ideas for historical charts.
- `NottWald0/mcprecios-madrid` — Uber Eats scraper for McDonald's Madrid; documents Uber's bot verification blocking headless scrapers (another reason to avoid Uber as a source).
- `schmwong/APAC-McDelivery-Menu-Logger`, `Kripu77/Pricescrapper` — McDelivery/AU scrapers; confirm McDelivery web surfaces also expose channel-specific prices.
- `hujjun/mcd-saver-strategist` et al. — McDonald's **China** exposes an official MCP server with `calculate-price`; nothing equivalent exists for Canada.
### 3.7 Phase 0 exit criteria
- [ ] Capture a CA login + refresh from a disposable McDonald's account; confirm refresh works server-side without `x-acf-sensor-data`.
- [ ] Fetch menus for 3 stores in 3 provinces; confirm `GMA_PICKUP` prices match the app UI and a physical receipt.
- [ ] Enumerate all CA restaurant IDs (via `/exp/v1/restaurant/location` grid sweep, or seed from OpenStreetMap / All The Places `ref` tags) — expect ~1,400–1,500 stores.
- [ ] Confirm whether a loyalty catalogue endpoint exists for CA (`/exp/v1/loyalty/...` surface is present in DE) — otherwise curate the rewards catalogue manually (§4).
- [ ] Measure payload size (raw and gzipped) and rate-limit behaviour to size the daily crawl and the raw-snapshot retention window.
- [ ] Test the GMA endpoints from a GCP egress IP, a Cloudflare IP and a residential IP; decide where the collector lives (§6, S5 fallback in the cost doc).
---
 
## 4. Rewards catalogue
 
### 4.1 Program facts (Canada)
- Earn: 100 pts per $1 pre-tax on eligible purchases; delivery excluded. Points expire 6 months after being earned.
- Five tiers: **2,000 / 4,000 / 6,000 / 10,000 / 14,000** pts.
- Redemption = one item per redemption, at any participating CA restaurant; code generated in-app.
- Catalogue changes a few times a year (notably **2025-09-16**: added cappuccinos, Chicken Snack Wrap 6k, Filet-O-Fish 10k, FoF EVM 14k; large drinks moved 2k→4k; large fries 4k→6k; several sandwiches/meals removed). Not every menu item is redeemable (historically no McGriddles, shakes).
### 4.2 Representation
`rewards_catalogue.yaml`, versioned with `valid_from` dates so historical CPP is computed against the catalogue that was live at the time:
 
```yaml
- tier: 2000
  items:
    - key: coffee_sm_md        # stable McDoCPP key
      names: {en: "Premium Roast Coffee (S/M)", fr: "Café Premium (P/M)"}
      product_match:           # how to find the price in a GMA snapshot
        name_regex: "^(Sm|Med) Premium Roast Coffee$"
        pick: max              # if several sizes qualify, use the most expensive (best CPP)
      availability: all_day
    - key: hash_brown
      product_match: {name_regex: "^Hash Brown$"}
      availability: breakfast
- tier: 4000
  ...
```
Matching is done against the localized `en-CA` string via regex, then **pinned to numeric product IDs** after first resolution (IDs are stable; names occasionally change). A nightly job flags reward entries that fail to resolve at >5 % of stores.
 
### 4.3 Catalogue sourcing
1. Preferred: loyalty endpoint on the GMA API (to be confirmed in Phase 0).
2. Otherwise: manual curation from the app's Rewards tab + change-announcement emails; diff monthly.
---
 
## 5. CPP computation
 
```
cpp(item, store, t) = price_cents(product_id(item), store, GMA_PICKUP, t) / item.tier_points
value_per_1k_pts    = cpp * 1000 / 100            # dollars per 1,000 pts
```
Rules:
- Use the **highest-priced qualifying variant** when a reward allows several (e.g. "small or medium" → medium).
- Items unavailable at a store (not in its menu) → `null`, excluded from rankings, shown greyed in the full list.
- Breakfast-only items are flagged; ranking offers an "all-day only" toggle.
- Per-store best = `argmax cpp` over the catalogue; per-tier best also computed.
- **Aggregates (U4):** for each item, daily median and mean CPP across all stores with a fresh snapshot (≤ 48 h), then a rolling 7-day window. Rank by median to resist outliers. Also expose per-province aggregates (prices cluster regionally).
- **Spread metric:** for each item, `p90 − p10` CPP across stores → tells users which rewards are worth "shopping around" for.
- **History (U7):** daily aggregates are rolled up to monthly (median of daily medians, mean, p10/p90, n_stores, share of stores where the item is the store-best); per scope, the "best available CPP" series = median over stores of each store's best CPP, plus the item most often best. Catalogue version boundaries are stored alongside so tier changes annotate the charts.
---
 
## 6. System architecture
 
Stack chosen to match existing tooling (Python, GCP) **and to stay inside free tiers** (cost doc, scenario S2.5). Principle: **the read path is static** — everything users see is a JSON file written once a day; no live API, no document DB, no load balancer in v1–v3.
 
```
Cloud Scheduler (daily) ──► Cloud Run Job "collector"  (Python 3.12, httpx, DuckDB; 1 vCPU / 512 MiB, ~25 min)
                              - token mgr: refresh, persist new refresh token (Secret Manager, ≤6 versions)
                              - fetcher: 1,500 stores @ ≤1 req/s jittered, randomized order, backoff on 401/403/429
                              - raw gz snapshots → object store "raw/"  (14-day lifecycle rule; change-only)
                              - parser → reward_price_daily (Parquet, kept forever)
                              - aggregator → cpp_aggregate_daily / monthly, best_cpp series (Parquet, kept forever)
                              - publisher → derived JSON → public bucket on a custom domain
                                   stores/{id}.json, aggregates/{scope}/{window}.json,
                                   history/{scope}/{item}.json, items/{key}/nearby.json, meta.json
                                   (Cache-Control: max-age=3600)
Static SPA (Svelte/React + MapLibre GL) on Cloudflare Pages (or Firebase Hosting)
Map tiles: OpenFreeMap (hosted, free) or self-hosted PMTiles Canada extract on Cloudflare R2
```
 
**Object store:** Cloudflare R2 (zero egress, 10 GB free) is the default for both `raw/`, `history/` and the public JSON; GCS is an acceptable substitute if everything should stay in one GCP project (adds ~$0.1–0.5/mo of egress at 10 k visits, more if tiles are served from it — don't). The collector stays a Cloud Run Job either way; it writes to R2 via the S3 API.
 
**Why not Firestore / Cloud Run API / Cloud CDN (v0.1 design):** none of U1–U7 needs per-request compute; the per-store document is a static file, the "best for my balance" query is client-side over that file. Cloud CDN requires an external HTTPS LB (~$18/mo floor), which was the single largest line in the v0.1 bill. Revisit when v4 price reports need writes (a Cloudflare Worker or an LB-less Cloud Run service behind Firebase Hosting rewrites).
 
**Why not BigQuery as the system of record:** the reward-price history is ≤1 GB/yr of Parquet; DuckDB inside the job queries it directly. An optional BigQuery mirror (batch-loaded from the same Parquet, free) is fine for ad-hoc SQL in the console.
 
**Collector details**
- One service account; secrets (`accessToken`, `refreshToken`, `mcd-clientid`, captured headers) in Secret Manager; refresh-token rotation persisted after every refresh (losing the chain means re-capturing a login on a device). Destroy the previous secret version after each rotation to stay in the free tier.
- Run as a single ~25-minute burst (idle CPU inside a Cloud Run Job is billed; "spread over 6 h" would cost ~$7/mo). If spreading is needed for rate reasons, use 6 scheduled batches of ~250 stores.
- Abort the run and alert if error rate > 10 % (likely schema or auth change).
- Snapshot dedup: hash the normalized price vector per store; only write a raw snapshot and new history rows when changed (prices change rarely → most days are near no-ops after the first).
- Store discovery job weekly: `/exp/v1/restaurant/location` sweep over a lat/lon grid covering Canada, merged with OSM `brand:wikidata=Q38076` + `ref` for cross-checking; store opening/closing tracked.
- Alternative homes for the same job if cloud egress IPs get bot-managed: a small VPS (~€5/mo) or a home box on a residential IP pushing to R2 (cost doc S4/S5). Nothing else in the architecture changes.
---
 
## 7. Data model & retention
 
Parquet on the object store, partitioned `year=/month=/`, written and read with DuckDB. Rows are **reward items only**; the other ~365 products per store are never persisted beyond the raw snapshot window.
 
```
restaurant(id PK, nsn, name, address, city, province, postal, lat, lon, status, first_seen, last_seen)        -- forever
product(id PK, name_en, name_fr, category, first_seen, last_seen)                                            -- forever (reward-matched products + candidates)
rewards_catalogue(version, valid_from, valid_to, tier_points, item_key, product_match, availability)        -- forever
reward_price_daily(date, restaurant_id, item_key, product_id, price_cents, cpp, available)                  -- forever; 52.5 k rows/day ≈ 0.2–1 GB/yr
cpp_aggregate_daily(date, scope {national|province|city}, item_key, n_stores, median_cpp, mean_cpp, p10, p90, share_best)
best_cpp_daily(date, scope, median_best_cpp, mean_best_cpp, best_item_mode)                                 -- forever; ~2–3 k rows/day
cpp_aggregate_monthly / best_cpp_monthly(month, scope, item_key, …)                                         -- forever; what the charts read
raw/{date}/{restaurant_id}.json.gz                                                                           -- 14-day lifecycle; change-only
```
 
| Tier | What | Retention | Why |
|---|---|---|---|
| A | `reward_price_daily` | ∞ | source for any future stat; cheap enough to keep whole |
| A′ (option) | `reward_price_events(restaurant_id, item_key, price_cents, valid_from, valid_to)` | ∞ | ~50× smaller than A; reconstruct any day with `ASOF JOIN`; pick one of A/A′ in Phase 1 |
| B | daily + monthly aggregates, best-CPP series | ∞ | pre-materialized so the frontend reads a few KB per chart |
| C | catalogue versions, product map, store lifecycle | ∞ | history is uninterpretable without them |
| D | raw GMA snapshots | 14 days | parser debugging / reprocessing a recent bug; switch to change-only-forever (~5 GB/yr) only if non-reward history is ever wanted |
 
Trade-off accepted: nothing about non-reward products is recoverable beyond 14 days.
 
---
 
## 8. Published JSON (static, replaces the v0.1 read API)
 
| Path | Contents |
|---|---|
| `meta.json` | catalogue version, last crawl time, store count, `as_of` |
| `stores/index.json` | all stores: id, name, lat/lon, province, best_cpp, as_of (for map + search; ~100 KB gz) |
| `stores/{id}.json` | full reward list ranked by CPP: item, price, tier, cpp, $/1k, availability, delta vs national median, as_of; en + fr names (U2, U3 computed client-side from this file) |
| `aggregates/{scope}/7d.json` | rolling 7-day medians/means/p10/p90/spread per item (U4) |
| `items/{key}/nearby.json` | per item: every store's cpp + lat/lon, for client-side radius filtering (U5) |
| `history/{scope}/{item}.json` | monthly series + catalogue-change markers (U7) |
| `history/{scope}/best.json` | monthly "best available CPP" series (U7) |
 
All files carry `as_of`; the UI shows staleness > 48 h explicitly. Everything is served with `Cache-Control: max-age=3600` and regenerated once a day.
 
---
 
## 9. Frontend behaviour
 
- Landing: map centred on user location (permission) or Canada; markers coloured by store's best CPP quantile; search box (address, city, postal, store #) over `stores/index.json`.
- Store panel: header (address, as_of), **best redemption** card (points-balance input, client-side), then **full table** grouped by tier: item, price, pts, CPP, $/1k pts, availability badge, delta vs national median (▲▼). Sort by CPP default; toggle all-day only; en/fr switch.
- "Deals" tab (U4): top items by 7-day national median CPP, with sparkline of the daily median, spread indicator, and province filter.
- "Compare" (U5): pick an item → nearby stores listed/plotted by CPP, radius filter client-side.
- "History" tab (U7): per-item CPP over time (national / province), best-available-CPP line, catalogue changes as annotations.
- Offline-friendly: last viewed store cached in localStorage.
- Footer: unofficial disclaimer + "hosting costs ~$1/month, ad-free" tip link (Stripe Payment Link or GitHub Sponsors; cost doc §7).
---
 
## 10. Operational / legal posture
 
- Low request volume (≈ 1 req/store/day), clear UA, no concurrency bursts, respect 429.
- Publish derived data (CPP, aggregates, reward-item prices), not raw menu dumps; raw snapshots are private and short-lived (14 days).
- Disposable McDonald's account dedicated to the collector; no user credentials ever handled.
- Clear disclaimer: unofficial, not affiliated with McDonald's; prices pre-tax, may lag.
- Monitoring: Cloud Monitoring alerts on crawl failure, auth failure, catalogue resolution failures, aggregate anomalies (e.g. national median moves > 15 % day-over-day → likely parsing bug, not a price change). GCP budget alert at $5; R2 ops notification.
- Donations framed as hosting-cost recovery only, not a product.
---
 
## 11. Roadmap
 
| Phase | Deliverable |
|---|---|
| 0 | Source investigation (§3.7 checklist), spike script fetching + parsing one store, IP-origin test, legal/ToS go/no-go |
| 1 | Collector job for all CA stores; rewards catalogue v1; `reward_price_daily` + aggregates in Parquet; published JSON; CLI output |
| 2 | Static SPA: map/search, full per-store ranking, best-for-balance (U1–U3) |
| 3 | Deals tab, nearby comparison, history tab (U4, U5, U7); fr-CA (U6) |
| 4 | Crowdsourced price reports overlay (§3.5) — first component needing writes; optional delivery-channel gap display; alerts ("McFlurry CPP at your store just improved") |
 
---
 
## 12. Open questions
 
1. Does a CA loyalty catalogue endpoint exist on the GMA API, and does it carry product IDs we can join directly?
2. Does the refresh endpoint stay Akamai-free long-term? Plan B is a sensor-data generator.
3. Are reward items priced identically across `GMA_PICKUP` and `EATIN`? (Expected yes; verify — if not, expose a channel toggle.)
4. Do franchisees exclude specific reward items ("participating restaurants")? If the loyalty endpoint is per-store, use it; otherwise flag items missing from the store menu.
5. Tax: provinces differ; CPP stays pre-tax by convention, but show post-tax value as a tooltip?
6. History table shape: A (daily partition) vs A′ (price-change events)? Decide in Phase 1.
7. R2 vs GCS for the object store — R2 unless single-project GCP simplicity wins.
---
 
## 13. References
 
- CyrilSLi/mcdonalds-price-tracker — https://github.com/CyrilSLi/mcdonalds-price-tracker (CA GMA endpoints, payload structure)
- Louuke/McReverse — https://github.com/Louuke/McReverse (GMA auth headers, Akamai sensor, `exp/v1` surface)
- api-evangelist/mcdonalds — https://github.com/api-evangelist/mcdonalds (no public API, partner-only integrations)
- vom00/sandwich-index — https://github.com/vom00/sandwich-index (crowdsourced price pattern)
- zivreich/McIndex — https://github.com/zivreich/McIndex
- NottWald0/mcprecios-madrid — https://github.com/NottWald0/mcprecios-madrid (Uber Eats scraping pitfalls)
- McDonald's Canada — MyMcDonald's Rewards — https://www.mcdonalds.com/ca/en-ca/mymcdonaldsrewards.html
- iPhone in Canada, 2025-08-13 — Rewards menu changes effective 2025-09-16 — https://www.iphoneincanada.ca/2025/08/13/mcdonalds-canada-rewards-program-just-got-worse-for-customers/
- Rewards Canada, 2025-09-16 — "5 best MyMcDonald's Rewards redemptions" — https://blog.rewardscanada.ca/news/5-best-mymcdonalds-rewards-redemptions/
- Milesopedia — MyMcDonald's Rewards guide — https://milesopedia.com/en/loyalty-program/mymcdonalds-rewards/
- Self.inc — delivery app markups study (2025) — https://www.self.inc/info/most-expensive-cities-for-food-delivery-apps/
- MobileSyrup — Ritual MenuIQ in-store vs delivery pricing — https://mobilesyrup.com/?p=959180
- McDoCPP hosting cost scenarios — `docs/mcdocpp-hosting-costs.md`
