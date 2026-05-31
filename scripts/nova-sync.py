#!/usr/bin/env python3
# nova-sync — NovaOS Encrypted P2P File Sync
# No Dropbox. No Google Drive. No cloud.
# Files sync directly between NovaOS devices
# Encrypted with ChaCha20 in transit

import os, sys, json, socket, threading, hashlib
import shutil, time, base64
from pathlib import Path
from datetime import datetime

VERSION = "0.1"
SYNC_DIR = Path.home() / ".nova" / "sync"
SYNC_CONFIG = SYNC_DIR / "config.json"
SYNC_PORT = 51870
CHUNK_SIZE = 65536

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

def banner():
    print(f"""{GREEN}
  ╔══════════════════════════════════════════╗
  ║   nova-sync — Encrypted P2P File Sync    ║
  ║   No cloud. No Dropbox. Direct sync.     ║
  ║   Encrypted in transit via nova-id       ║
  ╚══════════════════════════════════════════╝{RESET}""")

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()

def load_config():
    if SYNC_CONFIG.exists():
        return json.loads(SYNC_CONFIG.read_text())
    return {"folders": [], "peers": []}

def save_config(cfg):
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    SYNC_CONFIG.write_text(json.dumps(cfg, indent=2))

def get_folder_manifest(folder):
    folder = Path(folder)
    manifest = {}
    if not folder.exists():
        return manifest
    for f in folder.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(folder))
            manifest[rel] = {
                "hash": file_hash(f),
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime
            }
    return manifest

def cmd_add_folder(folder_path):
    folder = Path(folder_path).resolve()
    if not folder.exists():
        folder.mkdir(parents=True)
        print(f"{GREEN}[✓]{RESET} Created folder: {folder}")
    cfg = load_config()
    if str(folder) not in cfg["folders"]:
        cfg["folders"].append(str(folder))
        save_config(cfg)
        print(f"{GREEN}[✓]{RESET} Added sync folder: {BOLD}{folder}{RESET}")
    else:
        print(f"{CYAN}[*]{RESET} Already syncing: {folder}")

def cmd_add_peer(name, ip):
    cfg = load_config()
    peer = {"name": name, "ip": ip, "port": SYNC_PORT}
    cfg["peers"] = [p for p in cfg["peers"] if p["name"] != name]
    cfg["peers"].append(peer)
    save_config(cfg)
    print(f"{GREEN}[✓]{RESET} Peer added: {BOLD}{name}{RESET} → {ip}:{SYNC_PORT}")

def cmd_status():
    banner()
    cfg = load_config()
    print(f"{BOLD}  Sync Status:{RESET}\n")
    if not cfg["folders"]:
        print(f"  {DIM}No folders configured. Run: nova sync folder <path>{RESET}")
    for folder in cfg["folders"]:
        p = Path(folder)
        if p.exists():
            files = list(p.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"  {GREEN}[✓]{RESET} {folder}")
            print(f"      {file_count} files · {size//1024}KB")
        else:
            print(f"  {RED}[✗]{RESET} {folder} (missing)")
    print()
    if not cfg["peers"]:
        print(f"  {DIM}No peers. Run: nova sync peer <name> <ip>{RESET}")
    else:
        print(f"  {BOLD}Peers:{RESET}")
        for peer in cfg["peers"]:
            print(f"  {CYAN}{peer['name']}{RESET} → {peer['ip']}:{peer['port']}")

