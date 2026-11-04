"""Synthetic GMA payloads and stores for offline runs (make crawl-fixtures)."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .stores import Store, dump_stores

# (city, province, lat, lon); province multiplier applied on top of base prices
CITIES: list[tuple[str, str, float, float]] = [
    ("Montréal", "QC", 45.5017, -73.5673),
    ("Québec", "QC", 46.8139, -71.2080),
    ("Laval", "QC", 45.6066, -73.7124),
    ("Gatineau", "QC", 45.4765, -75.7013),
    ("Sherbrooke", "QC", 45.4042, -71.8929),
    ("Toronto", "ON", 43.6532, -79.3832),
    ("Ottawa", "ON", 45.4215, -75.6972),
    ("Mississauga", "ON", 43.5890, -79.6441),
    ("Hamilton", "ON", 43.2557, -79.8711),
    ("London", "ON", 42.9849, -81.2453),
    ("Kitchener", "ON", 43.4516, -80.4925),
    ("Windsor", "ON", 42.3149, -83.0364),
    ("Vancouver", "BC", 49.2827, -123.1207),
    ("Victoria", "BC", 48.4284, -123.3656),
    ("Surrey", "BC", 49.1913, -122.8490),
    ("Kelowna", "BC", 49.8880, -119.4960),
    ("Calgary", "AB", 51.0447, -114.0719),
    ("Edmonton", "AB", 53.5461, -113.4938),
    ("Red Deer", "AB", 52.2681, -113.8112),
    ("Winnipeg", "MB", 49.8951, -97.1384),
    ("Brandon", "MB", 49.8485, -99.9501),
    ("Saskatoon", "SK", 52.1332, -106.6700),
    ("Regina", "SK", 50.4452, -104.6189),
    ("Halifax", "NS", 44.6488, -63.5752),
    ("Moncton", "NB", 46.0878, -64.7782),
    ("Fredericton", "NB", 45.9636, -66.6431),
    ("St. John's", "NL", 47.5615, -52.7126),
    ("Charlottetown", "PE", 46.2382, -63.1311),
]
PROVINCE_MULT = {
    "BC": 1.06,
    "AB": 1.02,
    "ON": 1.03,
    "QC": 1.00,
    "MB": 0.97,
    "SK": 0.96,
    "NS": 1.01,
    "NB": 0.98,
    "NL": 1.05,
    "PE": 1.00,
}
STREETS = [
    "Rue Sainte-Catherine O",
    "Boul. René-Lévesque",
    "Yonge St",
    "Queen St W",
    "Main St",
    "King St E",
    "Granville St",
    "Robson St",
    "17 Ave SW",
    "Jasper Ave",
    "Portage Ave",
    "8th St E",
    "Spring Garden Rd",
    "Water St",
    "University Ave",
]
# Reward products a franchisee may not carry
OPTIONAL_IDS = [1070, 1050, 1051, 1060, 1093]


def build_menu(
    table: dict[str, Any],
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
    for p in table["products"]:
        if p["id"] in missing:
            continue
        price = round(p["base_price"] * multiplier * rng.uniform(0.985, 1.015))
        price = price // 10 * 10 + 9  # franchisee prices end in 9
        by_cat.setdefault(p["category"], []).append({"ID": p["id"], "price": price, "type": "PRODUCT"})
        add_string(p["id"], p["en"], p["fr"])
    for a in table["addons"]:
        by_cat.setdefault("Condiments", []).append({"ID": a["id"], "type": "QUANTITY", "options": a["options"]})
        add_string(a["id"], a["en"], a["fr"])
    for i, s in enumerate(table["delivery_strings"]):
        add_string(8000 + i, s, s)

    categories: list[dict[str, Any]] = [
        {"ID": 100 + i, "name": cat, "items": items} for i, (cat, items) in enumerate(by_cat.items())
    ]
    if duplicate_id_price_conflict:
        # Same product ID listed again as a combo component at a token price.
        categories.append(
            {"ID": 199, "name": "Combo components", "items": [{"ID": 1030, "price": 10, "type": "PRODUCT"}]}
        )

    def channel(uplift: float) -> dict[str, Any]:
        return {
            "categories": [
                {
                    **c,
                    "items": [
                        ({**it, "price": int(it["price"] * uplift)} if "price" in it else it) for it in c["items"]
                    ],
                }
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


def generate(products_path: Path, out_dir: Path, n: int = 40, seed: int = 42) -> list[Store]:
    table: dict[str, Any] = json.loads(products_path.read_text(encoding="utf-8"))
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    stores: list[Store] = []
    for i in range(n):
        city, prov, lat, lon = CITIES[i % len(CITIES)]
        sid = str(10001 + i)
        street = rng.choice(STREETS)
        number = rng.randint(100, 4999)
        stores.append(
            Store(
                id=sid,
                nsn=sid,
                name=f"{city} {street}",
                address=f"{number} {street}",
                city=city,
                province=prov,
                postal=None,
                lat=round(lat + rng.uniform(-0.08, 0.08), 5),
                lon=round(lon + rng.uniform(-0.1, 0.1), 5),
            )
        )
        mult = PROVINCE_MULT[prov] * rng.uniform(0.97, 1.05)
        missing = {rng.choice(OPTIONAL_IDS)} if rng.random() < 0.12 else set()
        menu = build_menu(table, mult, rng, missing, duplicate_id_price_conflict=(i % 7 == 0))
        (out_dir / f"{sid}.json").write_text(json.dumps(menu, ensure_ascii=False), encoding="utf-8")
    (out_dir / "stores.json").write_bytes(dump_stores(stores))
    return stores
