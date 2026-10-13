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

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping
from urllib.parse import urlparse


DEFAULT_AUTH_PATH = "/dna/system/api/v1/auth/token"


class SettingsError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def parse_bool(value: str | bool | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise SettingsError(f"Invalid boolean value: {value!r}")


def normalize_base_url(host: str) -> str:
    value = host.strip()
    if not value:
        raise SettingsError("CATALYST_CENTER_HOST is required")
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SettingsError(f"Invalid Catalyst Center host: {host!r}")
    return value.rstrip("/")


@dataclass(frozen=True)
class Settings:
    base_url: str
    username: str
    password: str
    verify_ssl: bool = False
    timeout_seconds: float = 30.0
    auth_path: str = DEFAULT_AUTH_PATH
    bundled_tools_dir: str | None = None

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        require_credentials: bool = True,
    ) -> "Settings":
        env = os.environ if environ is None else environ
        host = env.get("CATALYST_CENTER_HOST") or env.get("CATALYST_CENTER_IP") or ""
        username = env.get("CATALYST_CENTER_USERNAME", "")
        password = env.get("CATALYST_CENTER_PASSWORD", "")

        if require_credentials:
            missing = [
                name
                for name, value in {
                    "CATALYST_CENTER_HOST": host,
                    "CATALYST_CENTER_USERNAME": username,
                    "CATALYST_CENTER_PASSWORD": password,
                }.items()
                if not value
            ]
            if missing:
                raise SettingsError(
                    "Missing required environment variable(s): " + ", ".join(missing)
                )

        base_url = normalize_base_url(host) if host else ""
        timeout = float(env.get("CATALYST_CENTER_TIMEOUT_SECONDS", "30"))
        auth_path = env.get("CATALYST_CENTER_AUTH_PATH", DEFAULT_AUTH_PATH)
        if not auth_path.startswith("/"):
            auth_path = f"/{auth_path}"

        return cls(
            base_url=base_url,
            username=username,
            password=password,
            verify_ssl=parse_bool(env.get("CATALYST_CENTER_VERIFY_SSL"), default=False),
            timeout_seconds=timeout,
            auth_path=auth_path,
            bundled_tools_dir=env.get("CATALYST_CENTER_BUNDLED_TOOLS_DIR"),
        )

    def validate_credentials(self) -> None:
        missing = [
            name
            for name, value in {
                "CATALYST_CENTER_HOST": self.base_url,
                "CATALYST_CENTER_USERNAME": self.username,
                "CATALYST_CENTER_PASSWORD": self.password,
            }.items()
            if not value
        ]
        if missing:
            raise SettingsError(
                "Missing required environment variable(s): " + ", ".join(missing)
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env(require_credentials=False)


def reset_settings_cache() -> None:
    get_settings.cache_clear()
