import random
import time
import json
import os
import requests
import threading
import pygame

_bush_cooldowns = {}
_pokemon_cache = []
_CACHE_FILE = "pokemon_cache.json"
_CACHE_LOCK = threading.Lock()
_FETCH_THREAD = None
can_enter_hospital = True

def _point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

def _rect_collides_polygon(rect, polygon):
    corners = [
        (rect.left, rect.top),
        (rect.right, rect.top),
        (rect.left, rect.bottom),
        (rect.right, rect.bottom),
        (rect.centerx, rect.centery)
    ]

    for corner in corners:
        if _point_in_polygon(corner, polygon):
            return True

    for vertex in polygon:
        if rect.collidepoint(vertex):
            return True

    return False

def is_player_in_bush(player_rect, bush_shapes):
    for bush in bush_shapes:
        if isinstance(bush, pygame.Rect):
            if player_rect.colliderect(bush):
                return bush
        else:
            if _rect_collides_polygon(player_rect, bush):
                return bush
    return None

def can_trigger_bush(bush, cooldown_seconds=30):
    if isinstance(bush, pygame.Rect):
        bush_key = (bush.x, bush.y, bush.width, bush.height)
    else:
        bush_key = tuple(bush)

    last_time = _bush_cooldowns.get(bush_key)
    now = time.time()
    return not last_time or now - last_time >= cooldown_seconds

def mark_bush_triggered(bush):
    if isinstance(bush, pygame.Rect):
        bush_key = (bush.x, bush.y, bush.width, bush.height)
    else:
        bush_key = tuple(bush)

    _bush_cooldowns[bush_key] = time.time()

def trigger_encounter():
    return random.random() < 0.1

def fetch_and_store_all_moves():
    moves_file = "moves.json"
    moves_data = {}

    try:
        if os.path.exists(moves_file):
            with open(moves_file, "r") as f:
                moves_data = json.load(f)
                if moves_data:  # If moves.json is not empty, skip fetching
                    print(f"Moves data already exists in {moves_file}")
                    return
    except json.JSONDecodeError:
        print(f"{moves_file} is empty or corrupted. Fetching moves from PokéAPI...")
    except Exception as e:
        print(f"An error occurred while reading {moves_file}: {e}")

    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1025", timeout=20)
        response.raise_for_status()
        pokemon_list = response.json()["results"]
    except Exception as e:
        print(f"Failed to fetch Pokémon list from PokéAPI: {e}")
        return

    for pokemon in pokemon_list:
        pokemon_name = pokemon["name"]
        try:
            pokemon_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}", timeout=5)
            pokemon_response.raise_for_status()
            pokemon_data = pokemon_response.json()
            moves = []
            for move in pokemon_data["moves"][:4]:  # Limit to 4 moves
                move_name = move["move"]["name"].replace("-", " ").title()
                move_url = move["move"]["url"]
                try:
                    move_response = requests.get(move_url, timeout=5)
                    move_response.raise_for_status()
                    move_data = move_response.json()
                    move_power = move_data.get("power", 0)
                    move_type = move_data["type"]["name"]
                except Exception as e:
                    print(f"Failed to fetch move details for {move_name}: {e}")
                    move_power = 0
                    move_type = "normal"
                moves.append({"name": move_name, "power": move_power, "type": move_type})
            moves_data[pokemon_name] = moves
            print(f"Fetched moves for {pokemon_name}")
        except Exception as e:
            print(f"Failed to fetch moves for {pokemon_name}: {e}")
            moves_data[pokemon_name] = [{"name": "Tackle", "power": 40, "type": "normal"}]

    try:
        with open(moves_file, "w") as f:
            json.dump(moves_data, f, indent=2)
        print(f"Moves data saved to {moves_file}")
    except Exception as e:
        print(f"Failed to save moves data to {moves_file}: {e}")

def _load_cache():
    global _pokemon_cache
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                _pokemon_cache = [(p["name"], p.get("weight", 1)) for p in data]
                print(f"Loaded {len(_pokemon_cache)} Pokémon from cache.")
                return True
        except Exception as e:
            print(f"Cache load failed: {e}")
    return False

def _save_cache(pokemon_list):
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(pokemon_list, f, indent=2)
        print(f"Saved {len(pokemon_list)} Pokémon to cache.")
    except Exception as e:
        print(f"Failed to save cache: {e}")

def _fetch_pokemon_data_async():
    global _pokemon_cache
    with _CACHE_LOCK:
        if _pokemon_cache:
            return

    print("Fetching full Pokémon list from PokéAPI")

    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1025", timeout=20)
        response.raise_for_status()
        results = response.json()["results"]
    except Exception as e:
        print(f"Failed to fetch list from PokéAPI: {e}")
        return

    pokemon_list = []
    for i, p in enumerate(results, start=1):
        name = p["name"]
        if any(term in name for term in ["mega", "gmax", "-totem", "-hisui", "-alola", "-galar"]):
            continue

        try:
            species_data = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{name}", timeout=5)
            if not species_data.ok:
                continue
            species = species_data.json()
            capture_rate = species.get("capture_rate", 45)
        except Exception:
            capture_rate = 45

        weight = max(1, capture_rate / 255 * 10)
        pokemon_list.append({"name": name, "weight": weight})

        if i % 50 == 0:
            print(f"Fetched {i}/{len(results)} Pokémon...")

    with _CACHE_LOCK:
        _pokemon_cache = [(p["name"], p["weight"]) for p in pokemon_list]
        _save_cache(pokemon_list)
        print(f"Pokémon cache built with {len(_pokemon_cache)} entries.")

