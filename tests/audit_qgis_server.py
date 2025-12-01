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
qgs = QgsApplication([], False)
qgs.initQgis()

print("QGIS Initialized")

# Now import the plugin class
try:
    from qgis_mcp_plugin import QgisMCPServer
except ImportError as e:
    print(f"Failed to import QgisMCPServer: {e}")
    sys.exit(1)

def main():
    # Setup the server WITHOUT iface to test headless safety
    iface = None
    server = QgisMCPServer(host='localhost', port=9876, iface=iface)

    print("Starting Mock QGIS MCP Server on port 9876 (Headless/No Iface)...")
    if server.start():
        print("Server started successfully.")
    else:
        print("Failed to start server.")
        sys.exit(1)

    def signal_handler(sig, frame):
        print("\nStopping server...")
        server.stop()
        qgs.exitQgis()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    qgs.exec_()

if __name__ == "__main__":
    main()
