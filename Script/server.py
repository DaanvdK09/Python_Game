import socket
import threading
import json
import time

HOST = '0.0.0.0'
PORT = 65432

class MultiplayerServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {HOST}:{PORT}")

        self.clients = []  # List of (client_id, client_socket)
        self.waiting_players = []  # List of client_ids
        self.active_battles = {}  # client_id: battle_id
        self.battle_states = {}  # battle_id: battle_data
        self.next_client_id = 0
        self.next_battle_id = 0

        self.lock = threading.Lock()

    def handle_client(self, client_socket, client_address):
        print(f"New connection from {client_address}")
        with self.lock:
            client_id = self.next_client_id
            self.next_client_id += 1
            self.clients.append((client_id, client_socket))

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                self.process_message(client_id, message)
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            with self.lock:
                self.clients = [c for c in self.clients if c[0] != client_id]
                if client_id in self.waiting_players:
                    self.waiting_players.remove(client_id)
            client_socket.close()
            print(f"Connection closed for {client_address}")

    def process_message(self, client_id, message):
        msg_type = message.get('type')
        print(f"Server received from {client_id}: {msg_type}")
        if msg_type == 'enter_gym':
            with self.lock:
                if client_id not in self.waiting_players:
                    self.waiting_players.append(client_id)
                    print(f"Player {client_id} entered gym. Waiting players: {len(self.waiting_players)}")
                    if len(self.waiting_players) >= 2:
                        print("Starting battle...")
                        self.start_battle()
        elif msg_type == 'select_pokemon':
            battle_id = self.active_battles.get(client_id)
            if battle_id is not None:
                battle = self.battle_states[battle_id]
                battle['pokemons'][client_id] = message.get('pokemon')
                print(f"Player {client_id} selected pokemon")
                if len(battle['pokemons']) == 2:
                    # Both selected, start battle
                    battle['status'] = 'in_battle'
                    player1, player2 = battle['players']
                    print(f"Battle {battle_id} ready, sending to clients")
                    self.send_to_client(player1, {'type': 'battle_start', 'opponent_pokemon': battle['pokemons'][player2], 'your_turn': battle['current_turn'] == player1})
                    self.send_to_client(player2, {'type': 'battle_start', 'opponent_pokemon': battle['pokemons'][player1], 'your_turn': battle['current_turn'] == player2})
        elif msg_type == 'battle_action':
            self.handle_battle_action(client_id, message)

    def start_battle(self):
        if len(self.waiting_players) >= 2:
            player1 = self.waiting_players.pop(0)
            player2 = self.waiting_players.pop(0)
            battle_id = self.next_battle_id
            self.next_battle_id += 1
            self.battle_states[battle_id] = {
                'players': [player1, player2],
                'pokemons': {},  # client_id: pokemon_data
                'current_turn': player1,  # Start with player1
                'status': 'selecting_pokemon'
            }
            self.active_battles[player1] = battle_id
            self.active_battles[player2] = battle_id
            # Send select_pokemon to both
            self.send_to_client(player1, {'type': 'select_pokemon'})
            self.send_to_client(player2, {'type': 'select_pokemon'})
            print(f"Started battle {battle_id} between {player1} and {player2}")

    def handle_battle_action(self, client_id, message):
        battle_id = self.active_battles.get(client_id)
        if battle_id is not None:
            battle = self.battle_states[battle_id]
            if battle['status'] == 'in_battle' and battle['current_turn'] == client_id:
                action = message.get('action')
                # For now, just switch turns
                battle['current_turn'] = battle['players'][1] if battle['current_turn'] == battle['players'][0] else battle['players'][0]
                # Send action to both players
                self.send_to_client(battle['players'][0], {'type': 'battle_update', 'action': action, 'your_turn': battle['current_turn'] == battle['players'][0]})
                self.send_to_client(battle['players'][1], {'type': 'battle_update', 'action': action, 'your_turn': battle['current_turn'] == battle['players'][1]})
                print(f"Battle {battle_id}: Player {client_id} performed {action}")

    def send_to_client(self, client_id, message):
        for cid, sock in self.clients:
            if cid == client_id:
                try:
                    sock.send(json.dumps(message).encode('utf-8'))
                except:
                    pass

    def run(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    server = MultiplayerServer()
    server.run()
