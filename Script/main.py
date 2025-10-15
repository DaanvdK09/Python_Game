import pygame
import sys
from io import BytesIO
import requests
from Characters.character import Character, player_w, player_h
from Characters.encounter import is_player_in_bush, trigger_encounter, fetch_random_pokemon, can_trigger_bush, mark_bush_triggered
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD, RED, GREEN
from pathlib import Path

pygame.init()

# Game state
running = True
game_state = "menu"
show_coords = False
encounter_active = False
encounter_pokemon = None

# Screen
Screen_Width = 1285
Screen_Height = 800
screen = pygame.display.set_mode((Screen_Width, Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

# Fonts
menu_font = pygame.font.Font(None, 48)
coords_font = pygame.font.Font(None, 24)

# Map
base_dir = Path(__file__).parent
tmx_path = base_dir / "World" / "maps" / "Level_0.tmx"
game_map = TileMap(tmx_path=str(tmx_path), tile_size=64)

# Character
player = Character()

# Set player start
if game_map.player_start:
    px, py = game_map.player_start
    player.rect.midbottom = (px, py)
    print(f"Spawned player at TMX start: {px}, {py}")
else:
    print("No player start found in TMX. Spawning at (0,0).")
    player.rect.midbottom = (0, 0)

clock = pygame.time.Clock()
offset_x = 0
offset_y = 0

def _wait_for_mouse_release(clock):
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()
        clock.tick(60)
    pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

def draw_encounter_ui(surface, pokemon, w, h):
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    try:
        sprite = pygame.image.load(BytesIO(requests.get(pokemon["sprite"]).content))
        sprite = pygame.transform.scale(sprite, (128, 128))
        surface.blit(sprite, (w // 2 - 64, h // 2 - 100))
    except:
        pass
    name_font = pygame.font.Font(None, 48)
    name_text = name_font.render(f"A wild {pokemon['name']} appeared!", True, (255, 255, 255))
    surface.blit(name_text, (w // 2 - name_text.get_width() // 2, h // 2 - 50))
    stat_font = pygame.font.Font(None, 32)
    hp_text = stat_font.render(f"HP: {pokemon['hp']}", True, (255, 255, 255))
    atk_text = stat_font.render(f"Attack: {pokemon['attack']}", True, (255, 255, 255))
    surface.blit(hp_text, (w // 2 - hp_text.get_width() // 2, h // 2 + 50))
    surface.blit(atk_text, (w // 2 - atk_text.get_width() // 2, h // 2 + 90))
    prompt_font = pygame.font.Font(None, 28)
    prompt_text = prompt_font.render("Press SPACE to continue", True, (255, 255, 255))
    surface.blit(prompt_text, (w // 2 - prompt_text.get_width() // 2, h // 2 + 150))

def show_main_menu():
    while True:
        w, h = screen.get_size()
        menu_result = main_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
        if menu_result == "game":
            return "game"
        if menu_result == "quit":
            return "quit"
        if menu_result == "options":
            opt = options_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if opt == "quit":
                return "quit"

menu_start = show_main_menu()
if menu_start == "game":
    game_state = "game"
elif menu_start == "quit":
    running = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                show_coords = not show_coords
            if encounter_active and event.key == pygame.K_SPACE:
                encounter_active = False
                encounter_pokemon = None
                continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            result = "pause"
        else:
            result = player.handle_event(event)

        if result == "pause" and player.alive and not encounter_active:
            w, h = screen.get_size()
            pause_result = pause_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if pause_result == "game":
                game_state = "game"
            elif pause_result == "menu":
                _wait_for_mouse_release(clock)
                menu_res = show_main_menu()
                if menu_res == "game":
                    game_state = "game"
                elif menu_res == "quit":
                    running = False
            elif pause_result == "pause options":
                opt = options_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                if opt == "quit":
                    running = False
                elif opt == "back":
                    _wait_for_mouse_release(clock)
                    pause_result = pause_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                    if pause_result == "game":
                        game_state = "game"
                    elif pause_result == "menu":
                        _wait_for_mouse_release(clock)
                        menu_res = show_main_menu()
                        if menu_res == "game":
                            game_state = "game"
                        elif menu_res == "quit":
                            running = False

    if game_state == "game" and not encounter_active:
        keys = pygame.key.get_pressed()
        player.update(keys, game_map)
        bush_rects = game_map.get_bush_rects()
        bush_hit = is_player_in_bush(player.rect, bush_rects)

        if bush_hit and can_trigger_bush(bush_hit) and trigger_encounter():
            encounter_pokemon = fetch_random_pokemon()
            if encounter_pokemon:
                encounter_active = True
                mark_bush_triggered(bush_hit)
                print(f"Wild {encounter_pokemon['name']} appeared in bush at ({bush_hit.x}, {bush_hit.y})!")
        view_w, view_h = screen.get_size()
        try:
            map_w = game_map.width
            map_h = game_map.height
        except Exception:
            cols = getattr(game_map, "cols", None) or getattr(game_map, "columns", None) or getattr(game_map, "num_cols", None)
            rows = getattr(game_map, "rows", None) or getattr(game_map, "rows_count", None) or getattr(game_map, "num_rows", None)
            tile = getattr(game_map, "tile_size", None) or getattr(game_map, "tilewidth", None) or getattr(game_map, "tile_size_px", None)
            if cols and rows and tile:
                map_w = cols * tile
                map_h = rows * tile
            else:
                map_w, map_h = view_w, view_h
        cam_left = player.rect.centerx - view_w // 2
        cam_top = player.rect.centery - view_h // 2
        offset_x = -cam_left
        offset_y = -cam_top
    else:
        offset_x = 0
        offset_y = 0

    screen.fill(BG)
    game_map.draw(screen, offset_x=offset_x, offset_y=offset_y)
    player.draw(screen, offset_x=offset_x, offset_y=offset_y)

    #Debug
    if show_coords:
        debug_rect = pygame.Rect(
            player.rect.x + offset_x + player_w // 4,
            player.rect.y + offset_y,
            player_w // 2,
            player_h
        )
        pygame.draw.rect(screen, (RED), debug_rect, 2)

        bush_rects = game_map.get_bush_rects()
        bush_hit = None
        for b in bush_rects:
            if player.rect.colliderect(b):
                bush_hit = b
                break

        if bush_hit:
            debug_bush = pygame.Rect(
                bush_hit.x + offset_x,
                bush_hit.y + offset_y,
                bush_hit.width,
                bush_hit.height
            )
            pygame.draw.rect(screen, (GREEN), debug_bush, 2)

    if show_coords:
        world_x = player.rect.x
        world_y = player.rect.y
        tile_size = getattr(game_map, "tile_size", 64)
        tile_x = world_x // tile_size
        tile_y = world_y // tile_size
        text = f"World: {world_x}, {world_y}   Tile: {tile_x}, {tile_y}"
        surf = coords_font.render(text, True, (255, 255, 255))
        bg_rect = pygame.Rect(8, 8, surf.get_width() + 8, surf.get_height() + 8)
        pygame.draw.rect(screen, (0, 0, 0), bg_rect)
        screen.blit(surf, (12, 12))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()