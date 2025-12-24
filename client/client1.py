# =========================================================
# client1.py  (FINAL – ARCHITECTURE CONSISTENT)
# ROLE:
#   SOLO MODE        -> Problem Analysis + ALL Solutions
#   DATA SHARING     -> Problem Analysis + ALL Solutions -> Client2
# =========================================================

import socket
import json
import struct
import os
import sys
import base64
import time
import logging
import mimetypes

# ---------------------------------------------------------
# PATH SETUP (FORCE PROJECT ROOT)
# ---------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from config import (
    SERVER_HOST,
    SERVER_PORT,
    SOCKET_TIMEOUT_SECONDS,
    C2_WAIT_TIMEOUT_SECONDS,
    MAX_SOCKET_RETRIES,
    MODEL_CLIENT1
)

from llm_processor import analyze_image_and_text

# ---------------------------------------------------------
# CONSTANTS (CENTRALIZED STORAGE)
# ---------------------------------------------------------
HEADER_LEN_SIZE = 4
SOLO_LOG_DIR = os.path.join(PROJECT_ROOT, "storage", "client1_solo")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s"
)

# ---------------------------------------------------------
# SOCKET UTILITIES
# ---------------------------------------------------------
def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError("Socket closed")
        data.extend(packet)
    return bytes(data)

def send_string(sock, text):
    body = text.encode("utf-8")
    header = json.dumps({
        "type": "MESSAGE",
        "content_length": len(body)
    }).encode()

    sock.sendall(struct.pack(">I", len(header)))
    sock.sendall(header)
    sock.sendall(body)

def connect_with_retries():
    for attempt in range(MAX_SOCKET_RETRIES):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(SOCKET_TIMEOUT_SECONDS)
            s.connect((SERVER_HOST, SERVER_PORT))
            return s
        except socket.error as e:
            logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    raise ConnectionError("Unable to connect to server")

# ---------------------------------------------------------
# IMAGE UTILS (GLOBAL PATH SAFE)
# ---------------------------------------------------------
def image_to_base64(path):
    path = os.path.expanduser(path)
    path = os.path.abspath(path)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ---------------------------------------------------------
# INPUT COLLECTION
# ---------------------------------------------------------
def opt(prompt, cast=str):
    val = input(f"{prompt} (optional): ").strip()
    if not val:
        return None
    try:
        return cast(val)
    except ValueError:
        raise ValueError(f"Invalid value for {prompt}")

def collect_inputs():
    print("\n--- CLIENT 1 INPUT ---")

    image_path = input("Image path (MANDATORY): ").strip()
    if not image_path:
        raise ValueError("Image path is required")

    return {
        "image_path": image_path,
        "temperature": opt("Temperature °C", float),
        "humidity": opt("Humidity %", int),
        "wind_speed": opt("Wind speed km/h", float),
        "wind_direction": opt("Wind direction"),
        "soil_moisture": opt("Soil moisture %", float),
        "soil_ph": opt("Soil pH", float),
        "light_intensity": opt("Light intensity lux", float),
        "latitude": opt("Latitude", float),
        "longitude": opt("Longitude", float),
        "time": opt("Time HH:MM")
    }

# ---------------------------------------------------------
# PROMPT
# ---------------------------------------------------------
def build_prompt(d):
    def f(v, u=""):
        return f"{v}{u}" if v is not None else "N/A"

    context = (
        f"[TIME {f(d['time'])}] "
        f"[GPS {f(d['latitude'])},{f(d['longitude'])}] "
        f"[TEMP {f(d['temperature'],'°C')}] "
        f"[HUMIDITY {f(d['humidity'],'%')}] "
        f"[WIND {f(d['wind_speed'],'km/h')} {f(d['wind_direction'])}] "
        f"[SOIL {f(d['soil_moisture'],'%')} pH {f(d['soil_ph'])}] "
        f"[LIGHT {f(d['light_intensity'],'lux')}] "
    )

    instruction = (
        "Analyze the crop image and environmental data carefully.\n\n"
        "STRICT OUTPUT FORMAT:\n\n"
        "SECTION 1: PROBLEM ANALYSIS\n"
        "- Describe crop condition, disease or stress.\n"
        "- Mention visible symptoms and probable causes.\n\n"
        "SECTION 2: ALL POSSIBLE SOLUTIONS\n"
        "- List ALL viable solutions (chemical, biological, mechanical, environmental).\n"
        "- Mention precautions where necessary.\n"
        "- DO NOT divide tasks.\n"
        "- DO NOT assign jobs.\n"
        "- DO NOT create schedules.\n"
    )

    return context + instruction

# ---------------------------------------------------------
# LLM CALL
# ---------------------------------------------------------
def run_llm(data):
    img64 = image_to_base64(data["image_path"])
    mime, _ = mimetypes.guess_type(data["image_path"])
    if not mime:
        mime = "image/jpeg"

    return analyze_image_and_text(
        base64_image=img64,
        user_text=build_prompt(data),
        is_multimodal=True,
        mime_type=mime,
        model_override=MODEL_CLIENT1
    )

# ---------------------------------------------------------
# SOLO MODE
# ---------------------------------------------------------
def solo_mode():
    os.makedirs(SOLO_LOG_DIR, exist_ok=True)

    data = collect_inputs()
    result = run_llm(data)

    print("\n--- SOLO MODE OUTPUT ---\n")
    print(result)

    ts = time.strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(SOLO_LOG_DIR, f"solo_{ts}.log"), "w", encoding="utf-8") as f:
        f.write(result)

    print("✅ Solo report saved")

# ---------------------------------------------------------
# DATA SHARING MODE
# ---------------------------------------------------------
def data_sharing_mode():
    sock = connect_with_retries()
    print(sock.recv(1024).decode())
    sock.sendall(b"client1\n")

    data = collect_inputs()
    result = run_llm(data)

    send_string(sock, result)
    print("📤 Problem + ALL solutions sent to Client2")

    sock.settimeout(C2_WAIT_TIMEOUT_SECONDS)

    prefix = recv_all(sock, HEADER_LEN_SIZE)
    header_len = struct.unpack(">I", prefix)[0]
    header = json.loads(recv_all(sock, header_len))
    final = recv_all(sock, header["content_length"]).decode()

    print("\n--- RESPONSE FROM PIPELINE ---\n")
    print(final)

    sock.close()

# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------
def main():
    while True:
        print("\n--- CLIENT 1 MODE ---")
        print("1. Solo Mode (Problem + All Solutions)")
        print("2. Data Sharing Mode (Send to Client2)")
        print("QUIT to exit")

        choice = input("Select: ").strip().upper()
        if choice == "1":
            solo_mode()
        elif choice == "2":
            data_sharing_mode()
        elif choice == "QUIT":
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
