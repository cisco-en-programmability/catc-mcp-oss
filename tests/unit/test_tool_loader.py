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

import json
from pathlib import Path

import pytest

from catalyst_center_mcp.tool_loader import ToolLoadError, clean_json_schema, load_tools


def _write_tool(root: Path, filename: str, name: str = "api_getSomething") -> Path:
    path = root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "function": {
                    "name": name,
                    "description": "Get something",
                    "parameters": {
                        "type": "object",
                        "title": "Ignored",
                        "properties": {
                            "id": {"type": "string", "default": None, "title": "Ignored"}
                        },
                    },
                    "additionalMetadata": {
                        "uri": "/dna/intent/api/v1/something/{id}",
                        "method": "GET",
                        "parameterLocation": {"id": "path"},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_tools_preserves_additional_metadata(tmp_path):
    _write_tool(tmp_path, "api_getSomething.json")

    tools = load_tools(tmp_path)

    assert len(tools) == 1
    assert tools[0].name == "api_getSomething"
    assert tools[0].metadata["uri"] == "/dna/intent/api/v1/something/{id}"
    assert tools[0].parameters["properties"]["id"] == {"type": "string"}


def test_clean_json_schema_removes_titles_and_null_defaults():
    assert clean_json_schema({"title": "T", "default": None, "items": [{"title": "Nested"}]}) == {
        "items": [{}]
    }


def test_duplicate_tool_names_raise(tmp_path):
    _write_tool(tmp_path, "one.json", name="api_duplicate")
    _write_tool(tmp_path, "two.json", name="api_duplicate")

    with pytest.raises(ToolLoadError):
        load_tools(tmp_path)
