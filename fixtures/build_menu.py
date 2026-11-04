"""Build a GMA-shaped menu payload from products.json. Shared by the committed sample and the synthetic crawl."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
TABLE = json.loads((HERE / "products.json").read_text(encoding="utf-8"))


def build_menu(
    multiplier: float = 1.0,
    rng: random.Random | None = None,
    missing_ids: set[int] | None = None,
    duplicate_id_price_conflict: bool = False,
) -> dict[str, Any]:
    rng = rng or random.Random(0)
    missing = missing_ids or set()
    strings: list[str] = []
    strings_fr: list[str] = []
    lookup_en: dict[str, list[Any]] = {}
    lookup_fr: dict[str, list[Any]] = {}

    def add_string(pid: int, en: str, fr: str) -> None:
        lookup_en[str(pid)] = [pid, f"SKU{pid}", len(strings)]
        strings.append(en)
        lookup_fr[str(pid)] = [pid, f"SKU{pid}", len(strings_fr)]
        strings_fr.append(fr)

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for p in TABLE["products"]:
        if p["id"] in missing:
            continue
        price = round(p["base_price"] * multiplier * rng.uniform(0.985, 1.015))
        price = int(price) // 10 * 10 + 9  # franchisee prices end in 9
        by_cat.setdefault(p["category"], []).append({"ID": p["id"], "price": price, "type": "PRODUCT"})
        add_string(p["id"], p["en"], p["fr"])
    for a in TABLE["addons"]:
        by_cat.setdefault("Condiments", []).append({"ID": a["id"], "type": "QUANTITY", "options": a["options"]})
        add_string(a["id"], a["en"], a["fr"])
    for i, s in enumerate(TABLE["delivery_strings"]):
        add_string(8000 + i, s, s)

    categories = [{"ID": 100 + i, "name": cat, "items": items} for i, (cat, items) in enumerate(by_cat.items())]
    if duplicate_id_price_conflict:
        # Same product ID listed twice (e.g. as a meal component) at a different price.
        categories.append({"ID": 199, "name": "Combo components", "items": [{"ID": 1030, "price": 10, "type": "PRODUCT"}]})

    def channel(uplift: float) -> dict[str, Any]:
        return {
            "categories": [
                {**c, "items": [({**it, "price": int(it["price"] * uplift)} if "price" in it else it) for it in c["items"]]}
                for c in categories
            ]
        }

    return {
        "channelMenus": {
            "channels": {"GMA_PICKUP": channel(1.0), "EATIN": channel(1.0), "DELIVERY": channel(1.2)},
            "localizations": {
                "en-CA": {"strings": strings, "lookup": lookup_en},
                "fr-CA": {"strings": strings_fr, "lookup": lookup_fr},
            },
        }
    }


if __name__ == "__main__":
    out = HERE / "menu_sample.json"
    out.write_text(json.dumps(build_menu(duplicate_id_price_conflict=True), indent=1, ensure_ascii=False), encoding="utf-8")
    print(out, out.stat().st_size, "bytes")
