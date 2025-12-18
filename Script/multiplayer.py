import pygame
import subprocess
from pathlib import Path
from client import client
from UI.pokedex_menu import quick_pokemon_select
from Characters.encounter import get_moves_for_pokemon
from UI.battle_menu import battle_menu, show_move_menu

def start_server():
    """Start the multiplayer server."""
    try:
        server_process = subprocess.Popen([__import__('sys').executable, 'server.py'], cwd=Path(__file__).parent)
        print("Server started")
        return server_process
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def handle_multiplayer_logic(game_state, player, game_map, initial_no_switch_frames):
    """Handle entering and exiting the multiplayer gym."""
    gym_rect = game_map.get_multiplayer_gym_rect()
    gym_hit = gym_rect and gym_rect.colliderect(player.rect)

    if gym_hit and not client.in_gym and initial_no_switch_frames == 0:
        client.enter_gym()
        game_state = "waiting"
        print("Entered Multiplayer Gym")

    if not gym_hit and client.in_gym:
        client.exit_gym()
        game_state = "game"
        print("Exited Multiplayer Gym")

    initial_no_switch_frames = max(0, initial_no_switch_frames - 1)

    return game_state, initial_no_switch_frames

def handle_waiting_state(game_state, screen, menu_font, WHITE):
    """Handle the waiting screen for multiplayer."""
    w, h = screen.get_size()
    if client.selecting_pokemon or client.in_battle:
        print("Switching to multiplayer_battle state")
        game_state = "multiplayer_battle"
    else:
        # Add a semi-transparent overlay to darken the map background
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # Semi-transparent black to darken the map
        screen.blit(overlay, (0, 0))
        
        # Show waiting text on the darkened map
        text = menu_font.render("Waiting for another player to join the Multiplayer Gym...", True, WHITE)
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))
    return game_state

def handle_multiplayer_battle(game_state, screen, menu_font, coords_font, colors, clock, pokedex, current_player_pokemon, bag):
    """Handle the multiplayer battle state using existing battle system."""
    w, h = screen.get_size()

    if client.selecting_pokemon:
        # Use existing Pokémon selection menu
        selected_pokemon = quick_pokemon_select(screen, pokedex, menu_font, coords_font, colors, clock, current_player=current_player_pokemon)
        if selected_pokemon:
            client.selected_pokemon = selected_pokemon
            # Send selection to server
            client.send({'type': 'select_pokemon', 'pokemon': selected_pokemon.__dict__ if hasattr(selected_pokemon, '__dict__') else selected_pokemon})
            client.selecting_pokemon = False

    elif client.in_battle and client.selected_pokemon and client.opponent_pokemon:
        if client.my_turn:
            # Use existing battle menu
            choice = battle_menu(screen, client.opponent_pokemon, menu_font, coords_font, colors, clock, player_pokemon=client.selected_pokemon, initial_message=None, show_intro=False)
            if choice == 'fight':
                moves = get_moves_for_pokemon(client.selected_pokemon.name)
                selected_move = show_move_menu(screen, moves, menu_font, coords_font, colors, clock, None, None, None, None, None, client.opponent_pokemon, client.selected_pokemon, None)
                if selected_move:
                    client.send({'type': 'battle_action', 'action': 'fight', 'move': selected_move})
                    client.my_turn = False  # Wait for server confirmation
            elif choice == 'run':
                client.send({'type': 'battle_action', 'action': 'run'})
                client.in_battle = False
                game_state = "game"
            # Note: Bag and Pokémon switching not implemented for PvP yet
        else:
            # Display waiting for opponent
            text = menu_font.render("Waiting for opponent's turn...", True, colors.get('WHITE', (255, 255, 255)))
            screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

    elif not client.in_battle:
        game_state = "game"

    return game_state
