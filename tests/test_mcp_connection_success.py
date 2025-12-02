import subprocess
import time
import sys
import os
import json
import threading

# Handle import of sibling module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from mock_qgis_socket_server import MockQgisServer

def run_test():
    # Start Mock QGIS Server
    mock_server = MockQgisServer()
    mock_server.start()

    # Give it a moment to bind
    time.sleep(1)

    # Start MCP Server
    # We use python directly to avoid uv overhead in this tight loop test if possible,
    # but we need dependencies.
    # If .venv exists, use it.
    python_exe = sys.executable
    if os.path.exists(".venv/bin/python"):
        python_exe = ".venv/bin/python"

    # Assuming we run from repo root
    server_script = "src/qgis_mcp/qgis_mcp_server.py"
    if not os.path.exists(server_script):
        print(f"Error: {server_script} not found. Run from repo root.")
        mock_server.stop()
        sys.exit(1)

    cmd = [python_exe, server_script]

    print(f"Starting MCP Server with {cmd}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )

    try:
        # 1. Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        print("Sending Initialize...")
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()

        # Read response (blocking read might be dangerous if output is large or not flushed)
        # We read line by line.
        line = process.stdout.readline()
        print(f"Received: {line}")

        if not line:
            print("FAILED: No response received")
            print("--- STDERR ---")
            print(process.stderr.read())
            sys.exit(1)

        response = json.loads(line)
        if "result" not in response:
            print(f"FAILED: Initialize failed. Got: {response}")
            sys.exit(1)

        # 2. Call check_server_connection
        # Note: In MCP, after initialize, we usually expect 'notifications/initialized' but strictly speaking we can call tools.
        # Let's send initialized notification just in case.
        notify_init = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(notify_init) + "\n")
        process.stdin.flush()

        tool_call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "check_server_connection",
                "arguments": {}
            }
        }

        print("Sending tool call...")
        process.stdin.write(json.dumps(tool_call) + "\n")
        process.stdin.flush()

        line = process.stdout.readline()
        print(f"Received: {line}")
        response = json.loads(line)

        if "error" in response:
            print(f"FAILED: Tool call returned error: {response['error']}")
            sys.exit(1)

        result_content = response["result"]["content"][0]["text"]
        print(f"Tool result: {result_content}")

        inner_result = json.loads(result_content)
        if inner_result.get("pong") is True:
            print("SUCCESS: Connection verified!")
        else:
            print("FAILED: Did not receive pong")
            sys.exit(1)

    except Exception as e:
        print(f"Exception during test: {e}")
        # Print any stderr output
        print("--- STDERR ---")
        if process.stderr:
            print(process.stderr.read())
        sys.exit(1)
    finally:
        process.terminate()
        mock_server.stop()

if __name__ == "__main__":
    run_test()
