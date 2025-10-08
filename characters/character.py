import pygame
from .movement import handle_keydown, handle_keyup

#Int
RED = (200,50,50)
player_x = 100
player_y = 100
player_w = 48
player_h = 48
player_speed = 4

#movement/state
dir_x = 0
dir_y = 0
last_dir = 1
show_idle = True
hit_box = False
alive = True

#player rect
player_rect = pygame.Rect(player_x, player_y, player_w, player_h)

class Character:
    rect = player_rect
    color = RED
    speed = player_speed

    dir_x = dir_x
    dir_y = dir_y
    last_dir = last_dir
    show_idle = show_idle
    hit_box = hit_box
    alive = alive

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            return handle_keydown(event, self)
        if event.type == pygame.KEYUP:
            handle_keyup(event, self)
        return None

    def update(self, keys=None, game_map=None):
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
                if getattr(self, "dir_y", 0) != 0:
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
                if getattr(self, "dir_x", 0) != 0:
                    self.dir_x = 0
                    self.show_idle = True

        dx = int(self.dir_x * self.speed)
        dy = int(self.dir_y * self.speed)

        if game_map is None:
            self.rect.x += dx
            self.rect.y += dy
            return

        solid_rects = game_map.get_solid_rects()

        if dx != 0:
            new_rect = self.rect.copy()
            new_rect.x += dx
            for r in solid_rects:
                if new_rect.colliderect(r):
                    if dx > 0:
                        new_rect.right = r.left
                    else:
                        new_rect.left = r.right
            self.rect.x = new_rect.x

        if dy != 0:
            new_rect = self.rect.copy()
            new_rect.y += dy
            for r in solid_rects:
                if new_rect.colliderect(r):
                    if dy > 0:
                        new_rect.bottom = r.top
                    else:
                        new_rect.top = r.bottom
            self.rect.y = new_rect.y

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        if getattr(self, "hit_box", False):
            pygame.draw.rect(surface, (0, 255, 0), self.rect, 2)