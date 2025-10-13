import pygame
from Characters.character import Character
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD

pygame.init()

# Int
running = True
game_state = "menu"

# Screen
Screen_Width = 1285
Screen_Height = 800

screen = pygame.display.set_mode((Screen_Width, Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

# Fonts
menu_font = pygame.font.Font(None, 48)

# Map
game_map = TileMap(tmx_path="World/maps/Level_0.tmx", tile_size=64)

# Character
player = Character()

# set player start
if getattr(game_map, "player_start", None):
    px, py = game_map.player_start
    tile = getattr(game_map, "tile_size", 64)
    player.rect.topleft = (px + (tile - player.rect.width) // 2,
                           py + (tile - player.rect.height) // 2)

clock = pygame.time.Clock()

def _wait_for_mouse_release(clock):
    """Block until all mouse buttons are released and clear mouse events."""
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()
        clock.tick(60)
    pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

def show_main_menu():
    while True:
        w, h = screen.get_size()
        menu_result = main_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
        if menu_result == "game":
            return "game"
        if menu_result == "quit":
            return "quit"
        if menu_result == "options":
            opt = options_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if opt == "quit":
                return "quit"
            # loop to main menu

menu_start = show_main_menu()
if menu_start == "game":
    game_state = "game"
elif menu_start == "quit":
    running = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        result = player.handle_event(event)
        if result == "pause" and player.alive:
            # pause menu
            w, h = screen.get_size()
            pause_result = pause_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if pause_result == "game":
                game_state = "game"

            elif pause_result == "menu":
                # go back to main menu
                _wait_for_mouse_release(clock)
                menu_res = show_main_menu()
                if menu_res == "game":
                    game_state = "game"
                elif menu_res == "quit":
                    running = False

            elif pause_result == "pause options":
                # options
                opt = options_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                if opt == "quit":
                    running = False
                elif opt == "back":
                    _wait_for_mouse_release(clock)
                    pause_result = pause_menu(screen, w, h, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                    if pause_result == "game":
                        game_state = "game"
                    elif pause_result == "menu":
                        _wait_for_mouse_release(clock)
                        menu_res = show_main_menu()
                        if menu_res == "game":
                            game_state = "game"
                        elif menu_res == "quit":
                            running = False

    if game_state == "game":
        keys = pygame.key.get_pressed()
        player.update(keys, game_map)

        # Camera
        view_w, view_h = screen.get_size()
        try:
            map_w = game_map.width
            map_h = game_map.height
        except Exception:
            cols = getattr(game_map, "cols", None) or getattr(game_map, "columns", None) or getattr(game_map, "num_cols", None)
            rows = getattr(game_map, "rows", None) or getattr(game_map, "rows_count", None) or getattr(game_map, "num_rows", None)
            tile = getattr(game_map, "tile_size", None) or getattr(game_map, "tilewidth", None) or getattr(game_map, "tile_size_px", None)
            if cols and rows and tile:
                map_w = cols * tile
                map_h = rows * tile
            else:
                map_w, map_h = view_w, view_h

        # center camera on player
        cam_left = player.rect.centerx - view_w // 2
        cam_top = player.rect.centery - view_h // 2
        offset_x = -cam_left
        offset_y = -cam_top
    else:
        offset_x = 0
        offset_y = 0

    screen.fill(BG)
    try:
        game_map.draw(screen, offset_x=offset_x, offset_y=offset_y)
    except TypeError:
        game_map.draw(screen)

    try:
        player.draw(screen, offset_x=offset_x, offset_y=offset_y)
    except TypeError:
        player.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()