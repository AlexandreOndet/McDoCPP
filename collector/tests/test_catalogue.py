from pathlib import Path

import yaml

from mcdocpp.catalogue import Catalogue, CatalogueVersion, ResolutionStats, load_catalogue, pin_product_ids
from mcdocpp.parser import MenuSnapshot, Product


def req[T](x: T | None) -> T:
    assert x is not None
    return x


def test_five_tiers_and_unique_keys(version: CatalogueVersion) -> None:
    assert sorted({i.tier for i in version.items}) == [2000, 4000, 6000, 10000, 14000]
    keys = [i.key for i in version.items]
    assert len(keys) == len(set(keys))


def test_regex_resolves_against_fixture(version: CatalogueVersion, snapshot: MenuSnapshot) -> None:
    items = version.by_key()
    assert req(items["big_mac"].resolve(snapshot)).id == 1090
    # "^Big Mac$" must not match the meal
    assert req(items["big_mac_meal"].resolve(snapshot)).id == 1100


def test_pick_max_chooses_most_expensive_variant(version: CatalogueVersion, snapshot: MenuSnapshot) -> None:
    coffee = req(version.by_key()["coffee_sm_md"].resolve(snapshot))
    assert coffee.name_en == "Med Premium Roast Coffee"


def test_pinned_ids_take_precedence_over_regex(version: CatalogueVersion) -> None:
    item = version.by_key()["cheeseburger"].model_copy(update={"product_ids": [555]})
    snap = MenuSnapshot(
        {555: Product(555, 100, "Renamed Cheeseburger Deluxe", ""), 1040: Product(1040, 329, "Cheeseburger", "")}
    )
    assert req(item.resolve(snap)).id == 555


def test_pin_product_ids_writes_yaml(tmp_path: Path, catalogue: Catalogue) -> None:
    src = Path(__file__).resolve().parents[1] / "rewards_catalogue.yaml"
    dst = tmp_path / "cat.yaml"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    changed = pin_product_ids(dst, "2025-09-16", {"big_mac": {1090}, "nope": {1}})
    assert changed == 1
    assert load_catalogue(dst).version_for(catalogue.versions[0].valid_from).by_key()["big_mac"].product_ids == [1090]
    assert yaml.safe_load(dst.read_text(encoding="utf-8"))["versions"][0]["version"] == "2025-09-16"
    assert pin_product_ids(dst, "2025-09-16", {"big_mac": {1090}}) == 0


def test_unresolved_alert_above_five_percent() -> None:
    stats = ResolutionStats()
    p = Product(1, 100, "x", "")
    for i in range(100):
        stats.record({"a": p, "b": None if i < 6 else p, "c": None if i < 5 else p})
    alerts = stats.alerts()
    assert len(alerts) == 1 and alerts[0].startswith("b:")
    assert stats.pins["a"] == {1}
