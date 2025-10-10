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

    while True:
        screen.fill(BG)

        sw = screen.get_width()
        sh = screen.get_height()
        cx = sw // 2

        title_text = title_font.render("Options", True, GOLD)
        fullscreen_text = menu_font.render("Toggle Fullscreen", True, BLACK)
        back_text = menu_font.render("Back", True, BLACK)
        quit_text = menu_font.render("Quit", True, BLACK)

        title_y = int(sh * 0.12)
        fullscreen_y = sh // 2 - 60
        back_y = fullscreen_y + 120
        quit_y = back_y + 120

        fullscreen_rect = pygame.Rect(cx - fullscreen_text.get_width()//2 - 10, fullscreen_y - 10,
                                      fullscreen_text.get_width() + 20, fullscreen_text.get_height() + 20)
        back_rect = pygame.Rect(cx - back_text.get_width()//2 - 10, back_y - 10,
                                back_text.get_width() + 20, back_text.get_height() + 20)
        quit_rect = pygame.Rect(cx - quit_text.get_width()//2 - 10, quit_y - 10,
                                quit_text.get_width() + 20, quit_text.get_height() + 20)

        pygame.draw.rect(screen, GOLD, fullscreen_rect, border_radius=12)
        pygame.draw.rect(screen, GOLD, back_rect, border_radius=12)
        pygame.draw.rect(screen, GOLD, quit_rect, border_radius=12)

        screen.blit(title_text, (cx - title_text.get_width()//2, title_y))
        screen.blit(fullscreen_text, (cx - fullscreen_text.get_width()//2, fullscreen_y))
        screen.blit(back_text, (cx - back_text.get_width()//2, back_y))
        screen.blit(quit_text, (cx - quit_text.get_width()//2, quit_y))

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
                    # toggle fullscreen immediately
                    pygame.display.toggle_fullscreen()
                elif back_rect.collidepoint(mx, my):
                    return "back"
                elif quit_rect.collidepoint(mx, my):
                    return "quit"

        pygame.display.flip()
        clock.tick(fps)