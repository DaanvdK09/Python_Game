import pygame
from io import BytesIO
import requests

_SPRITE_CACHE = {}


def _load_pokemon_sprite(sprite_url, size=64):
    """Load and cache Pokémon sprite."""
    if not sprite_url:
        return None
    
    cache_key = (sprite_url, size)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]
    
    try:
        response = requests.get(sprite_url, timeout=3)
        if response.ok:
            sprite = pygame.image.load(BytesIO(response.content)).convert_alpha()
            sprite = pygame.transform.scale(sprite, (size, size))
            _SPRITE_CACHE[cache_key] = sprite
            return sprite
    except Exception:
        pass
    
    return None


def pokedex_menu(screen, pokedex, menu_font, small_font, colors, clock=None, is_battle_context=False):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    RED = colors.get("RED", (206, 0, 0))
    GREEN = colors.get("GREEN", (46, 129, 31))
    BLUE = colors.get("BLUE", (59, 76, 202))
    YELLOW = colors.get("YELLOW", (255, 222, 0))
    BG = colors.get("BG", (30, 30, 30))
    
    if clock is None:
        clock = pygame.time.Clock()
    
    # Get Pokémon list to display
    if is_battle_context:
        pokemon_list = pokedex.get_team()
        title = "Select Pokémon for Battle"
    else:
        pokemon_list = pokedex.captured_pokemon
        title = "Pokédex"
    
    if not pokemon_list:
        return None
    
    selected_index = 0
    fps = 60
    running = True
    
    while running:
        sw, sh = screen.get_size()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    return None
                
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected_index = (selected_index - 1) % len(pokemon_list)
                
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected_index = (selected_index + 1) % len(pokemon_list)
                
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                    return pokemon_list[selected_index]
        
        screen.fill(BG)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        panel_w = int(sw * 0.85)
        panel_h = int(sh * 0.85)
        panel_x = (sw - panel_w) // 2
        panel_y = (sh - panel_h) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (45, 45, 60), panel_rect, border_radius=12)
        pygame.draw.rect(screen, BLUE, panel_rect, 4, border_radius=12)
        
        title_bg = pygame.Rect(panel_x + 15, panel_y + 15, panel_w - 30, 50)
        pygame.draw.rect(screen, BLUE, title_bg, border_radius=8)
        pygame.draw.rect(screen, WHITE, title_bg, 2, border_radius=8)
        title_text = menu_font.render(title, True, WHITE)
        screen.blit(title_text, (panel_x + 25, panel_y + 22))
        
        count_text = small_font.render(f"{len(pokemon_list)} Pokémon", True, YELLOW)
        screen.blit(count_text, (panel_x + panel_w - count_text.get_width() - 25, panel_y + 28))
        
        list_start_y = panel_y + 75
        list_item_h = 80
        visible_items = (panel_h - 130) // list_item_h
        scroll_start = max(0, selected_index - visible_items // 2)
        scroll_start = min(scroll_start, len(pokemon_list) - visible_items)
        
        for i, pokemon in enumerate(pokemon_list[scroll_start:scroll_start + visible_items]):
            actual_index = scroll_start + i
            item_y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(panel_x + 15, item_y, panel_w - 30, list_item_h - 10)
            
            if actual_index == selected_index:
                glow_rect = item_rect.inflate(8, 8)
                pygame.draw.rect(screen, BLUE, glow_rect, border_radius=8)
                pygame.draw.rect(screen, (100, 200, 255), item_rect, border_radius=8, width=3)
                item_color = (60, 60, 80)
            else:
                pygame.draw.rect(screen, (50, 50, 70), item_rect, border_radius=8)
                item_color = (50, 50, 70)
            
            pygame.draw.rect(screen, item_color, item_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 100, 120), item_rect, 1, border_radius=8)
            
            # Load and draw sprite
            sprite = _load_pokemon_sprite(pokemon.sprite, size=70)
            if sprite:
                sprite_x = item_rect.x + 10
                sprite_y = item_rect.y + (list_item_h - 10 - 70) // 2
                screen.blit(sprite, (sprite_x, sprite_y))
                info_start_x = sprite_x + 80
            else:
                # Placeholder if no sprite
                placeholder = pygame.Rect(item_rect.x + 10, item_rect.y + 5, 70, 70)
                pygame.draw.rect(screen, (80, 80, 100), placeholder, border_radius=4)
                info_start_x = placeholder.right + 10
            
            # Draw Pokémon info
            name_text = menu_font.render(pokemon.name, True, YELLOW)
            screen.blit(name_text, (info_start_x, item_rect.y + 5))
            
            # Level and attack inline
            level_text = small_font.render(f"Lvl {pokemon.level}", True, WHITE)
            atk_text = small_font.render(f"ATK {pokemon.attack}", True, WHITE)
            screen.blit(level_text, (info_start_x, item_rect.y + 30))
            screen.blit(atk_text, (info_start_x + 100, item_rect.y + 30))
            
            # HP bar
            hp_bar_w = 200
            hp_bar_h = 10
            hp_bar_x = info_start_x
            hp_bar_y = item_rect.y + 50
            
            pygame.draw.rect(screen, (30, 30, 50), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), border_radius=3)
            pygame.draw.rect(screen, (80, 80, 100), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), 1, border_radius=3)
            
            if pokemon.max_hp > 0:
                hp_percent = pokemon.current_hp / pokemon.max_hp
                hp_fill = int(hp_bar_w * hp_percent)
                if hp_percent > 0.5:
                    hp_color = GREEN
                elif hp_percent > 0.25:
                    hp_color = YELLOW
                else:
                    hp_color = RED
                pygame.draw.rect(screen, hp_color, (hp_bar_x, hp_bar_y, hp_fill, hp_bar_h), border_radius=3)
            
            hp_label = small_font.render(f"HP: {pokemon.current_hp}/{pokemon.max_hp}", True, WHITE)
            screen.blit(hp_label, (hp_bar_x + hp_bar_w + 10, hp_bar_y + 1))
        
        # Draw footer
        footer_y = panel_y + panel_h - 40
        pygame.draw.line(screen, BLUE, (panel_x + 15, footer_y), (panel_x + panel_w - 15, footer_y), 2)
        
        instruct_text = small_font.render("⬆/⬇ Navigate  │  ENTER Confirm  │  ESC Cancel", True, WHITE)
        screen.blit(instruct_text, (panel_x + 25, footer_y + 8))
        
        pygame.display.flip()
        clock.tick(fps)
    
    return None


def quick_pokemon_select(screen, pokedex, menu_font, small_font, colors, clock=None):
    return pokedex_menu(
        screen, pokedex, menu_font, small_font, colors, clock, 
        is_battle_context=True
    )
