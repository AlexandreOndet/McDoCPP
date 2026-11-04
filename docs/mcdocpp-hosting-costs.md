# McDoCPP — Hosting cost scenarios & recommendation
 
**Status:** v0.2 — 2026-11-04 (v0.1 2026-11-03)
**Companion to:** `docs/mcdocpp-design.md` (§6 architecture, §11 roadmap)
**Prices:** USD list prices, Tier-1 / us-central1 (or northamerica-northeast1, same tier), checked 2026-11-03. GCP bills CAD accounts in CAD at Google's rate. All "always free" tiers below are per billing account, not per project.
 
---
 
## 0. TL;DR
 
- The app is tiny. Every feature in the design doc fits inside free tiers **except two things that are infrastructure choices, not features**: an external HTTPS load balancer (required for Cloud CDN, ≈ $18/mo floor) and map-tile bandwidth.
- **The national-average / U4 aggregates cost ≈ $0 extra.** The data behind them is ~1,500 stores × ~35 reward items × 7 days ≈ 370 k tiny rows. It is a few seconds of DuckDB/SQL inside the job that already runs. The "100×" fear doesn't materialize; build it.
- **Multi-year history is also ≈ $0** if you keep the *reward-item* price table (≈ 0.2–1 GB/yr Parquet) and discard the raw full-menu snapshots (≈ 110 GB/yr). See §4b.
- Realistic steady-state bill for the recommended architecture (**S2.5**): **$0–1/mo + domain (~$15/yr)** at up to ~50 k visits/month. A VPS alternative is a flat ~€5/mo. Either is covered by one or two coffees a month.
- Recommendation: **static read path** (derived JSON published daily to Cloudflare Pages/R2, or Firebase Hosting), **collector as a Cloud Run Job** (free tier), **PMTiles on R2 or OpenFreeMap** for the map, **no live API, no Firestore, no load balancer** for v1–v3.
---
 
## 1. Workload sizing (inputs to every scenario)
 
| Quantity | Value | Basis |
|---|---|---|
| Stores (CA) | ~1,500 | design §3.7 |
| Reward items | ~35 | 5 tiers, catalogue §4 |
| Menu products per store | ~400 | GMA payload |
| Raw menu payload / store | ~1–3 MB JSON, ~150–250 KB gzipped | price-tracker datasets; **verify in Phase 0** |
| Crawl | 1 req/s jittered → ~25 min active CPU/day at 1 vCPU / 512 MiB | design §6 |
| Monthly collector compute | ~45,000 vCPU-s, ~22,500 GiB-s | 1,500 s/day × 30 |
| Daily derived output | 1,500 store JSON (~5 KB gz each) + aggregates ≈ 8 MB | §8 API shapes |
| Reward-price rows/day (store × item) | 52,500 | 1,500 × 35 |
| Raw full-menu rows/day (store × product) | 600,000 | 1,500 × 400 |
| Visit payload | SPA ~300 KB gz (MapLibre is most of it) + ~50 KB JSON | — |
| Map tiles per visit | 2–5 MB (vector tiles, a few pans/zooms) | typical MapLibre session |
 
Traffic tiers used below: **1 k / 10 k / 100 k / 1 M visits per month**. For a Canada-only niche tool, 1 k–10 k is the realistic band; 100 k is "Reddit front page week".
 
---
 
## 2. Unit prices used
 
