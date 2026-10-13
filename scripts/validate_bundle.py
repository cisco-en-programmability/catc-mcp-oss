#!/usr/bin/env python3
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

import argparse
import json
from pathlib import Path

from catalyst_center_mcp.tool_loader import load_tools


SOURCE_RELATIVE_DIR = Path("Agent_DNAC") / "autogen" / "promoted"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a bundled Catalyst Center MCP tool set.")
    parser.add_argument("manifest", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.manifest.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    bundle_root = args.manifest.parent
    tools_root = bundle_root / SOURCE_RELATIVE_DIR
    tools = load_tools(tools_root)
    expected_count = manifest.get("included_tool_count")
    if expected_count != len(tools):
        raise ValueError(f"Manifest expects {expected_count} tools but loaded {len(tools)}")

    for tool in tools:
        if "mcp-tools" in str(tool.source_path):
            raise ValueError(f"Custom tool path was bundled unexpectedly: {tool.source_path}")
        missing = [key for key in ("uri", "method") if not tool.metadata.get(key)]
        if missing:
            raise ValueError(f"Tool {tool.name} is missing metadata field(s): {', '.join(missing)}")

    print(f"Validated {len(tools)} bundled Catalyst Center tools for release {manifest.get('release')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
