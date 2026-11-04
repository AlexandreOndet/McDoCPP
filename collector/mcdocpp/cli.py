"""mcdocpp CLI: crawl (fixtures or live), synth, discover."""

from __future__ import annotations

import gzip
import json
import logging
import os
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import httpx
import typer

from . import history as hist
from .auth import TokenManager
from .catalogue import ResolutionStats, load_catalogue, pin_product_ids
from .cpp import RewardPrice, compute_store
from .fetcher import AbortCrawl, FixtureSource, HttpSource, MenuSource
from .fetcher import crawl as run_crawl
from .parser import parse_menu
from .publisher import Publisher, dumps, scope_path, validate
from .storage import LocalFS, Storage, from_env
from .stores import Store, dump_stores, load_stores
from .stores import discover as run_discover
from .synth import generate

app = typer.Typer(add_completion=False, no_args_is_help=True)
log = logging.getLogger("mcdocpp")
REPO = Path(__file__).resolve().parents[2]
CATALOGUE_PATH = REPO / "collector" / "rewards_catalogue.yaml"
RAW_RETENTION_DAYS = 14
LOCAL_TZ = ZoneInfo("America/Toronto")


def _storage(out: Path | None) -> Storage:
    return LocalFS(out) if out else from_env()


def _put_json(storage: Storage, path: str, doc: dict[str, Any]) -> None:
    validate(path, doc)
    storage.put(path, dumps(doc), "application/json")


def _prune_raw(storage: Storage, today: date) -> None:
    """Bucket lifecycle rules do this on S3; LocalFS needs it done here."""
    cutoff = (today - timedelta(days=RAW_RETENTION_DAYS)).isoformat()
    for key in storage.list("raw/"):
        day = key.split("/")[1]
        if day < cutoff:
            storage.delete(key)


