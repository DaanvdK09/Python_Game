import pygame
import os

SPRITE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "characters"))
DEFAULT_SPRITE = os.path.join(SPRITE_DIR, "Professor_Oak.png")

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
    cols = max(1, sw // w)
    rows = max(1, sh // h)
    for r in range(rows):
        row = []
        for c in range(cols):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), pygame.Rect(c * w, r * h, w, h))
            row.append(surf)
        frames.append(row)
    return frames

class NPC:
    def __init__(self, x, y, name="Professor", sprite_path=None, w=16, h=16, use_sprite_sheet=True, scale=1.0):
        self.name = name
        self.use_sprite_sheet = use_sprite_sheet
        self.scale = scale
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.midbottom = (int(x), int(y))
        self.hitbox_rect = pygame.Rect(self.rect.x, self.rect.y, max(1, self.rect.width//2), max(1, self.rect.height//2))
        self.hitbox_rect.midbottom = self.rect.midbottom
        self._fx = float(self.hitbox_rect.x)
        self._fy = float(self.hitbox_rect.y)

        self.sprite_frames = None
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_speed = 12
        self.row_idx = 0

        if sprite_path is None:
            sprite_path = DEFAULT_SPRITE
        sheet = _load_sheet(sprite_path)
        if sheet:
            if not use_sprite_sheet:
                # Single image: wrap it as a 1x1 frame grid
                self.sprite_frames = [[sheet]]
            else:
                # Auto-detect sensible grid by using smallest non-1 divisors
                sw, sh = sheet.get_size()
                def _divisors(n):
                    divs = []
                    for i in range(2, int(n**0.5) + 1):
                        if n % i == 0:
                            divs.append(i)
                            j = n // i
                            if j != i:
                                divs.append(j)
                    divs.append(n)
                    divs = sorted(set(divs))
                    return divs

                cols = 4
                rows = 4
                found = False
                for c in _divisors(sw):
                    for r in _divisors(sh):
                        w_try = sw // c
                        h_try = sh // r
                        if w_try >= 12 and h_try >= 12:
                            cols = c
                            rows = r
                            w = w_try
                            h = h_try
                            found = True
                            break
                    if found:
                        break
                if not found:
                    # fallback to a 4x4 split
                    cols = 4
                    rows = 4
                    w = max(1, sw // cols)
                    h = max(1, sh // rows)
                try:
                    self.sprite_frames = _slice_sheet(sheet, w, h)
                except Exception:
                    self.sprite_frames = None

    def draw(self, surface, offset_x=0, offset_y=0):
        draw_pos = (self.rect.x + offset_x, self.rect.y + offset_y)
        if self.sprite_frames:
            row_idx = min(self.row_idx, len(self.sprite_frames) - 1)
            row = self.sprite_frames[row_idx] if row_idx < len(self.sprite_frames) else []
            frame = row[self.anim_index % max(1, len(row))] if row else None
            if frame:
                # Scale the frame if scale != 1.0
                if self.scale != 1.0:
                    new_w = max(1, int(frame.get_width() * self.scale))
                    new_h = max(1, int(frame.get_height() * self.scale))
                    frame = pygame.transform.scale(frame, (new_w, new_h))
                surface.blit(frame, draw_pos)
                return
        pygame.draw.rect(surface, (200, 200, 50), (draw_pos[0], draw_pos[1], self.rect.width, self.rect.height))

    def is_near(self, other_rect, distance=100):
        """Check if another rect (like player) is within interaction distance"""
        return self.rect.colliderect(other_rect.inflate(distance, distance))

    def speak(self, text):
        print(f"{self.name}: {text}")

    def ask(self, prompt, options):
        print(prompt)
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        try:
            sel = int(input("Choose option: ")) - 1
            return sel if 0 <= sel < len(options) else None
        except Exception:
            return None

    def set_temporary_scale(self, temp_scale):
        try:
            if not hasattr(self, "_saved_scale"):
                self._saved_scale = self.scale
            self.scale = float(temp_scale)
        except Exception:
            pass

    def clear_temporary_scale(self):
        try:
            if hasattr(self, "_saved_scale"):
                self.scale = float(self._saved_scale)
                try:
                    del self._saved_scale
                except Exception:
                    pass
        except Exception:
            pass
