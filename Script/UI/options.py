import pygame


def _ensure_clock_and_title(clock, title_font):
    if clock is None:
        clock = pygame.time.Clock()
    if title_font is None:
        title_font = pygame.font.Font(None, 72)
    return clock, title_font


def _draw_title(screen, title_font, text, cx, y, color):
    surf = title_font.render(text, True, color)
    screen.blit(surf, (cx - surf.get_width() // 2, y))


def _draw_button(screen, menu_font, label, cx, y, rect_color, text_color, padding=10, border_radius=12):
    surf = menu_font.render(label, True, text_color)
    rect = pygame.Rect(cx - surf.get_width() // 2 - padding, y - padding,
                       surf.get_width() + padding * 2, surf.get_height() + padding * 2)
    pygame.draw.rect(screen, rect_color, rect, border_radius=border_radius)
    screen.blit(surf, (cx - surf.get_width() // 2, y))
    return rect


def controls_menu(screen, menu_font, colors, clock=None, title_font=None):
    GOLD = colors.get("GOLD", (212, 175, 55))
    BG = colors.get("BG", (30, 30, 30))

    clock, title_font = _ensure_clock_and_title(clock, title_font)

    fps = 60

    keyboard_image = pygame.image.load("graphics/ui/Keyboard_Pokémon.png").convert_alpha()
    scale_factor = 0.8
    keyboard_image = pygame.transform.scale(keyboard_image, 
                                            (int(keyboard_image.get_width() * scale_factor), 
                                             int(keyboard_image.get_height() * scale_factor)))

    while True:
        screen.fill(BG)

        sw = screen.get_width()
        sh = screen.get_height()
        cx = sw // 2

        _draw_title(screen, title_font, "CONTROLS", cx, int(sh * 0.12), GOLD)

        img_x = cx - keyboard_image.get_width() // 2
        img_y = int(sh * 0.25)  
        screen.blit(keyboard_image, (img_x, img_y))

        info_text = menu_font.render("Press ESC or click to go back", True, GOLD)
        screen.blit(info_text, (cx - info_text.get_width() // 2, img_y + keyboard_image.get_height() + 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"

            if event.type == pygame.MOUSEBUTTONDOWN:
                return "back"

        pygame.display.flip()
        clock.tick(fps)




def options_menu(screen, screen_width, screen_height, menu_font, colors, clock=None, title_font=None):
    BLACK = colors.get("BLACK", (0, 0, 0))
    GOLD = colors.get("GOLD", (212, 175, 55))
    BG = colors.get("BG", (30, 30, 30))

    clock, title_font = _ensure_clock_and_title(clock, title_font)
    fps = 60

    slider_width = 400
    slider_height = 6
    knob_radius = 12

    volume = pygame.mixer.music.get_volume()
    sliding = False

    while True:
        screen.fill(BG)

        sw = screen.get_width()
        sh = screen.get_height()
        cx = sw // 2

        _draw_title(screen, title_font, "Options", cx, int(sh * 0.12), GOLD)

        # Layout: Volume (slider), Controls, Fullscreen, Back, Quit
        slider_y = int(sh * 0.30)
        label_y = slider_y - 50

        # Buttons start below the slider
        btn_start_y = slider_y + 60
        btn_spacing = 70

        controls_rect = _draw_button(screen, menu_font, "Controls", cx, btn_start_y, GOLD, BLACK)
        fullscreen_rect = _draw_button(screen, menu_font, "Toggle Fullscreen", cx, btn_start_y + btn_spacing, GOLD, BLACK)
        back_rect = _draw_button(screen, menu_font, "Back", cx, btn_start_y + btn_spacing * 2, GOLD, BLACK)
        quit_rect = _draw_button(screen, menu_font, "Quit", cx, btn_start_y + btn_spacing * 3 + 30, GOLD, BLACK)

        # Volume slider
        slider_x = cx - slider_width // 2
        knob_x = slider_x + int(volume * slider_width)
        knob_y = slider_y + slider_height // 2

        label_text = menu_font.render("Volume:", True, GOLD)
        screen.blit(label_text, (cx - label_text.get_width() // 2, label_y))

        pygame.draw.rect(screen, GOLD, (slider_x, slider_y, slider_width, slider_height), border_radius=3)
        pygame.draw.circle(screen, GOLD, (knob_x, knob_y), knob_radius)

        percent = int(volume * 100)
        percent_text = menu_font.render(f"{percent}%", True, GOLD)
        screen.blit(percent_text, (slider_x + slider_width + 20, slider_y - 12))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if controls_rect.collidepoint(mx, my):
                    result = controls_menu(screen, menu_font, colors, clock, title_font)
                    if result == "quit":
                        return "quit"

                elif fullscreen_rect.collidepoint(mx, my):
                    pygame.display.toggle_fullscreen()

                elif back_rect.collidepoint(mx, my):
                    return "back"

                elif quit_rect.collidepoint(mx, my):
                    return "quit"

                elif (mx - knob_x) ** 2 + (my - knob_y) ** 2 <= knob_radius ** 2:
                    sliding = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                sliding = False

            if event.type == pygame.MOUSEMOTION and sliding:
                mx, my = event.pos
                mx = max(slider_x, min(mx, slider_x + slider_width))

                volume = (mx - slider_x) / slider_width
                pygame.mixer.music.set_volume(volume)

        pygame.display.flip()
        clock.tick(fps)
