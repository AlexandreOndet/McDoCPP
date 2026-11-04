# McDoCPP

Cents-per-point for every MyMcDonald's Rewards item, at every McDonald's in Canada, from each store's own menu prices.

- `collector/`: Python 3.12 Cloud Run job. Crawls the GMA menu API, computes CPP, writes Parquet history and static JSON.
- `web/`: SvelteKit static site (MapLibre) reading that JSON. Deploys to Cloudflare Pages.
- `docs/`: design spec, hosting costs, decisions, capture procedure, status.

```sh
make setup
make crawl-fixtures   # full out/ tree from synthetic stores, no network
make web-dev
make check
```

Live runs need the credentials described in `docs/CAPTURE.md` in `.env` (see `.env.example`). Unofficial; not affiliated with McDonald's.
