# QGISMCP - QGIS Model Context Protocol Integration

**This project is a significantly enhanced fork of the original [qgis_mcp](https://github.com/jjsantos01/qgis_mcp) by [jjsantos01](https://github.com/jjsantos01).**

While based on the original concept, this version introduces advanced functionalities, performance improvements, and specialized tools tailored for **developers creating QGIS plugins and PyQGIS scripts**. It transforms QGIS into a fully controllable environment for AI agents, enabling sophisticated automation and rapid development workflows.

QGISMCP connects [QGIS](https://qgis.org/) to [Claude AI](https://claude.ai/chat) (or any MCP client) through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro).

This project is also influenced by the [BlenderMCP](https://github.com/ahujasid/blender-mcp/tree/main) project by [Siddharth Ahuja](https://x.com/sidahuj).

## Features

- **Two-way communication**: Connect AI agents to QGIS through a socket-based server.
- **Project manipulation**: Create, open, and save projects.
- **Layer manipulation**: Add/remove vector and raster layers, inspect features.
- **Processing Framework**: Execute any QGIS Processing algorithm from the toolbox.
- **Code Execution**: Run arbitrary PyQGIS code for unlimited flexibility.
- **Advanced Plugin Management**: Install, activate, and hot-reload QGIS plugins directly through AI prompts.
- **Automated Testing & Deployment**: specialized tools to run unit tests and deploy processing scripts in headless or GUI environments.
- **Persistent Settings**: Auto-start server functionality and remembered UI state.

## Components

The system consists of two main components:

1. **[QGIS plugin](/qgis_mcp_plugin/)**: A QGIS plugin that creates a socket server within QGIS to receive and execute commands.
2. **[MCP Server](/src/qgis_mcp/qgis_mcp_server.py)**: A Python server that implements the Model Context Protocol and connects to the QGIS plugin.

## Installation

### Prerequisites

- QGIS 3.X (tested on 3.22+)
- Claude Desktop or other MCP client
- Python 3.10 or newer
- `uv` package manager

If you're on Mac, please install uv as:
```bash
brew install uv
```

On Windows Powershell:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Otherwise see: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)

### Download code

```bash
git clone https://github.com/karolkaczmarek1/qgis_mcp_for_dev.git
```

### QGIS Plugin Setup

1. Copy the folder `qgis_mcp_plugin` to your QGIS profile plugins folder.
   - **Windows**: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
   - **MacOS**: `~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
2. Open QGIS.
3. Go to `Plugins` > `Manage and Install Plugins`.
4. Enable "QGIS MCP".
5. **Optional**: Check "Start automatically" in the QGIS MCP dock widget to have the server start when QGIS opens.

### MCP Client Integration (Claude Desktop)

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

## Usage

### Starting the Connection

1. In QGIS, go to `Plugins` > `QGIS MCP`.
2. Click "Start Server".

### Available Tools

The server exposes the following tools (descriptively named for LLM clarity):

- **Core & Project**:
    - `check_server_connection`: Ping the server.
    - `get_qgis_installation_info`: Check version/paths.
    - `open_qgis_project`: Load a `.qgz` project.
    - `create_new_qgis_project`: Start a fresh project.
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
    - `run_python_unit_tests`: Run `unittest` suites and get structured JSON results.
    - `install_qgis_plugin_from_directory`: Deploy a plugin for testing.
    - `reload_qgis_plugin`: Hot-reload a plugin during development.
    - `install_processing_script_from_file`: Deploy a Processing script.
    - `list_installed_processing_scripts`: List user scripts.

## Headless Usage (Automation/CI)

To run QGIS MCP in a headless environment (e.g., for automated testing pipelines):

1. **Environment Variables**:
   ```bash
   export QT_QPA_PLATFORM=offscreen
   export PYTHONPATH=/usr/lib/python3/dist-packages  # Adjust to point to QGIS bindings
   ```
2. **Mocking/Startup**:
   Use a script that initializes `QgsApplication` and starts the `QgisMCPServer` (see `tests/audit_qgis_server.py` for an example).
3. **Behavior**:
   GUI-dependent tools (like `zoom_map_to_layer`) will degrade gracefully (log a warning). `export_map_view_to_image` will use the project's combined extent instead of the canvas extent.

## Walkthrough & Examples

See [WALKTHROUGH.md](WALKTHROUGH.md) for detailed use cases and a step-by-step guide.
