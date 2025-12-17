import socket
import json
import threading
import time

HOST = '127.0.0.1'
PORT = 65432

class MultiplayerClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.in_gym = False
        self.waiting = False
        self.in_battle = False

    def connect(self):
        if self.connected:
            return
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.connected = True
            print("Connected to server")
            threading.Thread(target=self.listen).start()
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.socket = None

    def disconnect(self):
        if self.socket:
            self.socket.close()
        self.connected = False

    def listen(self):
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.handle_message(message)
            except Exception as e:
                print(f"Error in listen: {e}")
                break
        self.connected = False

    def handle_message(self, message):
        msg_type = message.get('type')
        if msg_type == 'battle_start':
            self.waiting = False
            self.in_battle = True
            print("Battle started!")
            # Trigger battle in game
        # Add more message handlers

    def enter_gym(self):
        if not self.connected:
            self.connect()
        if self.connected and not self.in_gym:
            self.in_gym = True
            self.waiting = True
            self.send({'type': 'enter_gym'})
            print("Entered gym, waiting for opponent")

    def exit_gym(self):
        self.in_gym = False
        self.waiting = False
        self.in_battle = False

    def send(self, message):
        if self.connected and self.socket:
            try:
                self.socket.send(json.dumps(message).encode('utf-8'))
            except Exception as e:
                print(f"Failed to send message: {e}")
                self.connected = False

# Global client instance
client = MultiplayerClient()
