# Catalyst Center MCP

Standalone MCP server for Cisco Catalyst Center auto-generated tools.

This repository intentionally bundles only the generated DNAC tools from
`dialographer-kb/Agent_DNAC/autogen/promoted`. It does not import PyFE at runtime,
does not mount custom tools, and does not delegate generated tool execution to the
Catalyst Center adapter. Tool calls are translated directly into Catalyst Center REST
requests by this server.

## Runtime

Set the Catalyst Center target through environment variables:

```bash
export CATALYST_CENTER_HOST=10.10.10.10
export CATALYST_CENTER_USERNAME=admin
export CATALYST_CENTER_PASSWORD='...'
export CATALYST_CENTER_VERIFY_SSL=false
```

Run locally:

```bash
pip install -e '.[test]'
uvicorn catalyst_center_mcp.main:app --host 0.0.0.0 --port 7001
```

The streamable HTTP MCP endpoint is mounted at:

```text
http://localhost:7001/v1/mcp
```

Health endpoints:

```text
GET /v1/health
GET /v1/readiness
```

## Bundling Tools

Tool bundles are exported by the `ci-tools` Jenkins helper from checked-out
`dialographer-kb` and `pyfe` repositories. The runtime repo intentionally only
consumes the exported metadata; it does not own the generation rules.

```bash
python /path/to/ci-tools/jenkinsfiles/scripts/catalyst_mcp_bundle.py \
  --kb-dir /path/to/dialographer-kb \
  --pyfe-dir /path/to/pyfe \
  --platform DNAC \
  --release 2.3.7.9 \
  --output catalyst_center_mcp/bundled_tools
```

Validate the resulting bundle:

```bash
python scripts/validate_bundle.py catalyst_center_mcp/bundled_tools/manifest.json
```

Supported version metadata keys include `min_controller_version`,
`max_controller_version`, camelCase variants, and `supportedVersions.min/max`.
The manifest records the ci-tools, PyFE, and dialographer-kb commits used to
produce the bundle.

## Docker

```bash
docker build -t catalyst-center-mcp:local .
docker run --rm -p 7001:7001 \
  -e CATALYST_CENTER_HOST \
  -e CATALYST_CENTER_USERNAME \
  -e CATALYST_CENTER_PASSWORD \
  -e CATALYST_CENTER_VERIFY_SSL=false \
  catalyst-center-mcp:local
```
