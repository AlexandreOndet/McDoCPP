"""Rewards catalogue: YAML model, versioning, regex → product ID resolution."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from .parser import MenuSnapshot, Product

TIERS = (2000, 4000, 6000, 10000, 14000)
UNRESOLVED_ALERT_SHARE = 0.05


class ProductMatch(BaseModel):
    name_regex: str
    pick: Literal["max", "min"] = "max"


class RewardItem(BaseModel):
    key: str
    tier: int
    names: dict[str, str]
    kind: str
    availability: Literal["all_day", "breakfast"]
    product_match: ProductMatch
    product_ids: list[int] = Field(default_factory=list)

    @property
    def breakfast(self) -> bool:
        return self.availability == "breakfast"

    def resolve(self, snapshot: MenuSnapshot) -> Product | None:
        """Pinned IDs win; otherwise regex over en-CA names. Several hits → pick max/min price."""
        hits = [snapshot.products[pid] for pid in self.product_ids if pid in snapshot.products]
        if not hits:
            rx = re.compile(self.product_match.name_regex)
            hits = [p for p in snapshot.products.values() if rx.search(p.name_en)]
        if not hits:
            return None
        key = (lambda p: p.price_cents) if self.product_match.pick == "max" else (lambda p: -p.price_cents)
        return max(hits, key=key)


class CatalogueVersion(BaseModel):
    version: str
    valid_from: date
    valid_to: date | None = None
    items: list[RewardItem]

    def covers(self, d: date) -> bool:
        return self.valid_from <= d and (self.valid_to is None or d < self.valid_to)

    def by_key(self) -> dict[str, RewardItem]:
        return {i.key: i for i in self.items}


class Catalogue(BaseModel):
    versions: list[CatalogueVersion]

    def version_for(self, d: date) -> CatalogueVersion:
        for v in self.versions:
            if v.covers(d):
                return v
        raise LookupError(f"no catalogue version covers {d}")

    def boundaries(self) -> list[dict[str, str]]:
        return [{"version": v.version, "valid_from": v.valid_from.isoformat()} for v in self.versions]


def load_catalogue(path: Path) -> Catalogue:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    versions = []
    for v in raw["versions"]:
        items = [RewardItem(tier=t["tier"], **i) for t in v["tiers"] for i in t["items"]]
        versions.append(
            CatalogueVersion(version=v["version"], valid_from=v["valid_from"], valid_to=v["valid_to"], items=items)
        )
    return Catalogue(versions=versions)


def pin_product_ids(path: Path, version: str, pins: dict[str, set[int]]) -> int:
    """Write resolved IDs back into the YAML (append-only). Returns number of items changed."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    changed = 0
    for v in raw["versions"]:
        if v["version"] != version:
            continue
        for t in v["tiers"]:
            for i in t["items"]:
                new = sorted(set(i.get("product_ids") or []) | pins.get(i["key"], set()))
                if new != (i.get("product_ids") or []):
                    i["product_ids"] = new
                    changed += 1
    if changed:
        path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return changed


class ResolutionStats:
    """Counts unresolved items per key across stores; flags keys unresolved at > 5 % of stores."""

    def __init__(self) -> None:
        self.stores = 0
        self.unresolved: Counter[str] = Counter()
        self.pins: dict[str, set[int]] = {}

    def record(self, resolved: dict[str, Product | None]) -> None:
        self.stores += 1
        for key, p in resolved.items():
            if p is None:
                self.unresolved[key] += 1
            else:
                self.pins.setdefault(key, set()).add(p.id)

    def alerts(self, threshold: float = UNRESOLVED_ALERT_SHARE) -> list[str]:
        if not self.stores:
            return []
        return [
            f"{key}: unresolved at {n}/{self.stores} stores ({n / self.stores:.0%})"
            for key, n in sorted(self.unresolved.items())
            if n / self.stores > threshold
        ]
