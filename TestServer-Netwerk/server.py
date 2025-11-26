# server.py
import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 12345

clients = []           # lijst van (conn, addr, id)
positions = {}         # id -> [x, y]
clients_lock = threading.Lock()

def broadcast_positions():
    """Stuur actuele positions dict naar alle clients (als JSON + newline)."""
    data = json.dumps({"type": "positions", "positions": positions}) + "\n"
    with clients_lock:
        for conn, addr, cid in clients[:]:
            try:
                conn.sendall(data.encode())
            except Exception:
                print("Verbinding verbroken met", addr)
                try:
                    conn.close()
                except:
                    pass
                clients.remove((conn, addr, cid))
                if cid in positions:
                    del positions[cid]

def handle_client(conn, addr, cid):
    """Lees berichten van één client en update positions."""
    print(f"[+] Client {cid} verbonden vanaf {addr}")
    # stuur meteen toegewezen id naar client
    try:
        conn.sendall((json.dumps({"type": "id", "id": cid}) + "\n").encode())
    except Exception as e:
        print("Kon id niet sturen:", e)
        return

    fileobj = conn.makefile('r')  # zo kunnen we per-regel lezen
    try:
        for line in fileobj:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "pos":
                # verwacht: {"type":"pos","x":..., "y":...}
                positions[cid] = [int(msg.get("x", 0)), int(msg.get("y", 0))]
                broadcast_positions()
            elif msg.get("type") == "quit":
                break
    except Exception as e:
        print("Fout met client", cid, e)
    finally:
        print(f"[-] Client {cid} verbreekt verbinding")
        with clients_lock:
            # verwijder client en pos
            for entry in clients:
                if entry[2] == cid:
                    try:
                        entry[0].close()
                    except:
                        pass
                    clients.remove(entry)
                    break
            if cid in positions:
                del positions[cid]
        broadcast_positions()

def accept_loop(s):
    next_id = 0
    while True:
        conn, addr = s.accept()
        with clients_lock:
            cid = next_id
            next_id += 1
            clients.append((conn, addr, cid))
            # initialiseer positie (spreid startposities)
            positions[cid] = [50 + cid * 200, 140]
        t = threading.Thread(target=handle_client, args=(conn, addr, cid), daemon=True)
        t.start()
        broadcast_positions()

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(4)
    print("Server gestart op", HOST, PORT)
    accept_loop(s)

if __name__ == "__main__":
    main()
