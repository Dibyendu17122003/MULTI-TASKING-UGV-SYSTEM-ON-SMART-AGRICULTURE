# =========================================================
# server.py  (FINAL – FIXED & RELIABLE)
# Central Message Router with Buffering
# =========================================================

import socket
import threading
import json
import struct
import logging
import os
from datetime import datetime
from collections import defaultdict, deque

from config import SERVER_HOST, SERVER_PORT

# =================================================
# CONSTANTS
# =================================================
HEADER_LEN_SIZE = 4
STORAGE_DIR = "storage"

# =================================================
# LOGGING
# =================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# =================================================
# CLIENT REGISTRY & MESSAGE BUFFERS
# =================================================
clients = {}                          # client_id -> socket
message_queue = defaultdict(deque)   # client_id -> queued packets

# =================================================
# SOCKET UTILITIES
# =================================================
def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionResetError("Socket closed")
        data.extend(packet)
    return bytes(data)

def send_packet(sock, packet):
    sock.sendall(packet)

# =================================================
# LOG STORAGE
# =================================================
def save_log(sender, receiver, content):
    log_dir = os.path.join(STORAGE_DIR, f"{sender}_to_{receiver}")
    os.makedirs(log_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(log_dir, f"{sender}_{receiver}_{ts}.log")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Sender    : {sender}\n")
        f.write(f"Receiver  : {receiver}\n")
        f.write(f"Timestamp : {datetime.now().isoformat()}\n")
        f.write(f"Size      : {len(content)} bytes\n")
        f.write("-" * 60 + "\n\n")
        f.write(content)

    logging.info(f"[LOG SAVED] {path}")

# =================================================
# ROUTING LOGIC
# =================================================
def get_target(sender):
    if sender == "client1":
        return "client2"
    elif sender == "client2":
        return "client3"
    return "client1"

# =================================================
# CLIENT HANDLER
# =================================================
def handle_client(conn, addr):
    client_id = None
    try:
        conn.sendall(b"Enter client ID (client1 / client2 / client3): ")
        client_id = conn.recv(1024).decode().strip()

        if client_id not in ("client1", "client2", "client3"):
            conn.close()
            return

        clients[client_id] = conn
        logging.info(f"[CONNECTED] {client_id} @ {addr}")
        logging.info(f"[INFO] {client_id} ready (solo or data-sharing mode)")

        # -------------------------------------------------
        # DELIVER ANY QUEUED MESSAGES
        # -------------------------------------------------
        if message_queue[client_id]:
            logging.info(
                f"[DELIVERY] Sending {len(message_queue[client_id])} queued messages to {client_id}"
            )
            while message_queue[client_id]:
                packet = message_queue[client_id].popleft()
                send_packet(conn, packet)

        # -------------------------------------------------
        # MAIN RECEIVE LOOP
        # -------------------------------------------------
        while True:
            prefix = recv_all(conn, HEADER_LEN_SIZE)
            header_len = struct.unpack(">I", prefix)[0]

            header_data = recv_all(conn, header_len)
            header = json.loads(header_data.decode("utf-8"))

            body = recv_all(conn, header["content_length"])
            message = body.decode("utf-8")

            packet = prefix + header_data + body

            target = get_target(client_id)

            logging.info(
                f"{client_id} → {target} | {header['content_length']} bytes"
            )

            if target in clients:
                send_packet(clients[target], packet)
            else:
                message_queue[target].append(packet)
                logging.warning(
                    f"[BUFFERED] {target} offline — message queued"
                )

            save_log(client_id, target, message)

    except (ConnectionResetError, ConnectionAbortedError, struct.error):
        logging.warning(f"[DISCONNECTED] {client_id}")

    except Exception as e:
        logging.error(f"[ERROR] {client_id}: {e}")

    finally:
        conn.close()
        if client_id:
            clients.pop(client_id, None)
            logging.info(f"[CLEANUP] {client_id} removed")

# =================================================
# SERVER START
# =================================================
def start_server():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(10)

    logging.info(f"🚀 Server running on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()

if __name__ == "__main__":
    start_server()
