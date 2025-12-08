import json
import os
from pathlib import Path


class Pokemon:
    def __init__(self, name, hp, attack, sprite=None, level=1):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.sprite = sprite
        self.level = level
        self.experience = 0
    
    def to_dict(self):
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "attack": self.attack,
            "sprite": self.sprite,
            "level": self.level,
            "experience": self.experience
        }
    
    @staticmethod
    def from_dict(data):
        poke = Pokemon(
            name=data.get("name", "Unknown"),
            hp=data.get("hp", 50),
            attack=data.get("attack", 50),
            sprite=data.get("sprite"),
            level=data.get("level", 1)
        )
        poke.max_hp = data.get("max_hp", poke.hp)
        poke.current_hp = data.get("current_hp", poke.hp)
        poke.experience = data.get("experience", 0)
        return poke


class Pokedex:
    def __init__(self, save_path="pokedex_save.json"):
        self.save_path = save_path
        self.captured_pokemon = []
        self.active_team = []
        self.load()
    
    def add_pokemon(self, pokemon):
        if isinstance(pokemon, dict):
            pokemon = Pokemon.from_dict(pokemon)
        self.captured_pokemon.append(pokemon)
        # Auto-add to team if team has space
        if len(self.active_team) < 6:
            self.active_team.append(pokemon)
        self.save()
        return True
    
    def get_captured_count(self):
        return len(self.captured_pokemon)
    
    def get_team(self):
        return self.active_team
    
    def set_active_team(self, pokemon_list):
        self.active_team = pokemon_list[:6]
        self.save()
    
    def get_active_pokemon(self, index):
        if 0 <= index < len(self.active_team):
            return self.active_team[index]
        return None
    
    def get_first_available_pokemon(self):
        return self.active_team[0] if self.active_team else None
    
    def remove_pokemon(self, pokemon):
        if pokemon in self.captured_pokemon:
            self.captured_pokemon.remove(pokemon)
        if pokemon in self.active_team:
            self.active_team.remove(pokemon)
        self.save()
    
    def save(self):
        try:
            data = {
                "captured": [p.to_dict() for p in self.captured_pokemon],
                "active_team": [p.to_dict() for p in self.active_team]
            }
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save Pokédex: {e}")
    
    def load(self):
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.captured_pokemon = [Pokemon.from_dict(p) for p in data.get("captured", [])]
                active_team_data = data.get("active_team", [])
                self.active_team = []
                for team_data in active_team_data:
                    for poke in self.captured_pokemon:
                        if poke.name == team_data.get("name"):
                            self.active_team.append(poke)
                            break
                
                print(f"Loaded Pokédex: {len(self.captured_pokemon)} captured, {len(self.active_team)} in team")
            else:
                print("No existing Pokédex save found")
        except Exception as e:
            print(f"Failed to load Pokédex: {e}")
            self.captured_pokemon = []
            self.active_team = []
