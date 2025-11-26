import pygame
import sys
from io import BytesIO
import requests
from Characters.character import Character, player_w, player_h
from Characters.encounter import (
    is_player_in_bush,
    trigger_encounter,
    fetch_random_pokemon,
    can_trigger_bush,
    mark_bush_triggered,
)
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from UI.battle_menu import battle_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD, RED, BLUE, GREEN, YELLOW, WHITE
from pathlib import Path

pygame.init()

# Game state
running = True
game_state = "menu"
show_coords = False
show_map = False
encounter_active = False
encounter_pokemon = None
encounter_animation_done = False

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
tmx_path = base_dir / "World" / "maps" / "World.tmx"
game_map = TileMap(tmx_path=str(tmx_path), tile_size=64)

# Character
player = Character()

# Set player start
if game_map.player_start:
    px, py = game_map.player_start
    player.rect.midbottom = (px, py)
    player.hitbox_rect.midbottom = player.rect.midbottom
    print(f"Spawned player at TMX start: {px}, {py}")
else:
    print("No player start found in TMX. Spawning at (0,0).")
    player.rect.midbottom = (0, 0)

clock = pygame.time.Clock()
offset_x = 0
offset_y = 0


def pokemon_encounter_animation(surface, w, h, clock, pokemon):
    flash_surface = pygame.Surface((w, h))
    flash_surface.fill((255, 255, 255))
    
    for alpha in range(0, 256, 15):
        flash_surface.set_alpha(alpha)
        surface.blit(flash_surface, (0, 0))
        pygame.display.update()
        clock.tick(60)
    
    flash_surface.set_alpha(255)
    surface.blit(flash_surface, (0, 0))
    pygame.display.update()
    pygame.time.delay(200)
    
    bg_img = None
    try:
        bg_img = pygame.image.load("../graphics/backgrounds/forest.png").convert()
        bg_img = pygame.transform.scale(bg_img, (w, h))
    except Exception:
        pass
    
    try:
        sprite_data = requests.get(pokemon["sprite"], timeout=5)
        sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
        sprite = pygame.transform.scale(sprite, (192, 192))
    except Exception:
        sprite = None
    
    if sprite:
        start_x = w
        end_x = w - 200 - 96
        end_y = h // 2 - 40 - 96
        frames = 15
        
        for frame in range(frames):
            if bg_img:
                surface.blit(bg_img, (0, 0))
            else:
                surface.fill((255, 255, 255))
            progress = frame / frames
            white_overlay = pygame.Surface((w, h))
            white_overlay.fill((255, 255, 255))
            white_overlay.set_alpha(int(255 * (1 - progress)))
            surface.blit(white_overlay, (0, 0))
            
            # Draw sprite
            x_pos = int(start_x - (start_x - end_x) * progress)
            y_pos = int(h // 2 - 100 - (h // 2 - 100 - end_y) * progress)
            surface.blit(sprite, (x_pos, y_pos))
            pygame.display.update()
            clock.tick(60)


def draw_encounter_ui(surface, pokemon, w, h):
    try:
        bg_img = pygame.image.load("../graphics/backgrounds/forest.png").convert()
        bg_img = pygame.transform.scale(bg_img, (w, h))
        surface.blit(bg_img, (0, 0))
    except:
        surface.fill((40, 120, 40))

    try:
        sprite_data = requests.get(pokemon["sprite"], timeout=5)
        sprite = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
        sprite = pygame.transform.scale(sprite, (128, 128))
    except Exception:
        sprite = None

    if sprite:
        x_pos = w
        target_x = w // 2 - 64
        for step in range(20):
            surface.fill((40, 120, 40))
            if sprite:
                surface.blit(sprite, (x_pos, h // 2 - 100))
            pygame.display.flip()
            pygame.time.delay(20)
            x_pos -= (w // 2 + 64) // 20

    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    surface.blit(overlay, (0, 0))

    name_font = pygame.font.Font(None, 48)
    stat_font = pygame.font.Font(None, 32)
    prompt_font = pygame.font.Font(None, 28)

    name_text = name_font.render(
        f"A wild {pokemon['name']} appeared!", True, (255, 255, 255)
    )
    hp_text = stat_font.render(f"HP: {pokemon['hp']}", True, (255, 255, 255))
    atk_text = stat_font.render(f"Attack: {pokemon['attack']}", True, (255, 255, 255))
    prompt_text = prompt_font.render(
        "Press SPACE to continue", True, (255, 255, 255)
    )

    surface.blit(name_text, (w // 2 - name_text.get_width() // 2, h // 2 + 30))
    surface.blit(hp_text, (w // 2 - hp_text.get_width() // 2, h // 2 + 90))
    surface.blit(atk_text, (w // 2 - atk_text.get_width() // 2, h // 2 + 130))
    surface.blit(prompt_text, (w // 2 - prompt_text.get_width() // 2, h // 2 + 200))


def _wait_for_mouse_release(clock):
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()
        clock.tick(60)
    pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))


def show_main_menu():
    while True:
        w, h = screen.get_size()
        menu_result = main_menu(
            screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock
        )
        if menu_result == "game":
            return "game"
        if menu_result == "quit":
            return "quit"
        if menu_result == "options":
            opt = options_menu(
                screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock
            )
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
            if event.key == pygame.K_m:
                # Toggle world map overlay
                show_map = not show_map

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            result = "pause"
        else:
            result = player.handle_event(event)

        if result == "pause" and player.alive and not encounter_active:
            w, h = screen.get_size()
            pause_result = pause_menu(
                screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock
            )
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
        try:
            keys = pygame.key.get_pressed()
        except pygame.error as e:
            # If the video system was lost for some reason, try to re-init the display
            print("Warning: pygame.video not initialized, attempting to re-init display:", e)
            try:
                pygame.display.init()
                screen = pygame.display.set_mode((Screen_Width, Screen_Height))
                keys = pygame.key.get_pressed()
            except Exception as e2:
                print("Failed to re-init display:", e2)
                # Skip this frame to avoid hard crash
                keys = [False] * 512
        player.update(keys, game_map)
        bush_rects = game_map.get_bush_rects()
        bush_hit = is_player_in_bush(player.rect, bush_rects)

        if bush_hit and can_trigger_bush(bush_hit) and trigger_encounter():
            encounter_pokemon = fetch_random_pokemon()
            if encounter_pokemon:
                pokemon_encounter_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
                encounter_active = True
                mark_bush_triggered(bush_hit)
                print(
                    f"Wild {encounter_pokemon['name']} appeared in bush at ({bush_hit.x}, {bush_hit.y})!"
                )

        view_w, view_h = screen.get_size()
        map_w = getattr(game_map, "width", view_w)
        map_h = getattr(game_map, "height", view_h)
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

    # World map overlay (optimized, cached, circular)
    if show_map and getattr(game_map, "tmx", None):
        try:
            # Use a cached mini-map surface so we don't rebuild every frame
            if not hasattr(game_map, "_cached_mini") or game_map._cached_mini is None:
                tmx = game_map.tmx
                tile_cols = getattr(tmx, "width", 0)
                tile_rows = getattr(tmx, "height", 0)
                if tile_cols <= 0 or tile_rows <= 0:
                    raise RuntimeError("Empty TMX dimensions")

                # Choose a small tile pixel size so the mini-map stays lightweight
                max_dim = 180  # max width/height of the mini map in pixels
                tile_pixel = max(1, min(6, max_dim // max(tile_cols, tile_rows)))
                overlay_w = tile_pixel * tile_cols
                overlay_h = tile_pixel * tile_rows

                # Build a simplified version of the map using colored blocks
                mini = pygame.Surface((overlay_w, overlay_h), pygame.SRCALPHA)
                # ground color
                mini.fill((200, 200, 200, 255))

                # Helpful variables for scaling world->mini coords
                world_tile_w = getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64))
                world_tile_h = getattr(game_map, "tileheight", getattr(game_map, "tile_size", 64))

                # Draw tile layers with simple colors for clarity (water, buildings) and fall back to image-presence
                try:
                    for layer in tmx.visible_layers:
                        layer_name = (getattr(layer, "name", "") or "").lower()
                        layer_props = getattr(layer, "properties", {}) or {}

                        # choose color by layer name
                        if "water" in layer_name:
                            tile_color = BLUE
                        elif "building" in layer_name or "buildings" in layer_name:
                            tile_color = (139, 69, 19)  # brown
                        else:
                            tile_color = None

                        if hasattr(layer, "tiles"):
                            for x, y, gid in layer.tiles():
                                if gid == 0:
                                    continue
                                rx = x * tile_pixel
                                ry = y * tile_pixel
                                if tile_color:
                                    pygame.draw.rect(mini, tile_color, pygame.Rect(rx, ry, tile_pixel, tile_pixel))
                                else:
                                    # draw a faint darkened block for any non-empty tile to indicate structure
                                    pygame.draw.rect(mini, (170, 170, 170), pygame.Rect(rx, ry, tile_pixel, tile_pixel))
                except Exception:
                    pass

                # Draw collisions as dark overlay (higher priority)
                for rect in game_map.get_solid_rects():
                    try:
                        x = int((rect.x / world_tile_w) * tile_pixel)
                        y = int((rect.y / world_tile_h) * tile_pixel)
                        w = max(1, int((rect.width / world_tile_w) * tile_pixel))
                        h = max(1, int((rect.height / world_tile_h) * tile_pixel))
                        pygame.draw.rect(mini, (80, 80, 80), pygame.Rect(x, y, w, h))
                    except Exception:
                        continue

                # Draw bushes as green hints (above ground but below marker)
                try:
                    for rect in game_map.get_bush_rects():
                        x = int((rect.x / world_tile_w) * tile_pixel)
                        y = int((rect.y / world_tile_h) * tile_pixel)
                        w = max(1, int((rect.width / world_tile_w) * tile_pixel))
                        h = max(1, int((rect.height / world_tile_h) * tile_pixel))
                        pygame.draw.rect(mini, (34, 139, 34), pygame.Rect(x, y, w, h))
                except Exception:
                    pass

                # Apply circular mask so minimap appears round
                mask = pygame.Surface((overlay_w, overlay_h), pygame.SRCALPHA)
                mask.fill((0, 0, 0, 0))
                radius = min(overlay_w, overlay_h) // 2
                pygame.draw.circle(mask, (255, 255, 255, 255), (overlay_w // 2, overlay_h // 2), radius)
                mini.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                # Cache useful values on the game_map object
                game_map._cached_mini = mini
                game_map._cached_tile_pixel = tile_pixel
                game_map._cached_overlay_size = (overlay_w, overlay_h)

            mini = game_map._cached_mini
            overlay_w, overlay_h = game_map._cached_overlay_size

            # Position (top-right) with margin; draw only the circular minimap and its circular border
            margin = 10
            x = screen.get_width() - overlay_w - margin
            y = margin
            screen.blit(mini, (x, y))
            pygame.draw.circle(screen, (255, 255, 255), (x + overlay_w // 2, y + overlay_h // 2), min(overlay_w, overlay_h) // 2, 1)

            # Draw player marker (compute relative position)
            world_w = getattr(game_map, "width", 1)
            world_h = getattr(game_map, "height", 1)
            if world_w and world_h:
                px = int(player.rect.centerx / world_w * overlay_w)
                py = int(player.rect.centery / world_h * overlay_h)
                # Translate to screen coords
                screen_px = x + px
                screen_py = y + py
                marker_radius = max(2, game_map._cached_tile_pixel // 2)
                pygame.draw.circle(screen, (255, 0, 0), (screen_px, screen_py), marker_radius)

        except Exception:
            # If something goes wrong with rendering the cached mini-map, clear cache and ignore overlay
            try:
                game_map._cached_mini = None
            except Exception:
                pass

    # Debug
    if show_coords:
        # Draw coordinates
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

        # Draw player hitbox
        pygame.draw.rect(
            screen,
            (RED),
            pygame.Rect(
                player.hitbox_rect.x + offset_x,
                player.hitbox_rect.y + offset_y,
                player.hitbox_rect.width,
                player.hitbox_rect.height,
            ),
            2,
        )

        # Draw bushes
        for bush in game_map.get_bush_rects():
            pygame.draw.rect(
                screen,
                (BLUE),
                pygame.Rect(
                    bush.x + offset_x, bush.y + offset_y, bush.width, bush.height
                ),
                2,
            )

        # Draw collision tiles
        for wall in game_map.get_solid_rects():
            pygame.draw.rect(
                screen,
                (GREEN),
                pygame.Rect(
                    wall.x + offset_x, wall.y + offset_y, wall.width, wall.height
                ),
                1,
            )

    # Encounter/Battle UI
    if encounter_active and encounter_pokemon:
        w, h = screen.get_size()
        choice = battle_menu(
            screen,
            encounter_pokemon,
            menu_font,
            coords_font,
            {"WHITE": WHITE, "BLACK": BLACK, "BG": BG},
            clock,
        )
        print(f"Battle choice: {choice}")
        if choice == "fight":
            # placeholder
            print(f"you attacked {encounter_pokemon['name']}")
        
        if choice == "pokémon":
            # placeholder
            print("your pokémon")

        if choice == "bag":
            # placeholder
            print("your items")

        if choice == "run":
            encounter_active = False
            encounter_pokemon = None
            encounter_animation_done = False
            
        else:
            encounter_active = False
            encounter_pokemon = None
            encounter_animation_done = False
    pygame.display.flip()
    clock.tick(60)

pygame.quit()