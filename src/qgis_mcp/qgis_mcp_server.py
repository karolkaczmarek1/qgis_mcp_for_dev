#!/usr/bin/env python3
"""
QGIS MCP Client - Simple client to connect to the QGIS MCP server
"""

import logging
from contextlib import asynccontextmanager
import socket
import json
from typing import AsyncIterator, Dict, Any
from mcp.server.fastmcp import FastMCP, Context

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QgisMCPServer")

class QgisMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        """Connect to the QGIS MCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            logger.error(f"Error connecting to server: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def send_command(self, command_type, params=None):
        """Send a command to the server and get the response"""
        if not self.socket:
            logger.error("Not connected to server")
            return None
        
        # Create command
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            # Send the command
            self.socket.sendall(json.dumps(command).encode('utf-8'))
            
            # Receive the response
            response_data = b''
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                # Try to decode as JSON to see if it's complete
                try:
                    json.loads(response_data.decode('utf-8'))
                    break  # Valid JSON, we have the full message
                except json.JSONDecodeError:
                    continue  # Keep receiving
            
            # Parse and return the response
            return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            return None

_qgis_connection = None

def get_qgis_connection():
    """Get or create a persistent Qgis connection"""
    global _qgis_connection
    
    # If we have an existing connection, check if it's still valid
    if _qgis_connection is not None:
        # Test if the connection is still alive with a simple ping
        try:
            # Just try to send a small message to check if the socket is still connected
            _qgis_connection.sock.sendall(b'')
            return _qgis_connection
        except Exception as e:
            # Connection is dead, close it and create a new one
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _qgis_connection.disconnect()
            except Exception:
                pass
            _qgis_connection = None
    
    # Create a new connection if needed
    if _qgis_connection is None:
        _qgis_connection = QgisMCPServer(host="localhost", port=9876)
        if not _qgis_connection.connect():
            logger.error("Failed to connect to Qgis")
            _qgis_connection = None
            raise Exception("Could not connect to Qgis. Make sure the Qgis plugin is running.")
        logger.info("Created new persistent connection to Qgis")
    
    return _qgis_connection

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    try:
        logger.info("QgisMCPServer server starting up")
        try:
            get_qgis_connection()
            logger.info("Successfully connected to Qgis on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Qgis on startup: {str(e)}")
            logger.warning("Make sure the Qgis addon is running before using Qgis resources or tools")
        yield {}
    finally:
        global _qgis_connection
        if _qgis_connection:
            logger.info("Disconnecting from Qgis on shutdown")
            _qgis_connection.disconnect()
            _qgis_connection = None
        logger.info("QgisMCPServer server shut down")

mcp = FastMCP(
    "Qgis_mcp",
    description="Qgis integration through the Model Context Protocol",
    lifespan=server_lifespan
)

@mcp.tool()
def check_server_connection(ctx: Context) -> str:
    """
    Check if the MCP server is successfully connected to the QGIS plugin.
    Returns a simple 'pong' response if connected.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("ping")
    return json.dumps(result, indent=2)

@mcp.tool()
def get_qgis_installation_info(ctx: Context) -> str:
    """
    Retrieve information about the QGIS installation, including version and profile paths.
    Use this to verify the QGIS environment details.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("get_qgis_info")
    return json.dumps(result, indent=2)

@mcp.tool()
def open_qgis_project(ctx: Context, path: str) -> str:
    """
    Load a QGIS project file (.qgz or .qgs) from the specified disk path.
    This will replace the currently open project.

    Args:
        path: Absolute path to the project file.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("load_project", {"path": path})
    return json.dumps(result, indent=2)

@mcp.tool()
def create_new_qgis_project(ctx: Context, path: str) -> str:
    """
    Create a new, empty QGIS project and save it to the specified path.
    This clears the current project state.

    Args:
        path: Absolute path where the new project file will be saved.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("create_new_project", {"path": path})
    return json.dumps(result, indent=2)

@mcp.tool()
def get_current_project_metadata(ctx: Context) -> str:
    """
    Get metadata about the currently open QGIS project, including title, file path, CRS, and a list of layers.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("get_project_info")
    return json.dumps(result, indent=2)

@mcp.tool()
def add_vector_layer(ctx: Context, path: str, provider: str = "ogr", name: str = None) -> str:
    """
    Add a vector layer (Shapefile, GeoJSON, etc.) to the current project.

    Args:
        path: Path to the vector file.
        provider: Data provider (default: 'ogr').
        name: Display name for the layer (optional).
    """
    qgis = get_qgis_connection()
    params = {"path": path, "provider": provider}
    if name:
        params["name"] = name
    result = qgis.send_command("add_vector_layer", params)
    return json.dumps(result, indent=2)

@mcp.tool()
def add_raster_layer(ctx: Context, path: str, provider: str = "gdal", name: str = None) -> str:
    """
    Add a raster layer (GeoTIFF, etc.) to the current project.

    Args:
        path: Path to the raster file.
        provider: Data provider (default: 'gdal').
        name: Display name for the layer (optional).
    """
    qgis = get_qgis_connection()
    params = {"path": path, "provider": provider}
    if name:
        params["name"] = name
    result = qgis.send_command("add_raster_layer", params)
    return json.dumps(result, indent=2)

