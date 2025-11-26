import pygame
from io import BytesIO
import requests


def battle_menu(screen, pokemon, menu_font, small_font, colors, clock=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    BATTLERED = colors.get("BATTLERED", (206, 0, 0))
    BATTLEBLUE = colors.get("BATTLEBLUE", (59, 76, 202))
    BATTLEGREEN = colors.get("BATTLEGREEN", (46, 129, 31))
    BATTLEYELLOW = colors.get("BATTLEYELLOW", (255, 222, 0))
    BG = colors.get("BG", (30, 30, 30))

    if clock is None:
        clock = pygame.time.Clock()

    options = ["Fight", "Pokémon", "Bag", "Run"]
    option_colors = [BATTLERED, BATTLEGREEN, BATTLEYELLOW, BATTLEBLUE]
    selected = 0

    bg_img = None
    try:
        bg_img = pygame.image.load("graphics/backgrounds/forest.png").convert()
    except Exception:
        bg_img = None

    sprite_surface = None
    try:
        if pokemon.get("sprite"):
            sprite_data = requests.get(pokemon["sprite"], timeout=5)
            sprite_surface = pygame.image.load(BytesIO(sprite_data.content)).convert_alpha()
    except Exception:
        sprite_surface = None

    state = "entrance"
    start_time = pygame.time.get_ticks()
    entrance_duration = 800  # ms

    fps = 60
    running = True
    while running:
        sw, sh = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "run"

            if event.type == pygame.KEYDOWN:
                if state == "message":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                        state = "options"
                elif state == "options":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                        return options[selected].lower()
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        if selected % 2 == 0:
                            selected = selected + 1
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        if selected % 2 == 1:
                            selected = selected - 1
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        if selected < 2:
                            selected = selected + 2
                    if event.key in (pygame.K_UP, pygame.K_w):
                        if selected >= 2:
                            selected = selected - 2
                    if event.key == pygame.K_ESCAPE:
                        return "run"


        if bg_img:
            try:
                b = pygame.transform.scale(bg_img, (sw, sh))
                screen.blit(b, (0, 0))
            except Exception:
                screen.fill(BG)
        else:
            screen.fill(BG)

        spr_w = 192
        spr_h = 192
        target_midright = (sw // 2, sh // 2)
        if sprite_surface:
            try:
                spr = pygame.transform.scale(sprite_surface, (spr_w, spr_h))
            except Exception:
                spr = None
        else:
            spr = None

        sprite_x = sw + spr_w
        sprite_y = target_midright[1]

        now = pygame.time.get_ticks()
        elapsed = now - start_time

        if state == "entrance":
            progress = min(1.0, elapsed / float(entrance_duration))
            ease = 1 - (1 - progress) * (1 - progress)
            start_x = sw + spr_w
            target_x = target_midright[0] - spr_w // 2
            sprite_x = int(start_x + (target_x - start_x) * ease)
            sprite_y = target_midright[1]
            if progress >= 1.0:
                state = "message"
                start_time = pygame.time.get_ticks()

        elif state in ("message", "options"):
            sprite_x = target_midright[0] - spr_w // 2
            sprite_y = target_midright[1]

        if spr:
            try:
                spr_rect = spr.get_rect()
                spr_rect.topleft = (sprite_x, sprite_y)
                screen.blit(spr, spr_rect)
            except Exception:
                pass
        else:
            ph_rect = pygame.Rect(sprite_x, sprite_y, spr_w, spr_h)
            pygame.draw.rect(screen, (100, 100, 100), ph_rect)

        padding = 18
        box_h = 160
        full_box_rect = pygame.Rect(20, sh - box_h - 20, sw - 40, box_h)
        pygame.draw.rect(screen, WHITE, full_box_rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, full_box_rect, 3, border_radius=8)

        if state == "message":
            msg = f"A wild {pokemon['name']} appeared!"
            text = menu_font.render(msg, True, BLACK)
            screen.blit(text, (full_box_rect.x + padding, full_box_rect.y + padding))

            hint = small_font.render("(Press ⎵ / Z to continue)", True, BLACK)
            screen.blit(hint, (full_box_rect.right - hint.get_width() - padding, full_box_rect.y + full_box_rect.height - hint.get_height() - padding))

        elif state == "options":
            area_w = int(full_box_rect.width * 0.5)
            area_h = full_box_rect.height - padding * 2
            area_x = full_box_rect.right - area_w - padding
            area_y = full_box_rect.y + padding
            opts_bg = pygame.Rect(area_x, area_y, area_w, area_h)
            pygame.draw.rect(screen, WHITE, opts_bg, border_radius=6)
            pygame.draw.rect(screen, BLACK, opts_bg, 2, border_radius=6)
            inner = max(8, padding // 2)
            opt_w = (opts_bg.width - inner * 3) // 2
            opt_h = (opts_bg.height - inner * 3) // 2

            for i, opt in enumerate(options):
                row = i // 2
                col = i % 2
                x = opts_bg.x + inner + col * (opt_w + inner)
                y = opts_bg.y + inner + row * (opt_h + inner)
                rect = pygame.Rect(x, y, opt_w, opt_h)
                pygame.draw.rect(screen, option_colors[i], rect, border_radius=6)
                if i == selected:
                    pygame.draw.rect(screen, BLACK, rect, 3, border_radius=6)
                text_color = WHITE

                text = menu_font.render(opt, True, text_color)
                screen.blit(
                    text,
                    (
                        rect.x + rect.width // 2 - text.get_width() // 2,
                        rect.y + rect.height // 2 - text.get_height() // 2,
                    ),
                )
            msg = "go (Placeholder Pokémon)" # First pokemon in bag
            text = menu_font.render(msg, True, BLACK)
            screen.blit(text, (full_box_rect.x + padding, full_box_rect.y + padding))
        pygame.display.flip()
        clock.tick(fps)
    return "run"