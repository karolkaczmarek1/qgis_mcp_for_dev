# AGENTS.md

Instructions for AI coding agents (Antigravity CLI, Claude Code, and others) working in this repository.

## Architecture

Two processes talk over a local TCP socket:

1. **QGIS plugin** (`qgis_mcp_plugin/qgis_mcp_plugin.py`) runs inside QGIS and listens on `localhost:9876`.
   - A `QTimer` (100 ms) polls non-blocking sockets. Every command runs synchronously on the Qt GUI thread, so a slow command blocks QGIS and all other clients until it finishes.
   - Multiple clients may be connected at once (e.g. Claude Code and Antigravity). Each has its own receive buffer, commands are executed one at a time, and all clients share the single `QgsProject`.
   - Commands are dispatched through the `handlers` dict in `execute_command`.
2. **MCP server** (`src/qgis_mcp/qgis_mcp_server.py`) is a FastMCP server over **stdio**. Each `@mcp.tool()` forwards one command to the plugin via `send_command`, keeping one persistent socket per MCP server process.

Wire protocol: one UTF-8 JSON object per request (`{"type", "params", "token"?}`) and per response (`{"status": "success"|"error", ...}`). There is no framing: a message is complete when the buffer parses as JSON. Keep it strictly request/response.

`src/qgis_mcp/qgis_socket_client.py` is a standalone demo client and is not used by the MCP server.

## Adding or changing a tool

1. Add a handler method to the plugin and register it in the `handlers` dict in `execute_command`.
2. Add a matching `@mcp.tool()` in `qgis_mcp_server.py` that calls `send_command("<type>", params)`. Write the docstring for the LLM: it becomes the tool description.
3. Update the tool list in `README.md`.

## Rules

- **Never write to stdout in the MCP server.** stdout is the stdio JSON-RPC channel. Use `logger` (stderr).
- `mcp` is pinned to `>=1.22.0,<2`. Older 1.x servers never finish the MCP handshake with Antigravity CLI, and 2.x renamed `FastMCP` to `MCPServer`. `FastMCP` takes `instructions=`, not `description=`.
- Plugin handlers run inside the user's QGIS: avoid long blocking work and never let exceptions escape `process_server`.
- `execute_arbitrary_python_code` runs arbitrary code with the user's permissions. The socket is unauthenticated unless `QGIS_MCP_TOKEN` is set for both QGIS and the MCP server.
- File-writing handlers create missing parent directories via `_ensure_parent_dir`; do the same in new ones.

## Environment variables

| Variable | Read by | Meaning |
|---|---|---|
| `QGIS_MCP_TOKEN` | plugin + MCP server | Optional shared secret; when set in QGIS, commands without a matching token are rejected. |
| `QGIS_MCP_TIMEOUT` | MCP server | Seconds to wait for a QGIS response (default `600`). On timeout the connection is dropped. |

## Running

- Install dependencies: `uv sync`
- MCP server: `uv run --directory src/qgis_mcp qgis_mcp_server.py` (needs the plugin server running in QGIS)
- Plugin: copy `qgis_mcp_plugin/` into the QGIS profile `python/plugins` folder, enable "QGIS MCP", click "Start Server" (or enable auto-start). After editing plugin code, reload the plugin or restart QGIS.

## Registering the MCP server

- **Claude Code**: `.mcp.json` in the repo root registers the `qgis` server for this project.
- **Antigravity CLI**: `agy mcp add qgis -- uv --directory <ABSOLUTE_REPO_PATH>/src/qgis_mcp run qgis_mcp_server.py` (the `--` is required because the arguments start with `-`) (stored in `~/.gemini/config/mcp_config.json`). Check with `agy mcp list`.
- **Claude Desktop**: see `README.md`.

## Testing

There is no automated test suite. `tests/audit_qgis_server.py` and `tests/audit_client.py` are manual scripts.

- Headless QGIS: set `QT_QPA_PLATFORM=offscreen` and run with QGIS's Python. On Windows: `"C:\Program Files\QGIS <version>\bin\python-qgis-ltr.bat" tests\audit_qgis_server.py`.
- Only one process can listen on port 9876. Stop the plugin server in a running QGIS before starting a headless one.
- After changing the protocol, test both a Claude Code and an Antigravity session against the same QGIS.
