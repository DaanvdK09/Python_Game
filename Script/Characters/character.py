import pygame
import os
from .movement import handle_keydown, handle_keyup

RED = (200, 50, 50)
player_x = 0
player_y = 0
player_w = 16
player_h = 16
player_speed = 180
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

    def __init__(self):
        self.hitbox_rect = pygame.Rect(0, 0, player_w // 2, player_h // 2)
        self.hitbox_rect.midbottom = self.rect.midbottom
        self._fx = float(self.hitbox_rect.x)
        self._fy = float(self.hitbox_rect.y)

        self.money = 2000
        self.gyms_defeated = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            return handle_keydown(event, self)
        if event.type == pygame.KEYUP:
            handle_keyup(event, self)
        return None

    def update(self, keys=None, game_map=None, dt=1/60.0):
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

        dx = self.dir_x * self.speed * dt
        dy = self.dir_y * self.speed * dt
        moving = (getattr(self, "dir_x", 0) != 0) or (getattr(self, "dir_y", 0) != 0)

        # Dynamic animation speed
        min_anim_speed = 2
        max_anim_speed = 16
        base_speed = 200
        self.anim_speed = max(min_anim_speed, min(max_anim_speed, int(base_speed * 8 / max(1, self.speed))))

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
            self._fx += dx
            self._fy += dy
            self.hitbox_rect.x = int(self._fx)
            self.hitbox_rect.y = int(self._fy)
            self.rect.midbottom = (self.hitbox_rect.centerx, self.hitbox_rect.bottom)
            return

        solid_rects = game_map.get_solid_rects()

        if dx != 0:
            new_rect = self.hitbox_rect.copy()
            new_rect.x = int(self._fx + dx)
            for r in solid_rects:
                if new_rect.colliderect(r):
                    if dx > 0:
                        new_rect.right = r.left
                    else:
                        new_rect.left = r.right
            self._fx = float(new_rect.x)
            self.hitbox_rect.x = new_rect.x
            self.rect.midbottom = (self.hitbox_rect.centerx, self.hitbox_rect.bottom)

        if dy != 0:
            new_rect = self.hitbox_rect.copy()
            new_rect.y = int(self._fy + dy)
            for r in solid_rects:
                if new_rect.colliderect(r):
                    if dy > 0:
                        new_rect.bottom = r.top
                    else:
                        new_rect.top = r.bottom
            self._fy = float(new_rect.y)
            self.hitbox_rect.y = new_rect.y
            self.rect.midbottom = (self.hitbox_rect.centerx, self.hitbox_rect.bottom)

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
                    hb = pygame.Rect(
                        self.hitbox_rect.x + offset_x,
                        self.hitbox_rect.y + offset_y,
                        self.hitbox_rect.width,
                        self.hitbox_rect.height
                    )
                    pygame.draw.rect(surface, (0, 255, 0), hb, 2)
                return
        draw_rect = pygame.Rect(draw_pos[0], draw_pos[1], self.rect.width, self.rect.height)
        pygame.draw.rect(surface, self.color, draw_rect)
        if getattr(self, "hit_box", False):
            pygame.draw.rect(surface, (0, 255, 0), draw_rect, 2)