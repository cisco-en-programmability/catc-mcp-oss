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

from catalyst_center_mcp.versioning import extract_version_range, is_tool_supported, is_version_in_range


def test_version_range_allows_unbounded_tools():
    assert is_version_in_range("2.3.7.9")


def test_version_range_enforces_min_and_max():
    assert is_version_in_range("2.3.7.9", min_version="2.3.7.0", max_version="2.3.8.0")
    assert not is_version_in_range("2.3.6.9", min_version="2.3.7.0")
    assert not is_version_in_range("2.3.8.1", max_version="2.3.8.0")


def test_extract_version_range_from_additional_metadata_aliases():
    payload = {
        "function": {
            "additionalMetadata": {
                "minControllerVersion": "2.3.7.0",
                "max_controller_version": "2.3.7.9",
            }
        }
    }
    version_range = extract_version_range(payload)
    assert version_range.min_version == "2.3.7.0"
    assert version_range.max_version == "2.3.7.9"


def test_tool_support_uses_metadata_range():
    payload = {"function": {"_meta": {"min_controller_version": "3.0.0"}}}
    assert is_tool_supported(payload, "3.1.0")
    assert not is_tool_supported(payload, "2.3.7.9")
