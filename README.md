# Catalyst Center MCP Server

Connect an MCP-compatible AI client to your Cisco Catalyst Center instance. This
standalone server exposes the APIs in its bundled Catalyst Center tool catalog
over a local, streamable HTTP [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
endpoint.

Use it to let an AI client retrieve and analyze Catalyst Center data, such as
inventory, device health, wireless experience, software, and compliance
information, without building a custom integration for each API.

## What Is MCP?

MCP is an open standard that lets AI clients discover and call structured tools
at runtime. In this integration, the client chooses a Catalyst Center tool,
supplies its parameters, and the server authenticates to Catalyst Center and
returns the API result. The client can then sequence multiple tools to answer a
broader operational question.

This server exposes a versioned bundle of generated Catalyst Center API tools, aligned with the Catalyst Center release and its API operations.

## Before You Start

Select the release branch that matches your Catalyst Center version before
building or running the server:

```bash
git clone https://github.com/cisco-en-programmability/catc-mcp-oss
cd catc-mcp-oss
git checkout release/<M.N.P.Q>
```

You need:

- Network access from the server host to your Catalyst Center instance
- A Catalyst Center username and password
- Docker
- An MCP-compatible client, such as Claude Desktop, Cursor, VS Code, or Codex

### Use a Dedicated, Least-Privilege Account

The server authenticates to Catalyst Center with the configured username and
password and executes tools with that account's permissions. It does not add an
authorization layer or enforce read-only access. The bundled catalog includes
generated API operations and may include operations that change configuration.

Create a dedicated Catalyst Center account with the minimum permissions needed
for the tasks you intend to perform. Treat every client connected to this server
as able to request any bundled operation that account is allowed to execute.

Keep the MCP endpoint private. The examples bind it to `127.0.0.1`; do not
expose it on an untrusted network without adding appropriate network controls
and authentication in front of it.

## Quick Start

From a clone of this repository, configure the target controller and account:

```bash
export CATALYST_CENTER_HOST="https://catalyst-center.example.com"
export CATALYST_CENTER_USERNAME="mcp-service-account"
export CATALYST_CENTER_PASSWORD="replace-with-a-password"
export CATALYST_CENTER_VERIFY_SSL=false
```

`CATALYST_CENTER_HOST` may be a hostname, IP address, or URL. When no scheme is
provided, the server uses `https://`.

Build the image and start the server on the local loopback interface:

```bash
docker build -t catalyst-center-mcp:local .
docker run --rm -p 127.0.0.1:7001:7001 \
  -e CATALYST_CENTER_HOST \
  -e CATALYST_CENTER_USERNAME \
  -e CATALYST_CENTER_PASSWORD \
  -e CATALYST_CENTER_VERIFY_SSL=false \
  catalyst-center-mcp:local
```

The MCP endpoint is:

```text
http://localhost:7001/v1/mcp
```

In a second terminal, verify the process and required credential configuration:

```bash
curl http://localhost:7001/v1/health
curl http://localhost:7001/v1/readiness
```

`/v1/health` confirms that the server process is running. `/v1/readiness`
validates that the required Catalyst Center configuration is present; it does
not make a Catalyst Center API request.

> **TLS note:** Keep `CATALYST_CENTER_VERIFY_SSL=true` for controllers with a
> trusted certificate. Set it to `false` only when you understand and accept
> the risk of bypassing certificate validation, such as a lab controller with a
> self-signed certificate.

## Runtime Modes

The examples below use the Docker image built in Quick Start.

### HTTP(S)

The Quick Start command runs the streamable HTTP endpoint on the local loopback
interface:

```text
http://localhost:7001/v1/mcp
```

Use plain HTTP for local testing or when TLS is terminated by external
infrastructure. HTTPS is recommended when exposing the MCP server beyond the
local machine. For enterprise deployments, prefer terminating TLS outside this
container using the organization's standard ingress, reverse proxy, service
mesh, API gateway, or load balancer. Use centrally managed certificates,
rotation, policy enforcement, and audit controls there, while keeping this
container on its default internal HTTP listener unless direct TLS termination in
the container is explicitly required.

For direct container TLS termination, mount the certificate and key read-only and
pass Uvicorn SSL options:

```bash
docker run --rm -p 127.0.0.1:7001:7001 \
  -v "$PWD/certs:/certs:ro" \
  -e CATALYST_CENTER_HOST \
  -e CATALYST_CENTER_USERNAME \
  -e CATALYST_CENTER_PASSWORD \
  -e CATALYST_CENTER_VERIFY_SSL=false \
  catalyst-center-mcp:local \
  python3 -m uvicorn catalyst_center_mcp.main:app \
    --host 0.0.0.0 \
    --port 7001 \
    --ssl-keyfile /certs/localhost-key.pem \
    --ssl-certfile /certs/localhost-cert.pem
```

The direct HTTPS endpoint is:

```text
https://localhost:7001/v1/mcp
```

#### Generating SSL Certificates

For local development or test environments, you can generate a self-signed
certificate with OpenSSL:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/localhost-key.pem \
  -out certs/localhost-cert.pem \
  -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

This creates the certificate and key expected by the direct HTTPS Docker example:

```text
certs/localhost-cert.pem
certs/localhost-key.pem
```

Use enterprise-managed certificates for shared, production, or externally
reachable deployments.

### STDIO

Use STDIO when your MCP client launches and communicates with the server as a
child process instead of connecting to an already-running HTTP server:

```bash
docker run --rm -i \
  -e CATALYST_CENTER_HOST \
  -e CATALYST_CENTER_USERNAME \
  -e CATALYST_CENTER_PASSWORD \
  -e CATALYST_CENTER_VERIFY_SSL \
  catalyst-center-mcp:local \
  fastmcp run catalyst_center_mcp/main.py:mcp --transport stdio
```

Use `-i` so stdin remains attached. Do not publish ports for STDIO mode.

## Connect an MCP Client

Start the server first, then add `http://localhost:7001/v1/mcp` as an HTTP MCP
server in your client. The local server does not require an inbound header; it
authenticates to Catalyst Center with the environment variables above.

### Claude Desktop

Add this server to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "catalyst-center": {
      "url": "http://localhost:7001/v1/mcp"
    }
  }
}
```

For STDIO access, add this server to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "catalyst-center": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "CATALYST_CENTER_HOST",
        "-e", "CATALYST_CENTER_USERNAME",
        "-e", "CATALYST_CENTER_PASSWORD",
        "-e", "CATALYST_CENTER_VERIFY_SSL",
        "catalyst-center-mcp:local",
        "fastmcp",
        "run",
        "catalyst_center_mcp/main.py:mcp",
        "--transport",
        "stdio"
      ],
      "env": {
        "CATALYST_CENTER_HOST": "https://catalyst-center.example.com",
        "CATALYST_CENTER_USERNAME": "mcp-service-account",
        "CATALYST_CENTER_PASSWORD": "replace-with-a-password",
        "CATALYST_CENTER_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Cursor

Add this server to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "catalyst-center": {
      "url": "http://localhost:7001/v1/mcp"
    }
  }
}
```

