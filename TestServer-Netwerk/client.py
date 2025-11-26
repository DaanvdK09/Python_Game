# client.py
import socket
import threading
import json
import pygame
import sys
import math

SERVER_IP = '127.0.0.1'
PORT = 12345

WIDTH, HEIGHT = 500, 350
BLOCK_SIZE = 30
BULLET_SIZE = 6
SPEED = 4
BULLET_SPEED = 8

positions = {}    # id -> [x, y]
bullets = {}      # id -> lijst van [x, y, vx, vy]
my_id = None
pos_lock = threading.Lock()
sock = None


def net_recv_loop():
    global my_id
    fileobj = sock.makefile('r')
    try:
        for line in fileobj:
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "id":
                my_id = msg.get("id")
                print("Mijn id:", my_id)
            elif msg.get("type") == "positions":
                with pos_lock:
                    positions.clear()
                    for k, v in msg.get("positions", {}).items():
                        if isinstance(v, dict):
                            positions[int(k)] = v.get("pos", [0, 0])
                            bullets[int(k)] = v.get("bullets", [])
                        else:
                            positions[int(k)] = v
    except Exception as e:
        print("Netwerkfout:", e)
    finally:
        print("Netwerk thread stopt")


def send_state(x, y):
    try:
        msg = json.dumps({"type": "pos", "x": int(x), "y": int(y)}) + "\n"
        sock.sendall(msg.encode())
    except Exception as e:
        print("Kon data niet sturen:", e)


def main():
    global sock, my_id
    sock = socket.socket()
    try:
        sock.connect((SERVER_IP, PORT))
    except Exception as e:
        print("Kon server niet bereiken:", e)
        return

    t = threading.Thread(target=net_recv_loop, daemon=True)
    t.start()

    import time
    timeout = 3.0
    t0 = time.time()
    while my_id is None and time.time() - t0 < timeout:
        time.sleep(0.01)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Multiplayer - Crosshair & Hits")

    clock = pygame.time.Clock()
    myx, myy = 50, HEIGHT // 2 - BLOCK_SIZE // 2
    my_bullets = []

    send_state(myx, myy)
    running = True
    while running:
        dt = clock.tick(60)
        moved = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Richting naar muis berekenen
                mx, my = pygame.mouse.get_pos()
                dx = mx - (myx + BLOCK_SIZE / 2)
                dy = my - (myy + BLOCK_SIZE / 2)
                length = math.hypot(dx, dy)
                if length == 0:
                    continue
                dx /= length
                dy /= length
                bx = myx + BLOCK_SIZE / 2
                by = myy + BLOCK_SIZE / 2
                my_bullets.append([bx, by, dx * BULLET_SPEED, dy * BULLET_SPEED])

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            myx -= SPEED
            moved = True
        if keys[pygame.K_RIGHT]:
            myx += SPEED
            moved = True
        if keys[pygame.K_UP]:
            myy -= SPEED
            moved = True
        if keys[pygame.K_DOWN]:
            myy += SPEED
            moved = True

        # Beweeg kogels
        for b in my_bullets:
            b[0] += b[2]
            b[1] += b[3]

        # Verwijder kogels buiten scherm
        my_bullets = [b for b in my_bullets if 0 < b[0] < WIDTH and 0 < b[1] < HEIGHT]

        # Check botsing met andere spelers
        hit_bullets = []
        with pos_lock:
            for cid, (px, py) in list(positions.items()):
                if cid == my_id:
                    continue
                for b in my_bullets:
                    if (px < b[0] < px + BLOCK_SIZE) and (py < b[1] < py + BLOCK_SIZE):
                        print(f"💥 Speler {cid} is geraakt!")
                        hit_bullets.append(b)   # deze kogel verwijderen
                        del positions[cid]      # speler verdwijnt
                        break

        # Verwijder kogels die geraakt hebben
        my_bullets = [b for b in my_bullets if b not in hit_bullets]

        myx = max(0, min(WIDTH - BLOCK_SIZE, myx))
        myy = max(0, min(HEIGHT - BLOCK_SIZE, myy))

        send_state(myx, myy)

        with pos_lock:
            positions[my_id] = [myx, myy]

        screen.fill((0, 0, 0))

        # teken spelers
        with pos_lock:
            for cid, p in positions.items():
                color = (0, 200, 0) if cid == my_id else (200, 0, 0)
                pygame.draw.rect(screen, color, (*p, BLOCK_SIZE, BLOCK_SIZE))
                font = pygame.font.SysFont(None, 20)
                img = font.render(str(cid), True, (200, 200, 200))
                screen.blit(img, (p[0], p[1] - 18))

        # teken kogels
        for bx, by, vx, vy in my_bullets:
            pygame.draw.rect(screen, (255, 255, 0), (bx, by, BULLET_SIZE, BULLET_SIZE))

        # teken crosshair
        mx, my = pygame.mouse.get_pos()
        pygame.draw.line(screen, (255, 255, 255), (mx - 6, my), (mx + 6, my), 1)
        pygame.draw.line(screen, (255, 255, 255), (mx, my - 6), (mx, my + 6), 1)

        pygame.display.flip()

    try:
        sock.sendall((json.dumps({"type": "quit"}) + "\n").encode())
    except:
        pass
    sock.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
