# QGIS MCP Server Audit Report

## Executive Summary
The QGIS MCP Server architecture consists of a Python-based MCP Server (client) and a QGIS Plugin (socket server). This audit focused on reliability, specifically addressing the "invalid trailing data" error reported during initialization in Google Antigravity.

## Key Findings

### 1. Protocol Violation (Fixed)
**Severity:** Critical
**Issue:** The `QgisMCPServer` class in `src/qgis_mcp/qgis_mcp_server.py` used `print()` statements to log connection errors. In the MCP protocol, `stdout` is reserved exclusively for JSON-RPC messages. Any text printed to `stdout` causes parsing errors in the MCP client.
**Resolution:** Replaced all `print()` statements with `logging.error()` or `logging.info()`. The logging configuration defaults to `stderr`, which is safe for MCP.

### 2. Socket Message Framing
**Severity:** High
**Issue:** The socket communication between the MCP server and the QGIS plugin relies on basic `socket.recv()` and `json.loads()`.
- **In Plugin (`qgis_mcp_plugin.py`):** It appends received data to a buffer and attempts to parse it. If multiple JSON commands are received in a single TCP chunk (which can happen with fast consecutive commands), `json.loads()` will fail because it does not support concatenated JSON objects (e.g., `}{`). The buffer might effectively get stuck or discard data.
- **In Server (`qgis_mcp_server.py`):** It reads until `json.loads()` succeeds. This is slightly more robust for a single response but fragile if the server sends fragmented or multiple responses.
**Recommendation:** Implement explicit message framing (e.g., Newline Delimited JSON or a length-prefix header) to ensure reliable stream processing.

### 3. Error Handling and Reliability
**Severity:** Medium
**Issue:**
- Connection establishment is checked once at startup. If the QGIS plugin is restarted, the persistent connection in the MCP server usually recovers via `get_qgis_connection` logic, but this relies on the socket appearing "dead".
- `execute_arbitrary_python_code` correctly captures stdout/stderr, which is excellent for remote execution.

### 4. Test Automation Capabilities
**Severity:** Medium (Feature Gaps)
**Observations:**
- **Visual Verification:** `export_map_view_to_image` saves the image to the filesystem where QGIS is running. If the MCP client (agent) is remote or containerized differently, it cannot see this image.
    - **Recommendation:** Return the image data as Base64 in the tool response, or ensure a `filesystem` MCP server is available and configured to access the same paths.
- **State Management:** There is no easy way to "reset" QGIS state between tests other than creating a new project.
    - **Recommendation:** Consider adding a `reset_qgis_state` tool that clears layers, resets canvas, and clears python variables if possible.
- **Assertions:** The agent currently needs to write Python code to assert conditions (e.g., `layer.featureCount() == 5`). This is powerful but requires the agent to know PyQGIS API well.
    - **Recommendation:** This is acceptable for an advanced coding agent.

## Verification
- A reproduction script confirmed the fix: the server no longer pollutes `stdout` with error messages.
- An integration test (`tests/test_mcp_connection_success.py`) with a mock QGIS server verified that the MCP server initializes correctly and communicates using valid JSON-RPC.
- A negative test (`tests/test_mcp_connection_failure.py`) verified that connection failures are logged to `stderr` and do not crash the server.

## Next Steps
1.  **Immediate:** Deploy the fix (`print` -> `logging`).
2.  **Short-term:** Implement robust socket framing (NDJSON) in both Plugin and Server to prevent data loss or corruption under load.
3.  **Long-term:** Enhance the test automation toolkit with remote file access (Base64 images) and state reset tools.