| Service | Free tier (monthly) | Beyond |
|---|---|---|
| Cloud Run **Jobs** | 240 k vCPU-s, 450 k GiB-s | $0.000018/vCPU-s, $0.000002/GiB-s |
| Cloud Run **Services** (request-based) | 180 k vCPU-s, 360 k GiB-s, 2 M req, 1 GB NA egress | $0.000024/vCPU-s, $0.0000025/GiB-s, $0.40/M req |
| Cloud Scheduler | 3 jobs | $0.10/job/mo |
| Secret Manager | 6 active secret versions | $0.06/version/mo |
| Cloud Storage (standard) | 5 GB (via Firebase/Always Free) | $0.020/GB/mo, $0.005/1k class-A ops, egress $0.12/GB |
| BigQuery | 10 GB storage, 1 TB query | $0.02/GB/mo active, $0.01/GB/mo long-term (>90 d untouched), batch load free |
| Firestore | 1 GiB, 50 k reads/day, 20 k writes/day, 10 GiB egress | $0.03/100 k reads, $0.09/100 k writes, $0.12/GiB |
| Firebase Hosting | 10 GB stored, 360 MB/day (~10 GB/mo) transfer | $0.026/GB stored, **$0.15/GB transfer** |
| Cloud CDN + external HTTPS LB | — | LB forwarding rule ≈ $18/mo floor + $0.08/GB + $0.0075/10 k req |
| Cloudflare Pages | unlimited bandwidth, 500 builds/mo | — |
| Cloudflare R2 | 10 GB, 1 M writes, 10 M reads, **egress always free** | $0.015/GB/mo |
| Cloudflare Workers (free) | 100 k req/day, 30 s cron execution | $5/mo paid plan: 15 min cron |
| Hetzner Cloud | — | CAX11 (ARM, 2 vCPU/4 GB) ≈ €3.3–3.8; CX23 ≈ €4–5.5 after the 2026 increases; 20 TB traffic |
| GitHub Actions | 2,000 min/mo private, unlimited public repos | — |
 
---
 
## 3. Feature-by-feature marginal cost
 
| Feature | What it adds to the pipeline | Marginal $/mo | Notes |
|---|---|---|---|
| **U1–U3** per-store CPP, best redemption, map/search | daily crawl + 1,500 derived JSON files + SPA | **$0** | all inside Cloud Run Jobs + hosting free tiers |
| **U4** national/provincial 7-day aggregates | keep 7 daily CPP tables (~50 k rows each) and run median/p10/p90 | **≈ $0** (seconds of CPU, <50 MB state) | does not need BigQuery or Firestore; DuckDB over Parquet in GCS/R2 is enough |
| **U5** nearby comparison | read-only, computed client-side from an item→stores index (~35 files × 1,500 entries) | **$0** | static JSON |
| **U6** fr-CA | second set of strings in the same JSON | $0 | — |
| **Multi-year history of reward prices / CPP** (§4b) | append 52.5 k rows/day of Parquet, forever | **$0.00–0.02 per year of history** | 0.2–1 GB/yr; under R2/BQ free tiers for ~10 yrs |
| Raw snapshot retention 90 d (§6) | 1,500 × ~200 KB × 90 d ≈ 27 GB in GCS | **$0.45–0.65** | drop to ~$0.05 by only storing snapshots whose hash changed; on R2 ($0.015/GB) it's $0.25 or free under 10 GB with change-only storage |
| Raw snapshots forever (every day) | ~110 GB/yr | **+$1.6–2.2 per year accumulated** | the only line that grows meaningfully; not needed for any user story |
| Weekly store-discovery sweep | a few thousand extra requests/week | $0 | — |
| Live read API (Cloud Run service) instead of static JSON | per-request compute | $0 at ≤10 k visits; ~$1–3 at 100 k | fine *without* Cloud CDN; see next line |
| **Cloud CDN in front of the API** | needs an external HTTPS load balancer | **≈ +$18–20** | the single biggest line item in the drafted design; not justified for this app |
| Firestore `latest` documents | 1,500 writes/day, N reads/visit | $0 up to ~1.5 M reads/mo | redundant if the read path is static |
| Map tiles (vector, Canada) | 2–5 MB per visit | **$0** on R2 (PMTiles) or OpenFreeMap; $0.15/GB on Firebase Hosting; $0.08–0.12/GB on GCS/Cloud CDN | this is where traffic cost actually lives; keep it off GCP egress |
| Price-report overlay (v4) | small writes from users | $0 on Firestore free tier; needs abuse controls more than money | — |
| Alerts (v4, email/push) | SendGrid/Resend free tiers, or FCM free | $0–$5 | — |
| Monitoring/logging | 50 GB logs free, basic alerting free | $0 | keep collector logs terse |
 
Fixed costs regardless of scenario: domain ~$15–20/yr; Secret Manager stays free if you keep ≤6 active versions (prune old refresh-token versions in the rotation code).
 
---
 
## 4. Scenarios
 
