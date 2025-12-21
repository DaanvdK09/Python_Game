import pygame
import os

SPRITE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "characters"))
_BG_CACHE = {}
BACKDROP_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "graphics", "backgrounds"))


def _find_speaker_image(speaker_name):
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
        
        # Clear screen
        screen.fill(BG)
        full_bg_path = None
        full_bg = None
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

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        speaker_img_path = _find_speaker_image(speaker_name)
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

        max_img_w = int(screen_width * 0.26)
        max_img_h = int(screen_height * 0.43)

        if spr is not None:
            try:
                sw, sh = spr.get_size()
                scale = min(1.2, max_img_w / sw, max_img_h / sh)
                img_w = max(1.2, int(sw * scale))
                img_h = max(1.2, int(sh * scale))
                spr_scaled = pygame.transform.smoothscale(spr, (img_w, img_h))
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

def show_tutorial(screen, screen_width, screen_height, font, small_font, colors, name, clock=None):
    tutorial_lines = [
        ("Professor Oak", f"Welcome, {name}! I'm Professor Oak, the local Pokémon expert."),
        ("Professor Oak", "You've embarked on an exciting journey! Let me teach you the basics."),
        ("Professor Oak", "Use WASD or Arrow Keys to move around the world."),
        ("Professor Oak", "Press 'M' to open the map and see where you are."),
        ("Professor Oak", "Walk through grass to encounter wild Pokémon!"),
        ("Professor Oak", "Remember: Your main goal is to catch and train Pokémon and defeat the three Gym Leaders!"),
        ("Professor Oak", "level up your Pokémon by battling gym leaders and wild Pokémon."),
        ("Professor Oak", "To catch Pokémon, weaken them in battle first, then use Poké Balls from your bag."),
        ("Professor Oak", "To test your skills, find and battle other trainers you meet on your journey."),
        ("Professor Oak", "Good luck, and remember - the bond between trainer and Pokémon is key!"),
        ("Professor Oak", "If you ever want to look at the full settings and controls, press 'ESC' to pause the game and go to options."),
        ("Professor Oak", "Before you leave, take this Pikachu as your starter Pokémon!"),
        ("Professor Oak", "Now, go forth and become a Pokémon Master!"),
    ]
    
    for speaker, text in tutorial_lines:
        if not show_dialogue(screen, speaker, text, screen_width, screen_height, font, small_font, colors, clock):
            return False
    
    return True


def show_tutorial_choice(screen, screen_width, screen_height, font, small_font, colors, clock=None):
    if clock is None:
        clock = pygame.time.Clock()
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BG = colors.get("BG", (30, 30, 30))
    GOLD = colors.get("GOLD", (212, 175, 55))

    box_w = int(screen_width * 0.75)
    box_h = int(screen_height * 0.35)
    box_x = (screen_width - box_w) // 2
    box_y = (screen_height - box_h) // 2

    yes_rect = pygame.Rect(box_x + 40, box_y + box_h - 70, 140, 40)
    no_rect = pygame.Rect(box_x + box_w - 40 - 140, box_y + box_h - 70, 140, 40)

    selected = "yes"
    fps = 60
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = "yes"
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = "no"
                elif event.key in (pygame.K_y, pygame.K_RETURN, pygame.K_SPACE):
                    # Confirm current selection
                    return selected == "yes"
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if yes_rect.collidepoint(mx, my):
                    return True
                if no_rect.collidepoint(mx, my):
                    return False

        # Draw modal
        # background
        screen.fill(BG)

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, GOLD, (box_x, box_y, box_w, box_h), 3)

        title = font.render("Play tutorial?", True, GOLD)
        screen.blit(title, (box_x + 20, box_y + 12))

        msg = small_font.render("Would you like Professor Oak to teach you the basics?", True, WHITE)
        screen.blit(msg, (box_x + 20, box_y + 50))

        # Buttons
        pygame.draw.rect(screen, (80, 120, 80) if selected == "yes" else (60, 60, 60), yes_rect)
        pygame.draw.rect(screen, (120, 80, 80) if selected == "no" else (60, 60, 60), no_rect)
        yes_txt = small_font.render("Yes", True, WHITE)
        no_txt = small_font.render("No", True, WHITE)
        screen.blit(yes_txt, (yes_rect.x + yes_rect.width//2 - yes_txt.get_width()//2, yes_rect.y + 8))
        screen.blit(no_txt, (no_rect.x + no_rect.width//2 - no_txt.get_width()//2, no_rect.y + 8))

        pygame.display.flip()
        clock.tick(fps)

