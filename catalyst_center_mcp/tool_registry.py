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
import logging
import re
from collections.abc import Callable
from inspect import Parameter, Signature
from typing import Annotated, Any
from urllib.parse import quote

from fastmcp import FastMCP
from pydantic import Field

from catalyst_center_mcp.catalyst_client import (
    CatalystCenterClient,
    CatalystCenterError,
    RequestPayload,
)
from catalyst_center_mcp.config import get_settings
from catalyst_center_mcp.tool_loader import ToolDefinition

logger = logging.getLogger(__name__)


ClientFactory = Callable[[], CatalystCenterClient]


class CatalystMCPTool:
    def __init__(self, mcp_instance: FastMCP):
        self.mcp = mcp_instance

    def tool(
        self,
        *,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ):
        def decorator(func):
            signature, annotations, argument_aliases = _signature_from_schema(input_schema)

            async def generated_tool_wrapper(**kwargs) -> str:
                restored_kwargs = {
                    argument_aliases.get(key, key): value for key, value in kwargs.items()
                }
                return await func(**restored_kwargs)

            generated_tool_wrapper.__name__ = _safe_identifier(name)
            generated_tool_wrapper.__doc__ = description
            generated_tool_wrapper.__signature__ = signature
            generated_tool_wrapper.__annotations__ = annotations

            self.mcp.tool(
                name=name,
                description=description,
                meta=metadata,
            )(generated_tool_wrapper)
            return generated_tool_wrapper

        return decorator


def _safe_identifier(name: str) -> str:
    value = re.sub(r"\W", "_", name)
    if not value or value[0].isdigit():
        value = f"_{value}"
    return value


def _unique_identifier(name: str, used: set[str]) -> str:
    base = _safe_identifier(name)
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def _python_type_from_schema(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((item for item in schema_type if item != "null"), None)

    if schema_type == "string":
        return str
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    if schema_type == "array":
        return list[Any]
    if schema_type == "object":
        return dict[str, Any]
    return Any


def _field_from_schema(schema: dict[str, Any], *, alias: str | None = None) -> Any:
    field_kwargs: dict[str, Any] = {}
    if alias:
        field_kwargs["alias"] = alias
    if description := schema.get("description"):
        field_kwargs["description"] = description
    if "minimum" in schema:
        field_kwargs["ge"] = schema["minimum"]
    if "maximum" in schema:
        field_kwargs["le"] = schema["maximum"]
    if "minLength" in schema:
        field_kwargs["min_length"] = schema["minLength"]
    if "maxLength" in schema:
        field_kwargs["max_length"] = schema["maxLength"]
    return Field(**field_kwargs)


def _signature_from_schema(
    input_schema: dict[str, Any],
) -> tuple[Signature, dict[str, Any], dict[str, str]]:
    properties = input_schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    required = input_schema.get("required")
    required_names = set(required if isinstance(required, list) else [])

    parameters: list[Parameter] = []
    annotations: dict[str, Any] = {"return": str}
    aliases: dict[str, str] = {}
    used_names: set[str] = set()

    for original_name, schema in properties.items():
        if not isinstance(schema, dict):
            schema = {}
        parameter_name = _unique_identifier(str(original_name), used_names)
        aliases[parameter_name] = str(original_name)
        is_required = original_name in required_names
        base_type = _python_type_from_schema(schema)
        if not is_required:
            base_type = base_type | None
        alias = str(original_name) if parameter_name != original_name else None
        annotation = Annotated[base_type, _field_from_schema(schema, alias=alias)]
        default = Parameter.empty if is_required else None
        parameters.append(
            Parameter(
                parameter_name,
                Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
        )
        annotations[parameter_name] = annotation

    return (
        Signature(parameters=parameters, return_annotation=str),
        annotations,
        aliases,
    )


def _json_result(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _drop_none_values(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _replace_path_params(uri: str, path_params: dict[str, Any]) -> str:
    path = uri
    for key, value in path_params.items():
        token = "{" + key + "}"
        path = path.replace(token, quote(str(value), safe=""))
    return path


def build_request_payload(tool: ToolDefinition, arguments: dict[str, Any]) -> RequestPayload:
    metadata = tool.metadata
    uri = metadata.get("uri") or metadata.get("path")
    method = metadata.get("method")
    if not uri or not method:
        raise ValueError(f"Tool {tool.name} is missing additionalMetadata.uri or method")

    filtered_args = _drop_none_values(arguments)
    parameter_locations = metadata.get("parameterLocation") or metadata.get("parameter_location") or {}
    if not isinstance(parameter_locations, dict):
        parameter_locations = {}

    query: dict[str, Any] = {}
    headers: dict[str, str] = {}
    body_fields: dict[str, Any] = {}
    path_params: dict[str, Any] = {}

    for key, value in filtered_args.items():
        location = str(parameter_locations.get(key) or "").lower()
        if location in {"path", "pathparam", "path_parameter"}:
            path_params[key] = value
        elif location in {"header", "headers"}:
            headers[key] = str(value)
        elif location in {"body", "requestbody", "json"}:
            body_fields[key] = value
        elif location in {"query", "queryparam", "query_parameter"}:
            query[key] = value
        elif method.upper() in {"GET", "DELETE"}:
            query[key] = value
        else:
            body_fields[key] = value

    path = _replace_path_params(str(uri), path_params)
    json_body: Any | None = body_fields or None
    if len(body_fields) == 1 and "request" in body_fields:
        json_body = body_fields["request"]

    return RequestPayload(
        method=str(method),
        path=path,
        query=query or None,
        json_body=json_body,
        headers=headers or None,
    )


def _default_client_factory() -> CatalystCenterClient:
    return CatalystCenterClient(get_settings())


def register_tools(
    mcp: FastMCP,
    tools: list[ToolDefinition],
    *,
    client_factory: ClientFactory = _default_client_factory,
) -> int:
    decorator = CatalystMCPTool(mcp)
    registered = 0
    seen: set[str] = set()

    for tool in tools:
        if tool.name in seen:
            raise ValueError(f"Duplicate tool name {tool.name!r}")
        seen.add(tool.name)

        async def execute_tool(_tool: ToolDefinition = tool, **kwargs) -> str:
            client = client_factory()
            try:
                payload = build_request_payload(_tool, kwargs)
                result = await client.request(payload)
                return _json_result(result)
            except Exception as exc:
                if isinstance(exc, CatalystCenterError):
                    logger.warning("Catalyst Center tool %s failed: %s", _tool.name, exc)
                else:
                    logger.exception("Tool %s failed", _tool.name)
                return f"Error executing tool {_tool.name}: {exc}"
            finally:
                await client.aclose()

        decorator.tool(
            name=tool.name,
            description=tool.description,
            input_schema=tool.parameters,
            metadata=tool.metadata,
        )(execute_tool)
        registered += 1

    return registered