### S0 — Static MVP (U1–U3)
Cloud Run Job (daily, 1 vCPU/512 MiB, ~25 min) → derived JSON to R2 or Firebase Hosting → SPA on Cloudflare Pages/Firebase Hosting → PMTiles on R2.
 
| Visits/mo | 1 k | 10 k | 100 k | 1 M |
|---|---|---|---|---|
| Collector | $0 | $0 | $0 | $0 |
| Hosting, Cloudflare Pages + R2 | $0 | $0 | $0 | $0 |
| Hosting, Firebase Hosting (site + JSON only, tiles on R2) | $0 | $0 | ~$4.50 (40 GB) | ~$150 |
| **Total (Cloudflare path)** | **$0** | **$0** | **$0** | **~$0** |
 
### S1 — S0 + U4/U5 aggregates
Same job keeps 7 daily Parquet/CPP tables (≈ 50 MB) and emits `aggregates/*.json` + per-item nearby indexes. **Delta vs S0: $0 at every traffic tier.**
 
### S2 — S1 + full history (90-day raw in GCS/R2 + BigQuery price_snapshot)
 
| | any traffic |
|---|---|
| Raw retention (change-only) | $0.05 |
| Raw retention (every snapshot, 27 GB on GCS) | $0.65 |
| BigQuery | $0–0.20 |
| **Total** | **$0.10–0.90** |
 
### S2.5 — S1 + long-term reward-price history, no raw archive ← **chosen**
Keep forever: `reward_price_daily` Parquet (52.5 k rows/day), daily aggregates, monthly rollups, catalogue versions. Keep raw full-menu snapshots only for the last 7–14 days (debugging parser changes). Details in §4b.
 
| | yr 1 | yr 3 | yr 10 |
|---|---|---|---|
| Reward-price history on R2 (≤1 GB/yr worst case) | $0 | $0 | $0–0.15 |
| Raw snapshots, 14-day rolling (~4 GB) | $0 (under R2 free 10 GB) or $0.08 on GCS | same | same |
| Aggregates + rollups | $0 | $0 | $0 |
| Optional mirror in BigQuery | $0 | $0 | $0–0.10 |
| **Total** | **$0–0.10** | **$0–0.10** | **$0–0.35** |
 
### S3 — Design doc as drafted (Cloud Run API + Firestore + Cloud CDN/LB + BigQuery + GCS + Firebase Hosting)
 
| | 1 k | 10 k | 100 k | 1 M |
|---|---|---|---|---|
| External HTTPS LB + Cloud CDN | $18 | $18.50 | $22 | $60 |
| Cloud Run API | $0 | $0 | $0–2 | $10–20 |
| Firestore | $0 | $0 | $0–1 | $10–20 |
| BigQuery + GCS | $0.70 | $0.70 | $0.70 | $0.70 |
| Firebase Hosting (SPA) | $0 | $0 | $3 | $45 |
| Tiles on GCS/CDN egress (3 MB/visit) | $0 | $2.40 | $24 | $240 |
| **Total** | **~$19** | **~$22** | **~$50–55** | **~$370–390** |
 
→ ~20× S2 at low traffic, entirely from the LB and tile egress, neither of which the features require.
 
### S3′ — S3 without the LB (Firebase Hosting rewrites → Cloud Run, Cache-Control) and tiles on R2
 
| | 1 k | 10 k | 100 k | 1 M |
|---|---|---|---|---|
| **Total** | **~$0.70** | **~$0.70** | **~$5** | **~$60** |
 
### S4 — Single VPS (Hetzner CAX11/CX23 or equivalent), Cloudflare free in front
cron + Python collector + DuckDB + Caddy serving static JSON and PMTiles. **€3.5–5.5 flat at any traffic** (20 TB included; Cloudflare caches the rest). Pros: no pricing surprises, one box, DuckDB holds all history. Cons: you patch it; single point of failure; datacenter IP same as GCP from Akamai's point of view.
 
### S5 — Home box collector + Cloudflare
Collector on a Pi / spare machine on a residential IP (lower Akamai risk than any cloud range), pushes Parquet + derived JSON to R2; site on Cloudflare Pages. **$0.** Plan B if cloud egress IPs get bot-managed; fine Plan A for a personal project.
 
---
 
