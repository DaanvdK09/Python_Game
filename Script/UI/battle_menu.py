import pygame
from io import BytesIO
import requests
import sys
from pathlib import Path

# Import your constants
from constants import (
    TYPEFIRE, TYPEWATER, TYPEGRASS, TYPEELECTRIC, TYPENORMAL, TYPEFIGHTING, TYPEFLYING,
    TYPEPOISON, TYPEGROUND, TYPEROCK, TYPEBUG, TYPEGHOST, TYPEDRAGON, TYPEDARK,
    TYPESTEEL, TYPEFAIRY, TYPEPSYCHIC, TYPEICE, BLACK, WHITE, BG
)

# Load type icons
def load_type_icons():
    base_dir = Path(__file__).parent.parent.parent
    icons = {}
    type_icon_mapping = {
        "fire": "fire-type-icon.png",
        "water": "water-type-icon.png",
        "grass": "grass-type-icon.png",
        "electric": "electric-type-icon.png",
        "normal": "normal-type-icon.png",
        "fighting": "fighting-type-icon.png",
        "flying": "flying-type-icon.png",
        "poison": "poison-type-icon.png",
        "ground": "ground-type-icon.png",
        "rock": "rock-type-icon.png",
        "bug": "bug-type-icon.png",
        "ghost": "ghost-type-icon.png",
        "dragon": "dragon-type-icon.png",
        "dark": "dark-type-icon.png",
        "steel": "steel-type-icon.png",
        "fairy": "fairy-type-icon.png",
        "psychic": "psychic-type-icon.png",
        "ice": "ice-type-icon.png",
    }

    for type_name, icon_filename in type_icon_mapping.items():
        icon_path = base_dir / "graphics" / "icons" / icon_filename
        if icon_path.exists():
            try:
                icon = pygame.image.load(str(icon_path)).convert_alpha()
                icon = pygame.transform.scale(icon, (38, 38))
                icons[type_name] = icon
            except Exception as e:
                icons[type_name] = None
        else:
            icons[type_name] = None
    return icons

def get_type_color(move_type):
    type_colors = {
        "fire": TYPEFIRE,
        "water": TYPEWATER,
        "grass": TYPEGRASS,
        "electric": TYPEELECTRIC,
        "normal": TYPENORMAL,
        "fighting": TYPEFIGHTING,
        "flying": TYPEFLYING,
        "poison": TYPEPOISON,
        "ground": TYPEGROUND,
        "rock": TYPEROCK,
        "bug": TYPEBUG,
        "ghost": TYPEGHOST,
        "dragon": TYPEDRAGON,
        "dark": TYPEDARK,
        "steel": TYPESTEEL,
        "fairy": TYPEFAIRY,
        "psychic": TYPEPSYCHIC,
        "ice": TYPEICE,
    }
    return type_colors.get(move_type.lower(), TYPENORMAL)

