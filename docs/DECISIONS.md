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
