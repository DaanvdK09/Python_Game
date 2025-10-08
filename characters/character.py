import pygame
from .movement import handle_keydown, handle_keyup

#Int
RED = (200,50,50)

class Character:
    def __init__(self, x=100, y=100, w=48, h=48, color=RED, speed=4):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.speed = speed

        # movement / state
        self.dir_x = 0
        self.dir_y = 0
        self.last_dir = 1
        self.show_idle = True
        self.hit_box = False
        self.alive = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            return handle_keydown(event, self)
        if event.type == pygame.KEYUP:
            handle_keyup(event, self)
        return None

    def update(self, keys=None):
        if keys is not None:
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.dir_y = -1
                self.show_idle = False
                self.last_dir = 3
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.dir_y = 1
                self.show_idle = False
                self.last_dir = 1
            else:
                if self.dir_y != 0:
                    self.dir_y = 0
                    self.show_idle = True

            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.dir_x = 1
                self.show_idle = False
                self.last_dir = 4
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.dir_x = -1
                self.show_idle = False
                self.last_dir = 2
            else:
                if self.dir_x != 0:
                    self.dir_x = 0
                    self.show_idle = True

        self.rect.x += int(self.dir_x * self.speed)
        self.rect.y += int(self.dir_y * self.speed)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        if self.hit_box:
            pygame.draw.rect(surface, (0,255,0), self.rect, 2)