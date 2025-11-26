import random
import time
import json
import os
import requests
import threading

_bush_cooldowns = {}
_pokemon_cache = []
_CACHE_FILE = "pokemon_cache.json"
_CACHE_LOCK = threading.Lock()
_FETCH_THREAD = None


def is_player_in_bush(player_rect, bush_rects):
    for bush in bush_rects:
        if player_rect.colliderect(bush):
            return bush
    return None


def can_trigger_bush(bush, cooldown_seconds=30):
    last_time = _bush_cooldowns.get((bush.x, bush.y, bush.width, bush.height))
    now = time.time()
    return not last_time or now - last_time >= cooldown_seconds


def mark_bush_triggered(bush):
    _bush_cooldowns[(bush.x, bush.y, bush.width, bush.height)] = time.time()


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