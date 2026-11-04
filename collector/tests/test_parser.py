from typing import Any

from mcdocpp.parser import MenuSnapshot, parse_menu


def test_parses_prices_and_both_locales(snapshot: MenuSnapshot) -> None:
    fries = snapshot.products[1030]
    assert fries.name_en == "Med Fries"
    assert fries.name_fr == "Frites Moy"
    assert fries.price_cents > 100


def test_quantity_addons_are_skipped(snapshot: MenuSnapshot) -> None:
    assert 9001 not in snapshot.products
    assert 9002 not in snapshot.products


def test_duplicate_id_keeps_max_and_records_conflict(snapshot: MenuSnapshot) -> None:
    # fixture lists Med Fries again as a 10-cent combo component
    assert snapshot.price_conflicts[1030] == {10, snapshot.products[1030].price_cents}
    assert snapshot.products[1030].price_cents != 10


def test_delivery_marker_strings_do_not_become_products(snapshot: MenuSnapshot) -> None:
    assert not any(p.name_en.startswith("** Delivery") for p in snapshot.products.values())


def test_price_hash_changes_with_price(payload: dict[str, Any]) -> None:
    a = parse_menu(payload).price_hash()
    cat = payload["channelMenus"]["channels"]["GMA_PICKUP"]["categories"][0]
    cat["items"][0]["price"] += 10
    b = parse_menu(payload).price_hash()
    cat["items"][0]["price"] -= 10
    assert a != b
    assert a == parse_menu(payload).price_hash()


def test_missing_channel_raises(payload: dict[str, Any]) -> None:
    import pytest

    with pytest.raises(KeyError):
        parse_menu(payload, channel="KIOSK")
