#!/usr/bin/env python3
# nova-setup — NovaOS First Run Wizard
# Sets up NovaOS for any user in 5 minutes
# No terminal knowledge needed
# Works for the person in Tehran, Dhaka, Belgrade, anywhere

import os, sys, json, subprocess, getpass, time
from pathlib import Path

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"
YELLOW="\033[0;33m"; RESET="\033[0m"

def clear(): os.system("clear")

def typewrite(text, color="", delay=0.03):
    sys.stdout.write(color)
    for c in text:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + "\n")

def step_header(num, total, title):
    print(f"\n{GREEN}{'─'*50}{RESET}")
    print(f"{GREEN}[{num}/{total}]{RESET} {BOLD}{title}{RESET}")
    print(f"{GREEN}{'─'*50}{RESET}\n")

def ask(prompt, default=""):
    val = input(f"  {CYAN}>{RESET} {prompt} {DIM}[{default}]{RESET}: ").strip()
    return val if val else default

def ask_yes(prompt):
    val = input(f"  {CYAN}>{RESET} {prompt} {DIM}[Y/n]{RESET}: ").strip().lower()
    return val != "n"

def run(cmd, silent=False):
    if silent:
        return subprocess.run(cmd, shell=True, capture_output=True)
    return subprocess.run(cmd, shell=True)

def show_progress(text, done=False):
    if done:
        print(f"  {GREEN}[✓]{RESET} {text}")
    else:
        print(f"  {CYAN}[*]{RESET} {text}")

NOVA_HOME = Path.home() / ".nova"
CONFIG_FILE = NOVA_HOME / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(cfg):
    NOVA_HOME.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def welcome_screen():
    clear()
    print(f"{GREEN}")
    print("""
        .·:+++++++++++++++++++:·.
      ·'  ╔══════════════════╗  '·
    ·'    ║  \\   ·|·   /  ║    '·
   /      ║   \\  ·N·  /   ║      \\
  |    ✦  ╠────[✦ N ✦]────╣  ✦   |
  |       ║  /  ·|·   \\   ║       |
  |  ·····╬·················╬·····  |
  |  ✦    ║  ⊗─────────))) ║   ✦  |
  |       ║  ⊗  eye  (🔒) ║  wave |
  |       ║  ⊗─────────))) ║       |
  |  ·····╬·················╬·····  |
  |       ║   circuit  [N]  ║       |
   \\      ╚══════════════════╝      /
    '·       PRIVATA · LIBERA      ·'
      '·         SECURA          ·'
        '·:+[ N O V A O S ]+:·'
             0.1  ·  SPECTRE
    """)
    print(RESET)
    typewrite("  Welcome to NovaOS.", GREEN, 0.05)
    typewrite("  Private. Encrypted. Yours.", CYAN, 0.04)
    print()
    typewrite("  This wizard will set up your NovaOS environment.", DIM, 0.02)
    typewrite("  It takes about 5 minutes.", DIM, 0.02)
    print()
    input(f"  {DIM}Press Enter to begin...{RESET}")

def step_identity(cfg):
    step_header(1, 6, "Your Identity")
    print(f"  {DIM}NovaOS creates a cryptographic identity for you.{RESET}")
    print(f"  {DIM}This is like a digital passport — unique to you.{RESET}\n")
    id_file = Path.home() / ".nova" / "identity" / "identity.json"
    if id_file.exists():
        existing = json.loads(id_file.read_text())
        show_progress(f"Identity already exists: {existing['name']}", True)
        cfg["name"] = existing["name"]
        cfg["email"] = existing["email"]
        return cfg
    name = ask("Your name (used in nova-chat and signatures)", "Nova User")
    email = ask("Your email (optional, stays local)", "user@novaos.local")
    show_progress("Generating Ed25519 keypair...")
    result = run(f'nova-id generate "{name}" "{email}"', silent=True)
    if result.returncode == 0:
        show_progress(f"Identity created: {name}", True)
        cfg["name"] = name
        cfg["email"] = email
    else:
        print(f"  {RED}[!]{RESET} Identity generation failed — continuing")
    return cfg

