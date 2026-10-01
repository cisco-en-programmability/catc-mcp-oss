# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from catalyst_center_mcp.config import Settings


class CatalystCenterError(RuntimeError):
    """Raised when Catalyst Center authentication or API execution fails."""


@dataclass
class RequestPayload:
    method: str
    path: str
    query: dict[str, Any] | None = None
    json_body: Any | None = None
    headers: dict[str, str] | None = None


class CatalystCenterClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            verify=settings.verify_ssl,
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def authenticate(self, *, force: bool = False) -> str:
        if self._token and not force:
            return self._token

        self._settings.validate_credentials()
        response = await self._client.post(
            self._settings.auth_path,
            auth=(self._settings.username, self._settings.password),
            headers={"Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise CatalystCenterError(
                f"Catalyst Center authentication failed with status {response.status_code}"
            )

        token = self._extract_token(response)
        if not token:
            raise CatalystCenterError("Catalyst Center authentication response did not include a token")
        self._token = token
        return token

    async def request(self, payload: RequestPayload) -> Any:
        token = await self.authenticate()
        response = await self._send(payload, token)
        if response.status_code == 401:
            token = await self.authenticate(force=True)
            response = await self._send(payload, token)

        if response.status_code >= 400:
            raise CatalystCenterError(
                f"Catalyst Center API call failed with status {response.status_code}: "
                f"{self._safe_response_text(response)}"
            )

        if not response.content:
            return {}
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            return response.json()
        try:
            return response.json()
        except ValueError:
            return response.text

    async def _send(self, payload: RequestPayload, token: str) -> httpx.Response:
        headers = dict(payload.headers or {})
        headers.setdefault("Accept", "application/json")
        headers["X-Auth-Token"] = token
        return await self._client.request(
            payload.method.upper(),
            payload.path,
            params=payload.query,
            json=payload.json_body,
            headers=headers,
        )

    @staticmethod
    def _extract_token(response: httpx.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            return text or None

        if isinstance(payload, dict):
            for key in ("Token", "token", "access_token"):
                value = payload.get(key)
                if value:
                    return str(value)
        return None

    @staticmethod
    def _safe_response_text(response: httpx.Response) -> str:
        text = response.text.strip()
        if len(text) > 500:
            text = text[:500] + "..."
        return text
