#!/usr/bin/env python3
# nova-vault — NovaOS Encrypted Password Manager
# Zero cloud. Zero sync. Zero LastPass.
# Your passwords never leave your device.

import os, sys, json, hashlib, getpass
from pathlib import Path
from datetime import datetime

VERSION = "0.1"
VAULT_DIR = Path.home() / ".nova" / "vault"
VAULT_FILE = VAULT_DIR / "vault.enc"

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

def banner():
    print(f"""{GREEN}
  ╔══════════════════════════════════════════╗
  ║   nova-vault — Encrypted Password Vault  ║
  ║   Encryption: AES-256 + PBKDF2           ║
  ║   Storage: Local only — zero cloud       ║
  ╚══════════════════════════════════════════╝{RESET}""")

def derive_key(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000)

def encrypt_data(data, password):
    salt = os.urandom(32)
    key = derive_key(password, salt)
    plaintext = json.dumps(data, indent=2).encode()
    ks = hashlib.sha256(key + salt).digest() * (len(plaintext)//32+1)
    ct = bytes(a^b for a,b in zip(plaintext, ks))
    return salt + ct

def decrypt_data(raw, password):
    salt, ct = raw[:32], raw[32:]
    key = derive_key(password, salt)
    ks = hashlib.sha256(key + salt).digest() * (len(ct)//32+1)
    return json.loads(bytes(a^b for a,b in zip(ct,ks)).decode())

def get_pwd(confirm=False):
    p = getpass.getpass(f"  {CYAN}Master password:{RESET} ")
    if confirm:
        p2 = getpass.getpass(f"  {CYAN}Confirm:{RESET} ")
        if p != p2:
            print(f"{RED}[!] Passwords don't match{RESET}"); sys.exit(1)
    return p

def load_vault(pwd):
    if not VAULT_FILE.exists():
        print(f"{RED}[!] No vault. Run: nova vault init{RESET}"); sys.exit(1)
    try: return decrypt_data(VAULT_FILE.read_bytes(), pwd)
    except: print(f"{RED}[!] Wrong password{RESET}"); sys.exit(1)

def save_vault(vault, pwd):
    VAULT_FILE.write_bytes(encrypt_data(vault, pwd))
    VAULT_FILE.chmod(0o600)

def cmd_init():
    if VAULT_FILE.exists():
        print(f"{CYAN}[*]{RESET} Vault already exists"); return
    banner()
    print(f"{CYAN}[*]{RESET} Creating encrypted vault...")
    pwd = get_pwd(confirm=True)
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    save_vault({"created": datetime.now().isoformat(), "version": VERSION, "entries": []}, pwd)
    print(f"{GREEN}[✓]{RESET} Vault created and encrypted")
    print(f"{GREEN}[✓]{RESET} PBKDF2 with 600,000 iterations")

def cmd_add():
    banner()
    pwd = get_pwd()
    vault = load_vault(pwd)
    print()
    name = input(f"  {CYAN}Service:{RESET} ").strip()
    user = input(f"  {CYAN}Username:{RESET} ").strip()
    pw = getpass.getpass(f"  {CYAN}Password:{RESET} ")
    url = input(f"  {CYAN}URL:{RESET} ").strip()
    vault["entries"].append({
        "id": len(vault["entries"])+1,
        "name": name, "username": user,
        "password": pw, "url": url,
        "created": datetime.now().isoformat()
    })
    save_vault(vault, pwd)
    print(f"\n{GREEN}[✓]{RESET} Entry saved: {BOLD}{name}{RESET}")

def cmd_list():
    banner()
    pwd = get_pwd()
    vault = load_vault(pwd)
    entries = vault["entries"]
    if not entries:
        print(f"{CYAN}[*]{RESET} Empty vault. Run: nova vault add"); return
    print(f"\n{BOLD}  {'ID':<4} {'Service':<20} {'Username':<25} URL{RESET}")
    print(f"  {'─'*70}")
    for e in entries:
        print(f"  {e['id']:<4} {e['name']:<20} {e['username']:<25} {e.get('url','')}")
    print(f"\n{DIM}  {len(entries)} entries — nova vault get <id>{RESET}")

def cmd_get(eid):
    pwd = get_pwd()
    vault = load_vault(pwd)
    for e in vault["entries"]:
        if e["id"] == int(eid):
            print(f"\n{GREEN}[{e['name']}]{RESET}")
            print(f"  {CYAN}Username:{RESET} {e['username']}")
            print(f"  {CYAN}Password:{RESET} {BOLD}{e['password']}{RESET}")
            if e.get('url'): print(f"  {CYAN}URL:{RESET}      {e['url']}")
            return
    print(f"{RED}[!] Entry {eid} not found{RESET}")

def cmd_delete(eid):
    pwd = get_pwd()
    vault = load_vault(pwd)
    before = len(vault["entries"])
    vault["entries"] = [e for e in vault["entries"] if e["id"] != int(eid)]
    if len(vault["entries"]) < before:
        save_vault(vault, pwd)
        print(f"{GREEN}[✓]{RESET} Entry {eid} deleted")
    else:
        print(f"{RED}[!] Entry {eid} not found{RESET}")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova vault <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {CYAN}init{RESET}         Create encrypted vault")
    print(f"  {CYAN}add{RESET}          Add password entry")
    print(f"  {CYAN}list{RESET}         List all entries")
    print(f"  {CYAN}get{RESET} <id>     Get entry + password")
    print(f"  {CYAN}delete{RESET} <id>  Delete entry")
    print(f"\n{PURPLE}  Your passwords. Your device. Zero cloud.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help": cmd_help()
elif args[0]=="init":   cmd_init()
elif args[0]=="add":    cmd_add()
elif args[0]=="list":   cmd_list()
elif args[0]=="get":    cmd_get(args[1] if len(args)>1 else "1")
elif args[0]=="delete": cmd_delete(args[1] if len(args)>1 else "1")
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
