# QGIS MCP Server Audit for Test Automation

## Overview

This audit evaluates the QGIS MCP Server's capability to serve as a test automation backend for a coding agent. The goal is to allow an AI agent to generate QGIS scripts/plugins and autonomously verify them using this server.

## Findings

### 1. Headless Execution Environment
- **Current State**: The plugin is designed to run within the QGIS Desktop GUI application. It relies on `iface` (QgisInterface) for several operations (`mapCanvas`, `zoomToActiveLayer`).
- **Issue**: Standard autonomous testing (CI/CD) often runs in a headless environment (no display).
- **Result**: Testing confirmed that the server **can** run in a headless environment by:
    1. Setting `QT_QPA_PLATFORM=offscreen` environment variable.
    2. Mocking the `iface` object in the startup script, as the real `QgisInterface` is unavailable outside the QGIS GUI.
- **Impact**: Without modifications or a specialized runner script, the plugin will fail to start or crash when GUI methods are called in a headless context.

### 2. Code Execution (`execute_code`)
- **Capabilities**: The `execute_code` tool successfully captures `stdout` and `stderr`. It catches `SyntaxError` and runtime `Exception` and returns them as structured JSON.
- **Test Frameworks**: It is possible to run `unittest` suites via `execute_code`, provided the code block explicitly imports `sys` and directs the runner output to `sys.stdout`.
- **Limitations**:
    - The agent must write boilerplate code to set up the test runner.
    - The output is unstructured text (string). The agent must parse "OK" or "FAILED" from `stdout`.
    - `sys` module must be imported explicitly in the code block for `sys.stdout` to work, even though the environment captures it.

### 3. State Management
- **Persistence**: The server process stays alive between commands. Variables defined in `execute_code` (in the local namespace) do not persist between calls (a new namespace is created for each call), but changes to the QGIS Project (layers, settings) **do** persist.
- **Reset**: `create_new_project` effectively clears the project state (layers), acting as a "reset" for tests that need a clean slate.

### 4. Dependencies
- **System**: Requires `qgis` python bindings (`apt install qgis`).
- **Python**: Requires `PYTHONPATH` to be set correctly if using a virtual environment that doesn't inherit system site-packages.

## Recommendations

### Critical Fixes for Automation
1.  **Headless Support**:
    - Update documentation to recommend `QT_QPA_PLATFORM=offscreen`.
    - Modify `QgisMCPServer` to gracefully handle `iface=None`. Methods that require GUI (like `zoom_to_layer`) should log a warning or no-op in headless mode instead of crashing.
2.  **Structured Test Runner**:
    - Add a new tool `run_test(code: str) -> JSON` or `run_test_file(path: str) -> JSON`.
    - This tool should run the tests and return a JSON object: `{ "passed": 5, "failed": 1, "failures": [...] }`.
    - This removes the burden of parsing text output from the agent.

### New Functionalities
1.  **`reset_session`**: A tool to clear not just the project, but potentially reset other global QGIS settings or caches to ensure test isolation.
2.  **`install_plugin` / `load_plugin`**: Tools to programmatically install and activate a plugin from a local path. This is essential if the agent is developing a plugin (folder) and wants to test it inside QGIS.

## Conclusion

The QGIS MCP Server is a viable tool for test automation but requires a specialized setup (headless configuration) and would benefit significantly from dedicated test-running tools to simplify the agent's workflow.
