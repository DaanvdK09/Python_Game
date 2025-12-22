import os
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
    is_player_in_hospital,
    is_player_in_house,
    is_player_in_GrassGym,
    is_player_in_IceGym,
    is_player_in_FireGym,
    get_moves_for_pokemon,
    fetch_and_store_all_moves,
)
from Characters.pokedex import Pokedex, Pokemon
from Characters.hospital import load_hospital_npcs, heal_pokemon_menu, show_shop_menu, SHOP_ITEMS
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from UI.battle_menu import battle_menu, show_move_menu
from UI.dialogue_box import show_dialogue, show_tutorial, show_tutorial_choice
from UI.pokedex_menu import quick_pokemon_select, pokedex_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD, RED, BLUE, GREEN, YELLOW, WHITE
from pathlib import Path
from UI.battle_menu import load_type_icons
from UI.level_up import show_level_up_screen, show_xp_gain
from multiplayer import start_server, handle_multiplayer_logic, handle_waiting_state, handle_multiplayer_battle

pygame.init()

# Start the multiplayer server
server_process = start_server()

# Fetch and store all moves at startup
fetch_and_store_all_moves()

# Game state
running = True
game_state = "menu"
show_coords = False
show_map = False
show_pokedex = False
encounter_active = False
encounter_pokemon = None
encounter_animation_done = False
tutorial_shown = False
current_player_pokemon = None
just_switched_pokemon = False
initial_no_switch_frames = 120
map_switch_cooldown = 120
faint_message = None

# Trainer battle state
trainer_battle_active = False
current_trainer = None
trainer_pokemon_team = []
current_trainer_pokemon = None
trainer_pokemon_index = 0  


# Initialize Pokédex
pokedex = Pokedex()
if pokedex.get_captured_count() == 0:
    starter = Pokemon(name="Pikachu", hp=35, attack=55, sprite="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png", level=5)
    starter.experience = 4 * 4 * 100  # Set XP for level 5
    pokedex.add_pokemon(starter)
    bulbasaur = Pokemon(name="Bulbasaur", hp=45, attack=49, sprite="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png", level=5)
    bulbasaur.experience = 4 * 4 * 100  # Set XP for level 5
    pokedex.add_pokemon(bulbasaur)
    print("Added starter Pokémon: Pikachu")
current_player_pokemon = pokedex.get_first_available_pokemon()

