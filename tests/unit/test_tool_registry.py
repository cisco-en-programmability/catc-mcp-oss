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

import pytest
from fastmcp import FastMCP

from catalyst_center_mcp.tool_loader import ToolDefinition
from catalyst_center_mcp.tool_registry import build_request_payload, register_tools


class FakeClient:
    def __init__(self):
        self.payloads = []
        self.closed = False

    async def request(self, payload):
        self.payloads.append(payload)
        return {"ok": True}

    async def aclose(self):
        self.closed = True


def test_build_request_payload_maps_path_query_header_and_body_fields(tmp_path):
    tool = ToolDefinition(
        name="api_updateDevice",
        description="Update device",
        parameters={"type": "object"},
        metadata={
            "uri": "/dna/intent/api/v1/network-device/{id}",
            "method": "PUT",
            "parameterLocation": {
                "id": "path",
                "siteId": "query",
                "X-Request-ID": "header",
                "payload": "body",
            },
        },
        source_path=tmp_path / "tool.json",
    )

    payload = build_request_payload(
        tool,
        {
            "id": "abc/123",
            "siteId": "site-1",
            "X-Request-ID": "request-1",
            "payload": {"hostname": "edge-1"},
            "ignored": None,
        },
    )

    assert payload.method == "PUT"
    assert payload.path == "/dna/intent/api/v1/network-device/abc%2F123"
    assert payload.query == {"siteId": "site-1"}
    assert payload.headers == {"X-Request-ID": "request-1"}
    assert payload.json_body == {"payload": {"hostname": "edge-1"}}


def test_build_request_payload_defaults_get_arguments_to_query(tmp_path):
    tool = ToolDefinition(
        name="api_getSites",
        description="Get sites",
        parameters={"type": "object"},
        metadata={"uri": "/dna/intent/api/v1/site", "method": "GET"},
        source_path=tmp_path / "tool.json",
    )

    payload = build_request_payload(tool, {"limit": 10})

    assert payload.query == {"limit": 10}
    assert payload.json_body is None


@pytest.mark.asyncio
async def test_registered_tool_accepts_schema_arguments(tmp_path):
    tool = ToolDefinition(
        name="api_devices",
        description="Get devices",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "description": "Maximum number of records",
                    "minimum": 1,
                    "maximum": 500,
                    "type": "integer",
                },
                "offset": {"description": "First record", "type": "integer"},
            },
        },
        metadata={
            "uri": "/dna/intent/api/v1/device-health",
            "method": "GET",
            "parameterLocation": {"limit": "query", "offset": "query"},
        },
        source_path=tmp_path / "api_devices.json",
    )
    client = FakeClient()
    mcp = FastMCP("test")

    register_tools(mcp, [tool], client_factory=lambda: client)
    registered_tool = await mcp.get_tool("api_devices")
    result = await mcp.call_tool("api_devices", {"limit": 5, "offset": 1})

    assert registered_tool.parameters["properties"]["limit"]["description"] == "Maximum number of records"
    assert client.payloads[0].query == {"limit": 5, "offset": 1}
    assert client.closed is True
    assert result.content[0].text == '{"ok":true}'


@pytest.mark.asyncio
async def test_registered_tool_accepts_non_python_identifier_argument_names(tmp_path):
    tool = ToolDefinition(
        name="api_withHeader",
        description="Get with header",
        parameters={
            "type": "object",
            "properties": {
                "X-CALLER-ID": {
                    "description": "Caller identifier",
                    "type": "string",
                }
            },
        },
        metadata={
            "uri": "/dna/intent/api/v1/header-test",
            "method": "GET",
            "parameterLocation": {"X-CALLER-ID": "header"},
        },
        source_path=tmp_path / "api_withHeader.json",
    )
    client = FakeClient()
    mcp = FastMCP("test")

    register_tools(mcp, [tool], client_factory=lambda: client)
    registered_tool = await mcp.get_tool("api_withHeader")
    await mcp.call_tool("api_withHeader", {"X-CALLER-ID": "request-1"})

    assert "X-CALLER-ID" in registered_tool.parameters["properties"]
    assert client.payloads[0].headers == {"X-CALLER-ID": "request-1"}
