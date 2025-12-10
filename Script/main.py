import pygame
import sys
from io import BytesIO
import requests
import threading
from collections import deque
import json
import random
from Characters.character import Character, player_w, player_h
from Characters.NPC import NPC
from Characters.encounter import (
    is_player_in_bush,
    trigger_encounter,
    fetch_random_pokemon,
    can_trigger_bush,
    mark_bush_triggered,
)
from Characters.pokedex import Pokedex, Pokemon
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from UI.battle_menu import battle_menu
from UI.dialogue_box import show_dialogue, show_tutorial, show_tutorial_choice
from UI.pokedex_menu import quick_pokemon_select, pokedex_menu
from World.map import TileMap
from Quests.Introduction import introduction_dialogue
from constants import BG, BLACK, GOLD, RED, BLUE, GREEN, YELLOW, WHITE
from pathlib import Path

pygame.init()

# Game state
running = True
game_state = "menu"
show_coords = False
show_map = False
show_pokedex = False
encounter_active = False
encounter_pokemon = None
encounter_animation_done = False
tutorial_shown = False  # Track if tutorial has been shown
current_player_pokemon = None
just_switched_pokemon = False

# Initialize Pokédex
pokedex = Pokedex()
#TEMP
if pokedex.get_captured_count() == 0:
    starter = Pokemon(name="Pikachu", hp=35, attack=55, sprite="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png", level=5)
    pokedex.add_pokemon(starter)
    print("Added starter Pokémon: Pikachu")
current_player_pokemon = pokedex.get_first_available_pokemon()

# Bag
bag = {
    "Potion": 0,
    "Pokeball": 0,
}

# Bag overlay toggle
show_bag = False

# Screen
Screen_Width = 1285
Screen_Height = 800
screen = pygame.display.set_mode((Screen_Width, Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

# Fonts
menu_font = pygame.font.Font(None, 48)
coords_font = pygame.font.Font(None, 24)
encounter_name_font = pygame.font.Font(None, 48)
encounter_stat_font = pygame.font.Font(None, 32)
encounter_prompt_font = pygame.font.Font(None, 28)
run_msg_font = pygame.font.Font(None, 56)

# Map
base_dir = Path(__file__).parent
tmx_path = base_dir / "World" / "maps" / "World.tmx"
game_map = TileMap(tmx_path=str(tmx_path), tile_size=64)

#Music
pygame.mixer.music.load("audio/secret.mp3")
pygame.mixer.music.set_volume(0.5)  
pygame.mixer.music.play(-1)          

# Character
player = Character()

# Professor NPC functional placeholder
professor = None

# Set player start
if game_map.player_start:
    px, py = game_map.player_start
    player.rect.midbottom = (px, py)
    player.hitbox_rect.midbottom = player.rect.midbottom
    print(f"Spawned player at TMX start: {px}, {py}")
else:
    print("No player start found in TMX. Spawning at (0,0).")
    player.rect.midbottom = (0, 0)
    # Ensure hitbox is positioned and float position synced
    player.hitbox_rect.midbottom = player.rect.midbottom

try:
    # if Character has _fx/_fy, sync them to the current hitbox position
    player._fx = float(player.hitbox_rect.x)
    player._fy = float(player.hitbox_rect.y)
except Exception:
    pass

# Initialize professor spawn if the TMX specified a spawn object for the professor
prof_pos = getattr(game_map, "professor_start", None)
if prof_pos:
    try:
        px, py = prof_pos
        professor = NPC(px, py, name="Professor Oak", use_sprite_sheet=False)
        print(f"Spawned professor at TMX start: {px}, {py}")
    except Exception as e:
        print(f"Failed to spawn professor: {e}")
else:
    try:
        px, py = player.rect.midbottom
        px += 100
        professor = NPC(px, py, name="Professor Oak", use_sprite_sheet=False, scale=0.8)
        print(f"Spawned professor at fallback position: {px}, {py}")
    except Exception as e:
        print(f"Failed to spawn fallback professor: {e}")

clock = pygame.time.Clock()
offset_x = 0
offset_y = 0

_IMAGE_BYTES_CACHE = {}
_SCALED_SURFACE_CACHE = {}
_BG_SURFACE_CACHE = {}

def _download_bytes(url, timeout=5.0):
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.ok:
            return resp.content
    except Exception:
        return None
    return None

def _prefetch_assets():
    try:
        root = base_dir.parent
        pfile = root / "pokemon_cache.json"
        if pfile.exists():
            try:
                with pfile.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                data = None

            if isinstance(data, list):
                for p in data:
                    url = p.get("sprite") if isinstance(p, dict) else None
                    if url and url not in _IMAGE_BYTES_CACHE:
                        b = _download_bytes(url)
                        if b:
                            _IMAGE_BYTES_CACHE[url] = b

        try:
            bg_path = base_dir.parent / "graphics" / "backgrounds" / "forest.png"
            if bg_path.exists():
                with bg_path.open("rb") as f:
                    _IMAGE_BYTES_CACHE["__bg_forest_local__"] = f.read()
        except Exception:
            pass
    except Exception:
        pass

try:
    t = threading.Thread(target=_prefetch_assets, daemon=True)
    t.start()
except Exception:
    pass

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
        key = ("forest", (w, h))
        if key in _BG_SURFACE_CACHE:
            bg_img = _BG_SURFACE_CACHE[key]
        else:
            if "__bg_forest_local__" in _IMAGE_BYTES_CACHE:
                surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE["__bg_forest_local__"]))
                surf = surf.convert()
                surf = pygame.transform.scale(surf, (w, h))
                _BG_SURFACE_CACHE[key] = surf
                bg_img = surf
            else:
                bg_path = base_dir.parent / "graphics" / "backgrounds" / "forest.png"
                if bg_path.exists():
                    surf = pygame.image.load(str(bg_path)).convert()
                    surf = pygame.transform.scale(surf, (w, h))
                    _BG_SURFACE_CACHE[key] = surf
                    bg_img = surf
    except Exception:
        bg_img = None

    sprite = None
    try:
        url = pokemon.get("sprite")
        if url:
            cache_key = (url, (192, 192))
            if cache_key in _SCALED_SURFACE_CACHE:
                sprite = _SCALED_SURFACE_CACHE[cache_key]
            else:
                if url in _IMAGE_BYTES_CACHE:
                    surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE[url])).convert_alpha()
                    surf = pygame.transform.scale(surf, (192, 192))
                    _SCALED_SURFACE_CACHE[cache_key] = surf
                    sprite = surf
                else:
                    b = _download_bytes(url, timeout=1.5)
                    if b:
                        _IMAGE_BYTES_CACHE[url] = b
                        surf = pygame.image.load(BytesIO(b)).convert_alpha()
                        surf = pygame.transform.scale(surf, (192, 192))
                        _SCALED_SURFACE_CACHE[cache_key] = surf
                        sprite = surf
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

