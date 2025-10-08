import pygame

def main_menu(screen, screen_width, screen_height, menu_font, colors, clock=None, title_font=None):
    BLACK = colors.get("BLACK", (0,0,0))
    GOLD = colors.get("GOLD", (212,175,55))
    BG = colors.get("BG", (30,30,30))

    if clock is None:
        clock = pygame.time.Clock()
    fps = 60

    if title_font is None:
        title_font = pygame.font.Font(None, 96)

    while True:
        screen.fill(BG)

        title_text = title_font.render("Game", True, GOLD)
        start_text = menu_font.render("Start Game", True, BLACK)
        options_text = menu_font.render("Options", True, BLACK)
        quit_text = menu_font.render("Quit", True, BLACK)

        # center title
        screen.blit(title_text, (screen_width//2 - title_text.get_width()//2, 50))

        # button rects (centered horizontally)
        start_rect = pygame.Rect(screen_width//2 - start_text.get_width()//2 - 10, 300-10, start_text.get_width()+20, start_text.get_height()+20)
        options_rect = pygame.Rect(screen_width//2 - options_text.get_width()//2 - 10, 420-10, options_text.get_width()+20, options_text.get_height()+20)
        quit_rect = pygame.Rect(screen_width//2 - quit_text.get_width()//2 - 10, 540-10, quit_text.get_width()+20, quit_text.get_height()+20)

        pygame.draw.rect(screen, GOLD, start_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, options_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, quit_rect, border_radius=15)

        screen.blit(start_text, (screen_width//2 - start_text.get_width()//2, 300))
        screen.blit(options_text, (screen_width//2 - options_text.get_width()//2, 420))
        screen.blit(quit_text, (screen_width//2 - quit_text.get_width()//2, 540))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # toggle fullscreen like your original behavior
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if start_rect.collidepoint(mx, my):
                    return "game"
                if options_rect.collidepoint(mx, my):
                    return "options"
                if quit_rect.collidepoint(mx, my):
                    pygame.quit()
                    return "quit"

        pygame.display.flip()
        clock.tick(fps)