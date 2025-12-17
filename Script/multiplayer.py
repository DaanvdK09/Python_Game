import pygame
import subprocess
from pathlib import Path
from client import client

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
    if client.in_battle:
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

def handle_multiplayer_battle(game_state):
    """Handle the multiplayer battle state (placeholder for now)."""
    # Handle multiplayer battle
    # For now, placeholder
    pass
