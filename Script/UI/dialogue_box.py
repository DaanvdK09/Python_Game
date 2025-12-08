import pygame
import os

SPRITE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "characters"))
_BG_CACHE = {}
BACKDROP_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "backgrounds"))


def _find_speaker_image(speaker_name):
    """Try to find an image file in `graphics/characters` matching the speaker_name.
    Returns full path or None.
    """
    if not os.path.isdir(SPRITE_DIR):
        return None
    token = speaker_name.replace(" ", "_").lower()
    # candidate exact names
    candidates = [f"{speaker_name}.png", f"{speaker_name}.PNG", f"{speaker_name.replace(' ', '_')}.png", f"{speaker_name.replace(' ', '_')}.PNG"]
    for c in candidates:
        p = os.path.join(SPRITE_DIR, c)
        if os.path.exists(p):
            return p
    # fallback: find any file that contains the token
    for fn in os.listdir(SPRITE_DIR):
        if token in fn.lower() and fn.lower().endswith(('.png', '.jpg', '.jpeg')):
            return os.path.join(SPRITE_DIR, fn)
    return None


def _find_speaker_bg(speaker_name):
    """Try to find a background image for the speaker (e.g. 'Professor_Oak_bg.png')."""
    # If speaker is professor, prefer the forest backdrop
    if "professor" in speaker_name.lower():
        try:
            forest_path = os.path.join(BACKDROP_DIR, "forest.png")
            if os.path.exists(forest_path):
                return forest_path
        except Exception:
            pass

    if not os.path.isdir(SPRITE_DIR):
        return None
    token = speaker_name.replace(" ", "_")
    candidates = [f"{token}_bg.png", f"{token}_bg.PNG", f"{speaker_name}_bg.png", f"{speaker_name}_bg.PNG"]
    for c in candidates:
        p = os.path.join(SPRITE_DIR, c)
        if os.path.exists(p):
            return p
    # fallback: any file containing token + 'bg'
    for fn in os.listdir(SPRITE_DIR):
        low = fn.lower()
        if token.lower() in low and "bg" in low and low.endswith(('.png', '.jpg', '.jpeg')):
            return os.path.join(SPRITE_DIR, fn)
    return None


def show_dialogue(screen, speaker_name, text, screen_width, screen_height, font, small_font, colors, clock=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BG = colors.get("BG", (30, 30, 30))
    GOLD = colors.get("GOLD", (212, 175, 55))
    
    if clock is None:
        clock = pygame.time.Clock()
    
    box_width = int(screen_width * 0.8)
    box_height = int(screen_height * 0.25)
    box_x = (screen_width - box_width) // 2
    box_y = screen_height - box_height - 30
    
    fps = 60
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        
        # Full-screen per-speaker background (draw under everything)
        full_bg = None
        full_bg_path = None
        try:
            speaker_bg_path = _find_speaker_bg(speaker_name)
            if speaker_bg_path:
                full_bg_path = speaker_bg_path
                if speaker_bg_path in _BG_CACHE:
                    full_bg = _BG_CACHE[speaker_bg_path]
                else:
                    try:
                        bg_img = pygame.image.load(speaker_bg_path).convert()
                        full_bg = pygame.transform.smoothscale(bg_img, (screen_width, screen_height))
                        _BG_CACHE[speaker_bg_path] = full_bg
                    except Exception:
                        full_bg = None
            else:
                # If no bg image, generate a professor placeholder full-screen
                if "professor" in speaker_name.lower():
                    bg = pygame.Surface((screen_width, screen_height))
                    # subtle vertical gradient
                    for i in range(screen_height):
                        t = i / max(1, screen_height)
                        r = int(30 + (80 - 30) * t)
                        g = int(90 + (140 - 90) * t)
                        b = int(160 + (200 - 160) * t)
                        pygame.draw.line(bg, (r, g, b), (0, i), (screen_width, i))
                    full_bg = bg
        except Exception:
            full_bg = None

        if full_bg is not None:
            try:
                screen.blit(full_bg, (0, 0))
            except Exception:
                pass

        # semi-transparent overlay on top of full background (or game)
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Speaker image (draw above dialogue box to the right)
        speaker_img_path = _find_speaker_image(speaker_name)
        # Only use a small panel bg if we did NOT already draw a full-screen bg
        if full_bg_path:
            panel_bg_path = None
        else:
            panel_bg_path = _find_speaker_bg(speaker_name)
        spr = None
        try:
            if speaker_img_path:
                spr = pygame.image.load(speaker_img_path).convert_alpha()
        except Exception:
            spr = None

        # Slightly larger max image area than before
        max_img_w = int(screen_width * 0.22)
        max_img_h = int(screen_height * 0.36)

        # We no longer draw a small panel background behind portraits when a full-screen
        # background is used (or at all). We'll only draw the speaker portrait itself.

        if spr is not None:
            try:
                sw, sh = spr.get_size()
                scale = min(1.0, max_img_w / sw, max_img_h / sh)
                img_w = max(1, int(sw * scale))
                img_h = max(1, int(sh * scale))
                spr_scaled = pygame.transform.smoothscale(spr, (img_w, img_h))
                # Position image above the dialogue box on the right (no panel)
                img_x = screen_width - img_w - 20
                img_y = max(10, box_y - img_h - 10)
                screen.blit(spr_scaled, (img_x, img_y))
            except Exception:
                pass
        
        pygame.draw.rect(screen, BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, GOLD, (box_x, box_y, box_width, box_height), 3)
        
        name_surf = font.render(speaker_name, True, GOLD)
        screen.blit(name_surf, (box_x + 20, box_y + 15))
        
        text_y = box_y + 60
        text_color = WHITE
        max_text_width = box_width - 40
        
        words = text.split()
        line = ""
        lines = []
        for word in words:
            test_line = line + word + " "
            test_surf = small_font.render(test_line, True, text_color)
            if test_surf.get_width() > max_text_width:
                if line:
                    lines.append(line)
                line = word + " "
            else:
                line = test_line
        if line:
            lines.append(line)
        
        for line_text in lines:
            line_surf = small_font.render(line_text, True, text_color)
            screen.blit(line_surf, (box_x + 20, text_y))
            text_y += 25
        
        hint_text = "Press SPACE or click to continue"
        hint_surf = small_font.render(hint_text, True, GOLD)
        screen.blit(hint_surf, (box_x + box_width - hint_surf.get_width() - 15, box_y + box_height - 30))
        
        pygame.display.flip()
        clock.tick(fps)

def show_tutorial(screen, screen_width, screen_height, font, small_font, colors, clock=None):
    tutorial_lines = [
        ("Professor Oak", "Welcome, young trainer! I'm Professor Oak, the local Pokémon expert."),
        ("Professor Oak", "You've embarked on an exciting journey! Let me teach you the basics."),
        ("Professor Oak", "Use WASD or Arrow Keys to move around the world."),
        ("Professor Oak", "Press 'M' to open the map and see where you are."),
        ("Professor Oak", "Walk through grass to encounter wild Pokémon!"),
        ("Professor Oak", "When you encounter a Pokémon, press SPACE to open the battle menu."),
        ("Professor Oak", "Good luck, and remember - the bond between trainer and Pokémon is key!"),
        ("Professor Oak", "If you ever want to look at the settings, press 'ESC' to pause the game and go to options."),
    ]
    
    for speaker, text in tutorial_lines:
        if not show_dialogue(screen, speaker, text, screen_width, screen_height, font, small_font, colors, clock):
            return False
    
    return True

