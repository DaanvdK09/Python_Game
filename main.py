import pygame

pygame.init()

#Int
running = True

#Screen
Screen_Width=1285
Screen_Height=800

screen=pygame.display.set_mode((Screen_Width,Screen_Height))
pygame.display.set_caption("Game")
pygame.display.toggle_fullscreen()

while running:



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()