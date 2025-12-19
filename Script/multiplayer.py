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

    # Load battle background
    bg_img = None
    try:
        bg_img = pygame.image.load("graphics/backgrounds/forest.png").convert()
        bg_img = pygame.transform.scale(bg_img, (w, h))
    except Exception:
        bg_img = None

    # Load opponent sprite
    opponent_sprite = None
    try:
        if client.opponent_pokemon and client.opponent_pokemon.get("sprite"):
            from io import BytesIO
            import requests
            sprite_data = requests.get(client.opponent_pokemon["sprite"], timeout=5)
            opponent_sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
            opponent_sprite = pygame.transform.scale(opponent_sprite, (269, 269))
    except Exception:
        opponent_sprite = None

    # Load player sprite
    player_sprite = None
    try:
        if client.selected_pokemon:
            sprite_url = None
            if isinstance(client.selected_pokemon, dict):
                sprite_url = client.selected_pokemon.get("sprite")
            else:
                sprite_url = getattr(client.selected_pokemon, "sprite", None)
            if sprite_url:
                from io import BytesIO
                import requests
                sprite_data = requests.get(sprite_url, timeout=5)
                player_sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
                player_sprite = pygame.transform.scale(player_sprite, (308, 308))
                player_sprite = pygame.transform.flip(player_sprite, True, False)
    except Exception:
        player_sprite = None

    if client.selecting_pokemon:
        # Use existing Pokémon selection menu
        selected_pokemon = quick_pokemon_select(screen, pokedex, menu_font, coords_font, colors, clock, current_player=current_player_pokemon)
        if selected_pokemon:
            client.selected_pokemon = selected_pokemon
            # Send selection to server
            client.send({'type': 'select_pokemon', 'pokemon': selected_pokemon.__dict__ if hasattr(selected_pokemon, '__dict__') else selected_pokemon})
            client.selecting_pokemon = False
            client.waiting_for_battle = True

    elif client.waiting_for_battle:
        # Add a semi-transparent overlay to darken the map background
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # Semi-transparent black to darken the map
        screen.blit(overlay, (0, 0))
        # Display waiting for battle to start
        text = menu_font.render("Waiting for battle to start...", True, colors.get('WHITE', (255, 255, 255)))
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

    elif client.in_battle and client.selected_pokemon and client.opponent_pokemon:
        # Draw battle background
        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill(colors.get('BG', (30, 30, 30)))

        # Draw opponent sprite
        if opponent_sprite:
            sprite_x = w - 269 - 50
            sprite_y = 50
            screen.blit(opponent_sprite, (sprite_x, sprite_y))

        # Draw player sprite
        if player_sprite:
            p_x = 50
            p_y = h - 308 - 50
            screen.blit(player_sprite, (p_x, p_y))

        # Draw HP bars (simplified)
        # Opponent HP
        try:
            enemy_curr = client.opponent_pokemon.get('current_hp', client.opponent_pokemon.get('hp', 100))
            enemy_max = client.opponent_pokemon.get('max_hp', enemy_curr)
            enemy_pct = max(0.0, min(1.0, enemy_curr / enemy_max)) if enemy_max > 0 else 0
            bar_w = 216
            bar_h = 14
            bar_x = int(w - 269 - 50 + 269 // 2 - bar_w // 2)
            bar_y = int(50 - 50)
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)
            fill_w = int(bar_w * enemy_pct)
            hp_color = (46, 129, 31) if enemy_pct > 0.5 else (255, 222, 0) if enemy_pct > 0.25 else (206, 0, 0)
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        except:
            pass

        # Player HP
        try:
            player_curr = client.selected_pokemon.current_hp if hasattr(client.selected_pokemon, 'current_hp') else client.selected_pokemon.get('current_hp', 100)
            player_max = client.selected_pokemon.max_hp if hasattr(client.selected_pokemon, 'max_hp') else client.selected_pokemon.get('max_hp', player_curr)
            player_pct = max(0.0, min(1.0, player_curr / player_max)) if player_max > 0 else 0
            bar_x = int(50 + 308 // 2 - bar_w // 2)
            bar_y = int(h - 50 + 20)
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)
            fill_w = int(bar_w * player_pct)
            hp_color = (46, 129, 31) if player_pct > 0.5 else (255, 222, 0) if player_pct > 0.25 else (206, 0, 0)
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        except:
            pass

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
                client.waiting_for_battle = False
                game_state = "game"
            # Note: Bag and Pokémon switching not implemented for PvP yet
        else:
            # Display waiting for opponent with darker background
            # Add a semi-transparent overlay to darken the battle background
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))  # Semi-transparent black to darken the battle background
            screen.blit(overlay, (0, 0))
            # Display waiting text centered
            text = menu_font.render("Waiting for opponent's turn...", True, colors.get('WHITE', (255, 255, 255)))
            screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

    elif not client.in_battle and not client.waiting_for_battle:
        game_state = "game"

    return game_state