def _ensure_pokemon_loaded():
    global _FETCH_THREAD
    if _pokemon_cache:
        return

    if not _load_cache():
        if not _FETCH_THREAD or not _FETCH_THREAD.is_alive():
            _FETCH_THREAD = threading.Thread(target=_fetch_pokemon_data_async, daemon=True)
            _FETCH_THREAD.start()
            print("Pokémon data loading in background...")

def fetch_random_pokemon():
    _ensure_pokemon_loaded()

    if not _pokemon_cache:
        fallback = random.choice(["pikachu", "charmander", "bulbasaur", "squirtle"])
        hp = random.randint(30, 80)
        return {
            "name": fallback.capitalize(),
            "sprite": None,
            "hp": hp,
            "max_hp": hp,
            "attack": random.randint(20, 70),
        }

    names, weights = zip(*_pokemon_cache)
    chosen_name = random.choices(names, weights=weights, k=1)[0]

    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{chosen_name}", timeout=5)
        response.raise_for_status()
        data = response.json()
        hp = data["stats"][0]["base_stat"]
        return {
            "name": data["name"].capitalize(),
            "sprite": data["sprites"]["front_default"],
            "hp": hp,
            "max_hp": hp,
            "attack": data["stats"][1]["base_stat"],
        }
    except Exception:
        hp = random.randint(30, 80)
        return {
            "name": chosen_name.capitalize(),
            "sprite": None,
            "hp": hp,
            "max_hp": hp,
            "attack": random.randint(20, 70),
        }

def get_moves_for_pokemon(pokemon_name):
    moves_file = "moves.json"
    if os.path.exists(moves_file):
        try:
            with open(moves_file, "r") as f:
                moves_data = json.load(f)
            if pokemon_name.lower() in moves_data:
                return moves_data[pokemon_name.lower()]
        except Exception as e:
            print(f"Error reading moves data: {e}")

    # Fallback if moves are not found in the file
    return [{"name": "Tackle", "power": 40, "type": "normal"}]

def is_player_in_hospital(player_rect, hospital_shapes):
    for hospital in hospital_shapes:
        if isinstance(hospital, pygame.Rect):
            if player_rect.colliderect(hospital):
                return hospital
        else:
            if _rect_collides_polygon(player_rect, hospital):
                return hospital
    return None

def can_enter_hospital(player, hospital):
    if not player.has_pokemon():
        return False
    if not player.is_near(hospital):
        return False
    else:
        return True

def trigger_hospital_visit(player):
    if player.can_enter_hospital():
        return True
    else:
        return False

def heal_player_pokemon(player):
    if player.run_hospital_interaction:
        player.run_hospital_interaction()

def run_hospital_interaction(player, hospital_npc):
    hospital_npc.speak("Welcome to the Pokémon Center! Your Pokémon will be fully healed here.")
    if player.has_pokemon():
        hospital_npc.speak("Let me take care of your team right away.")
        player.heal_all_pokemon()
        hospital_npc.speak("All done! Your Pokémon are healthy and ready to go.")
    else:
        hospital_npc.speak("It seems you don't have any Pokémon with you. Come back when you do!")
    hospital_npc.speak("Take care on your journey!")

#house
def is_player_in_house(player_rect, house_shapes):
    for house in house_shapes:
        if isinstance(house, pygame.Rect):
            if player_rect.colliderect(house):
                return house
        else:
            if _rect_collides_polygon(player_rect, house):
                return house
    return None

#GrassGym
def is_player_in_GrassGym(player_rect, GrassGym_shapes):
    for GrassGym in GrassGym_shapes:
        if isinstance(GrassGym, pygame.Rect):
            if player_rect.colliderect(GrassGym):
                return GrassGym
        else:
            if _rect_collides_polygon(player_rect, GrassGym):
                return GrassGym
    return None

#IceGym
def is_player_in_IceGym(player_rect, IceGym_shapes):
    for IceGym in IceGym_shapes:
        if isinstance(IceGym, pygame.Rect):
            if player_rect.colliderect(IceGym):
                return IceGym
        else:
            if _rect_collides_polygon(player_rect, IceGym):
                return IceGym
    return None

#FireGym
def is_player_in_FireGym(player_rect, FireGym_shapes):
    for FireGym in FireGym_shapes:
        if isinstance(FireGym, pygame.Rect):
            if player_rect.colliderect(FireGym):
                return FireGym
        else:
            if _rect_collides_polygon(player_rect, FireGym):
                return FireGym
    return None