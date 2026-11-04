from datetime import date

from mcdocpp.catalogue import CatalogueVersion
from mcdocpp.cpp import best, compute_cpp, compute_store
from mcdocpp.parser import MenuSnapshot


def req[T](x: T | None) -> T:
    assert x is not None
    return x


DAY = date(2026, 11, 3)


def test_cpp_definition() -> None:
    assert compute_cpp(479, 2000) == 0.2395
    assert compute_cpp(249, 2000) == 0.1245


def test_compute_store_rows(version: CatalogueVersion, snapshot: MenuSnapshot) -> None:
    rows, resolved = compute_store(snapshot, version, "10001", DAY)
    by_key = {r.item_key: r for r in rows}
    assert len(rows) == len(version.items)
    hb = by_key["hash_brown"]
    assert hb.breakfast and hb.available and hb.cpp == compute_cpp(req(hb.price_cents), 2000)
    assert not by_key["big_mac"].breakfast
    assert req(resolved["big_mac"]).id == 1090


def test_unavailable_item_is_null_and_excluded(version: CatalogueVersion, snapshot: MenuSnapshot) -> None:
    snap = MenuSnapshot({pid: p for pid, p in snapshot.products.items() if pid != 1070})
    rows, _ = compute_store(snap, version, "x", DAY)
    wrap = next(r for r in rows if r.item_key == "snack_wrap")
    assert wrap.cpp is None and wrap.price_cents is None and not wrap.available
    assert all(r.item_key != "snack_wrap" for r in rows if r.cpp is not None)


def test_best_respects_balance_and_breakfast(version: CatalogueVersion, snapshot: MenuSnapshot) -> None:
    rows, _ = compute_store(snapshot, version, "x", DAY)
    overall = best(rows)
    assert overall is not None and overall.cpp == max(r.cpp for r in rows if r.cpp is not None)
    assert req(best(rows, max_tier=2000)).tier == 2000
    assert not req(best(rows, all_day_only=True, max_tier=2000)).breakfast
    assert best([]) is None
