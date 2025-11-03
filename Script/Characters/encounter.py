import random
import time
import requests

_bush_cooldowns = {}

def is_player_in_bush(player_rect, bush_rects):
    for bush in bush_rects:
        if player_rect.colliderect(bush):
            return bush
    return None

def can_trigger_bush(bush, cooldown_seconds=30):
    global _bush_cooldowns
    last_time = _bush_cooldowns.get((bush.x, bush.y, bush.width, bush.height))
    now = time.time()
    if not last_time or now - last_time >= cooldown_seconds:
        return True
    return False

def mark_bush_triggered(bush):
    global _bush_cooldowns
    _bush_cooldowns[(bush.x, bush.y, bush.width, bush.height)] = time.time()

def trigger_encounter():
    encounter_chance = 0.1 # 10% chance
    return random.random() < encounter_chance

def fetch_random_pokemon():
    pokemon_id = random.randint(1, 1025)
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    if response.ok:
        data = response.json()
        return {
            "name": data["name"].capitalize(),
            "sprite": data["sprites"]["front_default"],
            "hp": data["stats"][0]["base_stat"],
            "attack": data["stats"][1]["base_stat"],
        }
    return None