import pygame
from io import BytesIO
import requests


def battle_menu(screen, pokemon, menu_font, small_font, colors, clock=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    GOLD = colors.get("GOLD", (212, 175, 55))
    RED = colors.get("RED", (255, 0, 0))
    BLUE = colors.get("BLUE", (0, 0, 255))
    GREEN = colors.get("GREEN", (0, 255, 0))
    YELLOW = colors.get("YELLOW", (255, 255, 0))
    BG = colors.get("BG", (30, 30, 30))

    if clock is None:
        clock = pygame.time.Clock()

    options = ["Fight", "Pokémon", "Bag", "Run"]
    option_colors = [RED, GREEN, YELLOW, BLUE]
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

    def draw():
        sw, sh = screen.get_size()
        if bg_img:
            try:
                b = pygame.transform.scale(bg_img, (sw, sh))
                screen.blit(b, (0, 0))
            except Exception:
                screen.fill(BG)
        else:
            screen.fill(BG)

        title = menu_font.render(f"A wild {pokemon['name']}", True, (255, 255, 255))
        hp = small_font.render(f"HP: {pokemon.get('hp','?')}", True, (255, 255, 255))
        atk = small_font.render(f"ATK: {pokemon.get('attack','?')}", True, (255, 255, 255))
        screen.blit(title, (20, 20))
        screen.blit(hp, (20, 20 + title.get_height() + 6))
        screen.blit(atk, (20, 20 + title.get_height() + 6 + hp.get_height() + 4))
        if sprite_surface:
            try:
                spr_w = 192
                spr_h = 192
                spr = pygame.transform.scale(sprite_surface, (spr_w, spr_h))
                spr_rect = spr.get_rect()
                spr_rect.midright = (sw - 200, sh // 2 - 40)
                screen.blit(spr, spr_rect)
            except Exception:
                pass

        box_h = 160
        box_rect = pygame.Rect(20, sh - box_h - 20, sw - 40, box_h)
        pygame.draw.rect(screen, (20, 20, 20), box_rect, border_radius=8)
        pygame.draw.rect(screen, GOLD, box_rect, 3, border_radius=8)
        padding = 18
        opt_w = (box_rect.width - padding * 3) // 2
        opt_h = (box_rect.height - padding * 3) // 2

        for i, opt in enumerate(options):
            row = i // 2
            col = i % 2
            x = box_rect.x + padding + col * (opt_w + padding)
            y = box_rect.y + padding + row * (opt_h + padding)
            rect = pygame.Rect(x, y, opt_w, opt_h)
            pygame.draw.rect(screen, option_colors[i], rect, border_radius=6)
            
            if i == selected:
                pygame.draw.rect(screen, (255, 255, 255), rect, 4, border_radius=6)

            text = menu_font.render(opt, True, (255, 255, 255))
            screen.blit(
                text,
                (
                    rect.x + rect.width // 2 - text.get_width() // 2,
                    rect.y + rect.height // 2 - text.get_height() // 2,
                ),
            )

    fps = 60
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "run"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    choice = options[selected].lower()
                    return choice
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

        draw()
        pygame.display.flip()
        clock.tick(fps)