def show_move_menu(
    screen, moves, menu_font, small_font, colors, clock, bg_img, sprite_surface,
    player_sprite_surface, sprite_x, sprite_y, p_x, p_y, pokemon, player_pokemon, type_icons
):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BG = colors.get("BG", (30, 30, 30))

    if not moves:
        return None

    options = [move["name"] for move in moves]
    option_colors = [get_type_color(move["type"]) for move in moves]
    selected = 0

    fps = 60
    running = True
    while running:
        sw, sh = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                    return moves[selected]
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    if selected % 2 == 0:
                        selected = selected + 1
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    if selected % 2 == 1:
                        selected = selected - 1
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    if selected < 2:
                        selected = selected + 2
                if event.key in (pygame.K_UP, pygame.K_w):
                    if selected >= 2:
                        selected = selected - 2
                if event.key == pygame.K_ESCAPE:
                    return None

        if bg_img:
            try:
                b = pygame.transform.scale(bg_img, (sw, sh))
                screen.blit(b, (0, 0))
            except Exception:
                screen.fill(BG)
        else:
            screen.fill(BG)

        spr_w = 269
        spr_h = 269
        if sprite_surface:
            try:
                spr = pygame.transform.scale(sprite_surface, (spr_w, spr_h))
                spr_rect = spr.get_rect()
                spr_rect.topleft = (sprite_x, sprite_y)
                screen.blit(spr, spr_rect)
            except Exception:
                ph_rect = pygame.Rect(sprite_x, sprite_y, spr_w, spr_h)
                pygame.draw.rect(screen, (100, 100, 100), ph_rect)

        p_spr = None
        if player_sprite_surface:
            try:
                p_spr = pygame.transform.scale(player_sprite_surface, (308, 308))
                p_spr = pygame.transform.flip(p_spr, True, False)
                p_rect = p_spr.get_rect()
                p_rect.topleft = (p_x, p_y)
                screen.blit(p_spr, p_rect)
            except Exception:
                p_ph_rect = pygame.Rect(p_x, p_y, 220, 220)
                pygame.draw.rect(screen, (80, 80, 80), p_ph_rect)

        def _get_hp(obj):
            try:
                if obj is None:
                    return 0.0, 0.0
                if isinstance(obj, dict):
                    curr = obj.get('hp', obj.get('current_hp', 0)) or 0
                    max_hp = obj.get('max_hp', None)
                    if max_hp is None:
                        max_hp = curr
                    return float(curr), float(max_hp)
                else:
                    curr = getattr(obj, 'current_hp', None)
                    if curr is None:
                        curr = getattr(obj, 'hp', 0)
                    max_hp = getattr(obj, 'max_hp', None)
                    if max_hp is None:
                        max_hp = getattr(obj, 'hp', curr)
                    return float(curr), float(max_hp)
            except Exception:
                return 0.0, 0.0

        def _get_name(obj):
            try:
                if obj is None:
                    return "Unknown"
                if isinstance(obj, dict):
                    return obj.get('name', 'Unknown')
                return getattr(obj, 'name', 'Unknown')
            except Exception:
                return "Unknown"

        try:
            enemy_curr, enemy_max = _get_hp(pokemon)
            if enemy_max <= 0:
                enemy_pct = 0.0
            else:
                enemy_pct = max(0.0, min(1.0, enemy_curr / enemy_max))
            bar_w = 216
            bar_h = 14
            bar_x = int(sprite_x + spr_w // 2 - bar_w // 2)
            bar_y = int(sprite_y - 50)
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)
            fill_w = int(bar_w * enemy_pct)
            if enemy_pct > 0.5:
                hp_color = (46, 129, 31)
            elif enemy_pct > 0.25:
                hp_color = (255, 222, 0)
            else:
                hp_color = (206, 0, 0)
            if fill_w > 0:
                pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, 2, border_radius=6)
            try:
                hp_txt = small_font.render(f"{int(enemy_curr)}/{int(enemy_max)}", True, BLACK)
                try:
                    ename = _get_name(pokemon)
                    name_txt = small_font.render(str(ename), True, BLACK)
                    spacing = 6
                    hp_w = hp_txt.get_width()
                    name_w = name_txt.get_width()
                    combined_w = name_w + spacing + hp_w
                    base_x = bar_x + bar_w // 2 - combined_w // 2
                    text_y = bar_y - hp_txt.get_height() - 2
                    screen.blit(name_txt, (base_x, text_y))
                    screen.blit(hp_txt, (base_x + name_w + spacing, text_y))
                except Exception:
                    screen.blit(hp_txt, (bar_x + bar_w // 2 - hp_txt.get_width() // 2, bar_y - hp_txt.get_height() - 2))
            except Exception:
                pass

            player_curr, player_max = _get_hp(player_pokemon)
            if player_max <= 0:
                player_pct = 0.0
            else:
                player_pct = max(0.0, min(1.0, player_curr / player_max))
            p_bar_w = bar_w
            p_bar_h = 14
            p_bar_x = int(p_x + (308 - p_bar_w) // 2)
            p_bar_y = int(p_y - p_bar_h + 38)
            p_bg = pygame.Rect(p_bar_x, p_bar_y, p_bar_w, p_bar_h)
            pygame.draw.rect(screen, (40, 40, 40), p_bg, border_radius=6)
            p_fill = int(p_bar_w * player_pct)
            if player_pct > 0.5:
                p_color = (46, 129, 31)
            elif player_pct > 0.25:
                p_color = (255, 222, 0)
            else:
                p_color = (206, 0, 0)
            if p_fill > 0:
                pygame.draw.rect(screen, p_color, (p_bar_x, p_bar_y, p_fill, p_bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), p_bg, 2, border_radius=6)
            try:
                p_txt = small_font.render(f"{int(player_curr)}/{int(player_max)}", True, BLACK)
                try:
                    pname = _get_name(player_pokemon)
                    pname_txt = small_font.render(str(pname), True, BLACK)
                    spacing = 6
                    hp_w = p_txt.get_width()
                    name_w = pname_txt.get_width()
                    combined_w = name_w + spacing + hp_w
                    base_x = p_bar_x + p_bar_w // 2 - combined_w // 2
                    text_y = p_bar_y - p_txt.get_height() - 2
                    screen.blit(pname_txt, (base_x, text_y))
                    screen.blit(p_txt, (base_x + name_w + spacing, text_y))
                except Exception:
                    screen.blit(p_txt, (p_bar_x + p_bar_w // 2 - p_txt.get_width() // 2, p_bar_y - p_txt.get_height() - 2))
            except Exception:
                pass
        except Exception:
            pass

        padding = 18
        box_h = 160
        full_box_rect = pygame.Rect(20, sh - box_h - 20, sw - 40, box_h)
        pygame.draw.rect(screen, WHITE, full_box_rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, full_box_rect, 3, border_radius=8)

        if player_pokemon:
            try:
                pname = player_pokemon.name if not isinstance(player_pokemon, dict) else player_pokemon.get('name')
            except Exception:
                pname = None
        else:
            pname = None
        if pname:
            msg = f"What will {pname} do?"
        else:
            msg = "What will the Pokémon do?"
        text = menu_font.render(msg, True, BLACK)
        screen.blit(text, (full_box_rect.x + padding, full_box_rect.y + padding))

        area_w = int(full_box_rect.width * 0.5)
        area_h = full_box_rect.height - padding * 2
        area_x = full_box_rect.right - area_w - padding
        area_y = full_box_rect.y + padding
        opts_bg = pygame.Rect(area_x, area_y, area_w, area_h)
        pygame.draw.rect(screen, WHITE, opts_bg, border_radius=6)
        pygame.draw.rect(screen, BLACK, opts_bg, 2, border_radius=6)
        inner = max(8, padding // 2)
        opt_w = (opts_bg.width - inner * 3) // 2
        opt_h = (opts_bg.height - inner * 3) // 2

        for i, opt in enumerate(options):
            row = i // 2
            col = i % 2
            x = opts_bg.x + inner + col * (opt_w + inner)
            y = opts_bg.y + inner + row * (opt_h + inner)
            rect = pygame.Rect(x, y, opt_w, opt_h)
            pygame.draw.rect(screen, option_colors[i], rect, border_radius=6)
            if i == selected:
                pygame.draw.rect(screen, BLACK, rect, 3, border_radius=6)

            # Render move name
            text = small_font.render(opt, True, WHITE)
            screen.blit(
                text,
                (
                    rect.x + rect.width // 2 - text.get_width() // 2,
                    rect.y + rect.height // 2 - text.get_height() // 2,
                ),
            )

            # Render type icon
            icon = None
            if type_icons:
                icon = type_icons.get(moves[i]["type"].lower())
            if icon:
                icon_rect = icon.get_rect(topleft=(rect.x + 5, rect.y + 5))
                screen.blit(icon, icon_rect)

        pygame.display.flip()
        clock.tick(fps)
    return None

def battle_menu(screen, pokemon, menu_font, small_font, colors, clock=None, player_pokemon=None, initial_message=None, show_intro=True, pokedex_obj=None, pokeball_img=None, bag=None, return_after_message=False):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BATTLERED = colors.get("RED", (206, 0, 0))
    BATTLEBLUE = colors.get("BLUE", (59, 76, 202))
    BATTLEGREEN = colors.get("GREEN", (46, 129, 31))
    BATTLEYELLOW = colors.get("YELLOW", (255, 222, 0))
    BG = colors.get("BG", (30, 30, 30))

    if clock is None:
        clock = pygame.time.Clock()

    options = ["Fight", "Pokémon", "Bag", "Run"]
    option_colors = [BATTLERED, BATTLEGREEN, BATTLEYELLOW, BATTLEBLUE]
    selected = 0

    bg_img = None
    try:
        bg_img = pygame.image.load("graphics/backgrounds/forest.png").convert()
    except Exception:
        bg_img = None

    sprite_surface = None
    try:
        if pokemon.get("sprite"):
            sprite_data = requests.get(pokemon["sprite"], timeout=5)
            sprite_surface = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
    except Exception:
        sprite_surface = None

    player_sprite_surface = None
    try:
        player_sprite_url = None
        if player_pokemon:
            if isinstance(player_pokemon, dict):
                player_sprite_url = player_pokemon.get("sprite")
            else:
                player_sprite_url = getattr(player_pokemon, "sprite", None)
        if player_sprite_url:
            sprite_data = requests.get(player_sprite_url, timeout=5)
            player_sprite_surface = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
    except Exception:
        player_sprite_surface = None

    if initial_message:
        state = "message"
    else:
        if show_intro:
            state = "entrance"
        else:
            state = "options"
    start_time = pygame.time.get_ticks()
    entrance_duration = 800

    fps = 60
    running = True
    while running:
        sw, sh = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "run"

            if event.type == pygame.KEYDOWN:
                if state == "message":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                        # If caller only wanted to show a message (e.g. faint/caught),
                        # return immediately after one keypress instead of entering options.
                        if return_after_message:
                            return None
                        state = "options"
                elif state == "options":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                        return options[selected].lower()
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        if selected % 2 == 0:
                            selected = selected + 1
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        if selected % 2 == 1:
                            selected = selected - 1
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        if selected < 2:
                            selected = selected + 2
                    if event.key in (pygame.K_UP, pygame.K_w):
                        if selected >= 2:
                            selected = selected - 2
                    if event.key == pygame.K_ESCAPE:
                        return "run"

        if bg_img:
            try:
                b = pygame.transform.scale(bg_img, (sw, sh))
                screen.blit(b, (0, 0))
            except Exception:
                screen.fill(BG)
        else:
            screen.fill(BG)

        spr_w = 269
        spr_h = 269
        target_midright = (sw - 200, sh // 2 - 200)
        if sprite_surface:
            try:
                spr = pygame.transform.scale(sprite_surface, (spr_w, spr_h))
            except Exception:
                spr = None
        else:
            spr = None

        p_spr = None
        if player_sprite_surface:
            try:
                p_spr = pygame.transform.scale(player_sprite_surface, (308, 308))
                p_spr = pygame.transform.flip(p_spr, True, False)
            except Exception:
                p_spr = None
        else:
            p_spr = None

        sprite_x = sw + spr_w
        sprite_y = target_midright[1]

        now = pygame.time.get_ticks()
        elapsed = now - start_time

        if state == "entrance":
            progress = min(1.0, elapsed / float(entrance_duration))
            ease = 1 - (1 - progress) * (1 - progress)
            start_x = sw + spr_w
            target_x = target_midright[0] - spr_w // 2
            sprite_x = int(start_x + (target_x - start_x) * ease)
            sprite_y = target_midright[1]
            if progress >= 1.0:
                state = "message"
                start_time = pygame.time.get_ticks()

        elif state in ("message", "options"):
            sprite_x = target_midright[0] - spr_w // 2
            sprite_y = target_midright[1]

        if spr:
            try:
                spr_rect = spr.get_rect()
                spr_rect.topleft = (sprite_x, sprite_y)
                screen.blit(spr, spr_rect)
            except Exception:
                pass
        else:
            ph_rect = pygame.Rect(sprite_x, sprite_y, spr_w, spr_h)
            pygame.draw.rect(screen, (100, 100, 100), ph_rect)

        p_x = 500
        p_y = sh // 2 + 40
        if p_spr:
            try:
                p_rect = p_spr.get_rect()
                p_rect.topleft = (p_x, p_y)
                screen.blit(p_spr, p_rect)
            except Exception:
                pass
        else:
            p_ph_rect = pygame.Rect(p_x, p_y, 220, 220)
            pygame.draw.rect(screen, (80, 80, 80), p_ph_rect)

        def _get_hp(obj):
            try:
                if obj is None:
                    return 0.0, 0.0
                if isinstance(obj, dict):
                    curr = obj.get('hp', obj.get('current_hp', 0)) or 0
                    max_hp = obj.get('max_hp', None)
                    if max_hp is None:
                        max_hp = curr
                    return float(curr), float(max_hp)
                else:
                    curr = getattr(obj, 'current_hp', None)
                    if curr is None:
                        curr = getattr(obj, 'hp', 0)
                    max_hp = getattr(obj, 'max_hp', None)
                    if max_hp is None:
                        max_hp = getattr(obj, 'hp', curr)
                    return float(curr), float(max_hp)
            except Exception:
                return 0.0, 0.0

        def _get_name(obj):
            try:
                if obj is None:
                    return "Unknown"
                if isinstance(obj, dict):
                    return obj.get('name', 'Unknown')
                return getattr(obj, 'name', 'Unknown')
            except Exception:
                return "Unknown"

        try:
            enemy_curr, enemy_max = _get_hp(pokemon)
            if enemy_max <= 0:
                enemy_pct = 0.0
            else:
                enemy_pct = max(0.0, min(1.0, enemy_curr / enemy_max))
            bar_w = 216
            bar_h = 14
            bar_x = int(sprite_x + spr_w // 2 - bar_w // 2)
            bar_y = int(sprite_y - 50)
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)
            fill_w = int(bar_w * enemy_pct)
            if enemy_pct > 0.5:
                hp_color = (46, 129, 31)
            elif enemy_pct > 0.25:
                hp_color = (255, 222, 0)
            else:
                hp_color = (206, 0, 0)
            if fill_w > 0:
                pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, 2, border_radius=6)
            try:
                hp_txt = small_font.render(f"{int(enemy_curr)}/{int(enemy_max)}", True, BLACK)
                try:
                    ename = _get_name(pokemon)
                    name_txt = small_font.render(str(ename), True, BLACK)
                    spacing = 6
                    hp_w = hp_txt.get_width()
                    name_w = name_txt.get_width()
                    combined_w = name_w + spacing + hp_w
                    base_x = bar_x + bar_w // 2 - combined_w // 2
                    text_y = bar_y - hp_txt.get_height() - 2
                    screen.blit(name_txt, (base_x, text_y))
                    screen.blit(hp_txt, (base_x + name_w + spacing, text_y))
                except Exception:
                    screen.blit(hp_txt, (bar_x + bar_w // 2 - hp_txt.get_width() // 2, bar_y - hp_txt.get_height() - 2))
            except Exception:
                pass

            player_curr, player_max = _get_hp(player_pokemon)
            if player_max <= 0:
                player_pct = 0.0
            else:
                player_pct = max(0.0, min(1.0, player_curr / player_max))
            p_bar_w = bar_w
            p_bar_h = 14
            p_bar_x = int(p_x + (308 - p_bar_w) / 2)
            p_bar_y = int(p_y - p_bar_h + 38)
            p_bg = pygame.Rect(p_bar_x, p_bar_y, p_bar_w, p_bar_h)
            pygame.draw.rect(screen, (40, 40, 40), p_bg, border_radius=6)
            p_fill = int(p_bar_w * player_pct)
            if player_pct > 0.5:
                p_color = (46, 129, 31)
            elif player_pct > 0.25:
                p_color = (255, 222, 0)
            else:
                p_color = (206, 0, 0)
            if p_fill > 0:
                pygame.draw.rect(screen, p_color, (p_bar_x, p_bar_y, p_fill, p_bar_h), border_radius=6)
            pygame.draw.rect(screen, (0, 0, 0), p_bg, 2, border_radius=6)
            try:
                p_txt = small_font.render(f"{int(player_curr)}/{int(player_max)}", True, BLACK)
                try:
                    pname = _get_name(player_pokemon)
                    pname_txt = small_font.render(str(pname), True, BLACK)
                    spacing = 6
                    hp_w = p_txt.get_width()
                    name_w = pname_txt.get_width()
                    combined_w = name_w + spacing + hp_w
                    base_x = p_bar_x + p_bar_w // 2 - combined_w // 2
                    text_y = p_bar_y - p_txt.get_height() - 2
                    screen.blit(pname_txt, (base_x, text_y))
                    screen.blit(p_txt, (base_x + name_w + spacing, text_y))

                    if player_pokemon and hasattr(pokedex_obj, 'get_team'):
                        team_count = len(pokedex_obj.get_team())

                except Exception:
                    screen.blit(p_txt, (p_bar_x + p_bar_w // 2 - p_txt.get_width() // 2, p_bar_y - p_txt.get_height() - 2))
            except Exception:
                pass
        except Exception:
            pass

        padding = 18
        box_h = 160
        full_box_rect = pygame.Rect(20, sh - box_h - 20, sw - 40, box_h)
        pygame.draw.rect(screen, WHITE, full_box_rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, full_box_rect, 3, border_radius=8)

        if state == "message":
            if initial_message:
                msg = initial_message
            else:
                msg = f"A wild {pokemon['name']} appeared!"
            text = menu_font.render(msg, True, BLACK)
            screen.blit(text, (full_box_rect.x + padding, full_box_rect.y + padding))

            hint = small_font.render("(Press ⎵ / Z to continue)", True, BLACK)
            screen.blit(hint, (full_box_rect.right - hint.get_width() - padding, full_box_rect.y + full_box_rect.height - hint.get_height() - padding))

        elif state == "options":
            area_w = int(full_box_rect.width * 0.5)
            area_h = full_box_rect.height - padding * 2
            area_x = full_box_rect.right - area_w - padding
            area_y = full_box_rect.y + padding

            # Render team as Pokéballs above the battle menu options
            if pokedex_obj and hasattr(pokedex_obj, 'get_team') and pokeball_img:
                team = pokedex_obj.get_team()
                team_count = len(team)

                # Position for team Pokéballs (above the options box)
                team_x = area_x
                team_y = area_y - 30  # Above the options box

                # Render Pokéballs for team
                for i in range(6):  # Max team size
                    ball_x = team_x + i * 30
                    if i < team_count:
                        screen.blit(pokeball_img, (ball_x, team_y))
                    else:
                        # Draw empty slot
                        empty_y = team_y + 5
                        pygame.draw.circle(screen, (180, 180, 180), (ball_x + 16, empty_y + 16), 16, 2)

            opts_bg = pygame.Rect(area_x, area_y, area_w, area_h)
            pygame.draw.rect(screen, WHITE, opts_bg, border_radius=6)
            pygame.draw.rect(screen, BLACK, opts_bg, 2, border_radius=6)
            inner = max(8, padding // 2)
            opt_w = (opts_bg.width - inner * 3) // 2
            opt_h = (opts_bg.height - inner * 3) // 2

            for i, opt in enumerate(options):
                row = i // 2
                col = i % 2
                x = opts_bg.x + inner + col * (opt_w + inner)
                y = opts_bg.y + inner + row * (opt_h + inner)
                rect = pygame.Rect(x, y, opt_w, opt_h)
                pygame.draw.rect(screen, option_colors[i], rect, border_radius=6)
                if i == selected:
                    pygame.draw.rect(screen, BLACK, rect, 3, border_radius=6)
                text_color = WHITE

                text = menu_font.render(opt, True, text_color)
                screen.blit(
                    text,
                    (
                        rect.x + rect.width // 2 - text.get_width() // 2,
                        rect.y + rect.height // 2 - text.get_height() // 2,
                    ),
                )
            if player_pokemon:
                try:
                    pname = player_pokemon.name if not isinstance(player_pokemon, dict) else player_pokemon.get('name')
                except Exception:
                    pname = None
            else:
                pname = None
            if pname:
                msg = f"Go {pname}!"
            else:
                msg = "go (Placeholder Pokémon)"
            text = menu_font.render(msg, True, BLACK)
            screen.blit(text, (full_box_rect.x + padding, full_box_rect.y + padding))
        pygame.display.flip()
        clock.tick(fps)
    return "run"