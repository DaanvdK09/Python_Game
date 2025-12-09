import pygame

def options_menu(screen, screen_width, screen_height, menu_font, colors, clock=None, title_font=None):
    BLACK = colors.get("BLACK", (0,0,0))
    GOLD = colors.get("GOLD", (212,175,55))
    BG = colors.get("BG", (30,30,30))

    if clock is None:
        clock = pygame.time.Clock()
    fps = 60

    if title_font is None:
        title_font = pygame.font.Font(None, 72)

    # SLIDER INSTELLINGEN
    slider_width = 400
    slider_height = 6
    knob_radius = 12

    volume = pygame.mixer.music.get_volume()  # tussen 0.0 en 1.0
    sliding = False

    while True:
        screen.fill(BG)

        sw = screen.get_width()
        sh = screen.get_height()
        cx = sw // 2

        # TEKST
        title_text = title_font.render("Options", True, GOLD)
        fullscreen_text = menu_font.render("Toggle Fullscreen", True, BLACK)
        back_text = menu_font.render("Back", True, BLACK)
        quit_text = menu_font.render("Quit", True, BLACK)

        # POSITIES TEKST & KNOPPEN
        title_y = int(sh * 0.12)
        fullscreen_y = sh // 2 - 40
        back_y = fullscreen_y + 80
        quit_y = back_y + 100

        fullscreen_rect = pygame.Rect(cx - fullscreen_text.get_width()//2 - 10, fullscreen_y - 10,
                                      fullscreen_text.get_width() + 20, fullscreen_text.get_height() + 20)
        back_rect = pygame.Rect(cx - back_text.get_width()//2 - 10, back_y - 10,
                                back_text.get_width() + 20, back_text.get_height() + 20)
        quit_rect = pygame.Rect(cx - quit_text.get_width()//2 - 10, quit_y - 10,
                                quit_text.get_width() + 20, quit_text.get_height() + 20)

        # TEKEN KNOPPEN
        pygame.draw.rect(screen, GOLD, fullscreen_rect, border_radius=12)
        pygame.draw.rect(screen, GOLD, back_rect, border_radius=12)
        pygame.draw.rect(screen, GOLD, quit_rect, border_radius=12)

        # TEKEN TEKST
        screen.blit(title_text, (cx - title_text.get_width()//2, title_y))
        screen.blit(fullscreen_text, (cx - fullscreen_text.get_width()//2, fullscreen_y))
        screen.blit(back_text, (cx - back_text.get_width()//2, back_y))
        screen.blit(quit_text, (cx - quit_text.get_width()//2, quit_y))

        # GEHELE SLIDER
        slider_y = int(sh * 0.40)  # gewoon één formule, net als bij knoppen
        label_y = slider_y - 50

        # slider positie
        slider_x = cx - slider_width // 2

        # knob positie
        knob_x = slider_x + int(volume * slider_width)
        knob_y = slider_y + slider_height // 2

        # text: "Volume:"
        label_text = menu_font.render("Volume:", True, GOLD)
        screen.blit(label_text, (cx - label_text.get_width()//2, label_y))

        # slider balk
        pygame.draw.rect(screen, GOLD, (slider_x, slider_y, slider_width, slider_height), border_radius=3)

        # slider knop 
        pygame.draw.circle(screen, GOLD, (knob_x, knob_y), knob_radius)

        # percentage text
        percent = int(volume * 100)
        percent_text = menu_font.render(f"{percent}%", True, GOLD)
        screen.blit(percent_text, (slider_x + slider_width + 20, slider_y - 12))

        # EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if fullscreen_rect.collidepoint(mx, my):
                    pygame.display.toggle_fullscreen()

                elif back_rect.collidepoint(mx, my):
                    return "back"

                elif quit_rect.collidepoint(mx, my):
                    return "quit"

                elif (mx - knob_x)**2 + (my - knob_y)**2 <= knob_radius**2:
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
