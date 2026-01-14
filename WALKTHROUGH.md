# QGIS MCP Walkthrough & Use Cases

This guide demonstrates how to leverage the QGIS MCP integration for various workflows, from data analysis to automated software testing.

## Use Case 1: Exploratory Data Analysis

**Goal**: Load data, inspect it, perform analysis, and visualize the result.

**Prompt for Agent**:
> "I have a shapefile at `/data/cities.shp`. Please load it into QGIS. Tell me how many cities are in the dataset. Then, create a 10km buffer around each city and save the result to `/data/city_buffers.shp`. Finally, export a map image of the result."

**Agent Actions**:
1.  `add_vector_layer(path="/data/cities.shp", name="Cities")`
2.  `read_vector_layer_features(layer_id="...", limit=0)` -> Returns feature count.
3.  `run_processing_algorithm(algorithm="native:buffer", parameters={"INPUT": "...", "DISTANCE": 10000, "OUTPUT": "/data/city_buffers.shp"})`
4.  `add_vector_layer(path="/data/city_buffers.shp", name="Buffers")`
5.  `export_map_view_to_image(path="/data/map_output.png")`

## Use Case 2: Automated Plugin Testing (Headless)

**Goal**: You are developing a QGIS plugin and want to verify it works using an autonomous agent in a CI environment.

**Prompt for Agent**:
> "I have a plugin in the folder `./my_plugin`. Install it and run the test suite defined in `./tests/test_plugin.py`."

**Agent Actions**:
1.  `install_qgis_plugin_from_directory(path="/abs/path/to/my_plugin")`
    - The server copies the plugin to the QGIS profile and attempts to reload it.
2.  `run_python_unit_tests(path="/abs/path/to/tests/test_plugin.py")`
    - The server executes the tests using `unittest`.
    - It returns a JSON object: `{ "passed": 5, "failed": 0, ... }`.
3.  **Validation**: The agent checks if `failed == 0`. If not, it can read the failure messages and attempt to fix the code (if it has access to source files via other MCP tools).

## Use Case 3: Processing Script Development

**Goal**: Create and deploy a custom Processing algorithm script.

**Prompt for Agent**:
> "Write a QGIS Processing script that calculates the centroid of a layer and adds a 'calculated_at' timestamp field. Install this script and verify it is available."

**Agent Actions**:
1.  **Write Code**: The agent generates the python script content (implementing `QgsProcessingAlgorithm`).
2.  **Save File**: The agent saves it to a temporary location (e.g., via standard filesystem MCP or `execute_arbitrary_python_code` to write file).
3.  `install_processing_script_from_file(path="/tmp/my_algorithm.py")`
    - Copies script to QGIS Processing scripts folder.
    - Refreshes the provider.
4.  `list_installed_processing_scripts()`
    - Verifies `my_algorithm.py` is in the list.
5.  `run_processing_algorithm(algorithm="script:myalgorithm", ...)`
    - Executes the newly created script to verify functionality.

## Guide: Setting up Headless Mode

For automated testing without a display (e.g., Docker, GitHub Actions):

1.  **Install Dependencies**:
    ```bash
    apt-get install qgis python3-qgis
    pip install mcp
    ```

2.  **Configure Environment**:
    ```bash
    export QT_QPA_PLATFORM=offscreen
    # Ensure python finds QGIS
    export PYTHONPATH=/usr/lib/python3/dist-packages
    ```

3.  **Run the Server**:
    Use a runner script (like `tests/audit_qgis_server.py`) that initializes `QgsApplication` with `GUIenabled=False` (or relies on `offscreen` platform) and starts `QgisMCPServer`.

    ```python
    from qgis.core import QgsApplication
    from qgis_mcp_plugin import QgisMCPServer

    qgs = QgsApplication([], False)
    qgs.initQgis()

    server = QgisMCPServer(iface=None) # iface=None signals headless mode
    server.start()

    qgs.exec_()
    ```