@app.command()
def crawl(
    fixture_dir: Annotated[
        Path | None, typer.Option(help="Read <id>.json payloads from here instead of the network")
    ] = None,
    stores_file: Annotated[
        Path | None, typer.Option(help="Store list JSON; default state/stores.json in storage")
    ] = None,
    out: Annotated[Path | None, typer.Option(help="LocalFS root; default from env")] = None,
    as_of: Annotated[str | None, typer.Option(help="ISO datetime, default now (UTC)")] = None,
    pin_ids: Annotated[bool, typer.Option(help="Write resolved product IDs back to the catalogue YAML")] = False,
    rate: Annotated[float, typer.Option(help="Min seconds between requests (0 for fixtures)")] = 1.0,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    t0 = time.monotonic()
    storage = _storage(out)
    now = datetime.fromisoformat(as_of).astimezone(UTC) if as_of else datetime.now(UTC)
    today = now.astimezone(LOCAL_TZ).date()
    catalogue = load_catalogue(CATALOGUE_PATH)
    version = catalogue.version_for(today)

    if stores_file:
        stores = load_stores(stores_file.read_bytes())
    else:
        data = storage.get("state/stores.json")
        if data is None:
            raise typer.BadParameter("no store list: pass --stores-file or run `mcdocpp discover`")
        stores = load_stores(data)
    by_id = {s.id: s for s in stores}

    source: MenuSource
    if fixture_dir:
        source = FixtureSource(fixture_dir)
        rate = 0.0
    else:
        tokens = TokenManager.from_env(persist=lambda t: storage.put("secrets/refresh_token", t.encode(), "text/plain"))
        source = HttpSource(tokens, httpx.Client(timeout=30))

    hashes: dict[str, str] = json.loads((storage.get("state/hashes.json") or b"{}").decode())
    stats = ResolutionStats()
    rows_by_store: dict[str, list[RewardPrice]] = {}
    all_rows: list[RewardPrice] = []
    failed: dict[str, str] = {}
    changed = 0
    aborted = False
    try:
        for rid, payload in run_crawl(source, list(by_id), min_interval=rate):
            if payload is None:
                failed[rid] = "fetch"
                continue
            try:
                snap = parse_menu(payload)
            except (KeyError, TypeError, ValueError) as e:
                failed[rid] = f"parse: {e}"
                continue
            h = snap.price_hash()
            if hashes.get(rid) != h:
                storage.put(f"raw/{today.isoformat()}/{rid}.json.gz", gzip.compress(dumps(payload)), "application/gzip")
                hashes[rid] = h
                changed += 1
            rows, resolved = compute_store(snap, version, rid, today)
            stats.record(resolved)
            rows_by_store[rid] = rows
            all_rows.extend(rows)
    except AbortCrawl as e:
        log.error("crawl aborted: %s", e)
        aborted = True

    alerts = stats.alerts()
    if aborted:
        alerts.insert(0, "crawl aborted: error rate above 10 %")
    if pin_ids and stats.pins:
        n = pin_product_ids(CATALOGUE_PATH, version.version, stats.pins)
        log.info("pinned product IDs on %d catalogue items", n)

    # Tier A: today's partition (overwrites a same-day re-run)
    hs = hist.History(storage, out if out else Path(os.environ.get("MCDOCPP_WORK_DIR", ".cache/history")))
    if all_rows:
        hs.write_table(
            hs.daily_path("reward_price_daily", today), hist.reward_rows_to_table(all_rows), hist.REWARD_PRICE_SCHEMA
        )
    daily_files = hs.daily_files("reward_price_daily", today - timedelta(days=hist.WINDOW_DAYS - 1), today)

    # Tier B
    agg_daily, best_daily = hist.daily_aggregates(daily_files, stores, today)
    hs.write_table(hs.daily_path("cpp_aggregate_daily", today), agg_daily)
    hs.write_table(hs.daily_path("best_cpp_daily", today), best_daily)
    window = hist.window_aggregates(daily_files, stores, today)
    agg_hist = hist.read_rows(
        hs.daily_files("cpp_aggregate_daily", today - timedelta(days=hist.WINDOW_DAYS - 1), today)
    )

    # Tier B′: current month, then every month on record for the charts
    month_start = today.replace(day=1)
    agg_m, best_m = hist.monthly_rollups(
        hs.daily_files("cpp_aggregate_daily", month_start, today), hs.daily_files("best_cpp_daily", month_start, today)
    )
    hs.write_table(hs.monthly_path("cpp_aggregate_monthly", today), agg_m)
    hs.write_table(hs.monthly_path("best_cpp_monthly", today), best_m)
    monthly = hist.read_rows([str(hs.local(k) or "") for k in storage.list("history/cpp_aggregate_monthly/")])
    monthly_best = hist.read_rows([str(hs.local(k) or "") for k in storage.list("history/best_cpp_monthly/")])

    # Publish
    pub = Publisher(now, catalogue, version)
    scopes = sorted({a["scope"] for a in agg_daily} | {"national"})
    for s in stores:
        if s.id in rows_by_store:
            _put_json(storage, f"stores/{s.id}.json", pub.store(s, rows_by_store[s.id], agg_daily))
    _put_json(storage, "stores/index.json", pub.stores_index(stores, rows_by_store))
    for scope in scopes:
        _put_json(
            storage, f"aggregates/{scope_path(scope)}/7d.json", pub.aggregate(scope, window, agg_hist, hist.WINDOW_DAYS)
        )
        _put_json(storage, f"history/{scope_path(scope)}/best.json", pub.history_best(scope, monthly_best))
        for item in version.items:
            _put_json(
                storage, f"history/{scope_path(scope)}/{item.key}.json", pub.history_item(scope, item.key, monthly)
            )
    for item in version.items:
        _put_json(storage, f"items/{item.key}/nearby.json", pub.nearby(item.key, stores, rows_by_store))
    crawl_info = {
        "ok": len(rows_by_store),
        "failed": len(failed),
        "changed": changed,
        "aborted": aborted,
        "duration_s": round(time.monotonic() - t0, 1),
    }
    _put_json(storage, "meta.json", pub.meta(stores, len(rows_by_store), crawl_info, alerts))
    storage.put("state/hashes.json", dumps(hashes), "application/json")
    storage.put("state/stores.json", dump_stores(stores), "application/json")
    _prune_raw(storage, today)
    log.info("done: %s", crawl_info)
    for a in alerts:
        log.warning("ALERT %s", a)
    if aborted or (failed and len(failed) / len(stores) > 0.10):
        raise typer.Exit(code=2)


@app.command()
def synth(
    out: Annotated[Path, typer.Option()] = REPO / "fixtures" / "synthetic",
    n: Annotated[int, typer.Option()] = 40,
    seed: Annotated[int, typer.Option()] = 42,
    sample: Annotated[bool, typer.Option(help="Also refresh fixtures/menu_sample.json")] = False,
) -> None:
    stores: list[Store] = generate(REPO / "fixtures" / "products.json", out, n, seed)
    typer.echo(f"{len(stores)} synthetic stores in {out}")
    if sample:
        from .synth import build_menu

        table = json.loads((REPO / "fixtures" / "products.json").read_text(encoding="utf-8"))
        (REPO / "fixtures" / "menu_sample.json").write_text(
            json.dumps(build_menu(table, duplicate_id_price_conflict=True), indent=1, ensure_ascii=False),
            encoding="utf-8",
        )


@app.command()
def discover(out: Annotated[Path | None, typer.Option()] = None) -> None:
    """Sweep /exp/v1/restaurant/location over Canada and write state/stores.json (needs MCD_* env)."""
    logging.basicConfig(level=logging.INFO)
    storage = _storage(out)
    tokens = TokenManager.from_env(persist=lambda t: storage.put("secrets/refresh_token", t.encode(), "text/plain"))
    with httpx.Client(timeout=30) as client:
        stores = run_discover(tokens, client)
    storage.put("state/stores.json", dump_stores(stores), "application/json")
    typer.echo(f"{len(stores)} stores")


if __name__ == "__main__":
    app()
