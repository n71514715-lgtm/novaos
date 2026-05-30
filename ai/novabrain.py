#!/usr/bin/env python3
# NovaBrain — NovaOS Local AI Daemon
# Zero cloud. Zero telemetry. Runs entirely on-device.
# Engine: llama.cpp | Model: Phi-3 Mini (3.8B) | RAM: ~4GB

import os
import sys
import json
import time
import socket
import threading
import subprocess
from pathlib import Path
from datetime import datetime

VERSION = "0.1-alpha"
NOVA_HOME = Path("/etc/nova")
BRAIN_HOME = Path("/opt/novabrain")
MODEL_PATH = BRAIN_HOME / "models" / "phi3-mini.gguf"
LLAMA_BIN = BRAIN_HOME / "llama.cpp" / "build" / "bin" / "llama-cli"
SOCKET_PATH = "/tmp/novabrain.sock"
LOG_PATH = "/var/log/novabrain.log"
MEMORY_PATH = BRAIN_HOME / "memory" / "knowledge.json"

SYSTEM_PROMPT = """You are NovaBrain, the intelligent core of NovaOS.
You run entirely on the user's device. You never send data to the cloud.
You are private, fast, and honest. You help with any task.
You know you are running on NovaOS — a privacy-first, encrypted operating system.
Keep responses concise and useful."""

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except:
        pass

def banner():
    print(f"""
╔══════════════════════════════════════════════╗
║   NovaBrain v{VERSION} — Local AI Daemon          ║
║   Privacy: Maximum | Cloud: None | RAM: ~4GB ║
╚══════════════════════════════════════════════╝
    Model: Phi-3 Mini (3.8B parameters)
    Engine: llama.cpp
    Socket: {SOCKET_PATH}
""")

def check_model():
    if not MODEL_PATH.exists():
        log(f"[!] Model not found at {MODEL_PATH}")
        log("[*] Run: novabrain --download-model")
        return False
    size = MODEL_PATH.stat().st_size / (1024**3)
    log(f"[OK] Model found: {MODEL_PATH.name} ({size:.1f}GB)")
    return True

def check_llama():
    if not LLAMA_BIN.exists():
        log(f"[!] llama.cpp not found at {LLAMA_BIN}")
        log("[*] Run: novabrain --install-engine")
        return False
    log(f"[OK] llama.cpp engine found")
    return True

def query_model(prompt, max_tokens=512):
    if not check_llama() or not check_model():
        return "NovaBrain engine not yet installed. Run: novabrain --install-engine"
    full_prompt = f"<|system|>{SYSTEM_PROMPT}<|end|><|user|>{prompt}<|end|><|assistant|>"
    cmd = [
        str(LLAMA_BIN),
        "-m", str(MODEL_PATH),
        "-p", full_prompt,
        "-n", str(max_tokens),
        "--temp", "0.7",
        "--top-p", "0.9",
        "-t", "8",
        "--no-display-prompt", "--simple-io", "--simple-io", "--simple-io", "--simple-io", "--simple-io", "--simple-io", "--simple-io", "--simple-io",
        "-s", "42"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Response timeout — try a shorter query"
    except Exception as e:
        return f"Engine error: {e}"

def save_memory(query, response):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory = []
    if MEMORY_PATH.exists():
        try:
            with open(MEMORY_PATH) as f:
                memory = json.load(f)
        except:
            pass
    memory.append({
        "time": datetime.now().isoformat(),
        "query": query,
        "response": response[:200]
    })
    memory = memory[-1000:]
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)

def interactive_mode():
    banner()
    log("[*] NovaBrain interactive mode — type 'exit' to quit")
    print("\nType your query (or 'exit' to quit):\n")
    while True:
        try:
            query = input("nova> ").strip()
            if query.lower() in ("exit", "quit", "q"):
                print("NovaBrain shutting down.")
                break
            if not query:
                continue
            log(f"[>] Query: {query[:50]}...")
            start = time.time()
            response = query_model(query)
            elapsed = time.time() - start
            print(f"\n{response}\n")
            log(f"[<] Response in {elapsed:.1f}s")
            save_memory(query, response)
        except KeyboardInterrupt:
            print("\nNovaBrain shutting down.")
            break

def download_model():
    BRAIN_HOME.joinpath("models").mkdir(parents=True, exist_ok=True)
    log("[*] Downloading Phi-3 Mini (GGUF Q4 — ~2.4GB)...")
    url = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
    cmd = ["wget", "-q", "--show-progress", "-O", str(MODEL_PATH), url]
    log(f"[*] Saving to: {MODEL_PATH}")
    os.execvp("wget", cmd)

def install_engine():
    BRAIN_HOME.mkdir(parents=True, exist_ok=True)
    log("[*] Installing llama.cpp engine...")
    os.chdir(str(BRAIN_HOME))
    cmds = [
        ["git", "clone", "--depth=1", "https://github.com/ggerganov/llama.cpp"],
        ["make", "-C", "llama.cpp", "-j8", "llama-cli"]
    ]
    for cmd in cmds:
        log(f"[*] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            log(f"[!] Failed: {' '.join(cmd)}")
            sys.exit(1)
    log("[OK] llama.cpp engine installed")

def show_status():
    banner()
    print(f"  Engine:  {'[OK]' if check_llama() else '[MISSING]'}")
    print(f"  Model:   {'[OK]' if check_model() else '[MISSING — run: novabrain --download-model]'}")
    print(f"  Memory:  {MEMORY_PATH}")
    print(f"  Log:     {LOG_PATH}")
    print(f"  Socket:  {SOCKET_PATH}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--install-engine" in args:
        install_engine()
    elif "--download-model" in args:
        download_model()
    elif "--status" in args:
        show_status()
    elif "--query" in args:
        idx = args.index("--query")
        if idx + 1 < len(args):
            print(query_model(args[idx + 1]))
    else:
        interactive_mode()
