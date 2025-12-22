import pygame
import os
from pathlib import Path

# Define paths
base_dir = Path(__file__).parent.parent.parent  # Adjust based on your project structure
SPRITE_DIR = base_dir / "graphics" / "characters"
BACKDROP_DIR = base_dir / "graphics" / "backgrounds"
_BG_CACHE = {}

def _find_speaker_image(speaker_name):
    if not SPRITE_DIR.is_dir():
        return None
    token = speaker_name.replace(" ", "_").lower()
    # Try exact match first (including "Proffessor Oak.png")
    exact_path = SPRITE_DIR / f"{speaker_name}.png"
    if exact_path.exists():
        return str(exact_path)
    # Try with "Proffessor" spelling
    exact_path = SPRITE_DIR / "Proffessor Oak.png"
    if exact_path.exists():
        return str(exact_path)
    # Fallback: search for any matching file
    for fn in SPRITE_DIR.iterdir():
        if fn.is_file() and token in fn.stem.lower() and fn.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            return str(fn)
    return None

def _find_speaker_bg(speaker_name):
    if "professor" in speaker_name.lower():
        forest_path = BACKDROP_DIR / "forest.png"
        if forest_path.exists():
            return str(forest_path)
    if not SPRITE_DIR.is_dir():
        return None
    token = speaker_name.replace(" ", "_")
    candidates = [
        SPRITE_DIR / f"{token}_bg.png",
        SPRITE_DIR / f"{speaker_name}_bg.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    # Fallback: search for any matching file
    for fn in SPRITE_DIR.iterdir():
        if fn.is_file() and token.lower() in fn.stem.lower() and "bg" in fn.stem.lower() and fn.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            return str(fn)
    return None

def show_dialogue(
    screen, speaker_name, text, screen_width, screen_height, font, small_font, colors, clock=None
):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BG = colors.get("BG", (30, 30, 30))
    GOLD = colors.get("GOLD", (212, 175, 55))

    if clock is None:
        clock = pygame.time.Clock()

    # Base dimensions for the dialogue box
    base_box_width = 800
    base_box_height = 200

    # Get actual screen dimensions
    actual_w, actual_h = screen.get_size()

    # Calculate scaling factors
    scale_x = actual_w / 1280  # Assuming 1280 is the base screen width
    scale_y = actual_h / 720   # Assuming 720 is the base screen height

    # Scale the dialogue box dimensions
    box_width = int(base_box_width * scale_x)
    box_height = int(base_box_height * scale_y)

    # Center horizontally, but position near the bottom
    box_x = (actual_w - box_width) // 2
    box_y = actual_h - box_height - 50  # 50 pixels from the bottom

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

        # Load background
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
                        full_bg = pygame.transform.smoothscale(bg_img, (actual_w, actual_h))
                        _BG_CACHE[speaker_bg_path] = full_bg
                    except Exception:
                        full_bg = None
            else:
                if "professor" in speaker_name.lower():
                    bg = pygame.Surface((actual_w, actual_h))
                    # Subtle vertical gradient
                    for i in range(actual_h):
                        t = i / max(1, actual_h)
                        r = int(30 + (80 - 30) * t)
                        g = int(90 + (140 - 90) * t)
                        b = int(160 + (200 - 160) * t)
                        pygame.draw.line(bg, (r, g, b), (0, i), (actual_w, i))
                    full_bg = bg
        except Exception:
            full_bg = None

        if full_bg is not None:
            try:
                screen.blit(full_bg, (0, 0))
            except Exception:
                pass

        overlay = pygame.Surface((actual_w, actual_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Load speaker image
        speaker_img_path = _find_speaker_image(speaker_name)
        spr = None
        try:
            if speaker_img_path:
                spr = pygame.image.load(speaker_img_path).convert_alpha()
        except Exception:
            spr = None

        # Scale and draw speaker image
        if spr is not None:
            try:
                sw, sh = spr.get_size()
                # Scale the sprite to be a little bigger
                scale_factor = 1.5  # Adjust this value to make the sprite bigger or smaller
                spr = pygame.transform.smoothscale(spr, (int(sw * scale_x * scale_factor), int(sh * scale_y * scale_factor)))
                # Position the sprite on the right side of the dialogue box
                img_x = box_x + box_width - int(sw * scale_x * scale_factor) - 20  # 20 pixels from the right edge of the box
                img_y = box_y - int(sh * scale_y * scale_factor)  # Position above the box
                screen.blit(spr, (img_x, img_y))
            except Exception:
                pass

        # Draw dialogue box
        pygame.draw.rect(screen, BG, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, GOLD, (box_x, box_y, box_width, box_height), 3)

        # Render speaker name
        name_surf = font.render(speaker_name, True, GOLD)
        screen.blit(name_surf, (box_x + 20, box_y + 15))

        # Render text
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

        # Render hint text
        hint_text = "Press SPACE or click to continue"
        hint_surf = small_font.render(hint_text, True, GOLD)
        screen.blit(hint_surf, (box_x + box_width - hint_surf.get_width() - 15, box_y + box_height - 30))

        pygame.display.flip()
        clock.tick(fps)

def show_tutorial(screen, screen_width, screen_height, font, small_font, colors, name, clock=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BG = colors.get("BG", (30, 30, 30))
    GOLD = colors.get("GOLD", (212, 175, 55))

    if clock is None:
        clock = pygame.time.Clock()

    # Base dimensions for scaling
    base_screen_width = 1280
    base_screen_height = 720

    # Calculate scaling factors
    scale_x = screen_width / base_screen_width
    scale_y = screen_height / base_screen_height

    # Tutorial dialogue lines
    tutorial_lines = [
        ("Professor Oak", f"Welcome, {name}! I'm Professor Oak, the local Pokémon expert."),
        ("Professor Oak", "You're going on an exciting journey! Let me teach you the basics."),
        ("Professor Oak", "Press 'M' to open the map and see where you are."),
        ("Professor Oak", "Walk through grass to encounter wild Pokémon!"),
        ("Professor Oak", "Remember: Your main goal is to catch and train Pokémon and defeat the three Gym Leaders!"),
        ("Professor Oak", "Level up your Pokémon by battling gym leaders and wild Pokémon."),
        ("Professor Oak", "To catch Pokémon, weaken them in battle first, then use Poké Balls from your bag."),
        ("Professor Oak", "To test your skills, find and battle other trainers you meet on your journey."),
        ("Professor Oak", "Good luck, and remember—the bond between trainer and Pokémon is key!"),
        ("Professor Oak", "If you ever want to look at the full settings and controls, press 'ESC' to pause the game and go to options."),
        ("Professor Oak", "You could also talk to me again to hear these instructions once more."),
        ("Professor Oak", "Before you leave, take this Pikachu as your starter Pokémon!"),
        ("Professor Oak", "Now, go forth and become a Pokémon Master!"),
    ]

    # Load Professor Oak sprite
    speaker_img_path = _find_speaker_image("Professor Oak")
    spr = None
    try:
        if speaker_img_path:
            spr = pygame.image.load(speaker_img_path).convert_alpha()
    except Exception:
        spr = None

    for speaker, text in tutorial_lines:
        # Clear screen
        screen.fill(BG)

        # Draw background (optional)
        full_bg = None
        try:
            speaker_bg_path = _find_speaker_bg(speaker)
            if speaker_bg_path:
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
                if "professor" in speaker.lower():
                    bg = pygame.Surface((screen_width, screen_height))
                    # Subtle vertical gradient
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

        # Draw overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Scale and draw Professor Oak sprite
        if spr is not None:
            try:
                sw, sh = spr.get_size()
                # Scale the sprite to be a little bigger
                scale_factor = 1.5  # Adjust this value to make the sprite bigger or smaller
                spr = pygame.transform.smoothscale(spr, (int(sw * scale_x * scale_factor), int(sh * scale_y * scale_factor)))
                # Position the sprite on the right side of the screen
                img_x = screen_width - int(sw * scale_x * scale_factor) - 50  # 50 pixels from the right edge of the screen
                img_y = screen_height // 2 - int(sh * scale_y * scale_factor) // 2  # Vertically centered
                screen.blit(spr, (img_x, img_y))
            except Exception:
                pass

        # Show dialogue
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