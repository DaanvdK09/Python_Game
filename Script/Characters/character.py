import pygame
import os

RED = (200, 50, 50)

player_x = 0
player_y = 0
player_w = 16
player_h = 16
player_speed = 4

dir_x = 0
dir_y = 0
last_dir = 1
show_idle = True
hit_box = False
alive = True

_SPRITE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "characters", "player.png")
)

SPRITE_COLS = 4
SPRITE_ROWS = 4

def _load_sheet(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        try:
            return pygame.image.load(path)
        except Exception:
            return None

def _slice_sheet(sheet, w, h):
    frames = []
    if sheet is None:
        return frames
    sw, sh = sheet.get_size()
    cols = sw // w
    rows = sh // h
    for r in range(rows):
        row = []
        for c in range(cols):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), pygame.Rect(c * w, r * h, w, h))
            row.append(surf)
        frames.append(row)
    return frames

_SHEET = _load_sheet(_SPRITE_PATH)
if _SHEET is not None:
    sw, sh = _SHEET.get_size()
    if SPRITE_COLS > 0:
        player_w = sw // SPRITE_COLS
    if SPRITE_ROWS > 0:
        player_h = sh // SPRITE_ROWS

player_rect = pygame.Rect(player_x, player_y, player_w, player_h)

SPRITE_FRAMES = _slice_sheet(_SHEET, player_w, player_h)
#Movement
def handle_keydown(event, obj):
    if event.key in (pygame.K_w, pygame.K_UP):
        obj.dir_y = -1
        obj.show_idle = False
        obj.last_dir = 3
    elif event.key in (pygame.K_s, pygame.K_DOWN):
        obj.dir_y = 1
        obj.show_idle = False
        obj.last_dir = 1
    elif event.key in (pygame.K_d, pygame.K_RIGHT):
        obj.dir_x = 1
        obj.show_idle = False
        obj.last_dir = 4
    elif event.key in (pygame.K_a, pygame.K_LEFT):
        obj.dir_x = -1
        obj.show_idle = False
        obj.last_dir = 2
    return None

def handle_keyup(event, obj):
    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
        obj.dir_y = 0
        obj.show_idle = True
    if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
        obj.dir_x = 0
        obj.show_idle = True

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

    sprite_frames = SPRITE_FRAMES
    anim_index = 0
    anim_timer = 0
    anim_speed = 8

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

        moving = (getattr(self, "dir_x", 0) != 0) or (getattr(self, "dir_y", 0) != 0)
        if moving:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                row_idx = self._row_for_direction()
                row = self.sprite_frames[row_idx] if self.sprite_frames and row_idx < len(self.sprite_frames) else []
                if row:
                    self.anim_index = (self.anim_index + 1) % len(row)
                else:
                    self.anim_index = 0
        else:
            self.anim_index = 0
            self.anim_timer = 0

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

    def _row_for_direction(self):
        row_map = {1: 0, 2: 1, 4: 2, 3: 3}
        idx = row_map.get(getattr(self, "last_dir", 1), 0)
        if self.sprite_frames:
            return min(idx, len(self.sprite_frames) - 1)
        return 0

    def draw(self, surface, offset_x=0, offset_y=0):
        draw_pos = (self.rect.x + offset_x, self.rect.y + offset_y)
        if self.sprite_frames:
            row_idx = self._row_for_direction()
            row = self.sprite_frames[row_idx] if row_idx < len(self.sprite_frames) else []
            if row:
                frame = row[self.anim_index % max(1, len(row))]
                surface.blit(frame, draw_pos)
                if getattr(self, "hit_box", False):
                    hb = pygame.Rect(draw_pos[0], draw_pos[1], self.rect.width, self.rect.height)
                    pygame.draw.rect(surface, (0, 255, 0), hb, 2)
                return

        draw_rect = pygame.Rect(draw_pos[0], draw_pos[1], self.rect.width, self.rect.height)
        pygame.draw.rect(surface, self.color, draw_rect)
        if getattr(self, "hit_box", False):
            pygame.draw.rect(surface, (0, 255, 0), draw_rect, 2)