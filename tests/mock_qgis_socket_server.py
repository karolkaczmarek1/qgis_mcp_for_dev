import socket
import json
import threading
import time

class MockQgisServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.client_handler_thread = None

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.running = True
        print(f"Mock QGIS Server listening on {self.host}:{self.port}")

        self.client_handler_thread = threading.Thread(target=self._accept_clients)
        self.client_handler_thread.daemon = True
        self.client_handler_thread.start()

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        print("Mock QGIS Server stopped")

    def _accept_clients(self):
        while self.running:
            try:
                self.socket.settimeout(1.0)
                try:
                    client, addr = self.socket.accept()
                    print(f"Client connected from {addr}")
                    self._handle_client(client)
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting client: {e}")
                break

    def _handle_client(self, client):
        with client:
            while True:
                data = client.recv(4096)
                if not data:
                    break

                try:
                    command = json.loads(data.decode('utf-8'))
                    print(f"Received command: {command}")

                    response = self._process_command(command)
                    response_json = json.dumps(response)
                    client.sendall(response_json.encode('utf-8'))
                except json.JSONDecodeError:
                    print("Received invalid JSON")
                except Exception as e:
                    print(f"Error processing command: {e}")
                    break

    def _process_command(self, command):
        cmd_type = command.get("type")

        if cmd_type == "ping":
            return {"pong": True}
        elif cmd_type == "get_qgis_info":
             return {"status": "success", "result": {"qgis_version": "3.34.0", "profile_folder": "/tmp", "plugins_count": 5}}
        else:
            return {"status": "error", "message": f"Unknown command: {cmd_type}"}

if __name__ == "__main__":
    server = MockQgisServer()
    server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
