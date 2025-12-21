import pygame
import subprocess
from pathlib import Path
from client import client
from UI.pokedex_menu import quick_pokemon_select
from Characters.encounter import get_moves_for_pokemon
from UI.battle_menu import battle_menu, show_move_menu
from io import BytesIO
import requests

def start_server():
    # Starts the multiplayer server process.
    try:
        server_process = subprocess.Popen([__import__('sys').executable, 'server.py'], cwd=Path(__file__).parent)
        print("Server started")
        return server_process
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def handle_disconnect():
    # Handles player disconnection from multiplayer, resetting all states.
    print("Player pressed ESC - disconnecting from multiplayer")
    try:
        client.send({'type': 'disconnect'})
    except:
        pass
    client.disconnect()
    client.in_battle = False
    client.waiting_for_battle = False
    client.selecting_pokemon = False
    client.waiting_for_opponent_selection = False
    return "game"

def handle_multiplayer_logic(game_state, player, game_map, initial_no_switch_frames):
    # Handles logic for entering/exiting the multiplayer gym.
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
    # Displays waiting screen while finding an opponent.
    w, h = screen.get_size()
    if client.selecting_pokemon or client.in_battle or client.waiting_for_opponent_selection:
        print("Switching to multiplayer_battle state")
        game_state = "multiplayer_battle"
    elif client.waiting:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        # Waiting text on multiplayer
        text = menu_font.render("Waiting for another player to join the Multiplayer Gym...", True, WHITE)
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))
    return game_state

