#!/usr/bin/env python3
import socket
import json
import time
import sys
import os

class QgisMCPClient:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Error connecting: {e}")
            return False

    def close(self):
        if self.socket:
            self.socket.close()

    def send_command(self, cmd_type, params=None):
        if not self.socket:
            return None
        cmd = {"type": cmd_type, "params": params or {}}
        try:
            self.socket.sendall(json.dumps(cmd).encode('utf-8'))
            response_data = b''
            while True:
                chunk = self.socket.recv(4096)
                if not chunk: break
                response_data += chunk
                try:
                    json.loads(response_data.decode('utf-8'))
                    break
                except:
                    continue
            return json.loads(response_data.decode('utf-8'))
        except Exception as e:
            print(f"Error sending: {e}")
            return None

def run_audit():
    client = QgisMCPClient()
    if not client.connect():
        print("FAIL: Could not connect to server")
        return

    print("--- 1. Ping ---")
    res = client.send_command("ping")
    print(f"Ping result: {res}")

    print("\n--- 2. Install Processing Script ---")
    # Using local path to the dummy script we created
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dummy_algorithm.py"))
    res = client.send_command("install_processing_script", {"path": script_path})
    print(f"Install Script result: {json.dumps(res, indent=2)}")

    print("\n--- 3. List Processing Scripts ---")
    res = client.send_command("list_processing_scripts")
    print(f"List Scripts result: {json.dumps(res, indent=2)}")

    client.close()

if __name__ == "__main__":
    run_audit()
