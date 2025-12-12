import pygame


# CONTROLS MENU
def controls_menu(screen, menu_font, colors, clock=None, title_font=None):
    GOLD = colors.get("GOLD", (212, 175, 55))
    BG = colors.get("BG", (30, 30, 30))

    clock = clock or pygame.time.Clock()
    title_font = title_font or pygame.font.Font(None, 72)

    keyboard_image = pygame.image.load("graphics/ui/Keyboard_Pokémon.png").convert_alpha()
    keyboard_image = pygame.transform.scale(
        keyboard_image,
        (int(keyboard_image.get_width() * 0.6),
         int(keyboard_image.get_height() * 0.6))
    )

    small_font = pygame.font.Font(None, 28)

    lines = [
        "ESC: Back / Quit",
        "ENTER / SPACE: Continue / Select",
        "WASD: Move",
        "E: Interact",
        "M: Map",
        "3: Debug mode",
        "V: Pokedex",
        "TAB: Bag (with Pokémon)"
    ]

    while True:
        screen.fill(BG)
        sw, sh = screen.get_size()
        cx = sw // 2

        # Titel
        title = title_font.render("CONTROLS", True, GOLD)
        screen.blit(title, (cx - title.get_width() // 2, int(sh * 0.12)))

        # Toetsenbord afbeelding
        img_x = cx - keyboard_image.get_width() // 2
        img_y = int(sh * 0.25)
        screen.blit(keyboard_image, (img_x, img_y))

        # Tekstregels
        line_height = small_font.get_height() + 6
        start_y = img_y + keyboard_image.get_height() + 12

        bottom_text = menu_font.render("Press ESC or click to go back", True, GOLD)
        bottom_y = sh - bottom_text.get_height() - 24

        # Zorg dat het past
        total_h = len(lines) * line_height
        if start_y + total_h > bottom_y:
            start_y -= (start_y + total_h - bottom_y)

        for i, txt in enumerate(lines):
            surf = small_font.render(txt, True, GOLD)
            screen.blit(surf, (cx - surf.get_width() // 2, start_y + i * line_height))

        screen.blit(bottom_text, (cx - bottom_text.get_width() // 2, bottom_y))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"
            if event.type == pygame.MOUSEBUTTONDOWN:
                return "back"

        pygame.display.flip()
        clock.tick(60)

# OPTIONS MENU
def options_menu(screen, screen_width, screen_height, menu_font, colors, clock=None, title_font=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    GOLD = colors.get("GOLD", (212, 175, 55))
    BG = colors.get("BG", (30, 30, 30))

    clock = clock or pygame.time.Clock()
    title_font = title_font or pygame.font.Font(None, 72)

    volume = pygame.mixer.music.get_volume()
    sliding = False

    slider_w = 400
    slider_h = 6
    knob_r = 12

    def draw_btn(text, x, y):
        surf = menu_font.render(text, True, BLACK)
        rect = pygame.Rect(x - surf.get_width() // 2 - 10, y - 10,
                           surf.get_width() + 20, surf.get_height() + 20)
        pygame.draw.rect(screen, GOLD, rect, border_radius=12)
        screen.blit(surf, (x - surf.get_width() // 2, y))
        return rect

    while True:
        screen.fill(BG)
        cx = screen_width // 2

        # Titel
        title = title_font.render("OPTIONS", True, GOLD)
        screen.blit(title, (cx - title.get_width() // 2, int(screen_height * 0.12)))

        # Slider positie
        slider_y = int(screen_height * 0.30)
        slider_x = cx - slider_w // 2

        # Slider label
        label = menu_font.render("Volume:", True, GOLD)
        screen.blit(label, (cx - label.get_width() // 2, slider_y - 50))

        knob_x = slider_x + int(volume * slider_w)
        knob_y = slider_y + slider_h // 2

        # Slider tekenen
        pygame.draw.rect(screen, GOLD, (slider_x, slider_y, slider_w, slider_h), border_radius=3)
        pygame.draw.circle(screen, GOLD, (knob_x, knob_y), knob_r)

        # Percentage
        pct = menu_font.render(f"{int(volume * 100)}%", True, GOLD)
        screen.blit(pct, (slider_x + slider_w + 20, slider_y - 12))

        # Knoppen
        btn_controls = draw_btn("Controls", cx, slider_y + 60)
        btn_fullscreen = draw_btn("Toggle Fullscreen", cx, slider_y + 130)
        btn_back = draw_btn("Back", cx, slider_y + 200)
        btn_quit = draw_btn("Quit", cx, slider_y + 270)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if btn_controls.collidepoint(mx, my):
                    res = controls_menu(screen, menu_font, colors, clock, title_font)
                    if res == "quit":
                        return "quit"

                elif btn_fullscreen.collidepoint(mx, my):
                    pygame.display.toggle_fullscreen()

                elif btn_back.collidepoint(mx, my):
                    return "back"

                elif btn_quit.collidepoint(mx, my):
                    return "quit"

                # Slider knop
                elif (mx - knob_x)**2 + (my - knob_y)**2 <= knob_r**2:
                    sliding = True

            if event.type == pygame.MOUSEBUTTONUP:
                sliding = False

            if event.type == pygame.MOUSEMOTION and sliding:
                mx = max(slider_x, min(event.pos[0], slider_x + slider_w))
                volume = (mx - slider_x) / slider_w
                pygame.mixer.music.set_volume(volume)

        pygame.display.flip()
        clock.tick(60)
