import pygame

def handle_keydown(event: pygame.event.Event, player):
    if event.key == pygame.K_w:
        player.last_dir = 3
        player.show_idle = False
        player.dir_y = -1
        player.dir_x = 0
    if event.key == pygame.K_s:
        player.last_dir = 1
        player.show_idle = False
        player.dir_y = 1
        player.dir_x = 0
    if event.key == pygame.K_d:
        player.last_dir = 4
        player.show_idle = False
        player.dir_x = 1
        player.dir_y = 0
    if event.key == pygame.K_a:
        player.last_dir = 2
        player.show_idle = False
        player.dir_x = -1
        player.dir_y = 0
    if event.key == pygame.K_ESCAPE and player.alive:
        return "pause"
    if event.key == pygame.K_h and player.alive:
        player.hit_box = not player.hit_box
    return None

def handle_keyup(event: pygame.event.Event, player):
    if event.key in (pygame.K_w, pygame.K_s):
        player.dir_y = 0
        player.show_idle = True
    if event.key in (pygame.K_a, pygame.K_d):
        player.dir_x = 0
        player.show_idle = True