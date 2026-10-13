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

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from packaging.version import InvalidVersion, Version


MIN_VERSION_KEYS = (
    "min_controller_version",
    "minControllerVersion",
    "minimumControllerVersion",
    "min_version",
    "minVersion",
    "minimumVersion",
)
MAX_VERSION_KEYS = (
    "max_controller_version",
    "maxControllerVersion",
    "maximumControllerVersion",
    "max_version",
    "maxVersion",
    "maximumVersion",
)
METADATA_PATHS = (
    ("function", "_meta"),
    ("function", "meta"),
    ("function", "additionalMetadata"),
    ("_meta",),
    ("meta",),
    ("additionalMetadata",),
)


@dataclass(frozen=True)
class VersionRange:
    min_version: str | None = None
    max_version: str | None = None


def _metadata_at_path(payload: Mapping[str, Any], path: tuple[str, ...]) -> Mapping[str, Any]:
    current: Any = payload
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return {}
        current = current[key]
    return current if isinstance(current, Mapping) else {}


def _first_value(metadata: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if value:
            return str(value)
    return None


def _range_from_supported_versions(metadata: Mapping[str, Any]) -> VersionRange | None:
    supported = metadata.get("supportedVersions")
    if not isinstance(supported, Mapping):
        supported = metadata.get("supported_versions")
    if not isinstance(supported, Mapping):
        return None
    min_version = _first_value(supported, MIN_VERSION_KEYS) or supported.get("min")
    max_version = _first_value(supported, MAX_VERSION_KEYS) or supported.get("max")
    if min_version or max_version:
        return VersionRange(
            str(min_version) if min_version else None,
            str(max_version) if max_version else None,
        )
    return None


def extract_version_range(payload: Mapping[str, Any]) -> VersionRange:
    for path in METADATA_PATHS:
        metadata = _metadata_at_path(payload, path)
        if not metadata:
            continue

        supported_range = _range_from_supported_versions(metadata)
        if supported_range:
            return supported_range

        min_version = _first_value(metadata, MIN_VERSION_KEYS)
        max_version = _first_value(metadata, MAX_VERSION_KEYS)
        if min_version or max_version:
            return VersionRange(min_version=min_version, max_version=max_version)

    return VersionRange()


def _parse_version(value: str | None) -> Version | None:
    if not value:
        return None
    try:
        return Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"Invalid Catalyst Center version: {value!r}") from exc


def is_version_in_range(
    release: str,
    *,
    min_version: str | None = None,
    max_version: str | None = None,
) -> bool:
    requested = _parse_version(release)
    minimum = _parse_version(min_version)
    maximum = _parse_version(max_version)
    if minimum and requested < minimum:
        return False
    if maximum and requested > maximum:
        return False
    return True


def is_tool_supported(payload: Mapping[str, Any], release: str) -> bool:
    version_range = extract_version_range(payload)
    return is_version_in_range(
        release,
        min_version=version_range.min_version,
        max_version=version_range.max_version,
    )
