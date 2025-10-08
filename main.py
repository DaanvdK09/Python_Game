import pygame
from characters.character import Character

pygame.init()

#Int
running = True
game_state = "game"

#Screen
Screen_Width=1285
Screen_Height=700

screen=pygame.display.set_mode((Screen_Width,Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

player = Character()
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        result = player.handle_event(event)
        if result == "pause" and game_state == "game" and player.alive:
            game_state = "pause"
        elif result == "pause" and game_state == "pause":
            game_state = "game"

    if game_state == "game":
        keys = pygame.key.get_pressed()
        player.update(keys)

    screen.fill((30,30,30))
    player.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()