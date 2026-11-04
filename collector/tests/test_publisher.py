import json
from pathlib import Path

import jsonschema
import pytest
from typer.testing import CliRunner

from mcdocpp.cli import app
from mcdocpp.publisher import schema_for, validate

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def out(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("out")
    fx = tmp_path_factory.mktemp("fx")
    r = CliRunner().invoke(app, ["synth", "--out", str(fx), "--n", "6"])
    assert r.exit_code == 0, r.output
    r = CliRunner().invoke(
        app,
        [
            "crawl",
            "--fixture-dir",
            str(fx),
            "--stores-file",
            str(fx / "stores.json"),
            "--out",
            str(out),
            "--as-of",
            "2026-11-03T10:12:00+00:00",
        ],
    )
    assert r.exit_code == 0, r.output
    return out


def test_every_json_validates_and_carries_as_of(out: Path) -> None:
    files = [p for p in out.rglob("*.json") if "state" not in p.parts]
    assert len(files) > 20
    for p in files:
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["as_of"] == "2026-11-03T10:12:00+00:00", p
        validate(str(p.relative_to(out)), doc)


def test_store_file_ranked_by_cpp_with_deltas(out: Path) -> None:
    doc = json.loads((out / "stores" / "10001.json").read_text(encoding="utf-8"))
    cpps = [i["cpp"] for i in doc["items"] if i["cpp"] is not None]
    assert cpps == sorted(cpps, reverse=True)
    assert doc["best_item_key"] == doc["items"][0]["key"]
    assert set(doc["best_by_tier"]) == {"2000", "4000", "6000", "10000", "14000"}
    assert doc["items"][0]["delta_vs_national"] is not None
    assert doc["items"][0]["value_per_1k"] == round(doc["items"][0]["cpp"] * 10, 2)


def test_index_quantiles_and_meta(out: Path) -> None:
    idx = json.loads((out / "stores" / "index.json").read_text(encoding="utf-8"))
    assert len(idx["stores"]) == 6 and len(idx["best_cpp_quantiles"]) == 4
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["crawl"]["ok"] == 6 and meta["store_count"] == 6


def test_history_and_raw_tiers_written(out: Path) -> None:
    assert list(out.glob("history/reward_price_daily/year=2026/month=11/2026-11-03.parquet"))
    assert list(out.glob("history/cpp_aggregate_monthly/year=2026/2026-11.parquet"))
    assert len(list(out.glob("raw/2026-11-03/*.json.gz"))) == 6
    assert (out / "history" / "national" / "best.json").exists()


def test_schema_rejects_missing_as_of() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate("meta.json", {"catalogue_version": "x"})
    assert schema_for("history/QC/best.json") == "history-best"
    assert schema_for("history/QC/big_mac.json") == "history"
