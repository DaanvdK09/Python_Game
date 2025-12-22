import pygame

def pause_menu(screen, screen_width, screen_height, menu_font, colors, clock=None, title_font=None):
    BLACK = colors.get("BLACK", (0,0,0))
    GOLD = colors.get("GOLD", (212,175,55))
    BG = colors.get("BG", (30,30,30))

    if clock is None:
        clock = pygame.time.Clock()
    title_font = title_font or pygame.font.Font(None, 72)
    fps = 60

    while True:
        screen.fill(BG)

        sw = screen.get_width()
        sh = screen.get_height()
        cx = sw // 2

        title_text = title_font.render("PAUSED", True, GOLD)
        resume_text = menu_font.render("Resume Game", True, BLACK)
        save_text = menu_font.render("Save Game", True, BLACK)
        options_text = menu_font.render("Options", True, BLACK)
        menu_text = menu_font.render("Main Menu", True, BLACK)

        title_y = int(sh * 0.2)
        resume_y = sh // 2 - 90
        save_y = resume_y + 60
        options_y = save_y + 60
        menu_y = options_y + 60

        resume_rect = pygame.Rect(cx - resume_text.get_width()//2 - 10, resume_y - 10, resume_text.get_width()+20, resume_text.get_height()+20)
        save_rect = pygame.Rect(cx - save_text.get_width()//2 - 10, save_y - 10, save_text.get_width()+20, save_text.get_height()+20)
        options_rect = pygame.Rect(cx - options_text.get_width()//2 - 10, options_y - 10, options_text.get_width()+20, options_text.get_height()+20)
        menu_rect = pygame.Rect(cx - menu_text.get_width()//2 - 10, menu_y - 10, menu_text.get_width()+20, menu_text.get_height()+20)

        pygame.draw.rect(screen, GOLD, resume_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, save_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, options_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, menu_rect, border_radius=15)

        screen.blit(title_text, (cx - title_text.get_width()//2, title_y))
        screen.blit(resume_text, (cx - resume_text.get_width()//2, resume_y))
        screen.blit(save_text, (cx - save_text.get_width()//2, save_y))
        screen.blit(options_text, (cx - options_text.get_width()//2, options_y))
        screen.blit(menu_text, (cx - menu_text.get_width()//2, menu_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "game"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if resume_rect.collidepoint(mx, my):
                    return "game"
                if save_rect.collidepoint(mx, my):
                    return "save"
                if options_rect.collidepoint(mx, my):
                    return "pause options"
                if menu_rect.collidepoint(mx, my):
                    return "menu"

        pygame.display.flip()
        clock.tick(fps)