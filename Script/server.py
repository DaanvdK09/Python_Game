import socket
import threading
import json
import time
import random

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

                # Handle player disconnection during battle
                battle_id = self.active_battles.get(client_id)
                if battle_id is not None:
                    self.handle_player_disconnect(client_id, battle_id)
                elif client_id in self.waiting_players:
                    # Player disconnected while waiting
                    self.waiting_players.remove(client_id)
                    print(f"Player {client_id} disconnected while waiting")

            client_socket.close()
            print(f"Connection closed for {client_address}")

    def handle_player_disconnect(self, client_id, battle_id):
        """Handle when a player disconnects during battle."""
        battle = self.battle_states.get(battle_id)
        if battle:
            # Notify the other player that their opponent left
            other_player = None
            for player in battle['players']:
                if player != client_id:
                    other_player = player
                    break

            if other_player:
                self.send_to_client(other_player, {
                    'type': 'battle_end',
                    'result': 'win',
                    'reason': 'opponent_disconnected'
                })

            # Clean up battle
            for player in battle['players']:
                if player in self.active_battles:
                    del self.active_battles[player]
            if battle_id in self.battle_states:
                del self.battle_states[battle_id]

            print(f"Battle {battle_id} ended due to player {client_id} disconnecting")

    def process_message(self, client_id, message):
        msg_type = message.get('type')
        print(f"Server received from {client_id}: {msg_type}")

        if msg_type == 'enter_gym':
            with self.lock:
                # Allow re-entry - remove from any existing battles first
                if client_id in self.active_battles:
                    battle_id = self.active_battles[client_id]
                    battle = self.battle_states.get(battle_id)
                    if battle:
                        # Notify other player
                        other_player = None
                        for player in battle['players']:
                            if player != client_id:
                                other_player = player
                                break
                        if other_player:
                            self.send_to_client(other_player, {
                                'type': 'battle_end',
                                'result': 'win',
                                'reason': 'opponent_disconnected'
                            })
                        # Clean up battle
                        for player in battle['players']:
                            if player in self.active_battles:
                                del self.active_battles[player]
                        if battle_id in self.battle_states:
                            del self.battle_states[battle_id]
                
                # Remove from waiting if already there
                if client_id in self.waiting_players:
                    self.waiting_players.remove(client_id)
                
                # Add to waiting players
                self.waiting_players.append(client_id)
                print("Starting battle...")
                self.start_battle()

        elif msg_type == 'select_pokemon':
            battle_id = self.active_battles.get(client_id)
            if battle_id is not None:
                battle = self.battle_states[battle_id]
                pokemon_data = message.get('pokemon')
                
                # Validate pokemon data
                if not pokemon_data:
                    print(f"Error: No pokemon data from client {client_id}")
                    return
                
                # Basic validation
                pokemon_name = None
                if isinstance(pokemon_data, dict):
                    pokemon_name = pokemon_data.get('name')
                elif hasattr(pokemon_data, 'name'):
                    pokemon_name = pokemon_data.name
                
                if not pokemon_name:
                    print(f"Error: Invalid pokemon data from client {client_id}")
                    return
                
                battle['pokemons'][client_id] = pokemon_data
                print(f"Player {client_id} selected pokemon: {pokemon_name}")
                
                # Store opponent's pokedex size (will be sent by client)
                if 'opponent_pokedex_size' in message:
                    opponent_id = battle['players'][1] if client_id == battle['players'][0] else battle['players'][0]
                    battle['opponent_pokedex_sizes'][opponent_id] = message['opponent_pokedex_size']
                
                if len(battle['pokemons']) == 2:
                    # Both selected, start battle
                    battle['status'] = 'in_battle'
                    player1, player2 = battle['players']
                    print(f"Battle {battle_id} ready, sending to clients")
                    
                    # Validate both players have pokemon
                    p1_pokemon = battle['pokemons'].get(player1)
                    p2_pokemon = battle['pokemons'].get(player2)
                    
                    if not p1_pokemon or not p2_pokemon:
                        print(f"Error: Missing pokemon data for battle {battle_id}")
                        # Clean up invalid battle
                        for player in battle['players']:
                            if player in self.active_battles:
                                del self.active_battles[player]
                        if battle_id in self.battle_states:
                            del self.battle_states[battle_id]
                        return
                    
                    # Determine who goes first (alternating turns)
                    current_turn = battle.get('current_turn', player1)
                    # For new battle rounds, alternate who starts
                    if battle.get('round_count', 0) > 0:
                        current_turn = player2 if current_turn == player1 else player1
                    battle['current_turn'] = current_turn
                    battle['round_count'] = battle.get('round_count', 0) + 1
                    
                    self.send_to_client(player1, {'type': 'battle_start', 'opponent_pokemon': p2_pokemon, 'your_turn': current_turn == player1})
                    self.send_to_client(player2, {'type': 'battle_start', 'opponent_pokemon': p1_pokemon, 'your_turn': current_turn == player2})

        elif msg_type == 'battle_action':
            self.handle_battle_action(client_id, message)

        elif msg_type == 'disconnect':
            print(f"Player {client_id} requested disconnect")
            battle_id = self.active_battles.get(client_id)
            if battle_id:
                self.handle_player_disconnect(client_id, battle_id)

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
                'status': 'selecting_pokemon',
                'damage_log': [],  # Track damage for animations
                'defeated_pokemon': {player1: [], player2: []},  # Track defeated pokemon for each player
                'opponent_pokedex_sizes': {player1: 0, player2: 0}  # Will be set when pokemon selected
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

                if action == 'fight':
                    move = message.get('move')
                    if move:
                        self.process_fight_action(client_id, battle_id, move)

                elif action == 'switch':
                    pokemon = message.get('pokemon')
                    if pokemon:
                        battle['pokemons'][client_id] = pokemon
                        # Switch turns after switching
                        battle['current_turn'] = battle['players'][1] if battle['current_turn'] == battle['players'][0] else battle['players'][0]
                        # Notify both players of the switch
                        self.send_to_client(battle['players'][0], {
                            'type': 'pokemon_switched',
                            'switcher': client_id,
                            'new_pokemon': pokemon,
                            'your_turn': battle['current_turn'] == battle['players'][0]
                        })
                        self.send_to_client(battle['players'][1], {
                            'type': 'pokemon_switched',
                            'switcher': client_id,
                            'new_pokemon': pokemon,
                            'your_turn': battle['current_turn'] == battle['players'][1]
                        })

                elif action == 'run':
                    # Player ran away - end battle
                    winner = battle['players'][1] if battle['current_turn'] == battle['players'][0] else battle['players'][0]
                    loser = client_id

                    self.send_to_client(winner, {'type': 'battle_end', 'result': 'win', 'reason': 'opponent_ran'})
                    self.send_to_client(loser, {'type': 'battle_end', 'result': 'loss', 'reason': 'ran_away'})

                    # Clean up battle
                    for player in battle['players']:
                        if player in self.active_battles:
                            del self.active_battles[player]
                    if battle_id in self.battle_states:
                        del self.battle_states[battle_id]

    def process_fight_action(self, client_id, battle_id, move):
        battle = self.battle_states[battle_id]
        attacker = client_id
        defender = battle['players'][1] if attacker == battle['players'][0] else battle['players'][0]

        # Validate move belongs to attacker's pokemon
        attacker_pokemon = battle['pokemons'].get(attacker)
        if not attacker_pokemon:
            print(f"Error: No pokemon found for attacker {attacker}")
            return

        attacker_name = None
        if isinstance(attacker_pokemon, dict):
            attacker_name = attacker_pokemon.get('name', '').lower()
        else:
            attacker_name = getattr(attacker_pokemon, 'name', '').lower()

        # Basic validation - check if move could belong to this pokemon
        move_name = move.get('name', '').lower()
        if not move_name:
            print(f"Error: Invalid move data from {attacker}")
            return

        # Calculate damage (basic implementation)
        damage = move.get('power', 0)
        if damage <= 0:
            damage = 10  # Minimum damage

        # Apply damage to defender's pokemon
        defender_pokemon = battle['pokemons'].get(defender)
        if not defender_pokemon:
            print(f"Error: No pokemon found for defender {defender}")
            return

        if isinstance(defender_pokemon, dict):
            current_hp = defender_pokemon.get('current_hp', defender_pokemon.get('hp', 100))
            max_hp = defender_pokemon.get('max_hp', current_hp)
            new_hp = max(0, current_hp - damage)
            defender_pokemon['current_hp'] = new_hp
        else:
            # Handle object pokemon
            if hasattr(defender_pokemon, 'current_hp'):
                defender_pokemon.current_hp = max(0, defender_pokemon.current_hp - damage)
            else:
                print(f"Error: Defender pokemon has no HP attribute")
                return

        # Check if defender's pokemon fainted
        defender_hp = 0
        if isinstance(defender_pokemon, dict):
            defender_hp = defender_pokemon.get('current_hp', defender_pokemon.get('hp', 0))
        elif hasattr(defender_pokemon, 'current_hp'):
            defender_hp = defender_pokemon.current_hp
        elif hasattr(defender_pokemon, 'hp'):
            defender_hp = defender_pokemon.hp
        else:
            print(f"Error: Cannot determine HP for defender pokemon")
            return

        battle['damage_log'].append({
            'attacker': attacker,
            'defender': defender,
            'damage': damage,
            'move': move
        })

        if defender_hp <= 0:
            # Pokemon fainted - mark as defeated and check if all pokemon are defeated
            defender_pokemon_name = None
            if isinstance(defender_pokemon, dict):
                defender_pokemon_name = defender_pokemon.get('name')
            else:
                defender_pokemon_name = getattr(defender_pokemon, 'name', 'Unknown')
            
            # Add to defeated list
            battle['defeated_pokemon'][defender].append(defender_pokemon_name)
            
            # Check if defender has any pokemon left (not defeated)
            opponent_pokedex_size = battle['opponent_pokedex_sizes'].get(attacker, 0)
            defeated_count = len(battle['defeated_pokemon'][defender])
            
            print(f"Pokemon {defender_pokemon_name} fainted. Player {defender} has {defeated_count}/{opponent_pokedex_size} pokemon defeated.")
            
            if defeated_count >= opponent_pokedex_size:
                # All pokemon defeated - attacker wins
                self.send_to_client(attacker, {
                    'type': 'battle_end',
                    'result': 'win',
                    'reason': 'all_pokemon_defeated'
                })
                self.send_to_client(defender, {
                    'type': 'battle_end',
                    'result': 'loss',
                    'reason': 'all_pokemon_defeated'
                })

                # Clean up battle
                for player in battle['players']:
                    if player in self.active_battles:
                        del self.active_battles[player]
                if battle_id in self.battle_states:
                    del self.battle_states[battle_id]
            else:
                # Pokemon fainted but battle continues - defender needs to select new pokemon
                battle['status'] = 'selecting_pokemon'
                battle['pokemons'][defender] = None  # Clear fainted pokemon
                
                # Send faint message and pokemon selection request
                self.send_to_client(attacker, {
                    'type': 'pokemon_fainted',
                    'fainted_pokemon': defender_pokemon_name,
                    'opponent_selecting': True
                })
                self.send_to_client(defender, {
                    'type': 'pokemon_fainted',
                    'fainted_pokemon': defender_pokemon_name,
                    'select_new_pokemon': True
                })
        else:
            # Continue battle - switch turns
            battle['current_turn'] = defender

            # Get current HP values for both players
            attacker_hp = 0
            if isinstance(attacker_pokemon, dict):
                attacker_hp = attacker_pokemon.get('current_hp', attacker_pokemon.get('hp', 0))
            elif hasattr(attacker_pokemon, 'current_hp'):
                attacker_hp = attacker_pokemon.current_hp
            elif hasattr(attacker_pokemon, 'hp'):
                attacker_hp = attacker_pokemon.hp

            # Send battle update to both players with correct HP values
            self.send_to_client(attacker, {
                'type': 'battle_update',
                'action': 'fight',
                'damage_dealt': damage,
                'opponent_hp': defender_hp,
                'your_hp': attacker_hp,
                'your_turn': False
            })
            self.send_to_client(defender, {
                'type': 'battle_update',
                'action': 'fight',
                'damage_taken': damage,
                'opponent_hp': attacker_hp,
                'your_hp': defender_hp,
                'your_turn': True
            })

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
