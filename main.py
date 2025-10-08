import pygame
from Characters.character import Character
from UI.pause_menu import pause_menu
from UI.main_menu import main_menu
from World.map import TileMap
from constants import BG, BLACK, GOLD, SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()

#Int
running = True
game_state = "menu"

#Screen
Screen_Width = 1285
Screen_Height = 800

screen = pygame.display.set_mode((Screen_Width, Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

#Fonts
menu_font = pygame.font.Font(None, 48)

game_map = TileMap(tile_size=64)

player = Character()
clock = pygame.time.Clock()

menu_result = main_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
if menu_result == "game":
    game_state = "game"
elif menu_result == "quit":
    running = False
else:
    game_state = menu_result

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        result = player.handle_event(event)
        if result == "pause" and player.alive:
            #Pause Menu
            pause_result = pause_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
            if pause_result == "game":
                game_state = "game"
            elif pause_result == "pause options":
                game_state = "pause options"
            elif pause_result == "menu":
                #Main Menu
                menu_result = main_menu(screen, Screen_Width, Screen_Height, menu_font, {"BLACK": BLACK, "GOLD": GOLD, "BG": BG}, clock)
                if menu_result == "game":
                    game_state = "game"
                elif menu_result == "quit":
                    running = False
                else:
                    game_state = menu_result
            elif pause_result == "quit":
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