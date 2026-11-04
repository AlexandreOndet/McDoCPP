import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from mcdocpp.catalogue import Catalogue, CatalogueVersion, load_catalogue
from mcdocpp.parser import MenuSnapshot, parse_menu

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def payload() -> dict[str, Any]:
    return dict(json.loads((REPO / "fixtures" / "menu_sample.json").read_text(encoding="utf-8")))


@pytest.fixture(scope="session")
def snapshot(payload: dict[str, Any]) -> MenuSnapshot:
    return parse_menu(payload)


@pytest.fixture(scope="session")
def catalogue() -> Catalogue:
    return load_catalogue(REPO / "collector" / "rewards_catalogue.yaml")


@pytest.fixture(scope="session")
def version(catalogue: Catalogue) -> CatalogueVersion:
    return catalogue.version_for(date(2026, 11, 3))
