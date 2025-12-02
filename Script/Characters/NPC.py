import pygame
import os

"""Simple NPC helper class.

This class is lightweight: it loads a sprite sheet (optional), provides a
basic `draw` method, and a `speak` method that calls `print`; the game
should provide a UI text overlay for better dialogue.
"""

SPRITE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "characters"))
DEFAULT_SPRITE = os.path.join(SPRITE_DIR, "blond.png")


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
    def __init__(self, x, y, name="Professor", sprite_path=None, w=16, h=16):
        self.name = name
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
            # Try to estimate frame size using default player sizes
            sw, sh = sheet.get_size()
            # default to 4x4 grid where possible
            cols = 4
            rows = 4
            w = max(1, sw // cols)
            h = max(1, sh // rows)
            try:
                self.sprite_frames = _slice_sheet(sheet, w, h)
            except Exception:
                self.sprite_frames = None

    def draw(self, surface, offset_x=0, offset_y=0):
        # Draw sprite if exists otherwise fallback rectangle
        draw_pos = (self.rect.x + offset_x, self.rect.y + offset_y)
        if self.sprite_frames:
            row_idx = min(self.row_idx, len(self.sprite_frames) - 1)
            row = self.sprite_frames[row_idx] if row_idx < len(self.sprite_frames) else []
            frame = row[self.anim_index % max(1, len(row))] if row else None
            if frame:
                surface.blit(frame, draw_pos)
                return
        # fallback rectangle if no sprite available
        pygame.draw.rect(surface, (200, 200, 50), (draw_pos[0], draw_pos[1], self.rect.width, self.rect.height))

    def speak(self, text):
        # Minimal fallback; prefer to integrate with the UI speech box
        print(f"{self.name}: {text}")

    # allow other code to ask questions from NPC (Dialog stub for UI to override)
    def ask(self, prompt, options):
        # Very simple console fallback: print options and wait for number
        print(prompt)
        for i, opt in enumerate(options):
            print(f"{i+1}. {opt}")
        try:
            sel = int(input("Choose option: ")) - 1
            return sel if 0 <= sel < len(options) else None
        except Exception:
            return None
