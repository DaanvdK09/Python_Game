import pygame
import os
import sys
from Characters.NPC import NPC
from pathlib import Path

base_dir = Path(__file__).parent.parent

def load_hospital_npcs(game_map):
    npcs = []
    tmx_objects = getattr(game_map, "objects", [])
    print("TMX Objects:", tmx_objects)  # Debug

    for obj in tmx_objects:
        print("Object name:", getattr(obj, "name", None))  # Debug
        if getattr(obj, "name", None) == "Nurse_Joy":
            nurse_path = os.path.join(base_dir.parent, "graphics", "characters", "Nurse_Joy.png")
            nurse = NPC(
                x=obj.x,
                y=obj.y,
                name="Nurse Joy",
                sprite_path=nurse_path,
                use_sprite_sheet=False,
                scale=0.5
            )
            npcs.append(nurse)
        elif getattr(obj, "name", None) == "Shopkeeper":
            shop_path = os.path.join(base_dir.parent, "graphics", "characters", "ShopKeeper.png")
            shop = NPC(
                x=obj.x,
                y=obj.y,
                name="Shopkeeper",
                sprite_path=shop_path,
                use_sprite_sheet=False,
                scale=0.25
            )
            npcs.append(shop)

    return npcs

SHOP_ITEMS = {
    "Pokéball": 200,
    "Potion": 300
}

def show_shop_menu(screen, npc, player, menu_font, small_font, colors, clock):
    shop_items = {
        "Pokéball": 200,
        "Potion": 300
    }

    items = list(shop_items.keys())
    selected = 0
    FPS = 60
    buying_quantity = 1  # Quantity to buy per transaction

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(items)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(items)
                elif event.key == pygame.K_RIGHT:
                    buying_quantity = min(buying_quantity + 1, 99)
                elif event.key == pygame.K_LEFT:
                    buying_quantity = max(buying_quantity - 1, 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    item_name = items[selected]
                    price = shop_items[item_name] * buying_quantity
                    if player.money >= price:
                        player.money -= price
                        if item_name in player.bag:
                            player.bag[item_name] += buying_quantity
                        else:
                            player.bag[item_name] = buying_quantity
                        # Reset quantity after purchase
                        buying_quantity = 1
                        npc.speak(f"Thank you for buying {item_name} x{buying_quantity}!")
                    else:
                        npc.speak("You don't have enough money!")
                elif event.key == pygame.K_ESCAPE:
                    return  # Close shop menu

        # Draw shop panel
        sw, sh = screen.get_size()
        panel_w = min(520, sw - 80)
        panel_h = min(360, sh - 120)
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h))
        panel.fill(colors.get('BG', (30, 30, 30)))

        # Title
        title_text = f"{npc.name}'s Shop"
        title = menu_font.render(title_text, True, colors.get('WHITE', (255,255,255)))
        panel.blit(title, (20, 12))

        # Player money
        money_text = small_font.render(f"Money: ${player.money}", True, colors.get('WHITE', (255,255,255)))
        panel.blit(money_text, (panel_w - money_text.get_width() - 20, 12))

        # Items
        list_start_y = 64
        list_item_h = 56
        visible = (panel_h - list_start_y - 20) // list_item_h
        start = max(0, selected - visible // 2)
        for i, name in enumerate(items[start:start + visible]):
            idx = start + i
            y = list_start_y + i * list_item_h
            item_rect = pygame.Rect(20, y, panel_w - 40, list_item_h - 8)

            # Highlight selected
            if idx == selected:
                pygame.draw.rect(panel, (80, 120, 160), item_rect)
            else:
                pygame.draw.rect(panel, (50, 50, 70), item_rect)
            pygame.draw.rect(panel, (120, 120, 140), item_rect, 1)

            # Item label with price
            label = small_font.render(f"{name} - ${shop_items[name]}", True, colors.get('WHITE', (255,255,255)))
            label_y = item_rect.y + max(0, (item_rect.height - label.get_height()) // 2)
            panel.blit(label, (item_rect.x + 8, label_y))

        # Quantity selector
        qty_text = small_font.render(f"Quantity: {buying_quantity}", True, colors.get('WHITE', (255,255,255)))
        panel.blit(qty_text, (20, panel_h - 40))

        # Draw panel
        screen.blit(panel, (px, py))
        pygame.display.flip()
        clock.tick(FPS)
