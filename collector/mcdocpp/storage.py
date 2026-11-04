"""Object storage behind one interface: local directory or any S3-compatible bucket (R2, GCS)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> None: ...
    def get(self, path: str) -> bytes | None: ...
    def list(self, prefix: str) -> list[str]: ...
    def delete(self, path: str) -> None: ...


class LocalFS:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, path: str) -> bytes | None:
        p = self.root / path
        return p.read_bytes() if p.is_file() else None

    def list(self, prefix: str) -> list[str]:
        base = self.root / prefix
        if not base.exists():
            return []
        return sorted(str(p.relative_to(self.root)) for p in base.rglob("*") if p.is_file())

    def delete(self, path: str) -> None:
        p = self.root / path
        if p.is_file():
            p.unlink()


class S3Compatible:
    """R2 / GCS via the S3 API. Lifecycle (raw/ 14 days) is configured on the bucket, not here."""

    def __init__(
        self, bucket: str, endpoint_url: str | None = None, public_cache_control: str = "max-age=3600"
    ) -> None:
        import boto3

        self.bucket = bucket
        self.cache_control = public_cache_control
        self.client = boto3.client("s3", endpoint_url=endpoint_url or os.environ.get("S3_ENDPOINT_URL"))

    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.client.put_object(
            Bucket=self.bucket, Key=path, Body=data, ContentType=content_type, CacheControl=self.cache_control
        )

    def get(self, path: str) -> bytes | None:
        try:
            return bytes(self.client.get_object(Bucket=self.bucket, Key=path)["Body"].read())
        except self.client.exceptions.NoSuchKey:
            return None

    def list(self, prefix: str) -> list[str]:
        keys: list[str] = []
        for page in self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
            keys.extend(o["Key"] for o in page.get("Contents", []))
        return keys

    def delete(self, path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=path)


def from_env() -> Storage:
    if os.environ.get("MCDOCPP_STORAGE", "local") == "s3":
        return S3Compatible(os.environ["S3_BUCKET"])
    return LocalFS(Path(os.environ.get("MCDOCPP_OUT_DIR", "./out")))