# Bag
bag = {
    "Potion": 2,
    "Pokéball": 5,
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
save_position_file = base_dir / "save_position.json"
world_tmx_path = base_dir / "World" / "maps" / "World.tmx"
world_map = TileMap(tmx_path=str(world_tmx_path), tile_size=64)

# Load bag icons
def _scale_icon(surface, size=40):
    if surface is None:
        return None
    try:
        w, h = surface.get_size()
        if w <= 0 or h <= 0:
            return None
        scale = float(size) / max(w, h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return pygame.transform.smoothscale(surface, (new_w, new_h))
    except Exception:
        return None

potion_img = None
pokeball_img = None
try:
    p_path = base_dir.parent / "graphics" / "icons" / "potion.png"
    if p_path.exists():
        img = pygame.image.load(str(p_path)).convert_alpha()
        potion_img = _scale_icon(img, 40)
except Exception:
    potion_img = None
try:
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
        pokeball_img = _scale_icon(img, 40)
except Exception:
    pokeball_img = None

BAG_ICONS = {
    "Potion": potion_img,
    "Pokéball": pokeball_img,
}

# Music
music_path = base_dir.parent / "audio" / "background_music.mp3"
pygame.mixer.music.load(music_path)
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

# Character
player = Character()
player.money = 1000


# Professor NPC functional placeholder
professor = None
nurse_joy = None
shopkeeper = None

# Trainer NPCs
trainer_npcs = []

# Type icons
TYPE_ICONS = load_type_icons()

# Set player start
if game_map.player_start:
    px, py = game_map.player_start
    player.rect.midbottom = (px, py)
    player.hitbox_rect.midbottom = player.rect.midbottom
    player._fx = float(player.hitbox_rect.x)
    player._fy = float(player.hitbox_rect.y)
    print(f"Spawned player at TMX start: {px}, {py}")
else:
    print("No player start found in TMX. Spawning at (0,0).")
    player.rect.midbottom = (0, 0)
    player.hitbox_rect.midbottom = player.rect.midbottom

try:
    player._fx = float(player.hitbox_rect.x)
    player._fy = float(player.hitbox_rect.y)
except Exception:
    pass

# Professor NPC spawn
prof_pos = getattr(game_map, "professor_start", None)
if prof_pos:
    try:
        px, py = prof_pos
        professor = NPC(px, py, name="Professor Oak", use_sprite_sheet=False)
        print(f"Spawned professor at TMX start: {px}, {py}")
    except Exception as e:
        print(f"Failed to spawn professor: {e}")

if "Hospital" in str(game_map.tmx_path):
    npcs = load_hospital_npcs(game_map)
    for npc in npcs:
        if npc.name == "Nurse Joy":
            nurse_joy = npc
        elif npc.name == "Shopkeeper":
            shopkeeper = npc

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
    # Get the actual screen size
    actual_w, actual_h = surface.get_size()
    print(f"Intended: {w}x{h}, Actual: {actual_w}x{actual_h}")

    # Scale the animation to fit the actual screen
    scale_x = actual_w / w
    scale_y = actual_h / h

    # Flash effect
    flash_surface = pygame.Surface((actual_w, actual_h))
    flash_surface.fill((255, 255, 255))

    for alpha in range(0, 256, 15):
        flash_surface.set_alpha(alpha)
        surface.blit(flash_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    flash_surface.set_alpha(255)
    surface.blit(flash_surface, (0, 0))
    pygame.display.flip()
    pygame.time.delay(200)

    # Load background
    bg_img = None
    try:
        key = ("forest", (actual_w, actual_h))
        if key in _BG_SURFACE_CACHE:
            bg_img = _BG_SURFACE_CACHE[key]
        else:
            bg_path = base_dir.parent / "graphics" / "backgrounds" / "forest.png"
            if bg_path.exists():
                surf = pygame.image.load(str(bg_path)).convert()
                surf = pygame.transform.scale(surf, (actual_w, actual_h))
                _BG_SURFACE_CACHE[key] = surf
                bg_img = surf
    except Exception:
        bg_img = None

    # Load and scale Pokémon sprite
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

    # Animate Pokémon entrance
    if sprite:
        start_x = actual_w
        end_x = actual_w - int(200 * scale_x) - int(96 * scale_x)
        end_y = actual_h // 2 - int(40 * scale_y) - int(96 * scale_y)
        frames = 15

        for frame in range(frames):
            # Always clear screen
            if bg_img:
                surface.blit(bg_img, (0, 0))
            else:
                surface.fill((40, 120, 40))  # Fallback

            progress = frame / frames
            white_overlay = pygame.Surface((actual_w, actual_h))
            white_overlay.fill((255, 255, 255))
            white_overlay.set_alpha(int(255 * (1 - progress)))
            surface.blit(white_overlay, (0, 0))

            # Calculate position
            x_pos = int(start_x - (start_x - end_x) * progress)
            y_pos = int(actual_h // 2 - int(100 * scale_y) - (actual_h // 2 - int(100 * scale_y) - end_y) * progress)
            surface.blit(sprite, (x_pos, y_pos))

            pygame.display.flip()
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

def show_bag_menu(screen, bag, menu_font, small_font, colors, clock, in_battle=False, encounter_pokemon=None, current_player_pokemon=None, pokedex_obj=None, player=None, is_trainer_battle=False):
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
                        pass
                    else:
                        if in_battle and encounter_pokemon and item.lower().startswith("pokeball"):
                            if is_trainer_battle:
                                # Can't catch trainer's Pokemon
                                continue
                            try:
                                hp = float(encounter_pokemon.get('hp', 1))
                            except Exception:
                                hp = 1.0
                            chance = 0.5
                            if hp <= 5:
                                chance = 0.9
                            elif hp <= 15:
                                chance = 0.7
                            bag[item] = max(0, count - 1)
                            got = random.random() < chance
                            if got and pokedex_obj is not None:
                                p = Pokemon(name=encounter_pokemon.get('name', 'Unknown'), hp=encounter_pokemon.get('hp', 10), attack=encounter_pokemon.get('attack', 10), sprite=encounter_pokemon.get('sprite'))
                                pokedex_obj.add_pokemon(p)
                            return {"action": "caught" if got else "escaped", "item": item, "caught_pokemon": encounter_pokemon if got else None}
                        elif item.lower().startswith("potion"):
                            if current_player_pokemon is not None:
                                heal = 20
                                try:
                                    max_hp = getattr(current_player_pokemon, 'hp', getattr(current_player_pokemon, 'max_hp', None))
                                except Exception:
                                    max_hp = None
                                if hasattr(current_player_pokemon, 'current_hp'):
                                    current_player_pokemon.current_hp = min(getattr(current_player_pokemon, 'current_hp', getattr(current_player_pokemon, 'hp', 0)) + heal, getattr(current_player_pokemon, 'hp', getattr(current_player_pokemon, 'current_hp', 0)))
                                bag[item] = max(0, count - 1)
                                return {"action": "used", "item": item}
                            else:
                                return {"action": "none", "item": item}
                        else:
                            if not (item.lower().startswith("pokeball") and not in_battle):
                                bag[item] = max(0, count - 1)
                            return {"action": "used", "item": item}
                elif event.key == pygame.K_ESCAPE:
                    return {"action": "closed", "item": None}

        sw, sh = screen.get_size()
        panel_w = min(520, sw - 80)
        panel_h = min(360, sh - 120)
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h))
        panel.fill(colors.get('BG', (30, 30, 30)))
        title = menu_font.render("Bag", True, colors.get('WHITE', (255,255,255)))
        panel.blit(title, (20, 12))

        list_start_y = 64
        list_item_h = 56
        visible = (panel_h - list_start_y - 20) // list_item_h
        start = max(0, selected - visible // 2)
        for i, name in enumerate(items[start:start + visible]):
            idx = start + i
            y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(20, y, panel_w - 40, list_item_h - 8)
            if name.lower().startswith("pokeball") and (not in_battle or is_trainer_battle):
                pygame.draw.rect(panel, (100, 100, 100), item_rect)
            elif idx == selected:
                pygame.draw.rect(panel, (80, 120, 160), item_rect)
            else:
                pygame.draw.rect(panel, (50, 50, 70), item_rect)
            pygame.draw.rect(panel, (120, 120, 140), item_rect, 1)

            icon = BAG_ICONS.get(name)
            label_x = item_rect.x + 8
            if icon:
                try:
                    ih = icon.get_height()
                    iw = icon.get_width()
                    icon_y = item_rect.y + max(0, (item_rect.height - ih) // 2)
                    panel.blit(icon, (item_rect.x + 8, icon_y))
                    label_x = item_rect.x + 8 + iw + 8
                except Exception:
                    label_x = item_rect.x + 8

            label = small_font.render(f"{name} x{bag.get(name,0)}", True, colors.get('WHITE', (255,255,255)))
            label_y = item_rect.y + max(0, (item_rect.height - label.get_height()) // 2)
            panel.blit(label, (label_x, label_y))
        
        money = getattr(player, 'money', 0)
        money_text = small_font.render(f"Money: ${money}", True, colors.get('WHITE', (255,255,255)))
        panel.blit(money_text, (panel_w - money_text.get_width() - 20, 12))

        screen.blit(panel, (px, py))
        pygame.display.flip()
        clock.tick(FPS)

def _wait_for_mouse_release(clock):
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()
        clock.tick(60)
    pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

def save_world_position(player):
    data = {
        "x": int(player.rect.x),
        "y": int(player.rect.y)
    }
    try:
        with open(save_position_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print("Failed to save position:", e)

def load_world_position():
    if save_position_file.exists():
        try:
            with open(save_position_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def restore_world_position(player, game_map):
    pos = load_world_position()

    if pos:
        player.rect.x = pos["x"]
        player.rect.y = pos["y"]
        player.hitbox_rect.midbottom = player.rect.midbottom
        player._fx = float(player.hitbox_rect.x)
        player._fy = float(player.hitbox_rect.y)
        print("Restored world position:", pos)
        return True

    if game_map.player_start:
        player.rect.midbottom = game_map.player_start
        player.hitbox_rect.midbottom = player.rect.midbottom
        player._fx = float(player.hitbox_rect.x)
        player._fy = float(player.hitbox_rect.y)

    return False

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

def start_build_full_map(tilemap=None):
    if tilemap is None:
        tilemap = game_map
    if getattr(tilemap, "_full_map_built", False):
        tilemap._full_map_progress = 1.0
        return
    if getattr(tilemap, "_full_map_building", False):
        return

    tilemap._full_map_building = True
    tilemap._full_map_progress = 0.0
    tilemap._full_map_built = False
    tilemap._full_map_build_queue = deque()
    tilemap._full_map_build_gid_scaled_cache = {}
    tilemap._full_map_build_gid_color_cache = {}
    tilemap._full_map_build_total = 0
    tilemap._full_map_processed = 0
    tilemap._full_map_present_count = 0
    tilemap._full_map_missing_count = 0

    def worker():
        try:
            import time
            t0 = time.perf_counter()
            tmx = tilemap.tmx
            world_w = getattr(tilemap, "width", 0)
            world_h = getattr(tilemap, "height", 0)
            if world_w <= 0 or world_h <= 0:
                tilemap._full_map_building = False
                return
            sw, sh = screen.get_size()
            scale = min((sw * 0.88) / world_w, (sh * 0.88) / world_h, 1.0)
            tile_px = max(1, int(getattr(tilemap, "tilewidth", getattr(tilemap, "tile_size", 64)) * scale))

            cols = int(world_w // getattr(tilemap, "tilewidth", getattr(tilemap, "tile_size", 64)))
            rows = int(world_h // getattr(tilemap, "tileheight", getattr(tilemap, "tile_size", 64)))
            full_surf = pygame.Surface((tile_px * cols, tile_px * rows), pygame.SRCALPHA)
            full_surf.fill((0, 0, 0, 0))

            tiles = []
            for layer in tmx.visible_layers:
                layer_name = (getattr(layer, "name", "") or "").lower()
                layer_props = getattr(layer, "properties", {}) or {}
                if layer_name == "collision" or layer_props.get("collision") is True:
                    continue
                if not hasattr(layer, "tiles"):
                    continue
                for x, y, gid in layer.tiles():
                    if gid == 0:
                        continue
                    tiles.append((x, y, gid))

            tilemap._full_map_build_total = len(tiles) if tiles else 1
            for (x, y, gid) in tiles:
                tilemap._full_map_build_queue.append((x, y, gid))

            tilemap._full_map_surf = full_surf
            tilemap._full_map_scale = tile_px / getattr(tilemap, "tilewidth", getattr(tilemap, "tile_size", 64))
            tilemap._full_map_tile_px = tile_px
            tilemap._full_map_cols = cols
            tilemap._full_map_rows = rows
        except Exception:
            tilemap._full_map_building = False
            tilemap._full_map_built = False

    try:
        th = threading.Thread(target=worker, daemon=True)
        tilemap._full_map_th = th
        th.start()
    except Exception:
        worker()

def show_full_map(tilemap=None):
    if tilemap is None:
        tilemap = world_map
    if not getattr(tilemap, "_full_map_surf", None):
        start_build_full_map(tilemap)

def process_full_map_build(tilemap=None, steps=256):
    if tilemap is None:
        tilemap = game_map
    q = getattr(tilemap, "_full_map_build_queue", None)
    if not q:
        return

    tmx = tilemap.tmx
    cols = getattr(tilemap, "_full_map_cols", 0)
    rows = getattr(tilemap, "_full_map_rows", 0)
    full_surf = getattr(tilemap, "_full_map_surf", None)
    tile_px = getattr(tilemap, "_full_map_tile_px", 1)
    gid_scaled_cache = getattr(tilemap, "_full_map_build_gid_scaled_cache", {})
    gid_color_cache = getattr(tilemap, "_full_map_build_gid_color_cache", {})
    total = getattr(tilemap, "_full_map_build_total", max(1, len(q)))
    processed = getattr(tilemap, "_full_map_processed", 0)

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
            if tile_img is not None:
                try:
                    scale_fact = getattr(tilemap, '_full_map_scale', tile_px / float(getattr(tilemap, 'tilewidth', tilemap.tile_size)))
                    new_w = max(1, int(round(tile_img.get_width() * scale_fact)))
                    new_h = max(1, int(round(tile_img.get_height() * scale_fact)))
                    if new_w <= 4 or new_h <= 4:
                        small = pygame.transform.scale(tile_img, (new_w, new_h))
                    else:
                        small = pygame.transform.smoothscale(tile_img, (new_w, new_h))
                    try:
                        tiny = pygame.transform.smoothscale(tile_img, (1, 1))
                        gid_color_cache[gid_key] = tiny.get_at((0, 0))
                    except Exception:
                        gid_color_cache[gid_key] = (120, 120, 120)
                except Exception:
                    small = None
            gid_scaled_cache[gid_key] = small

        if small:
            try:
                extra_h_scaled = max(0, small.get_height() - tile_px)
            except Exception:
                extra_h_scaled = 0
            full_surf.blit(small, (x * tile_px, y * tile_px - extra_h_scaled))
            tilemap._full_map_present_count = getattr(tilemap, '_full_map_present_count', 0) + 1
        else:
            col = gid_color_cache.get(gid_key)
            if not col:
                props = {}
                try:
                    if isinstance(gid_key, int):
                        props = tmx.get_tile_properties_by_gid(gid_key) or {}
                except Exception:
                    pass
                tname = (props.get('name') or props.get('type') or '').lower()
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
                tilemap._full_map_missing_count = getattr(tilemap, '_full_map_missing_count', 0) + 1

        processed += 1
        tilemap._full_map_processed = processed
        try:
            tilemap._full_map_progress = max(0.0, min(1.0, processed / float(total)))
        except Exception:
            tilemap._full_map_progress = 0.0

    if not q:
        tilemap._gid_scaled_cache = gid_scaled_cache
        tilemap._full_map_build_gid_scaled_cache = gid_scaled_cache
        tilemap._full_map_build_gid_color_cache = gid_color_cache
        tilemap._full_map_build_queue = deque()
        tilemap._full_map_built = True
        tilemap._full_map_building = False
        tilemap._full_map_progress = 1.0
        print(f"Full map incremental build finished; total processed: {processed} present: {getattr(tilemap, '_full_map_present_count', 0)} missing: {getattr(tilemap, '_full_map_missing_count', 0)}")

def create_trainer_team(trainer_name):
    teams = {
        "Grass Trainer": [
            {"name": "Bulbasaur", "hp": 145, "attack": 49, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/1.png", "level": 12},
            {"name": "Gogoat", "hp": 160, "attack": 100, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/673.png", "level": 16},
            {"name": "Rillaboom", "hp": 180, "attack": 125, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/812.png", "level": 18}
        ],
        "Ice Trainer": [
            {"name": "Starmie", "hp": 160, "attack": 75, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/121.png", "level": 15},
            {"name": "Garados", "hp": 190, "attack": 125, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/130.png", "level": 17},
            {"name": "Blastoise", "hp": 180, "attack": 83, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/9.png", "level": 19}
        ],
        "Fire Trainer": [
            {"name": "Thyphlosion", "hp": 160, "attack": 84, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/157.png", "level": 18},
            {"name": "Blaziken", "hp": 170, "attack": 120, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/257.png", "level": 20},
            {"name": "Charizard", "hp": 190, "attack": 84, "sprite": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/6.png", "level": 23}
        ]
    }
    team = teams.get(trainer_name, [])
    for pokemon in team:
        pokemon['current_hp'] = pokemon['hp']
        pokemon['max_hp'] = pokemon['hp']
    return team

def ask_player_name(screen, Screen_Width, Screen_Height, font, colors, clock):
    import sys
    name = ""
    active = True

    input_box_width = int(Screen_Width * 0.4)
    input_box_height = int(Screen_Height * 0.08)
    input_rect = pygame.Rect(
        Screen_Width // 2 - input_box_width // 2,
        Screen_Height // 2 - input_box_height // 2,
        input_box_width,
        input_box_height
    )

    cursor_visible = True
    cursor_timer = 0.0
    CURSOR_BLINK_SPEED = 0.5

    while active:
        dt = clock.tick(60) / 1000.0
        cursor_timer += dt

        if cursor_timer >= CURSOR_BLINK_SPEED:
            cursor_timer = 0
            cursor_visible = not cursor_visible

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 16 and event.unicode.isprintable():
                        name += event.unicode

        screen.fill(colors["BG"])

        title = font.render("Enter your name", True, colors["WHITE"])
        title_x = Screen_Width // 2 - title.get_width() // 2
        title_y = input_rect.y - title.get_height() - 20
        screen.blit(title, (title_x, title_y))

        pygame.draw.rect(screen, colors["WHITE"], input_rect, 2)

        text_surface = font.render(name, True, colors["WHITE"])

        text_x = input_rect.x + (input_rect.width - text_surface.get_width()) // 2
        text_y = input_rect.y + (input_rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

        if cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y = text_y
            cursor_h = text_surface.get_height()
            pygame.draw.line(
                screen,
                colors["WHITE"],
                (cursor_x, cursor_y),
                (cursor_x, cursor_y + cursor_h),
                2
            )

        hint = font.render("Press ENTER to confirm", True, colors["WHITE"])
        hint_x = Screen_Width // 2 - hint.get_width() // 2
        hint_y = input_rect.y + input_rect.height + 20
        screen.blit(hint, (hint_x, hint_y))

        instructions = font.render("Go near the professor and press 'E' to interact.", True, colors["WHITE"])
        instr_x = Screen_Width // 2 - instructions.get_width() // 2
        instr_y = hint_y + hint.get_height() + 10
        screen.blit(instructions, (instr_x, instr_y))

        pygame.display.flip()

    return name.strip()

menu_start = show_main_menu()

if menu_start == "game":
    game_state = "game"
    start_build_full_map()

    pygame.event.clear()
    pygame.key.get_pressed()

    name = ask_player_name(
        screen,
        Screen_Width,
        Screen_Height,
        menu_font,
        {"WHITE": WHITE, "BG": BG},
        clock
    )

    if name:
        player.name = name
    else:
        player.name = "Trainer"

elif menu_start == "quit":
    running = False

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
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_3:
                show_coords = not show_coords
            if event.key == pygame.K_m:
                show_map = not show_map
                print("show_map toggled ->", show_map)
                if show_map:
                    print("Preparing full map cache.")
                    show_full_map()
                continue
            if event.key == pygame.K_TAB:
                show_bag = not show_bag
                if show_bag:
                    try:
                        res = show_bag_menu(screen, bag, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "BG": BG}, clock, in_battle=False, current_player_pokemon=current_player_pokemon, pokedex_obj=pokedex, player=player)
                    except Exception as e:
                        print(f"Bag UI failed: {e}")
                    show_bag = False
            if event.key == pygame.K_v:
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
            if nurse_joy and nurse_joy.is_near(player.rect, distance=100):
                heal_pokemon_menu(
                    screen, pokedex, menu_font, coords_font,
                    {"WHITE": WHITE, "BLACK": BLACK, "BG": BG},
                    clock,
                    Screen_Width, Screen_Height, BLACK, GOLD, BG, WHITE, nurse_joy
                )

            if shopkeeper and shopkeeper.is_near(player.rect, distance=100):
                show_shop_menu(
                    screen, shopkeeper, player, bag, menu_font, coords_font,
                    {"WHITE": WHITE, "BLACK": BLACK, "BG": BG}, clock
                )

            if professor and professor.is_near(player.rect, distance=150):
                if not tutorial_shown:
                    try:
                        want_tutorial = show_tutorial_choice(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                        tutorial_shown = True
                        if want_tutorial:
                            try:
                                if professor:
                                    professor.set_temporary_scale(1.5)
                                show_tutorial(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, player.name, clock)
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
                    show_dialogue(screen, professor.name, f"Hello, {getattr(player, 'name', 'Trainer')}! Would you like me to teach you again?", Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                    try:
                        want_tutorial_again = show_tutorial_choice(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, clock)
                        if want_tutorial_again:
                            try:
                                if professor:
                                    professor.set_temporary_scale(1.5)
                                show_tutorial(screen, Screen_Width, Screen_Height, menu_font, coords_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE}, player.name, clock)
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
                for trainer in trainer_npcs:
                    if trainer.is_near(player.rect, distance=100):
                        show_dialogue(
                            screen,
                            trainer.name,
                            f"{trainer.name}: I challenge you to a battle!",
                            Screen_Width,
                            Screen_Height,
                            menu_font,
                            coords_font,
                            {"BLACK": BLACK, "GOLD": GOLD, "BG": BG, "WHITE": WHITE},
                            clock
                        )
                        # Start trainer battle
                        trainer_battle_active = True
                        current_trainer = trainer
                        trainer_pokemon_team = create_trainer_team(trainer.name)
                        trainer_pokemon_index = 0
                        current_trainer_pokemon = trainer_pokemon_team[0] if trainer_pokemon_team else None
                        encounter_active = True
                        encounter_pokemon = current_trainer_pokemon
                        encounter_animation_done = True
                        print(f"Started trainer battle with {trainer.name}")
                        break
        else:
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
                _wait_for_mouse_release(clock)
                opt = options_menu(
                    screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock
                )
                if opt == "quit":
                    running = False
                else:
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
        if not show_map:
            player.update(keys, game_map, dt=dt)
        bush_rects = game_map.get_bush_rects()
        bush_hit = is_player_in_bush(player.hitbox_rect, bush_rects)

        if bush_hit and can_trigger_bush(bush_hit) and trigger_encounter():
            encounter_pokemon = fetch_random_pokemon()
            if encounter_pokemon:
                pokemon_encounter_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
                encounter_active = True
                encounter_animation_done = True
                mark_bush_triggered(bush_hit)
                print(f"Wild {encounter_pokemon['name']} appeared in bush!")

        # Hospital entry
        hospital_rects = game_map.get_hospital_rects()
        hospital_hit = is_player_in_hospital(player.hitbox_rect, hospital_rects)

        if hospital_hit and initial_no_switch_frames == 0:
            save_world_position(player)

            hospital_tmx_path = base_dir / "World" / "maps" / "Hospital.tmx"
            game_map = TileMap(tmx_path=str(hospital_tmx_path), tile_size=64)
            if game_map.player_start:
                player.rect.x = game_map.player_start[0]
                player.rect.y = game_map.player_start[1]
                player.hitbox_rect.midbottom = player.rect.midbottom
                player._fx = float(player.hitbox_rect.x)
                player._fy = float(player.hitbox_rect.y)

            # Load Nurse Joy and Shopkeeper
            npcs = load_hospital_npcs(game_map)
            for npc in npcs:
                if npc.name == "Nurse Joy":
                    nurse_joy = npc
                elif npc.name == "Shopkeeper":
                    shopkeeper = npc

            professor = None
            start_build_full_map()
            print("Entered hospital")
            initial_no_switch_frames = map_switch_cooldown

        # House entry
        house_rects = game_map.get_house_rects()
        house_hit = is_player_in_house(player.hitbox_rect, house_rects)

        if house_hit and initial_no_switch_frames == 0:
            save_world_position(player)

            house_tmx_path = base_dir / "World" / "maps" / "House.tmx"
            game_map = TileMap(tmx_path=str(house_tmx_path), tile_size=64)
            if game_map.player_start:
                player.rect.x = game_map.player_start[0]
                player.rect.y = game_map.player_start[1]
                player.hitbox_rect.midbottom = player.rect.midbottom
                player._fx = float(player.hitbox_rect.x)
                player._fy = float(player.hitbox_rect.y)
            professor = None
            start_build_full_map()
            print("Entered house")
            initial_no_switch_frames = map_switch_cooldown

        # GrassGym entry
        GrassGym_rects = game_map.get_GrassGym_rects()
        GrassGym_hit = is_player_in_GrassGym(player.hitbox_rect, GrassGym_rects)

        if GrassGym_hit and initial_no_switch_frames == 0:
            save_world_position(player)

            GrassGym_tmx_path = base_dir / "World" / "maps" / "GrassGym.tmx"
            game_map = TileMap(tmx_path=str(GrassGym_tmx_path), tile_size=64)
            if game_map.player_start:
                player.rect.x = game_map.player_start[0]
                player.rect.y = game_map.player_start[1]
                player.hitbox_rect.midbottom = player.rect.midbottom
                player._fx = float(player.hitbox_rect.x)
                player._fy = float(player.hitbox_rect.y)

            # Spawn trainers for GrassGym
            trainer_npcs = []
            for (x, y, trainer_type) in game_map.trainer_starts:
                sprite_path = base_dir.parent / "graphics" / "characters" / "grass_boss_1.png"
                if sprite_path.exists():
                    trainer = NPC(x, y, name="Grass Trainer", sprite_path=str(sprite_path), use_sprite_sheet=False, scale=1.0)
                    trainer_npcs.append(trainer)
                else:
                    print(f"Sprite not found: {sprite_path}")

            professor = None
            start_build_full_map()
            print("Entered GrassGym")
            initial_no_switch_frames = map_switch_cooldown

        # IceGym entry
        IceGym_rects = game_map.get_IceGym_rects()
        IceGym_hit = is_player_in_IceGym(player.hitbox_rect, IceGym_rects)

        if IceGym_hit and initial_no_switch_frames == 0:
            save_world_position(player)

            IceGym_tmx_path = base_dir / "World" / "maps" / "IceGym.tmx"
            game_map = TileMap(tmx_path=str(IceGym_tmx_path), tile_size=64)
            if game_map.player_start:
                player.rect.x = game_map.player_start[0]
                player.rect.y = game_map.player_start[1]
                player.hitbox_rect.midbottom = player.rect.midbottom
                player._fx = float(player.hitbox_rect.x)
                player._fy = float(player.hitbox_rect.y)

            # Spawn trainers for IceGym
            trainer_npcs = []
            for (x, y, trainer_type) in game_map.trainer_starts:
                sprite_path = base_dir.parent / "graphics" / "characters" / "water_boss_1.png"
                if sprite_path.exists():
                    trainer = NPC(x, y, name="Ice Trainer", sprite_path=str(sprite_path), use_sprite_sheet=False, scale=1.0)
                    trainer_npcs.append(trainer)
                else:
                    print(f"Sprite not found: {sprite_path}")

            professor = None
            start_build_full_map()
            print("Entered IceGym")
            initial_no_switch_frames = map_switch_cooldown

        # FireGym entry
        FireGym_rects = game_map.get_FireGym_rects()
        FireGym_hit = is_player_in_FireGym(player.hitbox_rect, FireGym_rects)

        if FireGym_hit and initial_no_switch_frames == 0:
            save_world_position(player)

            FireGym_tmx_path = base_dir / "World" / "maps" / "FireGym.tmx"
            game_map = TileMap(tmx_path=str(FireGym_tmx_path), tile_size=64)
            if game_map.player_start:
                player.rect.x = game_map.player_start[0]
                player.rect.y = game_map.player_start[1]
                player.hitbox_rect.midbottom = player.rect.midbottom
                player._fx = float(player.hitbox_rect.x)
                player._fy = float(player.hitbox_rect.y)

            # Spawn trainers for FireGym
            trainer_npcs = []
            for (x, y, trainer_type) in game_map.trainer_starts:
                sprite_path = base_dir.parent / "graphics" / "characters" / "fire_boss_1.png"
                print(f"Looking for sprite at: {sprite_path}")
                print(f"Sprite exists: {sprite_path.exists()}")
                if sprite_path.exists():
                    trainer = NPC(
                        x, y,
                        name="Fire Trainer",
                        sprite_path=str(sprite_path),
                        use_sprite_sheet=False, 
                        scale=1.0
                    )
                    trainer_npcs.append(trainer)
                else:
                    print(f"Sprite not found: {sprite_path}")

            professor = None
            start_build_full_map()
            print("Entered FireGym")
            initial_no_switch_frames = map_switch_cooldown

        # Exit back to World
        exit_rects = game_map.get_exit_rects()
        exit_hit = is_player_in_hospital(player.hitbox_rect, exit_rects) or is_player_in_house(player.hitbox_rect, exit_rects) or is_player_in_GrassGym(player.hitbox_rect, exit_rects) or is_player_in_IceGym(player.hitbox_rect, exit_rects) or is_player_in_FireGym(player.hitbox_rect, exit_rects)

        if exit_hit and initial_no_switch_frames == 0:
            world_tmx_path = base_dir / "World" / "maps" / "World.tmx"
            game_map = TileMap(tmx_path=str(world_tmx_path), tile_size=64)

            restore_world_position(player, game_map)

            if game_map.professor_start:
                professor = NPC(
                    game_map.professor_start[0],
                    game_map.professor_start[1],
                    name="Professor Oak",
                    use_sprite_sheet=False,
                    scale=0.8
                )
            start_build_full_map()
            print("Exited to world map")
            initial_no_switch_frames = map_switch_cooldown

        game_state, initial_no_switch_frames = handle_multiplayer_logic(game_state, player, game_map, initial_no_switch_frames)

        view_w, view_h = screen.get_size()
        map_w = getattr(game_map, "width", view_w)
        map_h = getattr(game_map, "height", view_h)
        cam_left = player.rect.centerx - view_w // 2
        cam_top = player.rect.centery - view_h // 2

        offset_x = -cam_left
        offset_y = -cam_top
    elif game_state == "waiting":
        view_w, view_h = screen.get_size()
        map_w = getattr(game_map, "width", view_w)
        map_h = getattr(game_map, "height", view_h)
        cam_left = player.rect.centerx - view_w // 2
        cam_top = player.rect.centery - view_h // 2

        if "Hospital" or "House" or "GrassGym" or "FireGym" or "IceGym" in str(game_map.tmx_path):
            cam_left = max(0, min(cam_left, map_w - view_w))
            cam_top = max(0, min(cam_top, map_h - view_h))

        offset_x = -cam_left
        offset_y = -cam_top
    else:
        offset_x = 0
        offset_y = 0

    screen.fill(BG)

    player_behind_building = False
    roof_rects = game_map.get_roof_rects()
    for roof in roof_rects:
        if player.rect.colliderect(roof):
            player_behind_building = player.rect.bottom < roof.centery
            break
    
    inside_hospital = "Hospital" in str(game_map.tmx_path)

    # Draw lower layers (ground, walls, etc.)
    game_map.draw_lower(screen, player.rect, offset_x=offset_x, offset_y=offset_y)

    if professor:
        professor.draw(screen, offset_x=offset_x, offset_y=offset_y)

    if inside_hospital:
        if nurse_joy:
            nurse_joy.draw(screen, offset_x=offset_x, offset_y=offset_y)
        if shopkeeper:
            shopkeeper.draw(screen, offset_x=offset_x, offset_y=offset_y)

    for trainer in trainer_npcs:
        trainer.draw(screen, offset_x=offset_x, offset_y=offset_y)
    
    if inside_hospital:
        game_map.draw_counters(screen, offset_x=offset_x, offset_y=offset_y)

    player.draw(screen, offset_x=offset_x, offset_y=offset_y)
    try:
        game_map.draw_upper(screen, player.rect, offset_x=offset_x, offset_y=offset_y)
    except Exception:
        pass
    if not inside_hospital:
        game_map.draw_upper(screen, player.rect, offset_x=offset_x, offset_y=offset_y)

    if show_coords:
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

        for bush in game_map.get_bush_rects():
            if isinstance(bush, pygame.Rect):
                pygame.draw.rect(
                    screen,
                    (BLUE),
                    pygame.Rect(
                        bush.x + offset_x, bush.y + offset_y, bush.width, bush.height
                    ),
                    2,
                )
            else:
                offset_points = [(x + offset_x, y + offset_y) for x, y in bush]
                if len(offset_points) > 1:
                    pygame.draw.polygon(screen, (BLUE), offset_points, 2)

        for wall in game_map.get_solid_rects():
            pygame.draw.rect(
                screen,
                (GREEN),
                pygame.Rect(
                    wall.x + offset_x, wall.y + offset_y, wall.width, wall.height
                ),
                1,
            )

    if encounter_active and encounter_pokemon:
        w, h = screen.get_size()
        init_msg = None
        if just_switched_pokemon and current_player_pokemon:
            init_msg = f"Go {current_player_pokemon.name}!"

        if faint_message:
            battle_menu(
                screen,
                encounter_pokemon,
                menu_font,
                coords_font,
                {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW, "BLUE": BLUE, "BG": BG},
                clock,
                player_pokemon=current_player_pokemon,
                initial_message=faint_message,
                show_intro=False,
                return_after_message=True,
            )
            faint_message = None
            if not trainer_battle_active or trainer_pokemon_index >= len(trainer_pokemon_team):
                encounter_active = False
                encounter_pokemon = None
                encounter_animation_done = False
                trainer_battle_active = False
                current_trainer = None
                trainer_pokemon_team = []
                current_trainer_pokemon = None
                trainer_pokemon_index = 0
            pygame.display.flip()
            continue

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
            pokedex_obj=pokedex,
            pokeball_img=pokeball_img,
            bag=bag,
        )
        just_switched_pokemon = False
        print(f"Battle choice: {choice}")

        if choice == "fight":
            if current_player_pokemon:
                moves = get_moves_for_pokemon(current_player_pokemon.name)
                bg_img = None
                try:
                    bg_img = pygame.image.load("graphics/backgrounds/forest.png").convert()
                except Exception:
                    bg_img = None

                sprite_surface = None
                try:
                    if encounter_pokemon.get("sprite"):
                        sprite_data = requests.get(encounter_pokemon["sprite"], timeout=5)
                        sprite_surface = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
                except Exception:
                    sprite_surface = None

                player_sprite_surface = None
                try:
                    player_sprite_url = None
                    if current_player_pokemon:
                        if isinstance(current_player_pokemon, dict):
                            player_sprite_url = current_player_pokemon.get("sprite")
                        else:
                            player_sprite_url = getattr(current_player_pokemon, "sprite", None)
                    if player_sprite_url:
                        sprite_data = requests.get(player_sprite_url, timeout=5)
                        player_sprite_surface = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
                except Exception:
                    player_sprite_surface = None

                spr_w = 269
                spr_h = 269
                target_midright = (w - 200, h // 2 - 200)
                sprite_x = target_midright[0] - spr_w // 2
                sprite_y = target_midright[1]

                p_x = 500
                p_y = h // 2 + 40

                selected_move = show_move_menu(
                    screen, moves, menu_font, coords_font,
                    {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW, "BLUE": BLUE, "BG": BG},
                    clock, bg_img, sprite_surface, player_sprite_surface, sprite_x, sprite_y, p_x, p_y, encounter_pokemon, current_player_pokemon, TYPE_ICONS
                )
                if selected_move:
                    damage = selected_move.get("power", 0)
                    if damage is None:
                        damage = 0
                    encounter_pokemon['hp'] = max(0, encounter_pokemon.get('hp', 1) - damage)

                    if encounter_pokemon['hp'] <= 0:
                        # Award XP for defeating Pokemon
                        base_xp = encounter_pokemon.get('level', 1) * 10 + 25
                        leveled_up = pokedex.award_xp_to_team(base_xp, pokemon=current_player_pokemon, team_wide=False)
                        
                        # Show XP gain
                        show_xp_gain(screen, base_xp, menu_font, {"WHITE": WHITE, "BLACK": BLACK, "GOLD": GOLD}, clock)
                        
                        # Show level up notifications
                        for pokemon in leveled_up:
                            show_level_up_screen(screen, pokemon, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                            pygame.event.clear()
                        
                        if trainer_battle_active:
                            faint_message = f"{current_trainer.name}'s {encounter_pokemon['name']} fainted!"
                            trainer_pokemon_index += 1
                            if trainer_pokemon_index < len(trainer_pokemon_team):
                                current_trainer_pokemon = trainer_pokemon_team[trainer_pokemon_index]
                                encounter_pokemon = current_trainer_pokemon
                                faint_message += f" {current_trainer.name} sent out {encounter_pokemon['name']}!"
                            else:
                                # Gym beaten - award bonus XP
                                gym_name = current_trainer.name.replace(" Trainer", " Gym")
                                gym_leveled_up = pokedex.beat_gym(gym_name)
                                faint_message += f" You defeated {current_trainer.name}!"
                                
                                if gym_leveled_up:
                                    faint_message += " Bonus XP for beating the gym!"
                                    for pokemon in gym_leveled_up:
                                        show_level_up_screen(screen, pokemon, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                                
                                trainer_battle_active = False
                                current_trainer = None
                                trainer_pokemon_team = []
                                current_trainer_pokemon = None
                                trainer_pokemon_index = 0
                        else:
                            faint_message = f"Wild {encounter_pokemon['name']} fainted!"
                        continue

                    opponent_moves = get_moves_for_pokemon(encounter_pokemon["name"].lower())
                    if opponent_moves:
                        opponent_move = random.choice(opponent_moves)
                        opponent_damage = opponent_move.get("power", 0)
                        if opponent_damage is None:
                            opponent_damage = 0
                        current_player_pokemon.current_hp = max(0, current_player_pokemon.current_hp - opponent_damage)

                        if current_player_pokemon.current_hp <= 0:
                            faint_message = f"{current_player_pokemon.name} fainted!"
                            continue

        elif choice == "pokémon" or choice == "pokemon":
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

        elif choice == "bag":
            try:
                in_trainer_battle = trainer_battle_active
                res = show_bag_menu(screen, bag, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "BG": BG}, clock, in_battle=True, encounter_pokemon=encounter_pokemon, current_player_pokemon=current_player_pokemon, pokedex_obj=pokedex, player=player, is_trainer_battle=in_trainer_battle)
                if res:
                    act = res.get('action')
                    if act == 'caught':
                        faint_message = f"You caught a {encounter_pokemon.get('name', 'Pokémon')}!"
                    elif act == 'escaped':
                        faint_message = f"{encounter_pokemon.get('name', 'The Pokémon')} escaped!"
            except Exception as e:
                print(f"Bag usage failed: {e}")

        elif choice == "run":
            if trainer_battle_active:
                faint_message = "You can't run from a trainer battle!"
            else:
                try:
                    run_away_animation(screen, Screen_Width, Screen_Height, clock, encounter_pokemon)
                except Exception as e:
                    print(f"Run-away animation failed: {e}")
                faint_message = "You ran away!"

    if game_state == "waiting":
        game_state = handle_waiting_state(game_state, screen, menu_font, WHITE)

    if game_state == "multiplayer_battle":
        game_state = handle_multiplayer_battle(game_state, screen, menu_font, coords_font, {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW, "BLUE": BLUE, "BG": BG}, clock, pokedex, current_player_pokemon, bag, TYPE_ICONS)

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
                start_build_full_map()
        except Exception:
            pass

    if show_pokedex:
        pokedex_menu(
            screen, pokedex, menu_font, coords_font,
            {"WHITE": WHITE, "BLACK": BLACK, "RED": RED, "GREEN": GREEN, "BLUE": BLUE, "BG": BG},
            clock, is_battle_context=False, current_player=current_player_pokemon, bag=bag, pokedex_obj=pokedex
        )
        show_pokedex = False

    pygame.display.flip()

pygame.quit()