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

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp import FastMCP

from catalyst_center_mcp.config import SettingsError, get_settings
from catalyst_center_mcp.tool_loader import load_tools
from catalyst_center_mcp.tool_registry import register_tools

logger = logging.getLogger(__name__)


def create_mcp() -> FastMCP:
    mcp = FastMCP("catalyst-center-mcp")
    settings = get_settings()
    tools_root = settings.bundled_tools_dir
    tools = load_tools(tools_root)
    count = register_tools(mcp, tools)
    logger.info("Registered %s bundled Catalyst Center tools", count)
    return mcp


mcp = create_mcp()
mcp_app = mcp.http_app(path="/mcp", transport="streamable-http", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_settings().validate_credentials()
    except SettingsError as exc:
        logger.warning("Catalyst Center credentials are not fully configured: %s", exc)
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(title="Catalyst Center MCP", version="0.1.0", lifespan=lifespan)


@app.get("/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/readiness")
async def readiness() -> dict[str, str]:
    get_settings().validate_credentials()
    return {"status": "ready"}


app.mount("/v1", mcp_app)
