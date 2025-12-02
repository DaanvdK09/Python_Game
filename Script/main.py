import pygame
import sys
from io import BytesIO
import requests
import threading
from collections import deque
import json
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
encounter_name_font = pygame.font.Font(None, 48)
encounter_stat_font = pygame.font.Font(None, 32)
encounter_prompt_font = pygame.font.Font(None, 28)
run_msg_font = pygame.font.Font(None, 56)

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
    # Ensure hitbox is positioned and float position synced
    player.hitbox_rect.midbottom = player.rect.midbottom

# Sync internal float positions used by Character movement
try:
    # if Character has _fx/_fy, sync them to the current hitbox position
    player._fx = float(player.hitbox_rect.x)
    player._fy = float(player.hitbox_rect.y)
except Exception:
    pass

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
    # Begin building the full map in background so the first toggle is faster
    try:
        start_build_full_map()
    except Exception:
        pass
elif menu_start == "quit":
    running = False

def show_full_map_nonblocking():
    # Create and cache a scaled full map surface, but do not block UI with time.delay
    if not getattr(game_map, "_full_map_surf", None):
        # start background builder instead of blocking call
        start_build_full_map()


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

    # If a full map build is queued, process a portion of it on the main thread to avoid surface locks
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
                    show_full_map_nonblocking()
                else:
                    # If hiding the overlay while a background build is active, request abort
                    try:
                        if getattr(game_map, "_full_map_building", False) and getattr(game_map, "_full_map_abort", None):
                            game_map._full_map_abort.set()
                        if getattr(game_map, "_full_map_th", None):
                            game_map._full_map_th.join(timeout=0.5)
                    except Exception:
                        pass
                # Do not forward this event to player movement
                continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # If overlay is open, close it on ESC
            if show_map:
                show_map = False
                # Do not forward this to player movement
                continue
            else:
                result = "pause"
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

    # Draw player
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
            try:
                run_away_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
            except Exception as e:
                print(f"Run-away animation failed: {e}")
            encounter_active = False
            encounter_pokemon = None
            encounter_animation_done = False

        else:
            encounter_active = False
            encounter_pokemon = None
            encounter_animation_done = False
            
    # Full map overlay or loading UI (draw before flip)
    if show_map and getattr(game_map, "tmx", None):
        try:

            # If building, draw progress bar
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
    pygame.display.flip()

pygame.quit()