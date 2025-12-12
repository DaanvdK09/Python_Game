import pygame
from io import BytesIO
import requests

_SPRITE_CACHE = {}


def _load_pokemon_sprite(sprite_url, size=64):
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


def pokedex_menu(screen, pokedex, menu_font, small_font, colors, clock=None, is_battle_context=False, current_player=None, bag=None, pokedex_obj=None):
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
    notice_text = None
    notice_timer = 0.0
    NOTICE_DURATION = 1.2
    
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
                    sel = pokemon_list[selected_index]
                    try:
                        current_name = None
                        if current_player is not None:
                            if isinstance(current_player, dict):
                                current_name = current_player.get('name')
                            else:
                                current_name = getattr(current_player, 'name', None)
                        sel_name = sel.name if not isinstance(sel, dict) else sel.get('name')
                    except Exception:
                        current_name = None
                        sel_name = None

                    if is_battle_context and current_name and sel_name and sel_name == current_name:
                        notice_text = f"{sel_name} is already in battle"
                        notice_timer = NOTICE_DURATION
                    else:
                        return pokemon_list[selected_index]

                if not is_battle_context:
                    if event.key == pygame.K_t:
                        # Toggle team
                        sel = pokemon_list[selected_index]
                        try:
                            sel_name = sel.name if not isinstance(sel, dict) else sel.get('name')
                        except Exception:
                            sel_name = None
                        team = []
                        if pokedex_obj is not None:
                            try:
                                team = pokedex_obj.get_team()
                            except Exception:
                                team = []

                        in_team = False
                        if sel_name is not None and team:
                            for tp in team:
                                try:
                                    tname = getattr(tp, 'name', None) if not isinstance(tp, dict) else tp.get('name')
                                except Exception:
                                    tname = None
                                if tname and sel_name and tname == sel_name:
                                    in_team = True
                                    team_member = tp
                                    break
                        if in_team:
                            # remove from team
                            try:
                                if pokedex_obj is not None:
                                    pokedex_obj.remove_pokemon(team_member)
                                    # only remove from team
                            except Exception:
                                pass
                            try:
                                if pokedex_obj is not None:
                                    new_team = [t for t in pokedex_obj.get_team() if getattr(t, 'name', None) != sel_name]
                                    pokedex_obj.set_active_team(new_team)
                                notice_text = f"Removed {sel_name} from team"
                            except Exception:
                                notice_text = "Failed to remove from team"
                            notice_timer = NOTICE_DURATION
                        else:
                            # add to team if space
                            try:
                                if pokedex_obj is not None:
                                    if len(pokedex_obj.get_team()) >= 6:
                                        notice_text = "Team is full (6)"
                                    else:
                                        # find the captured Pokemon object to add
                                        candidate = None
                                        for cp in pokedex_obj.captured_pokemon:
                                            if getattr(cp, 'name', None) == sel_name:
                                                candidate = cp
                                                break
                                        if candidate is None and not isinstance(sel, dict):
                                            candidate = sel
                                        if candidate is not None:
                                            team = pokedex_obj.get_team()[:]
                                            team.append(candidate)
                                            pokedex_obj.set_active_team(team)
                                            notice_text = f"Added {sel_name} to team"
                                        else:
                                            notice_text = "Could not add to team"
                            except Exception:
                                notice_text = "Failed to add to team"
                            notice_timer = NOTICE_DURATION

                    if event.key == pygame.K_p:
                        # Use a potion on the selected pokemon
                        sel = pokemon_list[selected_index]
                        try:
                            sel_name = sel.name if not isinstance(sel, dict) else sel.get('name')
                        except Exception:
                            sel_name = None
                        count = 0
                        if bag is not None:
                            count = bag.get('Potion', 0)
                        if count <= 0:
                            notice_text = "No potions available"
                            notice_timer = NOTICE_DURATION
                        else:
                            target = None
                            if not isinstance(sel, dict):
                                target = sel
                            else:
                                if pokedex_obj is not None:
                                    for cp in pokedex_obj.captured_pokemon:
                                        if getattr(cp, 'name', None) == sel_name:
                                            target = cp
                                            break
                            if target is not None and hasattr(target, 'current_hp'):
                                heal = 20
                                try:
                                    target.current_hp = min(getattr(target, 'current_hp', 0) + heal, getattr(target, 'max_hp', getattr(target, 'hp', 0)))
                                    if bag is not None:
                                        bag['Potion'] = max(0, bag.get('Potion', 0) - 1)
                                    try:
                                        if pokedex_obj is not None:
                                            pokedex_obj.save()
                                    except Exception:
                                        pass
                                    notice_text = f"Healed {sel_name} (+{heal})"
                                except Exception:
                                    notice_text = "Failed to use potion"
                            else:
                                notice_text = "No valid target to heal"
                            notice_timer = NOTICE_DURATION
        
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
        scroll_start = min(scroll_start, max(0, len(pokemon_list) - visible_items))
        
        for i, pokemon in enumerate(pokemon_list[scroll_start:scroll_start + visible_items]):
            actual_index = scroll_start + i
            item_y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(panel_x + 15, item_y, panel_w - 30, list_item_h - 10)
            
            is_active = False
            in_team = False
            try:
                pname = None
                if isinstance(pokemon, dict):
                    pname = pokemon.get('name')
                else:
                    pname = getattr(pokemon, 'name', None)
                cur_name = None
                if current_player is not None:
                    if isinstance(current_player, dict):
                        cur_name = current_player.get('name')
                    else:
                        cur_name = getattr(current_player, 'name', None)
                if cur_name and pname and cur_name == pname:
                    is_active = True
                # team membership
                try:
                    if pokedex_obj is not None and pname:
                        for tp in pokedex_obj.get_team():
                            try:
                                tname = getattr(tp, 'name', None) if not isinstance(tp, dict) else tp.get('name')
                            except Exception:
                                tname = None
                            if tname and pname and tname == pname:
                                in_team = True
                                break
                except Exception:
                    in_team = False
            except Exception:
                is_active = False

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
            
            try:
                sprite_url = pokemon.sprite if not isinstance(pokemon, dict) else pokemon.get('sprite')
            except Exception:
                sprite_url = None
            sprite = _load_pokemon_sprite(sprite_url, size=70)
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
            try:
                display_name = pokemon.name if not isinstance(pokemon, dict) else pokemon.get('name')
            except Exception:
                display_name = "Unknown"
            if is_active:
                if is_battle_context:
                    name_text = menu_font.render(f"{display_name}  (In battle)", True, (160, 160, 160))
                else:
                    name_text = menu_font.render(f"{display_name}  (Active)", True, (160, 160, 160))
            else:
                if in_team:
                    name_text = menu_font.render(f"{display_name}  (Team)", True, YELLOW)
                else:
                    name_text = menu_font.render(display_name, True, YELLOW)
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
        
        if not is_battle_context:
            instruct_text = small_font.render("⬆/⬇ Navigate  │  ENTER Confirm  │  T Toggle Team  │  P Use Potion  │  ESC Cancel", True, WHITE)
        else:
            instruct_text = small_font.render("⬆/⬇ Navigate  │  ENTER Confirm  │  ESC Cancel", True, WHITE)
        screen.blit(instruct_text, (panel_x + 25, footer_y + 8))
        if notice_timer > 0 and notice_text:
            try:
                nt = small_font.render(notice_text, True, (255, 220, 100))
                screen.blit(nt, (panel_x + panel_w - nt.get_width() - 25, footer_y + 8))
            except Exception:
                pass
            # decrement timer
            notice_timer = max(0.0, notice_timer - (1.0 / float(fps)))
        
        pygame.display.flip()
        clock.tick(fps)
    
    return None


def quick_pokemon_select(screen, pokedex, menu_font, small_font, colors, clock=None, current_player=None):
    return pokedex_menu(
        screen, pokedex, menu_font, small_font, colors, clock, 
        is_battle_context=True,
        current_player=current_player,
    )
