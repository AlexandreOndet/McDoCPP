"""GMA token manager: refresh-token chain, header assembly, rotation persistence."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable

import httpx

BASE_URL = "https://us-prod.api.mcd.com"


class TokenManager:
    def __init__(
        self,
        refresh_token: str,
        client_id: str,
        extra_headers: dict[str, str],
        persist: Callable[[str], None] | None = None,
        base_url: str = BASE_URL,
    ) -> None:
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.extra_headers = extra_headers
        self.persist = persist
        self.base_url = base_url
        self.access_token: str | None = None

    @classmethod
    def from_env(cls, persist: Callable[[str], None] | None = None) -> TokenManager:
        return cls(
            refresh_token=os.environ["MCD_REFRESH_TOKEN"],
            client_id=os.environ["MCD_CLIENT_ID"],
            extra_headers=json.loads(os.environ.get("MCD_HEADERS_JSON", "{}")),
            persist=persist,
        )

    def headers(self) -> dict[str, str]:
        h = dict(self.extra_headers)
        h.update(
            {
                "mcd-clientid": self.client_id,
                "mcd-marketid": "CA",
                "mcd-uuid": str(uuid.uuid4()).upper(),
            }
        )
        if self.access_token:
            h["authorization"] = f"Bearer {self.access_token}"
        return h

    def refresh(self, client: httpx.Client) -> None:
        r = client.post(
            f"{self.base_url}/exp/v1/customer/login/refresh",
            json={"refreshToken": self.refresh_token},
            headers=self.headers(),
        )
        r.raise_for_status()
        body = r.json()["response"]
        self.access_token = body["accessToken"]
        new = body.get("refreshToken")
        if new and new != self.refresh_token:
            self.refresh_token = new
            if self.persist:
                self.persist(new)
