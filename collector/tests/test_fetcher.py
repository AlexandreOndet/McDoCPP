import random
from typing import Any

import pytest

from mcdocpp.fetcher import AbortCrawl, RetryableError, crawl


class Flaky:
    def __init__(self, fail: set[str], retry_once: set[str] | None = None) -> None:
        self.fail, self.retry_once, self.calls = fail, set(retry_once or ()), 0

    def fetch(self, rid: str) -> dict[str, Any]:
        self.calls += 1
        if rid in self.fail:
            raise RetryableError(403)
        if rid in self.retry_once:
            self.retry_once.discard(rid)
            raise RetryableError(429)
        return {"id": rid}


def test_randomized_order_and_backoff() -> None:
    ids = [str(i) for i in range(30)]
    sleeps: list[float] = []
    src = Flaky(set(), retry_once={"3"})
    got = [rid for rid, p in crawl(src, ids, sleep=sleeps.append, rng=random.Random(1)) if p]
    assert sorted(got) == sorted(ids) and got != ids
    assert src.calls == 31  # one 429 retry
    assert any(s >= 2.0 for s in sleeps)


def test_abort_past_error_budget() -> None:
    ids = [str(i) for i in range(40)]
    src = Flaky(fail={str(i) for i in range(10)})
    with pytest.raises(AbortCrawl):
        list(crawl(src, ids, sleep=lambda _: None, retries=0, rng=random.Random(2)))
