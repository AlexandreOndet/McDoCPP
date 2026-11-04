"""Parquet history (tiers A, B, B′) and DuckDB aggregates (design §5, §7)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .cpp import RewardPrice
from .storage import Storage
from .stores import Store

FRESH_DAYS = 2  # ≤ 48 h: today and yesterday at daily grain
WINDOW_DAYS = 7
SCOPE_SQL = "unnest(['national', 'province:' || s.province])"


class History:
    """Parquet files mirrored between a local work dir and the storage backend."""

    def __init__(self, storage: Storage, work_dir: Path) -> None:
        self.storage = storage
        self.work_dir = work_dir

    def local(self, path: str) -> Path | None:
        p = self.work_dir / path
        if p.is_file():
            return p
        data = self.storage.get(path)
        if data is None:
            return None
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def write_table(self, path: str, rows: list[dict[str, Any]], schema: pa.Schema | None = None) -> Path:
        p = self.work_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pylist(rows, schema=schema) if rows else pa.table({}, schema=schema)
        pq.write_table(table, p, compression="zstd")
        self.storage.put(path, p.read_bytes(), "application/vnd.apache.parquet")
        return p

    @staticmethod
    def daily_path(table: str, day: date) -> str:
        return f"history/{table}/year={day:%Y}/month={day:%m}/{day.isoformat()}.parquet"

    @staticmethod
    def monthly_path(table: str, day: date) -> str:
        return f"history/{table}/year={day:%Y}/{day:%Y-%m}.parquet"

    def daily_files(self, table: str, start: date, end: date) -> list[str]:
        out: list[str] = []
        d = start
        while d <= end:
            p = self.local(self.daily_path(table, d))
            if p:
                out.append(str(p))
            d += timedelta(days=1)
        return out


_FIELDS: list[pa.Field[Any]] = [
    pa.field("date", pa.date32()),
    pa.field("restaurant_id", pa.string()),
    pa.field("item_key", pa.string()),
    pa.field("tier", pa.int32()),
    pa.field("product_id", pa.int64()),
    pa.field("price_cents", pa.int32()),
    pa.field("cpp", pa.float64()),
    pa.field("available", pa.bool_()),
    pa.field("breakfast", pa.bool_()),
]
REWARD_PRICE_SCHEMA = pa.schema(_FIELDS)


def reward_rows_to_table(rows: list[RewardPrice]) -> list[dict[str, Any]]:
    return [
        {
            "date": r.date,
            "restaurant_id": r.restaurant_id,
            "item_key": r.item_key,
            "tier": r.tier,
            "product_id": r.product_id,
            "price_cents": r.price_cents,
            "cpp": r.cpp,
            "available": r.available,
            "breakfast": r.breakfast,
        }
        for r in rows
    ]


def _connect(stores: list[Store]) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.register("stores", pa.Table.from_pylist([{"id": s.id, "province": s.province} for s in stores]))
    return con


def _rows(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description or []]
    return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]


def _files_sql(files: list[str]) -> str:
    return "read_parquet([" + ", ".join(f"'{f}'" for f in files) + "])"


def daily_aggregates(
    files: list[str], stores: list[Store], day: date
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """cpp_aggregate_daily and best_cpp_daily for `day` over stores with a snapshot ≤ 48 h old."""
    if not files:
        return [], []
    con = _connect(stores)
    fresh_from = day - timedelta(days=FRESH_DAYS - 1)
    con.execute(
        f"""
        CREATE TEMP TABLE latest AS
        SELECT r.*, s.province FROM {_files_sql(files)} r JOIN stores s ON s.id = r.restaurant_id
        WHERE r.date BETWEEN ? AND ? AND r.cpp IS NOT NULL
        QUALIFY row_number() OVER (PARTITION BY r.restaurant_id, r.item_key ORDER BY r.date DESC) = 1
        """,
        [fresh_from, day],
    )
    con.execute(
        """
        CREATE TEMP TABLE scoped AS
        SELECT l.*, scope, cpp = max(cpp) OVER (PARTITION BY restaurant_id) AS is_best
        FROM latest l, unnest(['national', 'province:' || province]) AS u(scope)
        """
    )
    agg = _rows(
        con,
        """
        SELECT ?::DATE AS date, scope, item_key, count(*)::INT AS n_stores,
               round(median(cpp), 4) AS median_cpp, round(avg(cpp), 4) AS mean_cpp,
               round(quantile_cont(cpp, 0.1), 4) AS p10, round(quantile_cont(cpp, 0.9), 4) AS p90,
               round(avg(CASE WHEN is_best THEN 1 ELSE 0 END), 4) AS share_best
        FROM scoped GROUP BY scope, item_key ORDER BY scope, item_key
        """,
        [day],
    )
    best = _rows(
        con,
        """
        WITH sb AS (SELECT scope, restaurant_id, max(cpp) AS best_cpp, arg_max(item_key, cpp) AS best_item
                    FROM scoped GROUP BY scope, restaurant_id)
        SELECT ?::DATE AS date, scope, count(*)::INT AS n_stores, round(median(best_cpp), 4) AS median_best_cpp,
               round(avg(best_cpp), 4) AS mean_best_cpp, mode(best_item) AS best_item_mode
        FROM sb GROUP BY scope ORDER BY scope
        """,
        [day],
    )
    return agg, best


def window_aggregates(
    files: list[str], stores: list[Store], day: date, days: int = WINDOW_DAYS
) -> list[dict[str, Any]]:
    """Rolling window over all store-days: median/mean/p10/p90/spread per scope × item (U4)."""
    if not files:
        return []
    con = _connect(stores)
    return _rows(
        con,
        f"""
        WITH r AS (SELECT r.*, s.province FROM {_files_sql(files)} r JOIN stores s ON s.id = r.restaurant_id
                   WHERE r.date BETWEEN ? AND ? AND r.cpp IS NOT NULL),
             scoped AS (SELECT r.*, scope FROM r, unnest(['national', 'province:' || province]) AS u(scope))
        SELECT scope, item_key, count(DISTINCT restaurant_id)::INT AS n_stores, count(*)::INT AS n_obs,
               round(median(cpp), 4) AS median_cpp, round(avg(cpp), 4) AS mean_cpp,
               round(quantile_cont(cpp, 0.1), 4) AS p10, round(quantile_cont(cpp, 0.9), 4) AS p90,
               round(quantile_cont(cpp, 0.9) - quantile_cont(cpp, 0.1), 4) AS spread
        FROM scoped GROUP BY scope, item_key ORDER BY scope, item_key
        """,
        [day - timedelta(days=days - 1), day],
    )


def monthly_rollups(agg_files: list[str], best_files: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    con = duckdb.connect()
    agg = (
        _rows(
            con,
            f"""
            SELECT strftime(date_trunc('month', date), '%Y-%m') AS month, scope, item_key,
                   round(median(median_cpp), 4) AS median_cpp, round(avg(mean_cpp), 4) AS mean_cpp,
                   round(median(p10), 4) AS p10, round(median(p90), 4) AS p90,
                   round(avg(n_stores))::INT AS n_stores, round(avg(share_best), 4) AS share_best,
                   count(*)::INT AS n_days
            FROM {_files_sql(agg_files)} GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
            """,
        )
        if agg_files
        else []
    )
    best = (
        _rows(
            con,
            f"""
            SELECT strftime(date_trunc('month', date), '%Y-%m') AS month, scope,
                   round(median(median_best_cpp), 4) AS median_best_cpp, round(avg(mean_best_cpp), 4) AS mean_best_cpp,
                   mode(best_item_mode) AS best_item_mode, count(*)::INT AS n_days
            FROM {_files_sql(best_files)} GROUP BY 1, 2 ORDER BY 1, 2
            """,
        )
        if best_files
        else []
    )
    return agg, best


def read_rows(files: list[str], where: str = "1=1") -> list[dict[str, Any]]:
    if not files:
        return []
    return _rows(duckdb.connect(), f"SELECT * FROM {_files_sql(files)} WHERE {where}")
