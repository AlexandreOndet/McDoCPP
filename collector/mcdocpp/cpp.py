"""CPP per reward item for one store snapshot (design §5)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from .catalogue import CatalogueVersion
from .parser import MenuSnapshot, Product


@dataclass(frozen=True)
class RewardPrice:
    date: date
    restaurant_id: str
    item_key: str
    tier: int
    product_id: int | None
    price_cents: int | None
    cpp: float | None  # price_cents / tier, 4 decimals
    available: bool
    breakfast: bool

    def row(self) -> dict[str, Any]:
        d = asdict(self)
        d["date"] = self.date.isoformat()
        return d


def compute_cpp(price_cents: int, tier: int) -> float:
    return round(price_cents / tier, 4)


def compute_store(
    snapshot: MenuSnapshot, version: CatalogueVersion, restaurant_id: str, day: date
) -> tuple[list[RewardPrice], dict[str, Product | None]]:
    rows: list[RewardPrice] = []
    resolved: dict[str, Product | None] = {}
    for item in version.items:
        p = item.resolve(snapshot)
        resolved[item.key] = p
        rows.append(
            RewardPrice(
                date=day,
                restaurant_id=restaurant_id,
                item_key=item.key,
                tier=item.tier,
                product_id=p.id if p else None,
                price_cents=p.price_cents if p else None,
                cpp=compute_cpp(p.price_cents, item.tier) if p else None,
                available=p is not None,
                breakfast=item.breakfast,
            )
        )
    return rows, resolved


def best(rows: list[RewardPrice], all_day_only: bool = False, max_tier: int | None = None) -> RewardPrice | None:
    cands = [
        r
        for r in rows
        if r.cpp is not None and (not all_day_only or not r.breakfast) and (max_tier is None or r.tier <= max_tier)
    ]
    return max(cands, key=lambda r: r.cpp or 0) if cands else None
