.PHONY: setup test crawl-fixtures web-dev web-build check lint screens

PNPM ?= corepack pnpm
UV ?= uv --project collector
PY ?= uv --directory collector run
FIXTURES := fixtures/synthetic

setup:
	$(UV) sync --all-extras
	corepack enable pnpm >/dev/null 2>&1 || true
	cd web && $(PNPM) install

$(FIXTURES)/stores.json:
	$(UV) run mcdocpp synth --out $(FIXTURES)

crawl-fixtures: $(FIXTURES)/stores.json
	$(UV) run mcdocpp crawl --fixture-dir $(FIXTURES) --stores-file $(FIXTURES)/stores.json --out out
	rm -rf web/static/data && mkdir -p web/static && cp -r out web/static/data && rm -rf web/static/data/raw web/static/data/state web/static/data/history/*_daily web/static/data/history/*_monthly

test:
	$(PY) pytest -q
	cd web && $(PNPM) test

lint:
	$(PY) ruff check . && $(PY) ruff format --check . && $(PY) mypy
	cd web && $(PNPM) lint && $(PNPM) check

check: lint test

web-dev: crawl-fixtures
	cd web && $(PNPM) dev

web-build: crawl-fixtures
	cd web && $(PNPM) build

e2e: web-build
	cd web && $(PNPM) e2e

screens: web-build
	cd web && $(PNPM) screens