def handle_multiplayer_battle(game_state, screen, menu_font, coords_font, colors, clock, pokedex, current_player_pokemon, bag, type_icons=None):
    # Handles the multiplayer battle state, including rendering, input, and state transitions.
    w, h = screen.get_size()

    # Cache for background
    if not hasattr(handle_multiplayer_battle, '_bg_cache'):
        handle_multiplayer_battle._bg_cache = {}

    bg_img = handle_multiplayer_battle._bg_cache.get((w, h))
    if bg_img is None:
        try:
            bg_img_path = Path(__file__).parent.parent / "graphics" / "backgrounds" / "forest.png"
            bg_img = pygame.image.load(bg_img_path).convert()
            bg_img = pygame.transform.scale(bg_img, (w, h))
            handle_multiplayer_battle._bg_cache[(w, h)] = bg_img
        except Exception as e:
            print(f"Error loading background: {e}")
            bg_img = None

    pokeball_img = None
    try:
        base_dir = Path(__file__).parent
        candidates = [
            base_dir.parent / "graphics" / "icons" / "pokéball.png",
            base_dir.parent / "graphics" / "icons" / "pokéball-icon.png",
            base_dir.parent / "graphics" / "icons" / "pokeball.png",
        ]
        pb_path = None
        for c in candidates:
            if c.exists():
                pb_path = c
                break
        if pb_path:
            img = pygame.image.load(str(pb_path)).convert_alpha()
            pokeball_img = pygame.transform.scale(img, (40, 40))
    except Exception as e:
        print(f"Error loading pokeball image: {e}")
        pokeball_img = None

    opponent_sprite = None
    try:
        if client.opponent_pokemon and client.opponent_pokemon.get("sprite"):
            sprite_data = requests.get(client.opponent_pokemon["sprite"], timeout=5)
            opponent_sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
            opponent_sprite = pygame.transform.scale(opponent_sprite, (269, 269))
    except Exception as e:
        print(f"Error loading opponent sprite: {e}")
        opponent_sprite = None

    player_sprite = None
    try:
        if client.selected_pokemon:
            sprite_url = None
            if isinstance(client.selected_pokemon, dict):
                sprite_url = client.selected_pokemon.get("sprite")
            else:
                sprite_url = getattr(client.selected_pokemon, "sprite", None)
            if sprite_url:
                sprite_data = requests.get(sprite_url, timeout=5)
                player_sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
                player_sprite = pygame.transform.scale(player_sprite, (308, 308))
                player_sprite = pygame.transform.flip(player_sprite, True, False)
    except Exception as e:
        print(f"Error loading player sprite: {e}")
        player_sprite = None

    if client.selecting_pokemon:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = handle_disconnect()
                return game_state

        try:
            selected_pokemon = quick_pokemon_select(screen, pokedex, menu_font, coords_font, colors, clock, current_player=None)
            if selected_pokemon:
                # Only reset HP for the first battle, not subsequent switches
                if not hasattr(client, 'first_battle_done'):
                    selected_pokemon.current_hp = selected_pokemon.hp
                    client.first_battle_done = True
                
                client.selected_pokemon = selected_pokemon
                pokemon_data = selected_pokemon.__dict__ if hasattr(selected_pokemon, '__dict__') else selected_pokemon
                opponent_pokedex_size = len(pokedex.captured_pokemon) if hasattr(pokedex, 'captured_pokemon') else 0
                client.send({'type': 'select_pokemon', 'pokemon': pokemon_data, 'opponent_pokedex_size': opponent_pokedex_size})
                client.selecting_pokemon = False
                if hasattr(client, 'was_in_battle') and client.was_in_battle:
                    client.waiting_for_battle = True
                    client.was_in_battle = False
                else:
                    client.waiting_for_battle = True
        except Exception as e:
            print(f"Error in Pokémon selection: {e}")
            client.selecting_pokemon = False

    elif client.waiting_for_battle:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = handle_disconnect()
                return game_state

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  
        screen.blit(overlay, (0, 0))
        text = menu_font.render("Waiting for battle to start...", True, colors.get('WHITE', (255, 255, 255)))
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

    elif client.in_battle and client.selected_pokemon and client.opponent_pokemon:
        if not client.selected_pokemon or not client.opponent_pokemon:
            print("Error: Missing pokemon data for battle")
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            error_text = menu_font.render("Battle error - missing pokemon data", True, (255, 100, 100))
            screen.blit(error_text, (w // 2 - error_text.get_width() // 2, h // 2 - error_text.get_height() // 2))
            return game_state

        try:
            # Draw battle background
            if bg_img:
                screen.blit(bg_img, (0, 0))

            # Draw opponent sprite
            if opponent_sprite:
                sprite_x = w - 269 - 50
                if client.my_turn:
                    sprite_y = h // 2 + 50  # Lower position when it's player's turn
                else:
                    sprite_y = 50  # Higher position when it's opponent's turn
                screen.blit(opponent_sprite, (sprite_x, sprite_y))

            # Draw player sprite
            if player_sprite:
                p_x = 50
                if client.my_turn:
                    p_y = h // 2 - 308 - 50  # Higher position when it's player's turn
                else:
                    p_y = h - 308 - 50  # Lower position when it's opponent's turn
                screen.blit(player_sprite, (p_x, p_y))

            # Helper function to safely get HP values
            def get_hp_safe(pokemon_obj):
                try:
                    if isinstance(pokemon_obj, dict):
                        curr = pokemon_obj.get('current_hp', pokemon_obj.get('hp', 100))
                        max_hp = pokemon_obj.get('max_hp', curr)
                    else:
                        curr = getattr(pokemon_obj, 'current_hp', getattr(pokemon_obj, 'hp', 100))
                        max_hp = getattr(pokemon_obj, 'max_hp', curr)
                    return float(curr), float(max_hp)
                except:
                    return 100.0, 100.0

            # Helper function to safely get name
            def get_name_safe(pokemon_obj):
                try:
                    if isinstance(pokemon_obj, dict):
                        return pokemon_obj.get('name', 'Unknown')
                    return getattr(pokemon_obj, 'name', 'Unknown')
                except:
                    return 'Unknown'

            # Draw HP bars
            bar_w = 216
            bar_h = 14

            # Opponent HP
            enemy_curr, enemy_max = get_hp_safe(client.opponent_pokemon)
            enemy_pct = max(0.0, min(1.0, enemy_curr / enemy_max)) if enemy_max > 0 else 0
            bar_x = int(w - 269 - 50 + 269 // 2 - bar_w // 2)
            if client.my_turn:
                bar_y = int(h // 2 + 50 - 50)  # Above opponent sprite when lower
            else:
                bar_y = int(50 - 50)  # Above opponent sprite when higher
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)
            fill_w = int(bar_w * enemy_pct)
            if fill_w > 0:
                hp_color = (46, 129, 31) if enemy_pct > 0.5 else (255, 222, 0) if enemy_pct > 0.25 else (206, 0, 0)
                pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, 2, border_radius=6)

            # Player HP
            player_curr, player_max = get_hp_safe(client.selected_pokemon)
            player_pct = max(0.0, min(1.0, player_curr / player_max)) if player_max > 0 else 0
            p_bar_x = int(50 + 308 // 2 - bar_w // 2)
            if client.my_turn:
                p_bar_y = int(h // 2 - 308 - 50 - 30)  # Above player sprite when higher
            else:
                p_bar_y = int(h - 50 + 20)  # Below player sprite when lower
            p_bg_rect = pygame.Rect(p_bar_x, p_bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), p_bg_rect, border_radius=6)
            p_fill_w = int(bar_w * player_pct)
            if p_fill_w > 0:
                p_hp_color = (46, 129, 31) if player_pct > 0.5 else (255, 222, 0) if player_pct > 0.25 else (206, 0, 0)
                pygame.draw.rect(screen, p_hp_color, (p_bar_x, p_bar_y, p_fill_w, bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), p_bg_rect, 2, border_radius=6)

            # Draw team pokeballs on battle screen (only during battle and only when it's player's turn)
            if client.my_turn and pokeball_img and pokedex and hasattr(pokedex, 'get_team'):
                try:
                    team = pokedex.get_team()
                    team_x = w // 2 - (6 * 34) // 2  # Center the pokeballs
                    if client.my_turn:
                        team_y = h - 200  # Lower position when player is higher
                    else:
                        team_y = h - 380  # Original position when player is lower
                    for i in range(6):
                        ball_x = team_x + i * 34
                        if i < len(team):
                            screen.blit(pokeball_img, (ball_x, team_y))
                        else:
                            pygame.draw.circle(screen, (180, 180, 180), (int(ball_x + 16), int(team_y + 16)), 16, 2)
                except:
                    pass

            # Show damage texts
            client.damage_texts = show_damage_texts_multiplayer(screen, client.damage_texts, w, h)

            # Show faint message if any
            if client.faint_message:
                # Darker overlay for faint message
                faint_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                faint_overlay.fill((0, 0, 0, 150))
                screen.blit(faint_overlay, (0, 0))
                
                # Faint message in white text
                faint_font = pygame.font.Font(None, 48)
                faint_text = faint_font.render(client.faint_message, True, (255, 255, 255))
                screen.blit(faint_text, (w // 2 - faint_text.get_width() // 2, h // 2 - faint_text.get_height() // 2))
                
                # Clear message after a few frames, but not during Pokemon selection
                if client.selecting_pokemon:
                    # Keep the message visible during selection
                    pass
                else:
                    if not hasattr(client, 'faint_timer'):
                        client.faint_timer = 300  # Show for 5 seconds at 60 FPS
                    client.faint_timer -= 1
                    if client.faint_timer <= 0:
                        client.faint_message = None
                        client.faint_timer = 0

            if client.my_turn:
                try:
                    # Use existing battle menu with improved error handling
                    pygame.display.flip()  # Ensure the battle scene is displayed before showing menu
                    choice = battle_menu(
                        screen,
                        client.opponent_pokemon,
                        menu_font,
                        coords_font,
                        colors,
                        clock,
                        player_pokemon=client.selected_pokemon,
                        initial_message=None,
                        show_intro=False,
                        pokedex_obj=pokedex,
                        pokeball_img=pokeball_img
                    )

                    if choice is None:  # ESC pressed
                        game_state = handle_disconnect()
                        return game_state

                    if choice and choice.lower() == 'fight':
                        pokemon_name = get_name_safe(client.selected_pokemon)
                        if not pokemon_name:
                            print("Error: Cannot determine pokemon name for moves")
                            return game_state

                        moves = get_moves_for_pokemon(pokemon_name)

                        if not moves:
                            print(f"Error: No moves found for pokemon {pokemon_name}")
                        elif not isinstance(moves, list) or len(moves) == 0:
                            print(f"Error: Invalid moves data for pokemon {pokemon_name}")
                        else:
                            # Load sprites for move menu
                            sprite_surface = opponent_sprite
                            player_sprite_surface = player_sprite

                            spr_w = 269
                            spr_h = 269
                            # Use fixed positions for move menu (opponent right, player left)
                            sprite_x = w - 269 - 50
                            sprite_y = 50
                            p_x = 50
                            p_y = h - 308 - 50

                            pygame.display.flip()  # Ensure the battle scene is displayed before showing move menu
                            selected_move = show_move_menu(
                                screen,
                                moves,
                                menu_font,
                                coords_font,
                                colors,
                                clock,
                                bg_img,
                                sprite_surface,
                                player_sprite_surface,
                                sprite_x,
                                sprite_y,
                                p_x,
                                p_y,
                                client.opponent_pokemon,
                                client.selected_pokemon,
                                type_icons
                            )
                            if selected_move:
                                client.send({'type': 'battle_action', 'action': 'fight', 'move': selected_move})
                                client.my_turn = False  # Wait for server confirmation
                    elif choice and choice.lower() == 'run':
                        client.send({'type': 'battle_action', 'action': 'run'})
                        client.in_battle = False
                        client.waiting_for_battle = False
                        game_state = "game"
                    elif choice and (choice.lower() == 'pokémon' or choice.lower() == 'pokemon'):
                        # Switch pokemon
                        selected_pokemon = quick_pokemon_select(screen, pokedex, menu_font, coords_font, colors, clock, current_player=client.selected_pokemon)
                        if selected_pokemon:
                            client.selected_pokemon = selected_pokemon
                            pokemon_data = selected_pokemon.__dict__ if hasattr(selected_pokemon, '__dict__') else selected_pokemon
                            client.send({'type': 'battle_action', 'action': 'switch', 'pokemon': pokemon_data})
                            client.my_turn = False
                    elif choice and choice.lower() == 'bag':
                        # Bag usage not implemented for multiplayer
                        pass

                except Exception as e:
                    print(f"Error during battle action: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't crash, just wait for next turn
            else:
                # Display waiting for opponent with darker background
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))
                text = menu_font.render("Waiting for opponent's turn...", True, colors.get('WHITE', (255, 255, 255)))
                screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

        except Exception as e:
            print(f"Error in battle rendering: {e}")
            import traceback
            traceback.print_exc()
            # Show error overlay and continue
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            error_text = menu_font.render("Battle error - please wait...", True, (255, 100, 100))
            screen.blit(error_text, (w // 2 - error_text.get_width() // 2, h // 2 - error_text.get_height() // 2))

    elif client.battle_won is not None:
        # Victory/Defeat screen
        show_battle_result_screen(screen, menu_font, w, h, colors, clock, client.battle_won)
        client.battle_won = None  # Reset after showing
        client.in_battle = False
        client.waiting_for_battle = False
        game_state = "game"

    elif client.waiting_for_opponent_selection:
        # Check for ESC key to disconnect
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = handle_disconnect()
                return game_state

        # Add a semi-transparent overlay to darken the map background
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # Semi-transparent black to darken the map
        screen.blit(overlay, (0, 0))
        # Display waiting for opponent to select new pokemon
        text = menu_font.render("Waiting for opponent to select a new Pokémon...", True, colors.get('WHITE', (255, 255, 255)))
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))

    # If we're still in the gym but not in any active battle state, stay in multiplayer_battle
    # This handles transitions between battle rounds
    if client.in_gym and not client.selecting_pokemon and not client.waiting_for_battle and not client.in_battle and not client.waiting_for_opponent_selection and client.battle_won is None:
        # Show a general waiting message
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        text = menu_font.render("Preparing for battle...", True, colors.get('WHITE', (255, 255, 255)))
        screen.blit(text, (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2))
    elif not client.in_gym:
        game_state = "game"

    return game_state

def show_damage_texts_multiplayer(screen, damage_texts, w, h):
    # Displays damage texts on the battle screen with animation.
    updated_texts = []
    for text_item in damage_texts:
        if len(text_item) >= 3:
            text, target, timer = text_item
            timer -= 1
            if timer > 0:
                # Position based on target
                if target == "opponent":
                    x = w - 269 - 50 + 269 // 2
                    y = 50 - 30
                elif target == "player":
                    x = 50 + 308 // 2
                    y = h - 308 - 50 - 30
                else:
                    x, y = w // 2, h // 2

                # Draw damage text
                font = pygame.font.Font(None, 36)
                color = (255, 0, 0) if text.startswith("-") else (0, 255, 0)
                damage_surface = font.render(text, True, color)
                screen.blit(damage_surface, (x - damage_surface.get_width() // 2, y))

                updated_texts.append([text, target, timer])

    return updated_texts

def show_battle_result_screen(screen, menu_font, w, h, colors, clock, won):
    WHITE = colors.get('WHITE', (255, 255, 255))
    BLACK = colors.get('BLACK', (0, 0, 0))
    GOLD = (255, 215, 0)
    
    result_text = "You won the battle!" if won else "You lost the battle!"
    result_color = GOLD if won else (206, 0, 0)
    
    screen.fill(colors.get('BG', (30, 30, 30)))
    
    # Semi-transparent overlay
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    screen.blit(overlay, (0, 0))
    
    # Result text
    result = menu_font.render(result_text, True, result_color)
    screen.blit(result, (w // 2 - result.get_width() // 2, h // 2 - result.get_height() // 2 - 60))
    
    # Instruction text
    small_font = pygame.font.Font(None, 28)
    instruction = small_font.render("Press SPACE to continue...", True, WHITE)
    screen.blit(instruction, (w // 2 - instruction.get_width() // 2, h // 2 + 60))
    
    pygame.display.flip()
    
    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                    waiting = False
        clock.tick(60)
