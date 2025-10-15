import random
import requests

def is_player_in_bush(player_rect, bush_rects):
    for bush in bush_rects:
        if player_rect.colliderect(bush):
            return True
    return False

def trigger_encounter():
    encounter_chance = 0.01  # 1% chance
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