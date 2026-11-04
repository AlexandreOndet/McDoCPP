FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/venv
COPY collector/pyproject.toml collector/uv.lock collector/.python-version ./
RUN uv sync --frozen --no-dev --extra s3 --no-install-project
COPY collector/mcdocpp ./mcdocpp
COPY collector/rewards_catalogue.yaml ./
COPY schemas /schemas
RUN uv sync --frozen --no-dev --extra s3

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY --from=build /venv /venv
COPY --from=build /app /app
COPY --from=build /schemas /schemas
ENV PATH=/venv/bin:$PATH MCDOCPP_STORAGE=s3 MCDOCPP_WORK_DIR=/tmp/history
USER 65532:65532
ENTRYPOINT ["mcdocpp"]
CMD ["crawl"]