For STDIO access, use:

```json
{
  "mcpServers": {
    "catalyst-center": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "CATALYST_CENTER_HOST",
        "-e", "CATALYST_CENTER_USERNAME",
        "-e", "CATALYST_CENTER_PASSWORD",
        "-e", "CATALYST_CENTER_VERIFY_SSL",
        "catalyst-center-mcp:local",
        "fastmcp",
        "run",
        "catalyst_center_mcp/main.py:mcp",
        "--transport",
        "stdio"
      ],
      "env": {
        "CATALYST_CENTER_HOST": "https://catalyst-center.example.com",
        "CATALYST_CENTER_USERNAME": "mcp-service-account",
        "CATALYST_CENTER_PASSWORD": "replace-with-a-password",
        "CATALYST_CENTER_VERIFY_SSL": "false"
      }
    }
  }
}
```

### VS Code

Add this server to `.vscode/mcp.json`:

```json
{
  "servers": {
    "catalyst-center": {
      "type": "http",
      "url": "http://localhost:7001/v1/mcp"
    }
  }
}
```

For STDIO access, use:

```json
{
  "servers": {
    "catalyst-center": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "CATALYST_CENTER_HOST",
        "-e", "CATALYST_CENTER_USERNAME",
        "-e", "CATALYST_CENTER_PASSWORD",
        "-e", "CATALYST_CENTER_VERIFY_SSL",
        "catalyst-center-mcp:local",
        "fastmcp",
        "run",
        "catalyst_center_mcp/main.py:mcp",
        "--transport",
        "stdio"
      ],
      "env": {
        "CATALYST_CENTER_HOST": "https://catalyst-center.example.com",
        "CATALYST_CENTER_USERNAME": "mcp-service-account",
        "CATALYST_CENTER_PASSWORD": "replace-with-a-password",
        "CATALYST_CENTER_VERIFY_SSL": "false"
      }
    }
  }
}
```

