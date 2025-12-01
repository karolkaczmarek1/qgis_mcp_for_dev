#!/usr/bin/env python3
import socket
import json
import time
import sys

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

    print("\n--- 8. Execute Code (Test Framework) - FIXED ---")
    code_unittest = """
import unittest
import sys

class TestStringMethods(unittest.TestCase):
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')
    def test_fail(self):
        self.assertEqual(1, 2, "Intentional failure")

# We need to prevent unittest from trying to parse sys.argv
# unittest.main() calls sys.exit() by default, which we don't want.
# We use TestRunner directly.

suite = unittest.TestLoader().loadTestsFromTestCase(TestStringMethods)
runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)

if not result.wasSuccessful():
    print("TEST_SUMMARY: FAILED")
else:
    print("TEST_SUMMARY: PASSED")
"""
    res = client.send_command("execute_code", {"code": code_unittest})
    print(f"Exec Unittest result: {json.dumps(res, indent=2)}")

    client.close()

if __name__ == "__main__":
    run_audit()
