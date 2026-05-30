#!/usr/bin/env python3
# nova-guard — NovaOS Real-time Encryption Watchdog
# Monitors directories and auto-encrypts new files
# No other OS has this built in at system level

import os
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

VERSION = "0.1"
GUARD_CONFIG = Path.home() / ".nova" / "guard.json"
LOG_FILE = Path.home() / ".nova" / "guard.log"
CRYPT = "/mnt/d/NovaOS/encryption/nova-crypt.sh"
GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
RED = "\033[0;31m"
RESET = "\033[0m"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def banner():
    print(f"""{GREEN}
╔══════════════════════════════════════════╗
║   nova-guard v{VERSION} — Encryption Watchdog  ║
║   Monitoring your files in real-time     ║
║   PRIVATA · LIBERA · SECURA              ║
╚══════════════════════════════════════════╝{RESET}""")

def load_config():
    if GUARD_CONFIG.exists():
        with open(GUARD_CONFIG) as f:
            return json.load(f)
    return {"watched": [], "encrypted": [], "keyfile": ""}

def save_config(config):
    GUARD_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(GUARD_CONFIG, "w") as f:
        json.dump(config, f, indent=2)

def get_file_hash(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    except:
        return None

def encrypt_file(filepath, keyfile):
    try:
        result = subprocess.run(
            ["bash", CRYPT, "encrypt", filepath, filepath + ".nova", keyfile],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            os.remove(filepath)
            log(f"[✓] Auto-encrypted: {filepath}")
            return True
        else:
            log(f"[!] Failed to encrypt: {filepath}")
            return False
    except Exception as e:
        log(f"[!] Error: {e}")
        return False

def watch_directory(watch_path, keyfile, auto_encrypt=False):
    watch_path = Path(watch_path)
    if not watch_path.exists():
        print(f"{RED}[!] Directory not found: {watch_path}{RESET}")
        return

    log(f"[*] Watching: {watch_path}")
    log(f"[*] Auto-encrypt: {auto_encrypt}")
    log(f"[*] Keyfile: {keyfile}")

    known_files = {}
    for f in watch_path.rglob("*"):
        if f.is_file() and not str(f).endswith(".nova"):
            known_files[str(f)] = get_file_hash(f)

    print(f"{CYAN}[*]{RESET} Monitoring {len(known_files)} existing files")
    print(f"{CYAN}[*]{RESET} Press Ctrl+C to stop\n")

    try:
        while True:
            current_files = {}
            for f in watch_path.rglob("*"):
                if f.is_file() and not str(f).endswith(".nova"):
                    current_files[str(f)] = get_file_hash(f)

            # Detect new files
            for filepath, filehash in current_files.items():
                if filepath not in known_files:
                    log(f"[!] New file detected: {filepath}")
                    if auto_encrypt and keyfile:
                        encrypt_file(filepath, keyfile)
                    else:
                        print(f"{RED}[!] UNENCRYPTED FILE: {filepath}{RESET}")

            # Detect modified files
            for filepath, filehash in current_files.items():
                if filepath in known_files and known_files[filepath] != filehash:
                    log(f"[~] File modified: {filepath}")

            known_files = current_files
            time.sleep(2)

    except KeyboardInterrupt:
        log("[*] nova-guard stopped")
        print(f"\n{GREEN}[✓]{RESET} Guard stopped cleanly")

def show_status():
    config = load_config()
    print(f"{GREEN}╔══════════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║   nova-guard Status                      ║{RESET}")
    print(f"{GREEN}╚══════════════════════════════════════════╝{RESET}")
    print(f"  Watched dirs: {len(config['watched'])}")
    print(f"  Encrypted:    {len(config['encrypted'])} files")
    if LOG_FILE.exists():
        print(f"  Log:          {LOG_FILE}")
    else:
        print(f"  Log:          no activity yet")

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "help":
        banner()
        print("Usage: nova-guard <command> [options]")
        print("")
        print("Commands:")
        print("  watch <dir> [keyfile]   Monitor directory for new files")
        print("  watch <dir> --auto      Monitor and auto-encrypt new files")
        print("  status                  Show guard status")
        print("")
        print("Examples:")
        print("  nova-guard watch ~/Documents")
        print("  nova-guard watch ~/Documents --auto my.key")
        print("  nova-guard status")
    elif args[0] == "watch":
        banner()
        if len(args) < 2:
            print(f"{RED}[!] Specify directory to watch{RESET}")
            sys.exit(1)
        directory = args[1]
        auto = "--auto" in args
        keyfile = args[3] if auto and len(args) > 3 else ""
        watch_directory(directory, keyfile, auto_encrypt=auto)
    elif args[0] == "status":
        show_status()
    else:
        print(f"{RED}[!] Unknown command: {args[0]}{RESET}")