@mcp.tool()
def list_project_layers(ctx: Context) -> str:
    """
    List all layers currently loaded in the QGIS project with their IDs, names, and types.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("get_layers")
    return json.dumps(result, indent=2)

@mcp.tool()
def remove_layer_from_project(ctx: Context, layer_id: str) -> str:
    """
    Remove a specific layer from the project.

    Args:
        layer_id: The unique ID of the layer to remove (obtained from list_project_layers).
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("remove_layer", {"layer_id": layer_id})
    return json.dumps(result, indent=2)

@mcp.tool()
def zoom_map_to_layer(ctx: Context, layer_id: str) -> str:
    """
    Zoom the map canvas to the extent of a specific layer.
    Note: This may have no effect in headless mode if the GUI is not active.

    Args:
        layer_id: The unique ID of the layer.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("zoom_to_layer", {"layer_id": layer_id})
    return json.dumps(result, indent=2)

@mcp.tool()
def read_vector_layer_features(ctx: Context, layer_id: str, limit: int = 10) -> str:
    """
    Retrieve attributes and geometry for features in a vector layer.

    Args:
        layer_id: The unique ID of the layer.
        limit: Maximum number of features to return (default: 10).
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("get_layer_features", {"layer_id": layer_id, "limit": limit})
    return json.dumps(result, indent=2)

@mcp.tool()
def run_processing_algorithm(ctx: Context, algorithm: str, parameters: dict) -> str:
    """
    Execute a QGIS Processing algorithm.

    Args:
        algorithm: The algorithm ID (e.g., 'native:buffer').
        parameters: A dictionary of algorithm parameters.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("execute_processing", {"algorithm": algorithm, "parameters": parameters})
    return json.dumps(result, indent=2)

@mcp.tool()
def save_project(ctx: Context, path: str = None) -> str:
    """
    Save the current QGIS project to disk.

    Args:
        path: Optional path to save to. If omitted, saves to the current project path.
    """
    qgis = get_qgis_connection()
    params = {}
    if path:
        params["path"] = path
    result = qgis.send_command("save_project", params)
    return json.dumps(result, indent=2)

@mcp.tool()
def export_map_view_to_image(ctx: Context, path: str, width: int = 800, height: int = 600) -> str:
    """
    Render the current map view to an image file.
    In headless mode, this uses the combined extent of all layers.

    Args:
        path: Output path for the image (e.g., /tmp/map.png).
        width: Image width in pixels.
        height: Image height in pixels.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("render_map", {"path": path, "width": width, "height": height})
    return json.dumps(result, indent=2)

@mcp.tool()
def execute_arbitrary_python_code(ctx: Context, code: str) -> str:
    """
    DANGER: Execute arbitrary Python code within the QGIS process.

    Use this tool to run PyQGIS scripts, manipulate the QGIS API directly, or perform actions not covered by other tools.
    The code runs in a namespace with 'qgis', 'QgsProject', 'iface', etc. available.

    Args:
        code: The Python code string to execute.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("execute_code", {"code": code})
    return json.dumps(result, indent=2)

@mcp.tool()
def run_python_unit_tests(ctx: Context, code: str = None, path: str = None) -> str:
    """
    Run Python unittest suite within the QGIS environment.

    Use this to verify plugin logic or scripts. Returns structured results including pass/fail counts and failure messages.

    Args:
        code: A string containing the full python test suite (imports, TestCase classes).
        path: Absolute path to a python test file.
    """
    qgis = get_qgis_connection()
    params = {}
    if code: params["code"] = code
    if path: params["path"] = path
    result = qgis.send_command("run_test", params)
    return json.dumps(result, indent=2)

@mcp.tool()
def install_qgis_plugin_from_directory(ctx: Context, path: str) -> str:
    """
    Install a QGIS plugin from a local directory.

    Copies the directory to the QGIS plugins folder and attempts to reload/activate it.
    Useful for testing plugins during development.

    Args:
        path: Absolute path to the plugin directory (containing metadata.txt).
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("install_plugin", {"path": path})
    return json.dumps(result, indent=2)

@mcp.tool()
def reload_qgis_plugin(ctx: Context, plugin_name: str) -> str:
    """
    Reload or Activate a QGIS plugin by name.

    If the plugin is already active, it reloads it (useful for development).
    If it is not active, it attempts to load and start it.

    Args:
        plugin_name: The folder name of the plugin (e.g. 'my_plugin').
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("reload_plugin", {"name": plugin_name})
    return json.dumps(result, indent=2)

@mcp.tool()
def install_processing_script_from_file(ctx: Context, path: str) -> str:
    """
    Install a single Python Processing script.

    Copies the file to the QGIS Processing scripts folder and refreshes the Processing provider.

    Args:
        path: Absolute path to the python script file.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("install_processing_script", {"path": path})
    return json.dumps(result, indent=2)

@mcp.tool()
def list_installed_processing_scripts(ctx: Context) -> str:
    """
    List all user-installed Processing scripts.
    Returns a list of filenames found in the Processing scripts directory.
    """
    qgis = get_qgis_connection()
    result = qgis.send_command("list_processing_scripts")
    return json.dumps(result, indent=2)

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
