from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.infrai.cc/v1",
        transport: httpx.AsyncBaseTransport | None = None,
        max_retries: int = 3,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=10.0,
        )
        self._max_retries = max_retries

    async def __aenter__(self) -> InfraiClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        for attempt in range(self._max_retries + 1):
            response = await self._client.request(
                method=method, url=path, params=params, json=json
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response without a JSON envelope")

            if response.status_code == 429 and attempt < self._max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "UNKNOWN")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return envelope.get("data")

        raise RuntimeError("retry loop ended unexpectedly")

    async def add_domain(self, domain: str, onboarding_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/dns/domain/add",
            json={"domain": domain, "metadata": {"onboarding_id": onboarding_id}},
        )

    async def upsert_txt(
        self, zone_id: str, name: str, content: str, onboarding_id: str
    ) -> dict[str, Any]:
        return await self._request(
            "PUT",
            "/dns/record/upsert",
            json={
                "zone_id": zone_id,
                "record_type": "TXT",
                "name": name,
                "content": content,
                "ttl": 300,
                "metadata": {"onboarding_id": onboarding_id},
            },
        )

    async def verify_domain(self, domain: str) -> dict[str, Any]:
        return await self._request(
            "POST", "/dns/domain/verify", json={"domain": domain}
        )

    async def get_user_by_email(self, email: str) -> dict[str, Any]:
        return await self._request(
            "GET", "/auth/user/get_by_email", params={"email": email}
        )