## 4b. Long-term history without storing the whole dataset
 
What the long-term charts need (avg CPP per item over months/years, avg "best CPP" per store, tier changes) is a function of **reward-item prices only**, never the other ~365 products per store. So:
 
### Retention tiers
 
| Tier | Table | Grain | Size | Retention |
|---|---|---|---|---|
| **A — keep forever** | `reward_price_daily` | (date, store_id, item_key, price_cents, cpp, available) | 52.5 k rows/day ≈ 0.2–1 GB/yr Parquet (zstd, sorted by store then item compresses very well since prices rarely change) | ∞ |
| **A′ — alternative, even smaller** | `reward_price_events` | (store_id, item_key, price_cents, valid_from, valid_to) — one row per price *change* | ~1,500 × 35 × ~6 changes/yr ≈ 300 k rows/yr ≈ 5–10 MB/yr | ∞; reconstruct any day with a DuckDB `ASOF JOIN` |
| **B — keep forever** | `cpp_aggregate_daily` | (date, scope ∈ {national, province×13, city top-50}, item_key, n, median, mean, p10, p90) + `best_cpp_daily` (date, scope, median_best, mean_best, best_item_mode) | ~2–3 k rows/day ≈ 20–40 MB/yr | ∞ |
| **B′ — materialized** | `cpp_aggregate_monthly` | same as B at month grain | <1 MB/yr | ∞; this is what the frontend charts read |
| **C — keep forever** | `rewards_catalogue` versions, `product` id→name map, `restaurant` open/close | tiny | ∞ (history is uninterpretable without the catalogue in force at the time) |
| **D — short rolling** | raw GMA snapshots (gz JSON) | per store per day, change-only | ~15 MB/day change-only → ≤4 GB for 14 d of every-day, far less change-only | 7–14 days (parser debugging / reprocessing); or change-only forever at ~5 GB/yr if you want full reprocessability later |
 
Recommended: **A + B + B′ + C, D at 14 days.** If you later want to reprocess (e.g. add non-reward products), you can switch D to change-only-forever at that point; nothing before that date is recoverable, which is acceptable.
 
### Where it lives
- **Parquet on R2 (or GCS), partitioned `year=/month=/`**, written by the collector job with DuckDB. One file per day for A, one per month for B. Query locally or in the job with DuckDB; no warehouse needed. 10 years ≈ 2–10 GB → still mostly inside R2's free 10 GB.
- **Optional BigQuery mirror** (batch load from the same Parquet, free): useful only for ad-hoc SQL in the console; storage drops to long-term pricing after 90 days anyway. $0–0.10/mo over a decade.
- Frontend reads **B′ JSON** (monthly series per item, per scope) — a few KB per chart — never scans A.
### Stats to materialize (so the charts are one JSON read)
- per item × scope × month: median & mean CPP, p10/p90, n_stores, % stores where it's the store-best
- per scope × month: median "best CPP available" across stores, and the item that was best most often
- per item: CPP timeline with catalogue-version boundaries (tier changes, add/remove) as annotations
- per store: own CPP vs scope median over time (from A on demand, or precomputed per store if cheap enough — 1,500 × 35 × 12 points/yr is ~1 MB total)
---
 
## 5. Traffic sensitivity, in one line each
 
- **Collector and storage cost are flat** at any traffic level — functions of store count and days, not visitors.
- **Read path on Cloudflare (Pages + R2): flat $0** to ~1 M visits. The only metered thing is R2 ops (10 M reads free/mo).
- **Read path on Firebase Hosting: $0 to ~25 k visits, then ≈ $0.045 per thousand visits** for the SPA alone, ×8 if tiles are served from it too.
- **Anything behind a GCP external LB: $18/mo before the first visitor.**
---
 
## 6. Recommendation
 