### Codex

Add this server to `~/.codex/config.toml`:

```toml
[mcp_servers.catalyst_center]
url = "http://localhost:7001/v1/mcp"
```

For STDIO access, use:

```toml
[mcp_servers.catalyst_center]
command = "docker"
args = [
  "run",
  "--rm",
  "-i",
  "-e", "CATALYST_CENTER_HOST",
  "-e", "CATALYST_CENTER_USERNAME",
  "-e", "CATALYST_CENTER_PASSWORD",
  "-e", "CATALYST_CENTER_VERIFY_SSL",
  "catalyst-center-mcp:local",
  "fastmcp",
  "run",
  "catalyst_center_mcp/main.py:mcp",
  "--transport",
  "stdio",
]

[mcp_servers.catalyst_center.env]
CATALYST_CENTER_HOST = "https://catalyst-center.example.com"
CATALYST_CENTER_USERNAME = "mcp-service-account"
CATALYST_CENTER_PASSWORD = "replace-with-a-password"
CATALYST_CENTER_VERIFY_SSL = "false"
```

## Example Use Cases

The examples below tell the client the outcome you need. It will select the
generated Catalyst Center tools and sequence calls as needed. The exact tools
available depend on the checked-in bundle.

### Inventory and Device Health Review

> "Summarize device inventory and health for the Global/San Jose site. Identify
> devices with POOR health, group them by device role, and show the highest
> priority issues to investigate first. Include the device name, management IP,
> and health category."

The client can resolve the site, retrieve device-health data, then use device
details to make the results actionable.

### Wireless Client Experience Investigation

> "Investigate wireless client experience at the HQ building over the last 24
> hours. Identify the access points, SSIDs, or clients with the most degraded
> experience, explain the apparent pattern from the available data, and list
> the next checks an engineer should perform."

The client can first resolve the site and then retrieve the appropriate
wireless, client, and health records for the requested time range.

### Software and Compliance Review

> "Review the network for software and compliance risk. List devices with
> compliance issues, relevant field notices or security advisories, and their
> current software details. Prioritize the findings by likely operational
> impact. Do not make any changes."

Explicitly state the intended safety boundary in prompts. The client can use
read-oriented tools to gather the evidence, but the server does not prevent it
from selecting a bundled operation that the configured account can execute.

## Policies and Support

- [LICENSE](License.md) contains more information about the Apache 2.0 license
  under which this software is distributed.
- [NOTICE](NOTICE.md) describes the Cisco Catalyst Center and API terms that
  apply when this software communicates with Catalyst Center. Those terms are
  separate from the open-source license governing this code.
- [SECURITY](SECURITY.md) explains how to report a security issue privately.
- [CONTRIBUTING](CONTRIBUTING.md) describes the project's issue and contribution
  policy.
foo
