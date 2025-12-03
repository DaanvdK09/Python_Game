import pygame
from io import BytesIO
import requests


def pokedex_menu(screen, pokedex, menu_font, small_font, colors, clock=None, is_battle_context=False):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    RED = colors.get("RED", (206, 0, 0))
    GREEN = colors.get("GREEN", (46, 129, 31))
    BLUE = colors.get("BLUE", (59, 76, 202))
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
        
        # Draw background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        # Draw main panel
        panel_w = int(sw * 0.7)
        panel_h = int(sh * 0.8)
        panel_x = (sw - panel_w) // 2
        panel_y = (sh - panel_h) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, WHITE, panel_rect)
        pygame.draw.rect(screen, BLACK, panel_rect, 3)
        
        # Draw title
        title_text = menu_font.render(title, True, BLACK)
        screen.blit(title_text, (panel_x + 20, panel_y + 15))
        
        # Draw Pokémon list
        list_start_y = panel_y + 60
        list_item_h = 60
        visible_items = (panel_h - 80) // list_item_h
        
        # Calculate scroll position
        scroll_start = max(0, selected_index - visible_items // 2)
        scroll_start = min(scroll_start, len(pokemon_list) - visible_items)
        
        for i, pokemon in enumerate(pokemon_list[scroll_start:scroll_start + visible_items]):
            actual_index = scroll_start + i
            item_y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(panel_x + 10, item_y, panel_w - 20, list_item_h - 5)
            
            # Highlight selected
            if actual_index == selected_index:
                pygame.draw.rect(screen, BLUE, item_rect, border_radius=4)
                pygame.draw.rect(screen, BLACK, item_rect, 2, border_radius=4)
            else:
                pygame.draw.rect(screen, (200, 200, 200), item_rect, border_radius=4)
                pygame.draw.rect(screen, BLACK, item_rect, 1, border_radius=4)
            
            # Draw Pokémon info
            name_text = menu_font.render(pokemon.name, True, BLACK)
            screen.blit(name_text, (item_rect.x + 15, item_rect.y + 5))
            
            # Draw stats
            hp_bar_w = 100
            hp_bar_h = 8
            hp_bar_x = item_rect.x + 15
            hp_bar_y = item_rect.y + 30
            
            # HP bar background
            pygame.draw.rect(screen, (100, 100, 100), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h))
            
            # HP bar fill
            if pokemon.max_hp > 0:
                hp_percent = pokemon.current_hp / pokemon.max_hp
                hp_fill = int(hp_bar_w * hp_percent)
                hp_color = GREEN if hp_percent > 0.3 else RED
                pygame.draw.rect(screen, hp_color, (hp_bar_x, hp_bar_y, hp_fill, hp_bar_h))
            
            # HP text
            hp_text = small_font.render(f"HP: {pokemon.current_hp}/{pokemon.max_hp}", True, BLACK)
            screen.blit(hp_text, (hp_bar_x + hp_bar_w + 10, hp_bar_y - 2))
            
            # Level and Attack
            level_text = small_font.render(f"Lvl {pokemon.level}", True, BLACK)
            atk_text = small_font.render(f"ATK {pokemon.attack}", True, BLACK)
            screen.blit(level_text, (item_rect.right - 150, item_rect.y + 5))
            screen.blit(atk_text, (item_rect.right - 150, item_rect.y + 25))
        
        # Draw instructions
        instruct_y = panel_y + panel_h - 35
        instruct_text = small_font.render("⬆/⬇ Select  |  ENTER Confirm  |  ESC Cancel", True, BLACK)
        screen.blit(instruct_text, (panel_x + 20, instruct_y))
        
        pygame.display.flip()
        clock.tick(fps)
    
    return None


def quick_pokemon_select(screen, pokedex, menu_font, small_font, colors, clock=None):
    return pokedex_menu(
        screen, pokedex, menu_font, small_font, colors, clock, 
        is_battle_context=True
    )