**Architecture for v1–v3 (replaces design §6's read path and storage):**
 
```
Cloud Scheduler (daily) ──► Cloud Run Job "collector"
                              - refresh token, crawl 1,500 stores @1 req/s (~25 min)
                              - hash-dedup; raw gz snapshots → R2 "raw/" with 14-day lifecycle rule
                              - DuckDB: reward_price_daily (A), aggregates (B), monthly rollups (B′)
                                → Parquet on R2 "history/" (kept forever)
                              - publish derived JSON (stores/{id}.json, aggregates/*.json,
                                history/{item}.json, items/{key}/nearby.json, meta.json)
                                → R2 public bucket on a custom domain
Cloudflare Pages ◄── static SPA (MapLibre), reads JSON from R2, Cache-Control: max-age=3600
Cloudflare R2   ◄── PMTiles (Canada extract, ~2–4 GB) via range requests, or OpenFreeMap
```
 
- **$0–1/mo + domain.** Everything in the design's U1–U6, aggregates, and multi-year history.
- Don't spread the crawl over 6 h *inside* one Cloud Run Job (idle CPU is billed on jobs: ~$7/mo). Run the 25-minute burst, or 6 scheduled batches of 250 stores.
- Keep ≤6 secret versions; delete the old refresh-token version after each rotation.
- Skip Firestore, Cloud Run API, Cloud CDN and the LB until v4 price reports need per-request compute (a Cloudflare Worker or an LB-less Cloud Run service handles that for $0–5).
- Tiles: start with **OpenFreeMap** → zero ops; self-host PMTiles on R2 if you want control. Never serve tiles from Firebase Hosting or GCS.
- Set a **GCP budget alert at $5** and an R2 ops notification; the only realistic way to exceed $5 is a bug (collector looping on 401s and re-uploading).
**If you'd rather not touch GCP at all:** S4 (VPS, ~€5 flat) or S5 (home box, $0) are equally valid; S4 is the simplest mental model, S5 has the best IP posture.
 
---
 
## 7. Donations ("buy me a coffee")
 
Costs are ~$1/mo + domain, so the goal is "cover hosting + domain", i.e. ~$30–40/yr. One $5 coffee every 2–3 months does it.
 
Fees as of 2026-11 (**Ko-fi's pricing page now lists a 5 % service fee on its Standard plan — the "0 % on tips" figure in most third-party write-ups is stale**):
 
| Platform | Platform fee | Processor fee | Notes |
|---|---|---|---|
| Ko-fi Standard | 5 % | Stripe/PayPal ≈ 2.9 % + $0.30 | Gold ($12/mo) removes the 5 % — pointless at this volume |
| Buy Me a Coffee | 5 % | + Stripe | equivalent to Ko-fi; slightly nicer button UX |
| **GitHub Sponsors** | 0 % | 0 % for individual sponsors | best net if the repo is public; least discoverable from a web app |
| **Stripe Payment Link (CAD)** | 0 % | 2.9 % + $0.30 CAD | your own "tip" page, no third party; 5 min to set up |
| Liberapay | 0 % | processor only | recurring-only model, less familiar to donors |
| Interac e-Transfer (link/QR) | 0 % | 0 % | Canadian-only, manual, no button UX |
 
Net on a $5 tip: Stripe link ≈ $4.55, Ko-fi/BMC ≈ $4.30. Practical pick: **Stripe Payment Link** (CAD, one-time, preset $3/$5/$10) or GitHub Sponsors if the repo is public; keep Ko-fi/BMC only if you want their hosted page. Footer copy: "Hosting costs ~$1/month, ad-free — buy me a McCafé ☕" with the real number. Tips are taxable income in Canada but at tens of dollars a year it's a line on the T1.
 
Keep donations framed as *hosting cost recovery*, not a product you sell — consistent with the personal/educational posture (design §3.2 risks) if a takedown ever arrives.
 
---
 
## 8. Open items
 
1. Verify raw payload size and compressed size in Phase 0 (drives tier D sizing).
2. Decide tiles: OpenFreeMap (zero-ops) vs PMTiles on R2 (self-hosted, ~2–4 GB Canada extract).
3. Test whether `us-prod.api.mcd.com` behaves differently from GCP vs Cloudflare vs residential IPs before committing to the collector's home (S5 fallback).
4. Update `docs/mcdocpp-design.md` §6–7 to the static read path and the §4b retention tiers (drop Firestore/Cloud CDN from v1–v3; `price_snapshot` becomes reward-only + 14-day raw).
5. Decide A vs A′ (daily partition vs price-change events) — A is simpler to query, A′ is ~50× smaller; both are free.
