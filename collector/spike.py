#!/usr/bin/env python3
"""Phase 0 spike: refresh token, fetch one store's menu, print reward prices and CPP.

uv run spike.py --store 1234            # live, needs MCD_* env (docs/CAPTURE.md)
uv run spike.py --fixture ../fixtures/menu_sample.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import yaml

BASE = "https://us-prod.api.mcd.com"
HERE = Path(__file__).parent


def headers(access_token: str) -> dict[str, str]:
    h: dict[str, str] = json.loads(os.environ.get("MCD_HEADERS_JSON", "{}"))
    h.update(
        {
            "authorization": f"Bearer {access_token}",
            "mcd-clientid": os.environ["MCD_CLIENT_ID"],
            "mcd-marketid": "CA",
            "mcd-uuid": str(uuid.uuid4()).upper(),
        }
    )
    return h


def refresh(client: httpx.Client) -> tuple[str, str]:
    r = client.post(
        f"{BASE}/exp/v1/customer/login/refresh",
        json={"refreshToken": os.environ["MCD_REFRESH_TOKEN"]},
        headers=headers(""),
    )
    r.raise_for_status()
    body = r.json()["response"]
    return body["accessToken"], body["refreshToken"]


def fetch_menu(client: httpx.Client, access: str, store: str) -> dict[str, Any]:
    r = client.get(f"{BASE}/ca/gma/api/v1/restaurants/{store}/menus", headers=headers(access))
    r.raise_for_status()
    return dict(r.json())


def walk_items(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        if "ID" in node and "price" in node and node.get("type") != "QUANTITY":
            yield node
        else:
            for v in node.values():
                yield from walk_items(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_items(v)


def names(menu: dict[str, Any], lang: str) -> dict[int, str]:
    loc = menu["channelMenus"]["localizations"][lang]
    return {int(pid): loc["strings"][entry[2]].strip() for pid, entry in loc["lookup"].items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store")
    ap.add_argument("--fixture")
    ap.add_argument("--save", help="write raw payload here")
    a = ap.parse_args()

    if a.fixture:
        menu = json.loads(Path(a.fixture).read_text(encoding="utf-8"))
    elif a.store:
        with httpx.Client(timeout=30) as c:
            access, new_refresh = refresh(c)
            print(f"refresh ok; new refresh token ends …{new_refresh[-6:]} (persist it!)", file=sys.stderr)
            menu = fetch_menu(c, access, a.store)
        if a.save:
            Path(a.save).write_text(json.dumps(menu), encoding="utf-8")
    else:
        ap.error("--store or --fixture required")

    prices: dict[int, int] = {}
    for it in walk_items(menu["channelMenus"]["channels"]["GMA_PICKUP"]):
        prices[int(it["ID"])] = max(prices.get(int(it["ID"]), 0), int(it["price"]))
    en, fr = names(menu, "en-CA"), names(menu, "fr-CA")
    print(f"{len(prices)} priced products, {len(en)} en-CA strings\n")

    cat = yaml.safe_load((HERE / "rewards_catalogue.yaml").read_text(encoding="utf-8"))["versions"][0]
    print(f"{'tier':>6} {'item':<42} {'price':>7} {'cpp':>7}  {'$/1k':>6}  fr")
    for tier in cat["tiers"]:
        for item in tier["items"]:
            rx = re.compile(item["product_match"]["name_regex"])
            cands = [(p, pid) for pid, p in prices.items() if pid in en and rx.search(en[pid])]
            if not cands:
                print(f"{tier['tier']:>6} {item['names']['en']:<42} {'n/a':>7}")
                continue
            price, pid = max(cands)
            cpp = price / tier["tier"]
            name = item["names"]["en"]
            print(f"{tier['tier']:>6} {name:<42} {price / 100:>7.2f} {cpp:>7.4f}  {cpp * 10:>6.2f}  {fr.get(pid, '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
