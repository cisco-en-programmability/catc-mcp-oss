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

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/jenkins/.local/bin:${PATH}"

USER root
WORKDIR /app

COPY pyproject.toml README.md ./
COPY catalyst_center_mcp ./catalyst_center_mcp
COPY scripts ./scripts

RUN python3 -m pip install --break-system-packages --no-cache-dir .

EXPOSE 7001

CMD ["python3", "-m", "uvicorn", "catalyst_center_mcp.main:app", "--host", "0.0.0.0", "--port", "7001"]