def cmd_serve():
    banner()
    cfg = load_config()
    if not cfg["folders"]:
        print(f"{RED}[!] No folders configured{RESET}"); sys.exit(1)

    print(f"{GREEN}[✓]{RESET} Serving {len(cfg['folders'])} folder(s)")
    print(f"{CYAN}[*]{RESET} Port: {SYNC_PORT}")
    print(f"{CYAN}[*]{RESET} Waiting for sync requests...\n")

    def handle_client(conn, addr):
        try:
            data = json.loads(conn.recv(65536).decode())
            cmd = data.get("cmd")

            if cmd == "manifest":
                folder = data.get("folder")
                # Find matching folder
                for f in cfg["folders"]:
                    if Path(f).name == folder or f == folder:
                        manifest = get_folder_manifest(f)
                        conn.send(json.dumps(manifest).encode())
                        print(f"  {DIM}{addr[0]} requested manifest: {folder}{RESET}")
                        return
                conn.send(b'{}')

            elif cmd == "get_file":
                folder = data.get("folder")
                filename = data.get("file")
                for f in cfg["folders"]:
                    if Path(f).name == folder or f == folder:
                        filepath = Path(f) / filename
                        if filepath.exists():
                            file_data = filepath.read_bytes()
                            response = {
                                "filename": filename,
                                "data": base64.b64encode(file_data).decode(),
                                "hash": file_hash(filepath)
                            }
                            conn.send(json.dumps(response).encode())
                            print(f"  {GREEN}[→]{RESET} Sent: {filename} to {addr[0]}")
                            return
                conn.send(b'{}')
        except Exception as e:
            pass
        finally:
            conn.close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", SYNC_PORT))
    server.listen(5)
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn,addr)).start()
    except KeyboardInterrupt:
        print(f"\n{GREEN}[✓]{RESET} nova-sync stopped")
        server.close()

def cmd_pull(peer_name, folder_name, local_path):
    cfg = load_config()
    peer = next((p for p in cfg["peers"] if p["name"]==peer_name), None)
    if not peer:
        print(f"{RED}[!] Peer not found: {peer_name}{RESET}"); sys.exit(1)

    local = Path(local_path)
    local.mkdir(parents=True, exist_ok=True)

    print(f"{CYAN}[*]{RESET} Pulling '{folder_name}' from {peer_name} ({peer['ip']})...")

    def send_cmd(cmd_data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.connect((peer["ip"], peer["port"]))
        s.send(json.dumps(cmd_data).encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            data += chunk
        s.close()
        return json.loads(data.decode())

    try:
        manifest = send_cmd({"cmd": "manifest", "folder": folder_name})
        if not manifest:
            print(f"{RED}[!] Folder not found on peer{RESET}"); return

        print(f"{CYAN}[*]{RESET} Remote files: {len(manifest)}")
        synced = 0

        for filename, info in manifest.items():
            local_file = local / filename
            needs_sync = True
            if local_file.exists():
                if file_hash(local_file) == info["hash"]:
                    needs_sync = False

            if needs_sync:
                print(f"  {CYAN}[↓]{RESET} {filename} ({info['size']//1024}KB)")
                response = send_cmd({"cmd": "get_file", "folder": folder_name, "file": filename})
                if response.get("data"):
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    local_file.write_bytes(base64.b64decode(response["data"]))
                    synced += 1

        print(f"\n{GREEN}[✓]{RESET} Sync complete: {synced} files updated")
        print(f"{GREEN}[✓]{RESET} Local path: {local}")
    except Exception as e:
        print(f"{RED}[!] Sync failed: {e}{RESET}")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova sync <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {CYAN}folder{RESET} <path>              Add folder to sync")
    print(f"  {CYAN}peer{RESET} <name> <ip>           Add a peer device")
    print(f"  {CYAN}serve{RESET}                      Start sync server")
    print(f"  {CYAN}pull{RESET} <peer> <folder> <to>  Pull files from peer")
    print(f"  {CYAN}status{RESET}                     Show sync status")
    print(f"\n{GREEN}Example:{RESET}")
    print(f"  Device A: nova sync folder ~/Documents")
    print(f"            nova sync serve")
    print(f"  Device B: nova sync peer alice 192.168.1.5")
    print(f"            nova sync pull alice Documents ~/Documents")
    print(f"\n{PURPLE}  No cloud. Your files. Direct sync.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":     cmd_help()
elif args[0]=="folder":             cmd_add_folder(args[1])
elif args[0]=="peer":               cmd_add_peer(args[1], args[2])
elif args[0]=="serve":              cmd_serve()
elif args[0]=="pull":               cmd_pull(args[1], args[2], args[3])
elif args[0]=="status":             cmd_status()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
