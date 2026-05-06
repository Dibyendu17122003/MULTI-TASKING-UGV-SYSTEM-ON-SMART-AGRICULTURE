# =========================================================
# client2.py  
# ROLE:
#   SOLO MODE:
#     Problem Analysis + ALL Solutions (LLM only)
#   DATA SHARING MODE:
#     Client1 Solution → Tasks → Auction + Prioritized A*
# =========================================================

import socket
import json
import struct
import os
import sys
import time
import logging
import re
import random
import base64
import mimetypes

# ---------------------------------------------------------
# PROJECT ROOT RESOLUTION
# ---------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

# ---------------------------------------------------------
# CONFIG + LLM
# ---------------------------------------------------------
from config import (
    SERVER_HOST,
    SERVER_PORT,
    SOCKET_TIMEOUT_SECONDS,
    MAX_SOCKET_RETRIES,
    MODEL_CLIENT2
)

from llm_processor import analyze_image_and_text

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
HEADER_LEN_SIZE = 4
SOLO_LOG_DIR = os.path.join(PROJECT_ROOT, "storage", "client2_solo")

AGENTS = {
    "client1": {"role": "perception", "capability": 3},
    "client2": {"role": "planner",    "capability": 5},
    "client3": {"role": "executor",   "capability": 4}
}

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
    header = json.dumps({"type": "MESSAGE", "content_length": len(body)}).encode()
    sock.sendall(struct.pack(">I", len(header)))
    sock.sendall(header)
    sock.sendall(body)

def connect_with_retries():
    for _ in range(MAX_SOCKET_RETRIES):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(SOCKET_TIMEOUT_SECONDS)
            s.connect((SERVER_HOST, SERVER_PORT))
            return s
        except socket.error:
            time.sleep(2)
    raise ConnectionError("Server unreachable")

# ---------------------------------------------------------
# IMAGE UTILS (GLOBAL PATH SAFE)
# ---------------------------------------------------------
def image_to_base64(path):
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ---------------------------------------------------------
# INPUT COLLECTION (SAME AS CLIENT1)
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
    print("\n--- CLIENT 2 INPUT ---")

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
# PROMPT (IDENTICAL STRUCTURE TO CLIENT1)
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
    mime = mime or "image/jpeg"

    return analyze_image_and_text(
        base64_image=img64,
        user_text=build_prompt(data),
        is_multimodal=True,
        mime_type=mime,
        model_override=MODEL_CLIENT2
    )

# ---------------------------------------------------------
# SOLO MODE (🔥 NOW IDENTICAL TO CLIENT1)
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

    print("✅ Client2 solo report saved")

# ---------------------------------------------------------
# DATA SHARING MODE (UNCHANGED – PLANNING ONLY HERE)
# ---------------------------------------------------------
def extract_tasks(text):
    tasks = []
    for line in text.splitlines():
        if re.match(r"^(\d+\.|\-|\•)", line.strip()):
            tasks.append(line.lstrip("0123456789.-• ").strip())
    return tasks or ["Inspect crops", "Apply treatment", "Monitor recovery"]

def auction_allocate(tasks):
    allocation = {a: [] for a in AGENTS}
    for task in tasks:
        bids = {
            a: random.randint(1, 5) + random.randint(1, 5) - meta["capability"]
            for a, meta in AGENTS.items()
        }
        allocation[min(bids, key=bids.get)].append(task)
    return allocation

def generate_task_plan(text):
    tasks = extract_tasks(text)
    allocation = auction_allocate(tasks)

    report = "FINAL MULTI-AGENT TASK PLAN\n\n"
    for agent, jobs in allocation.items():
        report += f"{agent.upper()} ({AGENTS[agent]['role']}):\n"
        for j in jobs:
            report += f" - {j}\n"
        report += "\n"
    return report

def data_sharing_mode():
    sock = connect_with_retries()
    print(sock.recv(1024).decode())
    sock.sendall(b"client2\n")

    prefix = recv_all(sock, HEADER_LEN_SIZE)
    header_len = struct.unpack(">I", prefix)[0]
    header = json.loads(recv_all(sock, header_len))
    solution_text = recv_all(sock, header["content_length"]).decode()

    plan = generate_task_plan(solution_text)
    send_string(sock, plan)

    print("📤 Task plan sent")
    sock.close()

# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------
def main():
    while True:
        print("\n--- CLIENT 2 MODE ---")
        print("1. Solo Mode (Problem + All Solutions)")
        print("2. Data Sharing Mode (Client1 → Planning)")
        print("QUIT to exit")

        c = input("Select: ").strip().upper()
        if c == "1":
            solo_mode()
        elif c == "2":
            data_sharing_mode()
        elif c == "QUIT":
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
