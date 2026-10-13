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

import httpx
import pytest

from catalyst_center_mcp.catalyst_client import CatalystCenterClient, RequestPayload
from catalyst_center_mcp.config import Settings


def _settings() -> Settings:
    return Settings(
        base_url="https://catc.example.com",
        username="admin",
        password="password",
        verify_ssl=False,
    )


@pytest.mark.asyncio
async def test_client_authenticates_and_sends_token():
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/dna/system/api/v1/auth/token":
            return httpx.Response(200, json={"Token": "token-1"})
        assert request.headers["X-Auth-Token"] == "token-1"
        return httpx.Response(200, json={"response": []})

    client = CatalystCenterClient(_settings(), transport=httpx.MockTransport(handler))
    try:
        result = await client.request(RequestPayload(method="GET", path="/dna/intent/api/v1/network-device"))
    finally:
        await client.aclose()

    assert result == {"response": []}
    assert [request.url.path for request in seen] == [
        "/dna/system/api/v1/auth/token",
        "/dna/intent/api/v1/network-device",
    ]


@pytest.mark.asyncio
async def test_client_refreshes_token_once_on_unauthorized_response():
    auth_count = 0
    api_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal auth_count, api_count
        if request.url.path == "/dna/system/api/v1/auth/token":
            auth_count += 1
            return httpx.Response(200, json={"Token": f"token-{auth_count}"})

        api_count += 1
        if api_count == 1:
            assert request.headers["X-Auth-Token"] == "token-1"
            return httpx.Response(401, json={"message": "expired"})
        assert request.headers["X-Auth-Token"] == "token-2"
        return httpx.Response(200, json={"ok": True})

    client = CatalystCenterClient(_settings(), transport=httpx.MockTransport(handler))
    try:
        result = await client.request(RequestPayload(method="GET", path="/dna/intent/api/v1/site"))
    finally:
        await client.aclose()

    assert result == {"ok": True}
    assert auth_count == 2
    assert api_count == 2
