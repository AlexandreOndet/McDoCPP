"""Menu sources (HTTP or fixtures) and the rate-limited crawl loop."""

from __future__ import annotations

import gzip
import json
import logging
import random
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import httpx

from .auth import TokenManager

log = logging.getLogger(__name__)


class MenuSource(Protocol):
    def fetch(self, restaurant_id: str) -> dict[str, Any]: ...


class FixtureSource:
    """Reads fixtures/<dir>/<id>.json or .json.gz."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def fetch(self, restaurant_id: str) -> dict[str, Any]:
        p = self.directory / f"{restaurant_id}.json"
        if p.exists():
            return dict(json.loads(p.read_text(encoding="utf-8")))
        gz = self.directory / f"{restaurant_id}.json.gz"
        return dict(json.loads(gzip.decompress(gz.read_bytes())))


class RetryableError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status


class HttpSource:
    def __init__(self, tokens: TokenManager, client: httpx.Client) -> None:
        self.tokens = tokens
        self.client = client
        if tokens.access_token is None:
            tokens.refresh(client)

    def fetch(self, restaurant_id: str) -> dict[str, Any]:
        url = f"{self.tokens.base_url}/ca/gma/api/v1/restaurants/{restaurant_id}/menus"
        r = self.client.get(url, headers=self.tokens.headers())
        if r.status_code == 401:
            self.tokens.refresh(self.client)
            r = self.client.get(url, headers=self.tokens.headers())
        if r.status_code in (401, 403, 429) or r.status_code >= 500:
            raise RetryableError(r.status_code)
        r.raise_for_status()
        return dict(r.json())


@dataclass
class CrawlResult:
    ok: dict[str, dict[str, Any]] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)
    aborted: bool = False


class AbortCrawl(RuntimeError):
    pass


def crawl(
    source: MenuSource,
    restaurant_ids: list[str],
    *,
    min_interval: float = 1.0,
    jitter: float = 0.5,
    max_error_share: float = 0.10,
    min_requests_before_abort: int = 20,
    retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> Iterator[tuple[str, dict[str, Any] | None]]:
    """Yield (id, payload|None) in randomized order at ≤1 req/s (jittered). Raises AbortCrawl past the error budget."""
    rng = rng or random.Random()
    order = list(restaurant_ids)
    rng.shuffle(order)
    errors = 0
    for n, rid in enumerate(order, 1):
        payload: dict[str, Any] | None = None
        backoff = 2.0
        for attempt in range(retries + 1):
            try:
                payload = source.fetch(rid)
                break
            except RetryableError as e:
                log.warning("store %s: %s (attempt %d)", rid, e, attempt + 1)
                if attempt == retries:
                    break
                sleep(backoff + rng.uniform(0, backoff))
                backoff = min(backoff * 2, 60)
            except (httpx.HTTPError, KeyError, ValueError, OSError) as e:
                log.warning("store %s: %s", rid, e)
                break
        if payload is None:
            errors += 1
        yield rid, payload
        if n >= min_requests_before_abort and errors / n > max_error_share:
            raise AbortCrawl(f"{errors}/{n} failures: likely auth or schema change")
        if min_interval > 0:
            sleep(min_interval + rng.uniform(0, jitter))
