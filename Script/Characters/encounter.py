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
            # Rectangle collision
            if player_rect.colliderect(bush):
                return bush
        else:
            # Polygon collision
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
    return random.random() < 0.1 #10%


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
        return {
            "name": fallback.capitalize(),
            "sprite": None,
            "hp": random.randint(30, 80),
            "attack": random.randint(20, 70),
        }

    names, weights = zip(*_pokemon_cache)
    chosen_name = random.choices(names, weights=weights, k=1)[0]

    try:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{chosen_name}", timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "name": data["name"].capitalize(),
            "sprite": data["sprites"]["front_default"],
            "hp": data["stats"][0]["base_stat"],
            "attack": data["stats"][1]["base_stat"],
        }
    except Exception:
        return {
            "name": chosen_name.capitalize(),
            "sprite": None,
            "hp": random.randint(30, 80),
            "attack": random.randint(20, 70),
        }
    
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

def heal_player_pokemon(player):
    if trigger_hospital_visit(player):
        for pokemon in player.pokemon_team:
            pokemon.heal()
        return True
    else:
        return False

def run_hospital_interaction(player, hospital_npc):
    hospital_npc.speak("Welcome to the Pokémon Center! Your Pokémon will be fully healed here.")
    if player.has_pokemon():
        hospital_npc.speak("Let me take care of your team right away.")
        player.heal_all_pokemon()
        hospital_npc.speak("All done! Your Pokémon are healthy and ready to go.")
    else:
        hospital_npc.speak("It seems you don't have any Pokémon with you. Come back when you do!")
    hospital_npc.speak("Take care on your journey!")
