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

from catalyst_center_mcp.config import Settings, SettingsError, normalize_base_url


def test_from_env_can_defer_required_credentials_but_validate_later(monkeypatch):
    monkeypatch.setenv("CATALYST_CENTER_PASSWORD", "ambient-secret")

    settings = Settings.from_env({}, require_credentials=False)

    with pytest.raises(SettingsError) as exc_info:
        settings.validate_credentials()

    assert "CATALYST_CENTER_HOST" in str(exc_info.value)
    assert "CATALYST_CENTER_USERNAME" in str(exc_info.value)
    assert "CATALYST_CENTER_PASSWORD" in str(exc_info.value)


def test_normalize_base_url_adds_https_scheme():
    assert normalize_base_url("10.10.10.10/") == "https://10.10.10.10"
