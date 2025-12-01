#!/usr/bin/env python3
import sys
import os
import signal
import socket
import json

# Add qgis_mcp_plugin to path
plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'qgis_mcp_plugin'))
sys.path.append(plugin_path)

# Mock qgis.gui if it fails to import (common in headless)
# But we need qgis.core
try:
    from qgis.core import *
    from qgis.PyQt.QtCore import QObject, QTimer, QSize
    from qgis.PyQt.QtWidgets import QApplication
    # Try to import QgsMapCanvas but don't fail yet if it's missing,
    # though the plugin imports it.
except ImportError:
    print("Failed to import QGIS bindings. Make sure PYTHONPATH is set.")
    sys.exit(1)

# Initialize QgsApplication
# We use platformName="offscreen" if possible, or just regular.
# For pure headless without xvfb, we use GUIenabled=False.
# But the plugin imports qgis.gui which might require GUIenabled=True or fail.
# Let's try GUIenabled=False first.
qgs = QgsApplication([], False)
qgs.initQgis()

print("QGIS Initialized")

# Now import the plugin class
try:
    from qgis_mcp_plugin import QgisMCPServer
except ImportError as e:
    print(f"Failed to import QgisMCPServer: {e}")
    sys.exit(1)

class MockCanvas:
    def refresh(self):
        print("MockCanvas: refresh called")

    def extent(self):
        print("MockCanvas: extent called")
        return QgsRectangle(0, 0, 10, 10)

class MockInterface:
    def __init__(self):
        self.canvas = MockCanvas()

    def mapCanvas(self):
        return self.canvas

    def setActiveLayer(self, layer):
        print(f"MockInterface: setActiveLayer {layer.name() if layer else 'None'}")

    def zoomToActiveLayer(self):
        print("MockInterface: zoomToActiveLayer called")

def main():
    # Setup the server
    iface = MockInterface()
    server = QgisMCPServer(host='localhost', port=9876, iface=iface)

    print("Starting Mock QGIS MCP Server on port 9876...")
    if server.start():
        print("Server started successfully.")
    else:
        print("Failed to start server.")
        sys.exit(1)

    # Run the event loop
    # QgsApplication.exec_() is a wrapper around QApplication.exec_()
    # We need to handle SIGINT to exit cleanly
    def signal_handler(sig, frame):
        print("\nStopping server...")
        server.stop()
        qgs.exitQgis()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # We use a timer to quit after some time if needed, but for now we run indefinitely
    # or until client sends a "kill" command (which we don't have).
    # We'll just rely on the test runner killing the process.

    qgs.exec_()

if __name__ == "__main__":
    main()
