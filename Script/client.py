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
        self.selecting_pokemon = False
        self.waiting_for_battle = False
        self.selected_pokemon = None
        self.opponent_pokemon = None
        self.my_turn = False
        self.battle_won = None  # None = not in battle result, True = won, False = lost
        self.damage_texts = []  # For battle animations
        self.client_id = None  # Will be set by server

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
                # Add timeout to prevent hanging
                self.socket.settimeout(1.0)
                data = self.socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.handle_message(message)
            except socket.timeout:
                # Timeout is expected, continue listening
                continue
            except Exception as e:
                print(f"Error in listen: {e}")
                break
        self.connected = False

    def handle_message(self, message):
        msg_type = message.get('type')
        print(f"Client received: {msg_type}")
        if msg_type == 'select_pokemon':
            self.selecting_pokemon = True
            print("Select your Pokémon for battle!")
        elif msg_type == 'battle_start':
            # Validate we have required data
            opponent_pokemon = message.get('opponent_pokemon')
            if not opponent_pokemon:
                print("Error: No opponent pokemon data received")
                return

            if not self.selected_pokemon:
                print("Error: No selected pokemon for battle")
                return

            self.selecting_pokemon = False
            self.waiting_for_battle = False
            self.in_battle = True
            self.opponent_pokemon = opponent_pokemon
            self.my_turn = message.get('your_turn', False)
            self.battle_won = None  # Reset battle result
            self.damage_texts = []  # Reset damage texts
            print("Battle started!")
        elif msg_type == 'battle_update':
            # Update battle state
            action = message.get('action')
            if action == 'fight':
                damage_dealt = message.get('damage_dealt', 0)
                damage_taken = message.get('damage_taken', 0)
                opponent_hp = message.get('opponent_hp')
                your_hp = message.get('your_hp')

                # Update HP values safely
                if opponent_hp is not None and self.opponent_pokemon:
                    try:
                        if isinstance(self.opponent_pokemon, dict):
                            self.opponent_pokemon['current_hp'] = opponent_hp
                        elif hasattr(self.opponent_pokemon, 'current_hp'):
                            self.opponent_pokemon.current_hp = opponent_hp
                    except Exception as e:
                        print(f"Error updating opponent HP: {e}")

                if your_hp is not None and self.selected_pokemon:
                    try:
                        if isinstance(self.selected_pokemon, dict):
                            self.selected_pokemon['current_hp'] = your_hp
                        elif hasattr(self.selected_pokemon, 'current_hp'):
                            self.selected_pokemon.current_hp = your_hp
                    except Exception as e:
                        print(f"Error updating player HP: {e}")

                # Add damage text for animation
                if damage_dealt > 0:
                    self.damage_texts.append([f"-{damage_dealt}", "opponent", 60])
                if damage_taken > 0:
                    self.damage_texts.append([f"-{damage_taken}", "player", 60])

            self.my_turn = message.get('your_turn', False)
            print(f"Battle update: your_turn={self.my_turn}")
        elif msg_type == 'pokemon_switched':
            switcher = message.get('switcher')
            new_pokemon = message.get('new_pokemon')
            if switcher != self.client_id:  # Opponent switched
                self.opponent_pokemon = new_pokemon
            self.my_turn = message.get('your_turn', False)
            print("Opponent switched Pokemon")
        elif msg_type == 'battle_end':
            self.in_battle = False
            self.waiting_for_battle = False
            result = message.get('result')
            reason = message.get('reason', '')
            self.battle_won = result == 'win'
            print(f"Battle ended: {result} ({reason})")
            # Reset battle state after showing result
            self.selected_pokemon = None
            self.opponent_pokemon = None
            self.my_turn = False
            self.damage_texts = []

    def enter_gym(self):
        if not self.connected:
            self.connect()
        if self.connected and not self.in_gym:
            # Reset all battle states when entering gym
            self.in_battle = False
            self.selecting_pokemon = False
            self.waiting_for_battle = False
            self.selected_pokemon = None
            self.opponent_pokemon = None
            self.my_turn = False
            self.battle_won = None
            self.damage_texts = []
            
            self.in_gym = True
            self.waiting = True
            self.send({'type': 'enter_gym'})
            print("Entered gym, waiting for opponent")

    def exit_gym(self):
        self.in_gym = False
        self.waiting = False
        self.in_battle = False
        self.waiting_for_battle = False

    def send(self, message):
        if self.connected and self.socket:
            try:
                data = json.dumps(message).encode('utf-8')
                self.socket.settimeout(5.0)  # Timeout for send
                self.socket.send(data)
            except Exception as e:
                print(f"Failed to send message: {e}")
                self.connected = False
        else:
            print("Cannot send message: not connected")

# Global client instance
client = MultiplayerClient()
