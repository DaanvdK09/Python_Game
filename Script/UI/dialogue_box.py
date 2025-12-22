import pygame
import os
from pathlib import Path

# Define paths
base_dir = Path(__file__).parent.parent.parent
SPRITE_DIR = base_dir / "graphics" / "characters"
BACKDROP_DIR = base_dir / "graphics" / "backgrounds"

# Global caches
_SPEAKER_IMAGE_CACHE = {}
_SPEAKER_BG_CACHE = {}

def _load_and_cache_speaker_images():
    if not SPRITE_DIR.is_dir():
        print(f"Warning: SPRITE_DIR does not exist: {SPRITE_DIR}")
        return
    for fn in SPRITE_DIR.iterdir():
        if fn.is_file() and fn.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            try:
                img = pygame.image.load(str(fn)).convert_alpha()
                _SPEAKER_IMAGE_CACHE[fn.stem.lower()] = img
            except Exception as e:
                print(f"Error loading speaker image {fn}: {e}")

def _load_and_cache_speaker_bgs():
    if not BACKDROP_DIR.is_dir():
        print(f"Warning: BACKDROP_DIR does not exist: {BACKDROP_DIR}")
        return
    for fn in BACKDROP_DIR.iterdir():
        if fn.is_file() and fn.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            try:
                img = pygame.image.load(str(fn)).convert()
                _SPEAKER_BG_CACHE[fn.stem.lower()] = img
            except Exception as e:
                print(f"Error loading speaker background {fn}: {e}")

def _get_speaker_image(speaker_name):
    token = speaker_name.replace(" ", "_").lower()
    if token in _SPEAKER_IMAGE_CACHE:
        return _SPEAKER_IMAGE_CACHE[token]
    # Try with "Professor" spelling
    if "professor" in token and "professor_oak" in _SPEAKER_IMAGE_CACHE:
        return _SPEAKER_IMAGE_CACHE["professor_oak"]
    # Fallback: search for any matching file
    for key in _SPEAKER_IMAGE_CACHE:
        if token in key:
            return _SPEAKER_IMAGE_CACHE[key]
    print(f"Warning: No cached sprite found for {speaker_name}")
    return None

def _get_speaker_bg(speaker_name):
    token = speaker_name.replace(" ", "_").lower()
    if "professor" in speaker_name.lower() and "forest" in _SPEAKER_BG_CACHE:
        return _SPEAKER_BG_CACHE["forest"]
    if token in _SPEAKER_BG_CACHE:
        return _SPEAKER_BG_CACHE[token]
    # Fallback: search for any matching file
    for key in _SPEAKER_BG_CACHE:
        if token in key and "bg" in key:
            return _SPEAKER_BG_CACHE[key]
    print(f"Warning: No cached background found for {speaker_name}")
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
    scale_x = actual_w / 1280
    scale_y = actual_h / 720

    # Scale the dialogue box dimensions
    box_width = int(base_box_width * scale_x)
    box_height = int(base_box_height * scale_y)

    # Center horizontally, but position near the bottom
    box_x = (actual_w - box_width) // 2
    box_y = actual_h - box_height - 50

    fps = 60

    # Retrieve cached images
    spr_img = _get_speaker_image(speaker_name)
    bg_img = _get_speaker_bg(speaker_name)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True

        # Clear screen
        screen.fill(BG)

        # Draw background
        if bg_img is not None:
            try:
                scaled_bg = pygame.transform.smoothscale(bg_img, (actual_w, actual_h))
                screen.blit(scaled_bg, (0, 0))
            except Exception as e:
                print(f"Error scaling/drawing background: {e}")

        # Draw overlay
        overlay = pygame.Surface((actual_w, actual_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Draw speaker image
        if spr_img is not None:
            try:
                sw, sh = spr_img.get_size()
                scale_factor = 1.5
                scaled_spr = pygame.transform.smoothscale(
                    spr_img, (int(sw * scale_x * scale_factor), int(sh * scale_y * scale_factor))
                )
                img_x = box_x + box_width - scaled_spr.get_width() - 20
                img_y = box_y - scaled_spr.get_height()
                screen.blit(scaled_spr, (img_x, img_y))
            except Exception as e:
                print(f"Error scaling/drawing speaker image: {e}")

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

    # Preload images
    _load_and_cache_speaker_images()
    _load_and_cache_speaker_bgs()

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
                    return selected == "yes"
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if yes_rect.collidepoint(mx, my):
                    return True
                if no_rect.collidepoint(mx, my):
                    return False

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

        pygame.draw.rect(screen, (80, 120, 80) if selected == "yes" else (60, 60, 60), yes_rect)
        pygame.draw.rect(screen, (120, 80, 80) if selected == "no" else (60, 60, 60), no_rect)
        yes_txt = small_font.render("Yes", True, WHITE)
        no_txt = small_font.render("No", True, WHITE)
        screen.blit(yes_txt, (yes_rect.x + yes_rect.width//2 - yes_txt.get_width()//2, yes_rect.y + 8))
        screen.blit(no_txt, (no_rect.x + no_rect.width//2 - no_txt.get_width()//2, no_rect.y + 8))

        pygame.display.flip()
        clock.tick(fps)