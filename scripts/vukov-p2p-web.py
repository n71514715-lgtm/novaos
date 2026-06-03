#!/usr/bin/env python3
# nova-p2p-web — NovaOS Tor Hidden Service
# Host anonymous websites from your device
# .onion address — untraceable, uncensorable
# No hosting fees. No domain registration. No identity.

import os, sys, json, subprocess, time, shutil
from pathlib import Path

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

HIDDEN_DIR = Path.home() / ".nova" / "p2p-web"
SITES_DIR = HIDDEN_DIR / "sites"
TOR_HS_DIR = Path("/var/lib/tor/nova-hidden-service")
TOR_CONF = Path("/etc/tor/torrc")
DEFAULT_PORT = 8080

def banner():
    print(f"""{PURPLE}
  ╔══════════════════════════════════════════════╗
  ║   nova-p2p-web — Tor Hidden Service          ║
  ║   Host .onion sites from your device         ║
  ║   Uncensorable. Untraceable. Yours.          ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def setup_hidden_service():
    print(f"{CYAN}[*]{RESET} Setting up Tor hidden service...")
    HIDDEN_DIR.mkdir(parents=True, exist_ok=True)
    SITES_DIR.mkdir(parents=True, exist_ok=True)
    hs_config = f"""
# NovaOS Hidden Service
HiddenServiceDir {TOR_HS_DIR}
HiddenServicePort 80 127.0.0.1:{DEFAULT_PORT}
"""
    try:
        current = TOR_CONF.read_text() if TOR_CONF.exists() else ""
        if "nova-hidden-service" not in current:
            subprocess.run(f'echo "{hs_config}" | sudo tee -a {TOR_CONF}',
                         shell=True, capture_output=True)
        subprocess.run(f"sudo mkdir -p {TOR_HS_DIR} && sudo chown debian-tor:debian-tor {TOR_HS_DIR} && sudo chmod 700 {TOR_HS_DIR}",
                      shell=True, capture_output=True)
        subprocess.run("sudo service tor restart", shell=True, capture_output=True)
        time.sleep(5)
        onion_file = TOR_HS_DIR / "hostname"
        if onion_file.exists():
            onion = subprocess.run(f"sudo cat {onion_file}", shell=True,
                                  capture_output=True, text=True).stdout.strip()
            print(f"{GREEN}[✓]{RESET} Hidden service configured")
            print(f"{GREEN}[✓]{RESET} Your .onion address:")
            print(f"\n  {BOLD}{PURPLE}{onion}{RESET}\n")
            config = {"onion": onion, "port": DEFAULT_PORT}
            (HIDDEN_DIR / "config.json").write_text(json.dumps(config, indent=2))
            return onion
        else:
            print(f"{CYAN}[*]{RESET} Tor is generating your .onion address...")
            print(f"{DIM}  This takes 30-60 seconds on first run{RESET}")
            for i in range(12):
                time.sleep(5)
                if onion_file.exists():
                    onion = subprocess.run(f"sudo cat {onion_file}", shell=True,
                                          capture_output=True, text=True).stdout.strip()
                    print(f"{GREEN}[✓]{RESET} Your .onion address: {BOLD}{PURPLE}{onion}{RESET}")
                    config = {"onion": onion, "port": DEFAULT_PORT}
                    (HIDDEN_DIR / "config.json").write_text(json.dumps(config, indent=2))
                    return onion
                print(f"  {DIM}Waiting... ({(i+1)*5}s){RESET}")
            print(f"{RED}[!]{RESET} Timeout — check: sudo cat {onion_file}")
    except Exception as e:
        print(f"{RED}[!]{RESET} Error: {e}")
    return None

def create_site(name):
    site_dir = SITES_DIR / name
    site_dir.mkdir(parents=True, exist_ok=True)
    index_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{name} — NovaOS Hidden Site</title>
<style>
  body {{ background: #08080f; color: #e0e0ff; font-family: monospace; padding: 2rem; }}
  h1 {{ color: #00c896; }}
  .onion {{ color: #7c6aff; font-size: 0.8rem; }}
  footer {{ color: #444; margin-top: 3rem; font-size: 0.75rem; }}
</style>
</head>
<body>
  <h1>⬡ {name}</h1>
  <p>This site is hosted on NovaOS via Tor hidden service.</p>
  <p>Uncensorable. Untraceable. Private.</p>
  <footer>
    Hosted on NovaOS 0.1 (Spectre) · PRIVATA · LIBERA · SECURA
  </footer>
</body>
</html>"""
    (site_dir / "index.html").write_text(index_html)
    print(f"{GREEN}[✓]{RESET} Site created: {site_dir}")
    print(f"{CYAN}[i]{RESET} Edit: {site_dir}/index.html")
    return site_dir

def serve_site(name):
    site_dir = SITES_DIR / name
    if not site_dir.exists():
        print(f"{RED}[!]{RESET} Site not found: {name}")
        print(f"  Create with: nova p2p-web create {name}")
        return
    config_file = HIDDEN_DIR / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        onion = config.get("onion", "unknown")
        print(f"{GREEN}[✓]{RESET} Serving: {site_dir}")
        print(f"{PURPLE}[✓]{RESET} .onion: {BOLD}{onion}{RESET}")
        print(f"{CYAN}[*]{RESET} Starting web server on port {DEFAULT_PORT}...")
        print(f"{DIM}  Press Ctrl+C to stop{RESET}\n")
    os.chdir(site_dir)
    subprocess.run([sys.executable, "-m", "http.server", str(DEFAULT_PORT)])

def show_onion():
    config_file = HIDDEN_DIR / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        print(f"\n  {BOLD}{PURPLE}{config.get('onion','Not configured yet')}{RESET}\n")
    else:
        print(f"{RED}[!]{RESET} Not configured. Run: nova p2p-web setup")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova p2p-web <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {PURPLE}setup{RESET}              Configure Tor hidden service")
    print(f"  {PURPLE}create{RESET} <name>       Create a new site")
    print(f"  {PURPLE}serve{RESET} <name>        Serve a site over Tor")
    print(f"  {PURPLE}onion{RESET}               Show your .onion address")
    print(f"\n{GREEN}Example:{RESET}")
    print(f"  nova p2p-web setup")
    print(f"  nova p2p-web create mysite")
    print(f"  nova p2p-web serve mysite")
    print(f"  # Share your .onion address — site is live on Tor")
    print(f"\n{PURPLE}  Uncensorable. Untraceable. Yours.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":    cmd_help()
elif args[0]=="setup":             setup_hidden_service()
elif args[0]=="create":            create_site(args[1] if len(args)>1 else "mysite")
elif args[0]=="serve":             serve_site(args[1] if len(args)>1 else "mysite")
elif args[0]=="onion":             show_onion()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
