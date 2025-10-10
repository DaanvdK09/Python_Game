import pygame
from Characters.character import Character
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from UI.options import options_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD, SCREEN_WIDTH, SCREEN_HEIGHT

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

game_map = TileMap(tile_size=64)

player = Character()
clock = pygame.time.Clock()

def _wait_for_mouse_release(clock):
    """Block until all mouse buttons are released and clear mouse events."""
    while any(pygame.mouse.get_pressed()):
        pygame.event.pump()
        clock.tick(60)
    pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

def show_main_menu():
    while True:
        menu_result = main_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
        if menu_result == "game":
            return "game"
        if menu_result == "quit":
            return "quit"
        if menu_result == "options":
            opt = options_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
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
            pause_result = pause_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if pause_result == "game":
                game_state = "game"

            elif pause_result == "pause options":
                # options
                opt = options_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                if opt == "quit":
                    running = False
                elif opt == "back":
                    _wait_for_mouse_release(clock)
                    pause_result = pause_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                    if pause_result == "game":
                        game_state = "game"
                    elif pause_result == "menu":
                        menu_res = show_main_menu()
                        if menu_res == "game":
                            game_state = "game"
                        elif menu_res == "quit":
                            running = False

    if game_state == "game":
        keys = pygame.key.get_pressed()
        player.update(keys, game_map)

    screen.fill(BG)
    game_map.draw(screen)
    player.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()