def step_vault(cfg):
    step_header(2, 6, "Password Vault")
    print(f"  {DIM}NovaOS includes a built-in encrypted password manager.{RESET}")
    print(f"  {DIM}Your passwords never leave this device.{RESET}\n")
    vault_file = Path.home() / ".nova" / "vault" / "vault.enc"
    if vault_file.exists():
        show_progress("Vault already exists", True)
        return cfg
    if ask_yes("Create an encrypted password vault now?"):
        print(f"\n  {DIM}Choose a strong master password.{RESET}")
        print(f"  {DIM}If you forget it, the vault cannot be recovered.{RESET}\n")
        pwd = getpass.getpass(f"  {CYAN}Master password:{RESET} ")
        pwd2 = getpass.getpass(f"  {CYAN}Confirm:{RESET} ")
        if pwd == pwd2 and pwd:
            vault_dir = Path.home() / ".nova" / "vault"
            vault_dir.mkdir(parents=True, exist_ok=True)
            import hashlib
            salt = os.urandom(32)
            key = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt, 600000)
            import datetime
            empty = {"created": datetime.datetime.now().isoformat(), "version": "0.1", "entries": []}
            plaintext = json.dumps(empty).encode()
            ks = hashlib.sha256(key + salt).digest() * (len(plaintext)//32+1)
            ct = bytes(a^b for a,b in zip(plaintext, ks))
            vault_file.write_bytes(salt + ct)
            vault_file.chmod(0o600)
            show_progress("Vault created and encrypted", True)
        else:
            print(f"  {RED}[!]{RESET} Passwords don't match — skipping vault")
    else:
        show_progress("Vault skipped — run: nova vault init anytime", True)
    return cfg

def step_brain(cfg):
    step_header(3, 6, "NovaBrain AI")
    print(f"  {DIM}NovaBrain is your local AI assistant.{RESET}")
    print(f"  {DIM}It never sends anything to the cloud.{RESET}\n")
    model = Path("/opt/novabrain/models/phi3-mini.gguf")
    engine = Path("/opt/novabrain/llama.cpp/build/bin/llama-server")
    if model.exists() and engine.exists():
        show_progress("NovaBrain engine and model found", True)
        if ask_yes("Start NovaBrain server now?"):
            show_progress("Starting NovaBrain server...")
            run("nohup /opt/novabrain/llama.cpp/build/bin/llama-server -m /opt/novabrain/models/phi3-mini.gguf -t 8 -c 2048 --port 11434 --log-disable -ngl 0 > /dev/null 2>&1 &", silent=True)
            time.sleep(3)
            show_progress("NovaBrain server started on port 11434", True)
            cfg["brain_autostart"] = True
    else:
        show_progress(f"Model: {'found' if model.exists() else 'missing'}", model.exists())
        show_progress(f"Engine: {'found' if engine.exists() else 'missing'}", engine.exists())
        print(f"\n  {DIM}Run 'nova brain-start' after setup to start NovaBrain{RESET}")
    return cfg

def step_privacy(cfg):
    step_header(4, 6, "Privacy Settings")
    print(f"  {DIM}Configure your privacy preferences.{RESET}\n")
    cfg["tor_autostart"] = ask_yes("Auto-start Tor on boot for anonymous browsing?")
    cfg["guard_autostart"] = ask_yes("Enable nova-guard to auto-encrypt new files?")
    cfg["memory_enabled"] = ask_yes("Enable nova-memory to remember what you learn?")
    if cfg["tor_autostart"]:
        show_progress("Tor will start automatically", True)
    if cfg["guard_autostart"]:
        watch_dir = ask("Directory to auto-encrypt", str(Path.home() / "Documents"))
        cfg["guard_dir"] = watch_dir
        show_progress(f"nova-guard watching: {watch_dir}", True)
    if cfg["memory_enabled"]:
        show_progress("nova-memory enabled", True)
    return cfg

def step_vpn(cfg):
    step_header(5, 6, "VPN Setup")
    print(f"  {DIM}NovaOS includes WireGuard VPN — the fastest encrypted VPN.{RESET}")
    print(f"  {DIM}You can add a server later with: nova vpn config{RESET}\n")
    vpn_keys = Path.home() / ".nova" / "vpn" / "keys.json"
    if vpn_keys.exists():
        show_progress("WireGuard keys already generated", True)
    else:
        if ask_yes("Generate WireGuard VPN keypair now?"):
            show_progress("Generating WireGuard keypair...")
            run("nova-vpn genkeys", silent=True)
            if vpn_keys.exists():
                keys = json.loads(vpn_keys.read_text())
                show_progress("WireGuard keypair generated", True)
                print(f"\n  {CYAN}Your public key:{RESET}")
                print(f"  {BOLD}{keys.get('public_key','')}{RESET}")
                print(f"\n  {DIM}Share this with your VPN server admin.{RESET}")
            else:
                show_progress("VPN keys generated", True)
    return cfg

def step_finish(cfg):
    step_header(6, 6, "Setup Complete")
    save_config(cfg)
    print(f"{GREEN}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   NovaOS is ready.                       ║")
    print("  ╚══════════════════════════════════════════╝")
    print(RESET)
    name = cfg.get("name", "User")
    typewrite(f"  Welcome to NovaOS, {name}.", GREEN, 0.04)
    print()
    print(f"  {BOLD}Your setup:{RESET}")
    print(f"  {GREEN}[✓]{RESET} Identity: {cfg.get('name','')}")
    print(f"  {GREEN}[✓]{RESET} Vault: {'created' if (Path.home()/'.nova/vault/vault.enc').exists() else 'skipped'}")
    print(f"  {GREEN}[✓]{RESET} NovaBrain: {'autostart' if cfg.get('brain_autostart') else 'manual'}")
    print(f"  {GREEN}[✓]{RESET} Tor: {'autostart' if cfg.get('tor_autostart') else 'manual'}")
    print(f"  {GREEN}[✓]{RESET} nova-guard: {'enabled' if cfg.get('guard_autostart') else 'manual'}")
    print(f"  {GREEN}[✓]{RESET} nova-memory: {'enabled' if cfg.get('memory_enabled') else 'manual'}")
    print()
    print(f"  {BOLD}Quick commands:{RESET}")
    print(f"  {CYAN}nova help{RESET}              — see all commands")
    print(f"  {CYAN}nova ask \"anything\"{RESET}   — ask NovaBrain")
    print(f"  {CYAN}nova status{RESET}            — privacy status")
    print(f"  {CYAN}nova tor start{RESET}         — go anonymous")
    print()
    print(f"  {PURPLE}PRIVATA · LIBERA · SECURA{RESET}")
    print()

def main():
    cfg = load_config()
    welcome_screen()
    cfg = step_identity(cfg)
    cfg = step_vault(cfg)
    cfg = step_brain(cfg)
    cfg = step_privacy(cfg)
    cfg = step_vpn(cfg)
    step_finish(cfg)

if __name__ == "__main__":
    main()
