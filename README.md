# QGISMCP - QGIS Model Context Protocol Integration

**This project is a significantly enhanced fork of the original [qgis_mcp](https://github.com/jjsantos01/qgis_mcp) by [jjsantos01](https://github.com/jjsantos01).**

While based on the original concept, this version introduces advanced functionalities, performance improvements, and specialized tools tailored for **developers creating QGIS plugins and PyQGIS scripts**. It transforms QGIS into a fully controllable environment for AI agents, enabling sophisticated automation and rapid development workflows.

QGISMCP connects [QGIS](https://qgis.org/) to AI agents such as [Claude Code](https://claude.com/claude-code), [Antigravity CLI](https://antigravity.google/) and Claude Desktop (or any other MCP client) through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro).

This project is also influenced by the [BlenderMCP](https://github.com/ahujasid/blender-mcp/tree/main) project by [Siddharth Ahuja](https://x.com/sidahuj).

## Features

- **Two-way communication**: Connect AI agents to QGIS through a socket-based server.
- **Multiple agents at once**: Several MCP clients (e.g. Claude Code and Antigravity CLI) can be connected to the same QGIS at the same time.
- **Project manipulation**: Create, open, and save projects.
- **Layer manipulation**: Add/remove vector and raster layers, inspect features.
- **Processing Framework**: Execute any QGIS Processing algorithm from the toolbox.
- **Code Execution**: Run arbitrary PyQGIS code for unlimited flexibility.
- **Advanced Plugin Management**: Install, activate, and hot-reload QGIS plugins directly through AI prompts.
- **Automated Testing & Deployment**: Run unit tests and deploy processing scripts in headless or GUI environments.
- **Persistent Settings**: Auto-start server functionality and remembered UI state.
- **Optional authentication and timeouts** for the local socket (see [Security & Timeouts](#security--timeouts-optional)).

## Components

The system consists of two main components:

1. **[QGIS plugin](qgis_mcp_plugin/)**: A QGIS plugin that runs a socket server inside QGIS (`localhost:9876`) to receive and execute commands.
2. **[MCP Server](src/qgis_mcp/qgis_mcp_server.py)**: A Python server (stdio transport) that implements the Model Context Protocol and forwards tool calls to the QGIS plugin.

## Installation

### Prerequisites

- QGIS 3.x (tested with 3.34)
- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager
- An MCP client: Claude Code, Antigravity CLI, Claude Desktop, ...

Install uv on macOS:
```bash
brew install uv
```

On Windows PowerShell:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or with pip: `pip install uv`.

### Download code and install dependencies

```bash
git clone https://github.com/karolkaczmarek1/qgis_mcp_for_dev.git
cd qgis_mcp_for_dev
uv sync
```

The MCP server requires `mcp>=1.22,<2`. Older `mcp` releases never complete the MCP handshake with Antigravity CLI, and `mcp` 2.x changed the server API.

### QGIS Plugin Setup

1. Copy the folder `qgis_mcp_plugin` to your QGIS profile plugins folder.
   - **Windows**: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
2. Open QGIS.
3. Go to `Plugins` > `Manage and Install Plugins`.
4. Enable "QGIS MCP".
5. **Optional**: Check "Start automatically" in the QGIS MCP dock widget to have the server start when QGIS opens.

## MCP Client Configuration

All clients start the same command: `uv --directory <REPO>/src/qgis_mcp run qgis_mcp_server.py`. Replace `/ABSOLUTE/PATH/TO/REPO` with the path to your clone.

### Claude Code

The repository ships a project-scoped [`.mcp.json`](.mcp.json), so no manual registration is needed:

1. Start `claude` in the repository root.
2. Approve the `qgis` server when Claude Code asks about project MCP servers.
3. Check the connection with `claude mcp get qgis` (status `Connected`) or `/mcp` inside Claude Code. The tools appear as `mcp__qgis__*`.

### Antigravity CLI (`agy`)

Register the server once (it is stored in `~/.gemini/config/mcp_config.json`):

```bash
agy mcp add qgis -- uv --directory /ABSOLUTE/PATH/TO/REPO/qgis_mcp_for_dev/src/qgis_mcp run qgis_mcp_server.py
agy mcp list
```

The `--` is required because the arguments start with `-`.

### Claude Desktop

Go to `Claude` > `Settings` > `Developer` > `Edit Config` > `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "qgis": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/REPO/qgis_mcp_for_dev/src/qgis_mcp",
                "run",
                "qgis_mcp_server.py"
            ]
        }
    }
}
```

### Using several clients at once

Each MCP client starts its own MCP server process, and the QGIS plugin accepts several connections at the same time. Commands run one after another on the QGIS GUI thread, and all clients work on the **same** QGIS project: if one agent opens or creates a project, the others see it too.

### Security & Timeouts (optional)

The plugin listens on `localhost:9876` and can execute arbitrary Python code, so any local process can talk to it. To require a shared secret, set the same `QGIS_MCP_TOKEN` environment variable for **both** QGIS (e.g. a user environment variable, then restart QGIS) and the MCP server:

- **Claude Code / Claude Desktop**: add an `env` block to the server entry:
  ```json
  "env": { "QGIS_MCP_TOKEN": "some-long-random-string", "QGIS_MCP_TIMEOUT": "600" }
  ```
- **Antigravity CLI**: pass `-e` before the server name:
  ```bash
  agy mcp add -e QGIS_MCP_TOKEN=some-long-random-string qgis -- uv --directory /ABSOLUTE/PATH/TO/REPO/qgis_mcp_for_dev/src/qgis_mcp run qgis_mcp_server.py
  ```

`QGIS_MCP_TIMEOUT` (seconds, default `600`) limits how long the MCP server waits for QGIS to answer a command. Commands run on the QGIS GUI thread, so a long `execute_arbitrary_python_code` call still blocks QGIS until it finishes; the timeout only frees the agent.

## Usage

### Starting the Connection

1. In QGIS, go to `Plugins` > `QGIS MCP`.
2. Click "Start Server" (or enable "Start automatically").
3. Start your MCP client and ask it to call `check_server_connection`.

### Available Tools

The server exposes the following tools (descriptively named for LLM clarity):

- **Core & Project**:
    - `check_server_connection`: Ping the server.
    - `get_qgis_installation_info`: Check version/paths.
    - `open_qgis_project`: Load a `.qgz` project.
    - `create_new_qgis_project`: Start a fresh project (missing directories are created).
    - `save_project`: Save current work.
    - `get_current_project_metadata`: Inspect loaded layers/CRS.

- **Layers**:
    - `add_vector_layer`: Add vector data (shapefile, gpkg, etc).
    - `add_raster_layer`: Add raster data (tif, etc).
    - `list_project_layers`: List all layers.
    - `remove_layer_from_project`: Remove a layer.
    - `zoom_map_to_layer`: Zoom extent to layer.
    - `read_vector_layer_features`: Inspect attribute table/geometry.

- **Analysis & Output**:
    - `run_processing_algorithm`: Execute QGIS Processing tools (buffer, clip, etc).
    - `export_map_view_to_image`: Render map canvas to image.

- **Developer & Automation**:
    - `execute_arbitrary_python_code`: **Power Tool** - Execute any PyQGIS script.
    - `run_python_unit_tests`: Run `unittest` suites and get structured JSON results. Edited test files are reloaded on every run.
    - `install_qgis_plugin_from_directory`: Deploy a plugin for testing.
    - `reload_qgis_plugin`: Hot-reload a plugin during development.
    - `install_processing_script_from_file`: Deploy a Processing script.
    - `list_installed_processing_scripts`: List user scripts.

## Headless Usage (Automation/CI)

To run QGIS MCP without the QGIS GUI (e.g. in automated testing pipelines):

1. **Environment variables**:
   ```bash
   export QT_QPA_PLATFORM=offscreen
   export PYTHONPATH=/usr/lib/python3/dist-packages  # Linux: point to the QGIS bindings
   ```
2. **Start the plugin server** with QGIS's Python using [`scripts/headless_qgis_server.py`](scripts/headless_qgis_server.py):
   ```bash
   python3 scripts/headless_qgis_server.py
   ```
   On Windows, use the Python launcher shipped with QGIS:
   ```powershell
   & "C:\Program Files\QGIS <version>\bin\python-qgis-ltr.bat" scripts\headless_qgis_server.py
   ```
   Only one process can listen on port `9876`, so stop the plugin server in a running QGIS first.
3. **Behavior**:
   GUI-dependent tools (like `zoom_map_to_layer`) degrade gracefully (log a warning). `export_map_view_to_image` uses the project's combined extent instead of the canvas extent.

## Working on this repository with AI agents

- [`AGENTS.md`](AGENTS.md) describes the architecture, the socket protocol, how to add tools and how to test. Antigravity CLI reads it automatically.
- [`CLAUDE.md`](CLAUDE.md) imports `AGENTS.md` for Claude Code.

## Walkthrough & Examples

See [WALKTHROUGH.md](WALKTHROUGH.md) for detailed use cases and a step-by-step guide.
