import pygame
import sys
import math

def show_level_up_screen(screen, pokemon, menu_font, small_font, colors, clock):
    import math
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    GOLD = colors.get("GOLD", (255, 215, 0))
    BG = colors.get("BG", (30, 30, 30))

    sw, sh = screen.get_size()

    # Animation variables
    start_time = pygame.time.get_ticks()
    animation_duration = 2000  # 2 seconds

    print(f"Showing level-up screen for {pokemon.name} (Level {pokemon.level})")  # Debug print

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z, pygame.K_x):
                    print("Level-up screen closed by user input")  # Debug print
                    return

        # Auto-close after animation
        if elapsed >= animation_duration:
            print("Level-up screen auto-closed after animation")  # Debug print
            return

        # Background
        screen.fill(BG)

        # Calculate animation progress
        progress = min(1.0, elapsed / animation_duration)

        # Pulsing effect for the text
        pulse = abs(math.sin(elapsed * 0.01)) * 0.3 + 0.7

        # Main level up text
        level_text = menu_font.render(f"{pokemon.name} leveled up!", True, GOLD)
        level_rect = level_text.get_rect(center=(sw // 2, sh // 2 - 60))

        # Scale effect
        scale = 1.0 + pulse * 0.2
        scaled_text = pygame.transform.scale(level_text,
                                           (int(level_text.get_width() * scale),
                                            int(level_text.get_height() * scale)))
        scaled_rect = scaled_text.get_rect(center=level_rect.center)
        screen.blit(scaled_text, scaled_rect)

        # Level info
        level_info = small_font.render(f"Level {pokemon.level}!", True, WHITE)
        level_info_rect = level_info.get_rect(center=(sw // 2, sh // 2))
        screen.blit(level_info, level_info_rect)

        # Stats increase info
        stats_text = small_font.render("HP +5, Attack +3", True, WHITE)
        stats_rect = stats_text.get_rect(center=(sw // 2, sh // 2 + 40))
        screen.blit(stats_text, stats_rect)

        # Continue hint (appears after 1 second)
        if elapsed > 1000:
            hint_alpha = min(255, (elapsed - 1000) * 0.5)
            hint_text = small_font.render("Press any key to continue", True, WHITE)
            hint_surface = pygame.Surface(hint_text.get_size())
            hint_surface.set_alpha(hint_alpha)
            hint_surface.blit(hint_text, (0, 0))
            hint_rect = hint_surface.get_rect(center=(sw // 2, sh // 2 + 100))
            screen.blit(hint_surface, hint_rect)

        pygame.display.flip()  # Update the screen
        clock.tick(60)

def show_xp_gain(screen, xp_amount, menu_font, colors, clock, duration=1500):
    BLACK = colors.get("BLACK", (0, 0, 0))
    WHITE = colors.get("WHITE", (255, 255, 255))
    GOLD = colors.get("GOLD", (255, 215, 0))
    
    sw, sh = screen.get_size()
    start_time = pygame.time.get_ticks()
    
    # Create XP text
    xp_text = menu_font.render(f"+{xp_amount} XP", True, GOLD)
    
    while pygame.time.get_ticks() - start_time < duration:
        elapsed = pygame.time.get_ticks() - start_time
        progress = elapsed / duration
        
        # Handle events to prevent freezing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Fade out effect
        alpha = int(255 * (1 - progress))
        xp_surface = pygame.Surface(xp_text.get_size())
        xp_surface.set_alpha(alpha)
        xp_surface.blit(xp_text, (0, 0))
        
        # Float up effect
        y_offset = -progress * 50
        xp_rect = xp_surface.get_rect(center=(sw // 2, sh // 2 + 150 + y_offset))
        
        screen.blit(xp_surface, xp_rect)
        pygame.display.flip()
        clock.tick(60)