def run_away_animation(surface, w, h, clock, pokemon):
    sw, sh = surface.get_size()

    sprite = None
    try:
        url = pokemon.get("sprite") if pokemon else None
        if url:
            cache_key = (url, (128, 128))
            if cache_key in _SCALED_SURFACE_CACHE:
                sprite = _SCALED_SURFACE_CACHE[cache_key]
            else:
                if url in _IMAGE_BYTES_CACHE:
                    surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE[url])).convert_alpha()
                    surf = pygame.transform.scale(surf, (128, 128))
                    _SCALED_SURFACE_CACHE[cache_key] = surf
                    sprite = surf
                else:
                    b = _download_bytes(url, timeout=1.5)
                    if b:
                        _IMAGE_BYTES_CACHE[url] = b
                        surf = pygame.image.load(BytesIO(b)).convert_alpha()
                        surf = pygame.transform.scale(surf, (128, 128))
                        _SCALED_SURFACE_CACHE[cache_key] = surf
                        sprite = surf
    except Exception:
        sprite = None

    bg_img = None
    try:
        key = ("forest", (sw, sh))
        if key in _BG_SURFACE_CACHE:
            bg_img = _BG_SURFACE_CACHE[key]
        else:
            if "__bg_forest_local__" in _IMAGE_BYTES_CACHE:
                surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE["__bg_forest_local__"]))
                surf = surf.convert()
                surf = pygame.transform.scale(surf, (sw, sh))
                _BG_SURFACE_CACHE[key] = surf
                bg_img = surf
            else:
                bg_path = base_dir.parent / "graphics" / "backgrounds" / "forest.png"
                if bg_path.exists():
                    surf = pygame.image.load(str(bg_path)).convert()
                    surf = pygame.transform.scale(surf, (sw, sh))
                    _BG_SURFACE_CACHE[key] = surf
                    bg_img = surf
    except Exception:
        bg_img = None

    frames = 24
    for frame in range(frames):
        progress = frame / float(frames - 1)

        # background
        if bg_img:
            surface.blit(bg_img, (0, 0))
        else:
            surface.fill((40, 120, 40))

        if sprite:
            start_x = sw // 2 - 64
            end_x = sw + 200
            x = int(start_x + (end_x - start_x) * progress)
            y = sh // 2 - 100
            surface.blit(sprite, (x, y))
        else:
            box_w, box_h = 128, 128
            start_x = sw // 2 - box_w // 2
            end_x = sw + 200
            x = int(start_x + (end_x - start_x) * progress)
            y = sh // 2 - 100
            pygame.draw.rect(surface, (100, 100, 100), pygame.Rect(x, y, box_w, box_h))

        alpha = int(255 * progress)
        msg_surf = run_msg_font.render("You ran away!", True, (255, 255, 255))
        msg_bg = pygame.Surface((msg_surf.get_width() + 24, msg_surf.get_height() + 16), pygame.SRCALPHA)
        msg_bg.fill((0, 0, 0, int(alpha * 0.6)))
        msg_pos = (sw // 2 - msg_bg.get_width() // 2, sh // 2 + 80)
        surface.blit(msg_bg, msg_pos)
        surface.blit(msg_surf, (msg_pos[0] + 12, msg_pos[1] + 8))

        pygame.display.update()
        clock.tick(60)

    pygame.time.delay(220)

def draw_encounter_ui(surface, pokemon, w, h):
    try:
        key = ("forest", (w, h))
        if key in _BG_SURFACE_CACHE:
            surface.blit(_BG_SURFACE_CACHE[key], (0, 0))
        else:
            if "__bg_forest_local__" in _IMAGE_BYTES_CACHE:
                surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE["__bg_forest_local__"]))
                surf = surf.convert()
                surf = pygame.transform.scale(surf, (w, h))
                _BG_SURFACE_CACHE[key] = surf
                surface.blit(surf, (0, 0))
            else:
                bg_path = base_dir.parent / "graphics" / "backgrounds" / "forest.png"
                if bg_path.exists():
                    surf = pygame.image.load(str(bg_path)).convert()
                    surf = pygame.transform.scale(surf, (w, h))
                    _BG_SURFACE_CACHE[key] = surf
                    surface.blit(surf, (0, 0))
                else:
                    surface.fill((40, 120, 40))
    except Exception:
        surface.fill((40, 120, 40))

    sprite = None
    try:
        url = pokemon.get("sprite")
        if url:
            cache_key = (url, (128, 128))
            if cache_key in _SCALED_SURFACE_CACHE:
                sprite = _SCALED_SURFACE_CACHE[cache_key]
            else:
                if url in _IMAGE_BYTES_CACHE:
                    surf = pygame.image.load(BytesIO(_IMAGE_BYTES_CACHE[url])).convert_alpha()
                    surf = pygame.transform.scale(surf, (128, 128))
                    _SCALED_SURFACE_CACHE[cache_key] = surf
                    sprite = surf
                else:
                    b = _download_bytes(url, timeout=1.5)
                    if b:
                        _IMAGE_BYTES_CACHE[url] = b
                        surf = pygame.image.load(BytesIO(b)).convert_alpha()
                        surf = pygame.transform.scale(surf, (128, 128))
                        _SCALED_SURFACE_CACHE[cache_key] = surf
                        sprite = surf
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

    name_text = encounter_name_font.render(f"A wild {pokemon['name']} appeared!", True, (255, 255, 255))
    hp_text = encounter_stat_font.render(f"HP: {pokemon['hp']}", True, (255, 255, 255))
    atk_text = encounter_stat_font.render(f"Attack: {pokemon['attack']}", True, (255, 255, 255))
    prompt_text = encounter_prompt_font.render("Press SPACE to continue", True, (255, 255, 255))

    surface.blit(name_text, (w // 2 - name_text.get_width() // 2, h // 2 + 30))
    surface.blit(hp_text, (w // 2 - hp_text.get_width() // 2, h // 2 + 90))
    surface.blit(atk_text, (w // 2 - atk_text.get_width() // 2, h // 2 + 130))
    surface.blit(prompt_text, (w // 2 - prompt_text.get_width() // 2, h // 2 + 200))

def show_bag_menu(screen, bag, menu_font, small_font, colors, clock, in_battle=False, encounter_pokemon=None, current_player_pokemon=None, pokedex_obj=None):
    items = [k for k in bag.keys()]
    if not items:
        return {"action": "closed", "item": None}

    selected = 0
    FPS = 60
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(items)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(items)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    item = items[selected]
                    count = bag.get(item, 0)
                    if count <= 0:
                        # nothing to use
                        pass
                    else:
                        # Use item
                        if in_battle and encounter_pokemon and item.lower().startswith("pokeball"):
                            try:
                                hp = float(encounter_pokemon.get('hp', 1))
                            except Exception:
                                hp = 1.0
                            # base chance
                            chance = 0.5
                            # if hp small, improve chance
                            if hp <= 5:
                                chance = 0.9
                            elif hp <= 15:
                                chance = 0.7
                            # consume ball
                            bag[item] = max(0, count - 1)
                            got = random.random() < chance
                            if got and pokedex_obj is not None:
                                # Add to pokedex
                                try:
                                    p = Pokemon(name=encounter_pokemon.get('name', 'Unknown'), hp=encounter_pokemon.get('hp', 10), attack=encounter_pokemon.get('attack', 10), sprite=encounter_pokemon.get('sprite'))
                                    pokedex_obj.add_pokemon(p)
                                except Exception:
                                    pass
                            return {"action": "caught" if got else "used", "item": item, "caught_pokemon": encounter_pokemon if got else None}
                        elif item.lower().startswith("potion"):
                            # Heal current player's pokemon
                            if current_player_pokemon is not None:
                                # heal amount
                                heal = 20
                                try:
                                    max_hp = getattr(current_player_pokemon, 'hp', getattr(current_player_pokemon, 'max_hp', None))
                                except Exception:
                                    max_hp = None
                                # If object has current_hp, heal that
                                if hasattr(current_player_pokemon, 'current_hp'):
                                    current_player_pokemon.current_hp = min(getattr(current_player_pokemon, 'current_hp', getattr(current_player_pokemon, 'hp', 0)) + heal, getattr(current_player_pokemon, 'hp', getattr(current_player_pokemon, 'current_hp', 0)))
                                bag[item] = max(0, count - 1)
                                return {"action": "used", "item": item}
                            else:
                                # no pokemon to use on
                                return {"action": "none", "item": item}
                        else:
                            # Unknown item: just consume
                            bag[item] = max(0, count - 1)
                            return {"action": "used", "item": item}
                elif event.key == pygame.K_ESCAPE:
                    return {"action": "closed", "item": None}

        # Render bag UI
        sw, sh = screen.get_size()
        panel_w = min(520, sw - 80)
        panel_h = min(360, sh - 120)
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h))
        panel.fill(colors.get('BG', (30, 30, 30)))
        # Title
        title = menu_font.render("Bag", True, colors.get('WHITE', (255,255,255)))
        panel.blit(title, (20, 12))

        # List items
        list_start_y = 64
        list_item_h = 56
        visible = (panel_h - list_start_y - 20) // list_item_h
        start = max(0, selected - visible // 2)
        for i, name in enumerate(items[start:start + visible]):
            idx = start + i
            y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(20, y, panel_w - 40, list_item_h - 8)
            if idx == selected:
                pygame.draw.rect(panel, (80, 120, 160), item_rect)
            else:
                pygame.draw.rect(panel, (50, 50, 70), item_rect)
            pygame.draw.rect(panel, (120, 120, 140), item_rect, 1)
            label = small_font.render(f"{name} x{bag.get(name,0)}", True, colors.get('WHITE', (255,255,255)))
            panel.blit(label, (item_rect.x + 8, item_rect.y + 8))

        # Blit centered
        screen.blit(panel, (px, py))
        pygame.display.flip()
        clock.tick(FPS)

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

def start_build_full_map():
    # Avoid starting twice
    if getattr(game_map, "_full_map_built", False):
        game_map._full_map_progress = 1.0
        return
    if getattr(game_map, "_full_map_building", False):
        return
    # Prepare non-blocking incremental build state (processed in main loop)
    game_map._full_map_building = True
    game_map._full_map_progress = 0.0
    game_map._full_map_built = False
    # queue and caches
    game_map._full_map_build_queue = deque()
    game_map._full_map_build_gid_scaled_cache = {}
    game_map._full_map_build_gid_color_cache = {}
    game_map._full_map_build_total = 0
    game_map._full_map_processed = 0
    game_map._full_map_present_count = 0
    game_map._full_map_missing_count = 0

    def worker():
        try:
            import time
            t0 = time.perf_counter()
            tmx = game_map.tmx
            world_w = getattr(game_map, "width", 0)
            world_h = getattr(game_map, "height", 0)
            if world_w <= 0 or world_h <= 0:
                game_map._full_map_building = False
                return
            sw, sh = screen.get_size()
            scale = min((sw * 0.88) / world_w, (sh * 0.88) / world_h, 1.0)
            tile_px = max(1, int(getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64)) * scale))
            cols = int(world_w // getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64)))
            rows = int(world_h // getattr(game_map, "tileheight", getattr(game_map, "tile_size", 64)))
            full_w = tile_px * cols
            full_h = tile_px * rows
            full_surf = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
            full_surf.fill((0, 0, 0, 0))

            # Collect tiles
            tiles = []
            for layer in tmx.visible_layers:
                # Skip entire layers flagged as collision
                layer_name = (getattr(layer, "name", "") or "").lower()
                layer_props = getattr(layer, "properties", {}) or {}
                if layer_name == "collision" or layer_props.get("collision") is True:
                    print(f"Skipping collision layer in full map build: {layer_name}")
                    continue
                if not hasattr(layer, "tiles"):
                    continue
                for x, y, gid in layer.tiles():
                    if gid == 0:
                        continue
                    tiles.append((x, y, gid))
            print(f"Full map tiles collected: {len(tiles)} (example gids: {[type(gid) for (_,_,gid) in tiles[:6]] if tiles else 'none'})")
            total = len(tiles) if tiles else 1
            # record progress total
            game_map._full_map_build_total = total

            gid_scaled_cache = game_map._full_map_build_gid_scaled_cache
            gid_color_cache = game_map._full_map_build_gid_color_cache
            processed = 0
            missing_tiles = 0
            present_tiles = 0
            # Store tiles into the queue for incremental processing in main loop (no pygame transforms here)
            for (x, y, gid) in tiles:
                game_map._full_map_build_queue.append((x, y, gid))

            # store bounds/sizes and surface to blit into
            cols = int(world_w // getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64)))
            rows = int(world_h // getattr(game_map, "tileheight", getattr(game_map, "tile_size", 64)))
            full_w = tile_px * cols
            full_h = tile_px * rows
            full_surf = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
            full_surf.fill((0, 0, 0, 0))

            # finalize caches (worker only queues tiles; main thread will do pygame operations)
            game_map._full_map_surf = full_surf
            game_map._full_map_scale = tile_px / getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64))
            game_map._full_map_tile_px = tile_px
            game_map._full_map_cols = cols
            game_map._full_map_rows = rows
            # do not assert built/completion here; main thread will finalize after processing the queue
            game_map._gid_scaled_cache = gid_scaled_cache
            game_map._tile_gid_map = { (x,y): int(gid) if not isinstance(gid, pygame.Surface) else None for (x,y,gid) in tiles }
            t1 = time.perf_counter()
            print(f"Full map build queued in {t1 - t0:.3f} seconds (tiles queued: {total})")
        except Exception:
            game_map._full_map_building = False
            game_map._full_map_built = False

    try:
        th = threading.Thread(target=worker, daemon=True)
        game_map._full_map_th = th
        th.start()
    except Exception:
        # as a fallback, build synchronously
        worker()
        tmx = game_map.tmx
        world_w = getattr(game_map, "width", 0)
        world_h = getattr(game_map, "height", 0)
        if world_w <= 0 or world_h <= 0:
            return
        sw, sh = screen.get_size()
        scale = min((sw * 0.88) / world_w, (sh * 0.88) / world_h, 1.0)
        tile_px = max(1, int(getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64)) * scale))
        cols = int(world_w // getattr(game_map, "tilewidth", getattr(game_map, "tile_size", 64)))
        rows = int(world_h // getattr(game_map, "tileheight", getattr(game_map, "tile_size", 64)))
        full_w = tile_px * cols
        full_h = tile_px * rows
        full_surf = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
        gid_scaled_cache = {}
        for layer in tmx.visible_layers:
            layer_name = (getattr(layer, "name", "") or "").lower()
            layer_props = getattr(layer, "properties", {}) or {}
            if layer_name == "collision" or layer_props.get("collision") is True:
                print(f"Skipping collision layer in fallback full map build: {layer_name}")
                continue
            if not hasattr(layer, "tiles"):
                continue
            for x, y, gid in layer.tiles():
                if gid == 0:
                    continue
                if gid in gid_scaled_cache:
                    small = gid_scaled_cache[gid]
                else:
                    try:
                        tile_img = tmx.get_tile_image_by_gid(gid)
                        if tile_img is not None:
                            # Preserve aspect ratio for sync fallback scaling too (scale both width and height)
                            scale_fact = tile_px / float(getattr(game_map, 'tilewidth', game_map.tile_size))
                            orig_w = tile_img.get_width()
                            orig_h = tile_img.get_height()
                            new_w = max(1, int(round(orig_w * scale_fact)))
                            new_h = max(1, int(round(orig_h * scale_fact)))
                            small = pygame.transform.smoothscale(tile_img, (new_w, new_h))
                        else:
                            small = None
                    except Exception:
                        small = None
                    gid_scaled_cache[gid] = small
                if small:
                    try:
                        extra_scaled = max(0, small.get_height() - tile_px)
                    except Exception:
                        extra_scaled = 0
                    full_surf.blit(small, (x * tile_px, y * tile_px - extra_scaled))
        game_map._full_map_surf = full_surf
        game_map._full_map_built = True
        game_map._full_map_building = False
        game_map._full_map_progress = 1.0

menu_start = show_main_menu()
# Ask Player name
def ask_player_name(screen, screen_width, screen_height, menu_font, colors, clock):
    name = ""
    prompt = "Enter your name: "
    FPS = 60
    if clock is None:
        clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    return name.strip()
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and len(name) < 32:
                        name += ch

        screen.fill(colors.get("BG", (30,30,30)))
        txt = menu_font.render(prompt + (name + "_")[:60], True, colors.get("WHITE", (255,255,255)))
        screen.blit(txt, (screen_width//2 - txt.get_width()//2, screen_height//2))
        pygame.display.flip()
        clock.tick(FPS)
if menu_start == "game":
    game_state = "game"
    try:
        start_build_full_map()
    except Exception:
        pass
    try:
        player_name = ask_player_name(screen, Screen_Width, Screen_Height, menu_font, {"WHITE": WHITE, "BG": BG}, clock)
    except Exception:
        player_name = ""
    if player_name:
        setattr(player, "name", player_name)
elif menu_start == "quit":
    running = False

def show_full_map():
    if not getattr(game_map, "_full_map_surf", None):
        start_build_full_map()


    pass

def process_full_map_build(steps=256):
    q = getattr(game_map, "_full_map_build_queue", None)
    if not q:
        return
    tmx = game_map.tmx
    cols = getattr(game_map, "_full_map_cols", 0)
    rows = getattr(game_map, "_full_map_rows", 0)
    full_surf = getattr(game_map, "_full_map_surf", None)
    tile_px = getattr(game_map, "_full_map_tile_px", 1)
    gid_scaled_cache = getattr(game_map, "_full_map_build_gid_scaled_cache", {})
    gid_color_cache = getattr(game_map, "_full_map_build_gid_color_cache", {})
    total = getattr(game_map, "_full_map_build_total", max(1, len(q)))
    processed = getattr(game_map, "_full_map_processed", 0)
    for _ in range(steps):
        if not q:
            break
        x, y, gid = q.popleft()
        tile_img = None
        gid_key = None
        if isinstance(gid, pygame.Surface):
            tile_img = gid
            gid_key = ('surf', id(gid))
        else:
            try:
                g = int(gid)
            except Exception:
                g = None
            if g is None or g == 0:
                continue
            gid_key = g
        small = gid_scaled_cache.get(gid_key)
        if small is None:
            if tile_img is None and isinstance(gid_key, int):
                try:
                    tile_img = tmx.get_tile_image_by_gid(gid_key)
                except Exception:
                    tile_img = None
            small = None
            if tile_img is not None:
                try:
                    # Preserve aspect ratio when scaling tile images (scale both width and height)
                    scale_fact = getattr(game_map, '_full_map_scale', tile_px / float(getattr(game_map, 'tilewidth', game_map.tile_size)))
                    orig_w = tile_img.get_width()
                    orig_h = tile_img.get_height()
                    new_w = max(1, int(round(orig_w * scale_fact)))
                    new_h = max(1, int(round(orig_h * scale_fact)))
                    if new_w <= 4 or new_h <= 4:
                        small = pygame.transform.scale(tile_img, (new_w, new_h))
                    else:
                        small = pygame.transform.smoothscale(tile_img, (new_w, new_h))
                    try:
                        tiny = pygame.transform.smoothscale(tile_img, (1, 1))
                        cid = tiny.get_at((0, 0))
                        gid_color_cache[gid_key] = cid
                    except Exception:
                        gid_color_cache[gid_key] = (120, 120, 120)
                except Exception:
                    small = None
            gid_scaled_cache[gid_key] = small
        if small:
            try:
                # Use the scaled small surface's height to compute extra height above the base tile
                new_h = small.get_height()
                extra_h_scaled = max(0, new_h - tile_px)
            except Exception:
                extra_h_scaled = 0
            full_surf.blit(small, (x * tile_px, y * tile_px - extra_h_scaled))
            game_map._full_map_present_count = getattr(game_map, '_full_map_present_count', 0) + 1
        else:
            col = gid_color_cache.get(gid_key)
            if not col:
                props = {}
                try:
                    if isinstance(gid_key, int):
                        props = tmx.get_tile_properties_by_gid(gid_key) or {}
                except Exception:
                    props = {}
                tname = (props.get('name') or props.get('type') or '') if props else ''
                tname = (tname or '').lower()
                if 'water' in tname or props.get('water'):
                    col = (50, 100, 220)
                elif 'grass' in tname or props.get('grass'):
                    col = (60, 160, 60)
                elif 'road' in tname or props.get('road'):
                    col = (150, 150, 120)
                elif 'house' in tname or 'building' in tname or props.get('building'):
                    col = (140, 100, 50)
                else:
                    col = (120, 120, 120)
                gid_color_cache[gid_key] = col
                pygame.draw.rect(full_surf, col, (x * tile_px, y * tile_px, tile_px, tile_px))
                game_map._full_map_missing_count = getattr(game_map, '_full_map_missing_count', 0) + 1
        processed += 1
        game_map._full_map_processed = processed
        # update progress guard (cap between 0 and 1)
        try:
            game_map._full_map_progress = max(0.0, min(1.0, processed / float(total)))
        except Exception:
            game_map._full_map_progress = 0.0
    if not q:
        # finalize
        game_map._gid_scaled_cache = gid_scaled_cache
        game_map._full_map_build_gid_scaled_cache = gid_scaled_cache
        game_map._full_map_build_gid_color_cache = gid_color_cache
        game_map._full_map_build_queue = deque()
        game_map._full_map_built = True
        game_map._full_map_building = False
        game_map._full_map_progress = 1.0
        print(f"Full map incremental build finished; total processed: {processed} present: {getattr(game_map, '_full_map_present_count', 0)} missing: {getattr(game_map, '_full_map_missing_count', 0)}")
        # Save a debug image so the developer can open it for verification
        try:
            import os
            dbg_path = base_dir.parent / 'data' / 'full_map_debug.png'
            os.makedirs(str(dbg_path.parent), exist_ok=True)
            pygame.image.save(game_map._full_map_surf, str(dbg_path))
            print('Saved full map debug image to:', dbg_path)
        except Exception:
            pass

while running:
    dt_ms = clock.tick(60)
    dt = dt_ms / 1000.0

    try:
        process_full_map_build(steps=512)
    except Exception:
        pass

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            # Signal background build thread to abort and join it briefly
            try:
                if getattr(game_map, "_full_map_abort", None):
                    game_map._full_map_abort.set()
                if getattr(game_map, "_full_map_th", None):
                    game_map._full_map_th.join(timeout=1.0)
            except Exception:
                pass
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                show_coords = not show_coords
            if event.key == pygame.K_m:
                # Toggle full map overlay
                show_map = not show_map
                print("show_map toggled ->", show_map)
                if show_map:
                    print("Preparing full map cache (non-blocking).")
                    show_full_map()
                else:
                    try:
                        if getattr(game_map, "_full_map_building", False) and getattr(game_map, "_full_map_abort", None):
                            game_map._full_map_abort.set()
                        if getattr(game_map, "_full_map_th", None):
                            game_map._full_map_th.join(timeout=0.5)
                    except Exception:
                        pass # not forward to player
                continue
            if event.key == pygame.K_TAB:
                # Toggle bag overlay and open bag UI
                show_bag = not show_bag
                if show_bag:
                    try:
                        res = show_bag_menu(screen, bag, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "BG": BG}, clock, in_battle=False, current_player_pokemon=current_player_pokemon, pokedex_obj=pokedex)
                    except Exception as e:
                        print(f"Bag UI failed: {e}")
                    show_bag = False
            if event.key == pygame.K_b:
                show_pokedex = not show_pokedex
                print("show_pokedex toggled ->", show_pokedex)
                continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if show_map:
                show_map = False
                continue
            elif show_pokedex:
                show_pokedex = False
                continue
            else:
                result = "pause"
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            # Interaction key: check if professor is near
            if professor and professor.is_near(player.rect, distance=150):
                if not tutorial_shown:
                    # First interaction: ask the player if they want the tutorial
                    try:
                        want_tutorial = show_tutorial_choice(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                        tutorial_shown = True
                        if want_tutorial:
                            try:
                                if professor:
                                    professor.set_temporary_scale(1.5)
                                show_tutorial(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                            except Exception as e:
                                print(f"Tutorial failed: {e}")
                            finally:
                                try:
                                    if professor:
                                        professor.clear_temporary_scale()
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"Tutorial choice failed: {e}")
                else:
                    # Subsequent interactions: show greeting and offer to restart tutorial
                    show_dialogue(screen, professor.name, f"Hello, {getattr(player, 'name', 'Trainer')}! Would you like me to teach you again?", Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                    # Ask if they want to see the tutorial again
                    try:
                        want_tutorial_again = show_tutorial_choice(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                        if want_tutorial_again:
                            try:
                                if professor:
                                    professor.set_temporary_scale(1.5)
                                show_tutorial(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                            except Exception as e:
                                print(f"Tutorial re-run failed: {e}")
                            finally:
                                try:
                                    if professor:
                                        professor.clear_temporary_scale()
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"Tutorial re-run choice failed: {e}")
            else:
                # Silent — no console spam
                pass
        else:
            # If the map overlay is visible, suppress player input
            if show_map:
                result = None
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
            elif pause_result == "pause options" or pause_result == "options":
                # Open options menu from pause. Wait for mouse release to avoid
                # immediately triggering buttons with the same click.
                _wait_for_mouse_release(clock)
                opt = options_menu(
                    screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock
                )
                if opt == "quit":
                    running = False
                else:
                    # After returning from options, re-open the pause menu so
                    # player can choose Resume/Menu/Quit again.
                    _wait_for_mouse_release(clock)
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
            try:
                pygame.display.init()
                screen = pygame.display.set_mode((Screen_Width, Screen_Height))
                keys = pygame.key.get_pressed()
            except Exception as e2:
                print("Failed to re-init display:", e2)
                keys = [False] * 512
        # Only update player movement if the map overlay isn't open
        if not show_map:
            player.update(keys, game_map, dt=dt)
        bush_rects = game_map.get_bush_rects()
        bush_hit = is_player_in_bush(player.rect, bush_rects)

        if bush_hit and can_trigger_bush(bush_hit) and trigger_encounter():
            encounter_pokemon = fetch_random_pokemon()
            if encounter_pokemon:
                pokemon_encounter_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
                encounter_active = True
                encounter_animation_done = True
                mark_bush_triggered(bush_hit)
                print(
                    f"Wild {encounter_pokemon['name']} appeared in bush!"
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
    try:
        game_map.draw_lower(screen, player.rect, offset_x=offset_x, offset_y=offset_y)
    except Exception:
        game_map.draw(screen, offset_x=offset_x, offset_y=offset_y)

    # Draw professor first (so the player is rendered above him)
    if professor:
        professor.draw(screen, offset_x=offset_x, offset_y=offset_y)
    # Draw player (on top of professor)
    player.draw(screen, offset_x=offset_x, offset_y=offset_y)
    try:
        game_map.draw_upper(screen, player.rect, offset_x=offset_x, offset_y=offset_y)
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
        try:
            surf = coords_font.render(text, True, (255, 255, 255))
        except Exception:
            surf = None
        if surf:
            bg_rect = pygame.Rect(8, 8, surf.get_width() + 8, surf.get_height() + 8)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect)
            screen.blit(surf, (12, 12))
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
            if isinstance(bush, pygame.Rect):
                # Rect bush
                pygame.draw.rect(
                    screen,
                    (BLUE),
                    pygame.Rect(
                        bush.x + offset_x, bush.y + offset_y, bush.width, bush.height
                    ),
                    2,
                )
            else:
                # Polygon bush
                offset_points = [(x + offset_x, y + offset_y) for x, y in bush]
                if len(offset_points) > 1:
                    pygame.draw.polygon(screen, (BLUE), offset_points, 2)

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
        init_msg = None
        if just_switched_pokemon and current_player_pokemon:
            init_msg = f"Go {current_player_pokemon.name}!"
        choice = battle_menu(
            screen,
            encounter_pokemon,
            menu_font,
            coords_font,
            {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW, "BLUE": BLUE, "BG": BG},
            clock,
            player_pokemon=current_player_pokemon,
            initial_message=init_msg,
            show_intro=not encounter_animation_done,
        )
        just_switched_pokemon = False
        print(f"Battle choice: {choice}")
        if choice == "fight":
            if current_player_pokemon:
                damage = max(1, current_player_pokemon.attack - (encounter_pokemon.get('attack', 20) // 3))
                encounter_pokemon['hp'] = max(0, encounter_pokemon.get('hp', 1) - damage)
                print(f"You attacked {encounter_pokemon['name']} for {damage} damage!")
                print(f"Wild {encounter_pokemon['name']} has {encounter_pokemon['hp']} HP left")

                # Check if wild Pokémon is defeated
                if encounter_pokemon['hp'] <= 0:
                    print(f"You caught {encounter_pokemon['name']}!")
                    # Capture the Pokémon
                    captured_pokemon = Pokemon(
                        name=encounter_pokemon['name'],
                        hp=encounter_pokemon.get('hp', 50),
                        attack=encounter_pokemon.get('attack', 50),
                        sprite=encounter_pokemon.get('sprite'),
                        level=1
                    )
                    pokedex.add_pokemon(captured_pokemon)
                    print(f"Added {encounter_pokemon['name']} to Pokédex!")
                    encounter_active = False
                    encounter_pokemon = None
                    encounter_animation_done = False
            else:
                print("You have no Pokémon to battle with!")

        elif choice == "pokémon" or choice == "pokemon":
            # Open Pokédex to select a Pokémon
            selected_pokemon = quick_pokemon_select(
                screen, pokedex, menu_font, coords_font,
                {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW, "BLUE": BLUE, "BG": BG},
                clock,
                current_player=current_player_pokemon,
            )
            if selected_pokemon:
                current_player_pokemon = selected_pokemon
                print(f"Switched to {current_player_pokemon.name}!")
                just_switched_pokemon = True
                if current_player_pokemon.current_hp > 0:
                    counter_damage = max(1, encounter_pokemon.get('attack', 20) - (current_player_pokemon.attack // 3))
                    current_player_pokemon.current_hp = max(0, current_player_pokemon.current_hp - counter_damage)
                    print(f"{encounter_pokemon['name']} attacks back for {counter_damage} damage!")
                    if current_player_pokemon.current_hp <= 0:
                        print(f"{current_player_pokemon.name} fainted!")
                        current_player_pokemon = pokedex.get_first_available_pokemon()
                        if current_player_pokemon:
                            print(f"Switched to {current_player_pokemon.name}")
                        else:
                            print("You have no more Pokémon!")
                            encounter_active = False
                            encounter_pokemon = None

        elif choice == "bag":
            try:
                res = show_bag_menu(screen, bag, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "BG": BG}, clock, in_battle=True, encounter_pokemon=encounter_pokemon, current_player_pokemon=current_player_pokemon, pokedex_obj=pokedex)
                if res:
                    act = res.get('action')
                    if act == 'caught':
                        # successful catch
                        encounter_active = False
                        encounter_pokemon = None
                        encounter_animation_done = False
            except Exception as e:
                print(f"Bag usage failed: {e}")
        elif choice == "run":
            try:
                run_away_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
            except Exception as e:
                print(f"Run-away animation failed: {e}")
            encounter_active = False
            encounter_pokemon = None
            encounter_animation_done = False
        else:
            pass
            
    # Full map overlay or loading UI
    if show_map and getattr(game_map, "tmx", None):
        try:

            if getattr(game_map, "_full_map_building", False) and not getattr(game_map, "_full_map_built", False):
                sw, sh = screen.get_size()
                overlay_bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay_bg.fill((0, 0, 0, 180))
                screen.blit(overlay_bg, (0, 0))
                progress = getattr(game_map, "_full_map_progress", 0.0)
                bar_w = min(500, sw - 80)
                bar_h = 20
                bx = sw // 2 - bar_w // 2
                by = sh // 2 - bar_h // 2
                pygame.draw.rect(screen, (100, 100, 100), (bx, by, bar_w, bar_h))
                pygame.draw.rect(screen, (255, 255, 255), (bx - 2, by - 2, bar_w + 4, bar_h + 4), 2)
                fill_w = int(bar_w * max(0.0, min(1.0, progress)))
                pygame.draw.rect(screen, (0, 120, 220), (bx, by, fill_w, bar_h))
                pct = int(progress * 100)
                txt = menu_font.render(f"Loading map... {pct}%", True, (255, 255, 255))
                screen.blit(txt, (sw // 2 - txt.get_width() // 2, by - 28))
            elif getattr(game_map, "_full_map_built", False) and getattr(game_map, "_full_map_surf", None):
                full_surf = game_map._full_map_surf
                full_w, full_h = full_surf.get_size()
                sw, sh = screen.get_size()
                ox = (sw - full_w) // 2
                oy = (sh - full_h) // 2
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                screen.blit(overlay, (0, 0))
                screen.blit(full_surf, (ox, oy))
                border_rect = pygame.Rect(ox - 2, oy - 2, full_w + 4, full_h + 4)
                pygame.draw.rect(screen, (255, 255, 255), border_rect, 2)
                px = int((player.rect.centerx / (getattr(game_map, "width", 1))) * full_w)
                py = int((player.rect.centery / (getattr(game_map, "height", 1))) * full_h)
                screen_px = ox + px
                screen_py = oy + py
                pygame.draw.circle(screen, (255, 255, 255), (screen_px, screen_py), 6)
                pygame.draw.circle(screen, (255, 0, 0), (screen_px, screen_py), 4)
            else:
                # Not built and not building: trigger start
                start_build_full_map()
        except Exception:
            pass
    
    # Handle Pokédex overlay
    if show_pokedex:
        # Call the blocking Pokédex menu
        pokedex_menu(
            screen, pokedex, menu_font, coords_font,
            {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "BLUE": BLUE, "BG": BG},
            clock, is_battle_context=False
        )
        show_pokedex = False
    
    pygame.display.flip()

pygame.quit()