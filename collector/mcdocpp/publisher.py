"""Derived JSON for the static site (design §8). Every file carries as_of."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema

from .catalogue import Catalogue, CatalogueVersion
from .cpp import RewardPrice, best
from .stores import Store

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


def scope_path(scope: str) -> str:
    return scope.removeprefix("province:")


def value_per_1k(cpp: float) -> float:
    return round(cpp * 10, 2)


def quantiles(values: list[float], k: int = 5) -> list[float]:
    """k-1 cut points splitting values into k equal bins."""
    if not values:
        return []
    v = sorted(values)
    return [round(v[min(len(v) - 1, int(len(v) * i / k))], 4) for i in range(1, k)]


class Publisher:
    def __init__(self, as_of: datetime, catalogue: Catalogue, version: CatalogueVersion) -> None:
        self.as_of = as_of.isoformat(timespec="seconds")
        self.catalogue = catalogue
        self.version = version
        self.items = version.by_key()

    def _item_meta(self, key: str) -> dict[str, Any]:
        it = self.items[key]
        return {"key": key, "tier": it.tier, "names": it.names, "kind": it.kind, "breakfast": it.breakfast}

    def meta(self, stores: list[Store], fresh: int, crawl: dict[str, Any], alerts: list[str]) -> dict[str, Any]:
        return {
            "as_of": self.as_of,
            "catalogue_version": self.version.version,
            "store_count": len(stores),
            "stores_fresh": fresh,
            "crawl": crawl,
            "alerts": alerts,
            "tiers": sorted({i.tier for i in self.version.items}),
        }

    def stores_index(self, stores: list[Store], rows_by_store: dict[str, list[RewardPrice]]) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        for s in stores:
            b = best(rows_by_store.get(s.id, []))
            entries.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "address": s.address,
                    "city": s.city,
                    "province": s.province,
                    "postal": s.postal,
                    "lat": s.lat,
                    "lon": s.lon,
                    "best_cpp": b.cpp if b else None,
                    "best_item_key": b.item_key if b else None,
                    "as_of": self.as_of if s.id in rows_by_store else None,
                }
            )
        return {
            "as_of": self.as_of,
            "stores": entries,
            "best_cpp_quantiles": quantiles([e["best_cpp"] for e in entries if e["best_cpp"] is not None]),
        }

    def store(self, s: Store, rows: list[RewardPrice], agg_daily: list[dict[str, Any]]) -> dict[str, Any]:
        med = {(a["scope"], a["item_key"]): a["median_cpp"] for a in agg_daily}
        items = []
        for r in rows:
            nat = med.get(("national", r.item_key))
            prov = med.get((f"province:{s.province}", r.item_key))
            items.append(
                {
                    **self._item_meta(r.item_key),
                    "product_id": r.product_id,
                    "price_cents": r.price_cents,
                    "cpp": r.cpp,
                    "value_per_1k": value_per_1k(r.cpp) if r.cpp is not None else None,
                    "available": r.available,
                    "national_median_cpp": nat,
                    "province_median_cpp": prov,
                    "delta_vs_national": round(r.cpp / nat - 1, 4) if r.cpp is not None and nat else None,
                    "delta_vs_province": round(r.cpp / prov - 1, 4) if r.cpp is not None and prov else None,
                }
            )
        items.sort(key=lambda i: (i["cpp"] is None, -(i["cpp"] or 0)))
        b = best(rows)
        by_tier: dict[str, str | None] = {}
        for t in sorted({r.tier for r in rows}):
            tb = best([r for r in rows if r.tier == t])
            by_tier[str(t)] = tb.item_key if tb else None
        return {
            "as_of": self.as_of,
            "catalogue_version": self.version.version,
            "store": s.model_dump(),
            "items": items,
            "best_item_key": b.item_key if b else None,
            "best_by_tier": by_tier,
        }

    def aggregate(
        self, scope: str, window: list[dict[str, Any]], daily_history: list[dict[str, Any]], days: int
    ) -> dict[str, Any]:
        spark: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for d in daily_history:
            if d["scope"] == scope:
                spark[d["item_key"]].append({"date": d["date"].isoformat(), "median_cpp": d["median_cpp"]})
        items = [
            {
                **self._item_meta(w["item_key"]),
                "n_stores": w["n_stores"],
                "median_cpp": w["median_cpp"],
                "mean_cpp": w["mean_cpp"],
                "p10": w["p10"],
                "p90": w["p90"],
                "spread": w["spread"],
                "value_per_1k": value_per_1k(w["median_cpp"]),
                "daily_median": sorted(spark[w["item_key"]], key=lambda x: x["date"]),
            }
            for w in window
            if w["scope"] == scope and w["item_key"] in self.items
        ]
        items.sort(key=lambda i: -i["median_cpp"])
        return {"as_of": self.as_of, "scope": scope, "window_days": days, "items": items}

    def nearby(self, key: str, stores: list[Store], rows_by_store: dict[str, list[RewardPrice]]) -> dict[str, Any]:
        pts = []
        for s in stores:
            r = next((x for x in rows_by_store.get(s.id, []) if x.item_key == key), None)
            if r and r.cpp is not None:
                pts.append({"id": s.id, "lat": s.lat, "lon": s.lon, "cpp": r.cpp, "price_cents": r.price_cents})
        return {"as_of": self.as_of, "item": self._item_meta(key), "stores": pts}

    def history_item(self, scope: str, key: str, monthly: list[dict[str, Any]]) -> dict[str, Any]:
        series = [
            {k: v for k, v in m.items() if k not in ("scope", "item_key")}
            for m in monthly
            if m["scope"] == scope and m["item_key"] == key
        ]
        return {
            "as_of": self.as_of,
            "scope": scope,
            "item": self._item_meta(key),
            "series": series,
            "catalogue_changes": self.catalogue.boundaries(),
        }

    def history_best(self, scope: str, monthly_best: list[dict[str, Any]]) -> dict[str, Any]:
        series = [{k: v for k, v in m.items() if k != "scope"} for m in monthly_best if m["scope"] == scope]
        return {"as_of": self.as_of, "scope": scope, "series": series, "catalogue_changes": self.catalogue.boundaries()}


_SCHEMA_FOR_PATH = (
    ("meta.json", "meta"),
    ("stores/index.json", "stores-index"),
    ("stores/", "store"),
    ("aggregates/", "aggregate"),
    ("items/", "nearby"),
    ("history/", "history"),
)


def schema_for(path: str) -> str:
    if path.endswith("/best.json"):
        return "history-best"
    for prefix, name in _SCHEMA_FOR_PATH:
        if path.startswith(prefix):
            return name
    raise KeyError(path)


_cache: dict[str, jsonschema.Draft202012Validator] = {}


def validate(path: str, doc: dict[str, Any]) -> None:
    name = schema_for(path)
    if name not in _cache:
        _cache[name] = jsonschema.Draft202012Validator(json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text()))
    _cache[name].validate(doc)


def dumps(doc: dict[str, Any]) -> bytes:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode()
