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

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    metadata: dict[str, Any]
    source_path: Path
    responses: dict[str, Any] | None = None


class ToolLoadError(ValueError):
    """Raised when bundled tool metadata is malformed."""


def default_bundled_tools_dir() -> Path:
    package_root = resources.files("catalyst_center_mcp")
    return Path(str(package_root / "bundled_tools" / "Agent_DNAC" / "autogen" / "promoted"))


def clean_json_schema(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema

    cleaned: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "title":
            continue
        if key == "default" and value is None:
            continue
        if isinstance(value, dict):
            cleaned[key] = clean_json_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_json_schema(item) for item in value]
        else:
            cleaned[key] = value
    return cleaned


def _iter_tool_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.json")
        if not path.name.endswith(".patch.json") and path.name != "manifest.json"
    )


def _metadata_from_function(function: Mapping[str, Any]) -> dict[str, Any]:
    metadata = function.get("additionalMetadata") or function.get("_meta") or {}
    if not isinstance(metadata, dict):
        raise ToolLoadError("Tool metadata must be a JSON object")
    return dict(metadata)


def load_tool_file(path: Path) -> ToolDefinition:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    function = payload.get("function")
    if not isinstance(function, dict):
        raise ToolLoadError(f"{path} does not contain a function object")

    name = function.get("name") or path.stem
    if not isinstance(name, str) or not name:
        raise ToolLoadError(f"{path} does not define a tool name")

    parameters = function.get("parameters") or {"type": "object", "properties": {}}
    if not isinstance(parameters, dict):
        raise ToolLoadError(f"{path} parameters must be a JSON object")

    return ToolDefinition(
        name=name,
        description=str(function.get("description") or f"Tool: {name}"),
        parameters=clean_json_schema(parameters),
        metadata=_metadata_from_function(function),
        source_path=path,
        responses=function.get("responses") if isinstance(function.get("responses"), dict) else None,
    )


def load_tools(root: Path | str | None = None) -> list[ToolDefinition]:
    tools_root = Path(root) if root else default_bundled_tools_dir()
    tools: list[ToolDefinition] = []
    seen: dict[str, Path] = {}
    for path in _iter_tool_files(tools_root):
        tool = load_tool_file(path)
        if tool.name in seen:
            raise ToolLoadError(
                f"Duplicate tool name {tool.name!r}: {seen[tool.name]} and {path}"
            )
        seen[tool.name] = path
        tools.append(tool)
    return tools
