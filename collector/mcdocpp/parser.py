"""GMA menu payload → priced products for the GMA_PICKUP channel."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

CHANNEL = "GMA_PICKUP"


@dataclass(frozen=True)
class Product:
    id: int
    price_cents: int
    name_en: str
    name_fr: str


@dataclass
class MenuSnapshot:
    products: dict[int, Product]
    # IDs that appeared at more than one price; the max is kept in products.
    price_conflicts: dict[int, set[int]] = field(default_factory=dict)

    def price_hash(self) -> str:
        h = hashlib.sha256()
        for pid in sorted(self.products):
            h.update(f"{pid}:{self.products[pid].price_cents};".encode())
        return h.hexdigest()


def walk_items(node: Any) -> Iterator[dict[str, Any]]:
    """Yield every standalone priced item; QUANTITY add-ons are skipped (their price lives in options[][0])."""
    if isinstance(node, dict):
        if node.get("type") == "QUANTITY":
            return
        if "ID" in node and "price" in node:
            yield node
            return
        for v in node.values():
            yield from walk_items(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_items(v)


def _names(payload: dict[str, Any], lang: str) -> dict[int, str]:
    loc = payload["channelMenus"]["localizations"].get(lang)
    if not loc:
        return {}
    strings = loc["strings"]
    out: dict[int, str] = {}
    for pid, entry in loc["lookup"].items():
        idx = entry[2]
        if 0 <= idx < len(strings):
            out[int(pid)] = str(strings[idx]).strip()
    return out


def parse_menu(payload: dict[str, Any], channel: str = CHANNEL) -> MenuSnapshot:
    channels = payload["channelMenus"]["channels"]
    if channel not in channels:
        raise KeyError(f"channel {channel!r} missing; have {sorted(channels)}")
    en, fr = _names(payload, "en-CA"), _names(payload, "fr-CA")
    prices: dict[int, set[int]] = {}
    for it in walk_items(channels[channel]):
        prices.setdefault(int(it["ID"]), set()).add(int(it["price"]))
    products = {pid: Product(pid, max(ps), en.get(pid, ""), fr.get(pid, "")) for pid, ps in prices.items()}
    return MenuSnapshot(products, {pid: ps for pid, ps in prices.items() if len(ps) > 1})
