"""Restaurant records and discovery sweep."""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Iterator
from typing import Any

import httpx
from pydantic import BaseModel

from .auth import TokenManager

log = logging.getLogger(__name__)

PROVINCES = ("AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT")


class Store(BaseModel):
    id: str
    nsn: str | None = None
    name: str
    address: str
    city: str
    province: str
    postal: str | None = None
    lat: float
    lon: float


def load_stores(data: bytes) -> list[Store]:
    return [Store.model_validate(s) for s in json.loads(data)]


def dump_stores(stores: list[Store]) -> bytes:
    return json.dumps([s.model_dump() for s in stores], ensure_ascii=False, indent=1).encode()


def grid(
    lat0: float = 42.0, lat1: float = 62.0, lon0: float = -141.0, lon1: float = -52.0, step_km: float = 40.0
) -> Iterator[tuple[float, float]]:
    """Lat/lon grid over populated Canada; 40 km steps with a 30 km radius overlap."""
    dlat = step_km / 111.0
    lat = lat0
    while lat <= lat1:
        dlon = step_km / (111.0 * math.cos(math.radians(lat)))
        lon = lon0
        while lon <= lon1:
            yield round(lat, 4), round(lon, 4)
            lon += dlon
        lat += dlat


def parse_location_response(body: dict[str, Any]) -> list[Store]:
    """Shape per exp/v1/restaurant/location (DE market lib); field names to confirm against a CA capture."""
    out: list[Store] = []
    for r in body.get("response", {}).get("restaurants", []):
        addr = r.get("address", {})
        try:
            out.append(
                Store(
                    id=str(r.get("nationalStoreNumber") or r["id"]),
                    nsn=str(r.get("nationalStoreNumber")) if r.get("nationalStoreNumber") else None,
                    name=r.get("name") or addr.get("addressLine1", ""),
                    address=addr.get("addressLine1", ""),
                    city=addr.get("cityTown", ""),
                    province=addr.get("subdivision", "")[-2:].upper(),
                    postal=addr.get("postalZip"),
                    lat=float(r["location"]["latitude"]),
                    lon=float(r["location"]["longitude"]),
                )
            )
        except (KeyError, TypeError, ValueError) as e:
            log.warning("skipping restaurant record: %s", e)
    return out


def discover(tokens: TokenManager, client: httpx.Client, radius_km: float = 30.0) -> list[Store]:
    if tokens.access_token is None:
        tokens.refresh(client)
    found: dict[str, Store] = {}
    for lat, lon in grid():
        r = client.get(
            f"{tokens.base_url}/exp/v1/restaurant/location",
            params={"distance": radius_km, "latitude": lat, "longitude": lon, "pageSize": 100, "filter": "summary"},
            headers=tokens.headers(),
        )
        if r.status_code == 401:
            tokens.refresh(client)
            continue
        r.raise_for_status()
        for s in parse_location_response(r.json()):
            found[s.id] = s
    return sorted(found.values(), key=lambda s: s.id)
