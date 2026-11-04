from datetime import date, timedelta
from pathlib import Path

from mcdocpp.cpp import RewardPrice
from mcdocpp.history import (
    REWARD_PRICE_SCHEMA,
    History,
    daily_aggregates,
    monthly_rollups,
    reward_rows_to_table,
    window_aggregates,
)
from mcdocpp.storage import LocalFS
from mcdocpp.stores import Store

DAY = date(2026, 11, 3)


def store(i: int, prov: str) -> Store:
    return Store(id=str(i), name=f"s{i}", address="", city="", province=prov, lat=0.0, lon=0.0)


def row(sid: str, key: str, cpp: float, day: date = DAY, tier: int = 2000) -> RewardPrice:
    return RewardPrice(day, sid, key, tier, 1, int(cpp * tier), cpp, True, False)


def write(tmp_path: Path, day: date, rows: list[RewardPrice]) -> History:
    h = History(LocalFS(tmp_path), tmp_path)
    h.write_table(h.daily_path("reward_price_daily", day), reward_rows_to_table(rows), REWARD_PRICE_SCHEMA)
    return h


def test_median_p10_p90_spread_and_scopes(tmp_path: Path) -> None:
    stores = [store(i, "QC" if i < 5 else "ON") for i in range(10)]
    cpps = [0.10, 0.11, 0.12, 0.13, 0.14, 0.20, 0.21, 0.22, 0.23, 0.24]
    rows = [row(str(i), "a", c) for i, c in enumerate(cpps)] + [row(str(i), "b", 0.05) for i in range(10)]
    h = write(tmp_path, DAY, rows)
    files = h.daily_files("reward_price_daily", DAY, DAY)
    agg, best = daily_aggregates(files, stores, DAY)
    nat = {a["item_key"]: a for a in agg if a["scope"] == "national"}
    assert nat["a"]["n_stores"] == 10
    assert nat["a"]["median_cpp"] == 0.17
    assert nat["a"]["p10"] == 0.109 and nat["a"]["p90"] == 0.231
    assert nat["a"]["share_best"] == 1.0 and nat["b"]["share_best"] == 0.0
    qc = {a["item_key"]: a for a in agg if a["scope"] == "province:QC"}
    assert qc["a"]["median_cpp"] == 0.12
    nb = next(b for b in best if b["scope"] == "national")
    assert nb["median_best_cpp"] == 0.17 and nb["best_item_mode"] == "a"
    win = {w["item_key"]: w for w in window_aggregates(files, stores, DAY) if w["scope"] == "national"}
    assert win["a"]["spread"] == round(0.231 - 0.109, 4)


def test_freshness_filter_drops_snapshots_older_than_48h(tmp_path: Path) -> None:
    stores = [store(1, "QC"), store(2, "QC"), store(3, "QC")]
    h = write(tmp_path, DAY - timedelta(days=3), [row("1", "a", 0.90, DAY - timedelta(days=3))])
    write(tmp_path, DAY - timedelta(days=1), [row("2", "a", 0.10, DAY - timedelta(days=1))])
    write(tmp_path, DAY, [row("3", "a", 0.20)])
    files = h.daily_files("reward_price_daily", DAY - timedelta(days=6), DAY)
    agg, _ = daily_aggregates(files, stores, DAY)
    nat = next(a for a in agg if a["scope"] == "national")
    assert nat["n_stores"] == 2 and nat["median_cpp"] == 0.15


def test_latest_snapshot_per_store_wins(tmp_path: Path) -> None:
    stores = [store(1, "QC")]
    h = write(tmp_path, DAY - timedelta(days=1), [row("1", "a", 0.10, DAY - timedelta(days=1))])
    write(tmp_path, DAY, [row("1", "a", 0.30)])
    agg, _ = daily_aggregates(h.daily_files("reward_price_daily", DAY - timedelta(days=1), DAY), stores, DAY)
    assert next(a for a in agg if a["scope"] == "national")["median_cpp"] == 0.30


def test_monthly_rollup(tmp_path: Path) -> None:
    stores = [store(1, "QC"), store(2, "ON")]
    h = History(LocalFS(tmp_path), tmp_path)
    for d, c in ((DAY - timedelta(days=1), 0.10), (DAY, 0.20)):
        write(tmp_path, d, [row("1", "a", c, d), row("2", "a", c + 0.02, d)])
        agg, best = daily_aggregates(h.daily_files("reward_price_daily", d, d), stores, d)
        h.write_table(h.daily_path("cpp_aggregate_daily", d), agg)
        h.write_table(h.daily_path("best_cpp_daily", d), best)
    m, mb = monthly_rollups(
        h.daily_files("cpp_aggregate_daily", DAY - timedelta(days=1), DAY),
        h.daily_files("best_cpp_daily", DAY - timedelta(days=1), DAY),
    )
    nat = next(x for x in m if x["scope"] == "national")
    assert nat["month"] == "2026-11" and nat["n_days"] == 2 and nat["median_cpp"] == 0.16
    assert next(x for x in mb if x["scope"] == "national")["best_item_mode"] == "a"
