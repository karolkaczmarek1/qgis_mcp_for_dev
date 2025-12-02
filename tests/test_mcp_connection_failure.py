import subprocess
import time
import sys
import os
import json

def run_negative_test():
    # Start MCP Server without Mock QGIS

    python_exe = sys.executable
    if os.path.exists(".venv/bin/python"):
        python_exe = ".venv/bin/python"

    cmd = [python_exe, "src/qgis_mcp/qgis_mcp_server.py"]

    print(f"Starting MCP Server (Negative Test) with {cmd}")
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

        # 2. Call check_server_connection (Should fail gracefully)

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

        # It might return an error result or successful result with error info?
        # send_command returns None if not connected.
        # check_server_connection calls send_command.
        # result = qgis.send_command("ping") -> None
        # return json.dumps(None, indent=2) -> "null"

        if "result" in response:
            content = response["result"]["content"][0]["text"]
            print(f"Tool result: {content}")
            if content.strip() == "null":
                print("SUCCESS: Handled disconnection gracefully (returned null).")
            else:
                print("WARNING: Unexpected result for disconnected state.")
        elif "error" in response:
            print(f"SUCCESS: Handled disconnection with error: {response['error']}")
        else:
            print("FAILED: Malformed response")
            sys.exit(1)

        # Verify Logs in Stderr
        # We need to read stderr without blocking.
        # Popen.communicate() waits for process to end.
        # We can terminate and read.

    except Exception as e:
        print(f"Exception during test: {e}")
        sys.exit(1)
    finally:
        process.terminate()
        outs, errs = process.communicate()
        print("--- STDERR ---")
        print(errs)

        if "Failed to connect to Qgis" in errs or "Error connecting to server" in errs:
            print("SUCCESS: Found connection error logs in stderr.")
        else:
            print("FAILED: Did not find error logs in stderr.")
            sys.exit(1)

if __name__ == "__main__":
    run_negative_test()
