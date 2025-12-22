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
        self.status = None

    def gain_experience(self, xp):
        self.experience += xp
        leveled_up = False

        # Level up formula: level^2 * 100 XP needed for next level
        while self.experience >= (self.level + 1) * (self.level + 1) * 100:
            self.level += 1
            leveled_up = True
            # Increase stats on level up
            self.max_hp += 5
            self.hp += 5
            self.current_hp += 5
            self.attack += 3

        return leveled_up

    def get_xp_for_next_level(self):
        return (self.level + 1) * (self.level + 1) * 100

    def get_xp_progress(self):
        current_level_xp = self.level * self.level * 100
        next_level_xp = self.level * self.level * 100
        progress = self.experience - current_level_xp
        needed = next_level_xp - current_level_xp
        return progress, needed

    def to_dict(self):
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "attack": self.attack,
            "sprite": self.sprite,
            "level": self.level,
            "experience": self.experience,
            "status": self.status
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
        poke.status = data.get("status", None)
        return poke

class Pokedex:
    def __init__(self, save_path="pokedex_save.json"):
        self.save_path = save_path
        self.captured_pokemon = []
        self.active_team = []
        self.gyms_beaten = []
        self.load()

    def add_pokemon(self, pokemon):
        if isinstance(pokemon, dict):
            pokemon = Pokemon.from_dict(pokemon)

        # Avoid adding duplicates to captured_pokemon
        if pokemon not in self.captured_pokemon:
            self.captured_pokemon.append(pokemon)

        # Add to active team if there's space
        if len(self.active_team) < 6 and pokemon not in self.active_team:
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

    def award_xp_to_team(self, xp_amount, pokemon=None, team_wide=False):
        leveled_up_pokemon = []
        if team_wide:
            for p in self.active_team:
                if p.current_hp > 0:  # Only conscious Pokémon gain XP
                    if p.gain_experience(xp_amount):
                        leveled_up_pokemon.append(p)
        else:
            target = pokemon if pokemon else (self.active_team[0] if self.active_team else None)
            if target and target.current_hp > 0:
                if target.gain_experience(xp_amount):
                    leveled_up_pokemon.append(target)
        self.save()
        return leveled_up_pokemon

    def beat_gym(self, gym_name):
        if gym_name not in self.gyms_beaten:
            self.gyms_beaten.append(gym_name)
            # Award 500 XP for beating a gym, to the whole team
            leveled_up = self.award_xp_to_team(500, team_wide=True)
            self.save()
            return leveled_up
        return []

    def save(self):
        try:
            data = {
                "captured": [p.to_dict() for p in self.captured_pokemon],
                "active_team": [p.to_dict() for p in self.active_team],
                "gyms_beaten": self.gyms_beaten
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

                self.captured_pokemon = []
                self.active_team = []

                # Load captured Pokémon
                for p in data.get("captured", []):
                    pokemon = Pokemon.from_dict(p)
                    self.captured_pokemon.append(pokemon)

                # Load active team
                for team_data in data.get("active_team", []):
                    for poke in self.captured_pokemon:
                        if poke.name == team_data.get("name"):
                            self.active_team.append(poke)
                            break

                self.gyms_beaten = data.get("gyms_beaten", [])
                print(f"Loaded Pokédex: {len(self.captured_pokemon)} captured, {len(self.active_team)} in team, {len(self.gyms_beaten)} gyms beaten")
            else:
                print("No existing Pokédex save found")
        except Exception as e:
            print(f"Failed to load Pokédex: {e}")
            self.captured_pokemon = []
            self.active_team = []
            self.gyms_beaten = []

    def clear_team(self):
        self.active_team = []