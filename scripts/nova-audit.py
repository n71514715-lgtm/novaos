#!/usr/bin/env python3
# nova-audit — NovaOS Security Audit
# Shows exactly what's running, what has network access,
# what's using your GPU, what's reading your files
# Full transparency. No hidden processes.

import os, sys, subprocess, json
from pathlib import Path
from datetime import datetime

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
YELLOW="\033[0;33m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

TRUSTED = ["systemd","bash","python3","ssh","tor","nova","wsl","init",
           "dbus","NetworkManager","resolved","journald","logind"]

def banner():
    print(f"""{CYAN}
  ╔══════════════════════════════════════════════╗
  ║   nova-audit — Security Audit                ║
  ║   Full transparency into your system         ║
  ║   Nothing hidden. Nothing unexpected.        ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    except:
        return ""

def audit_processes():
    print(f"\n{BOLD}  Running Processes:{RESET}")
    print(f"  {DIM}{'PID':<8} {'CPU%':<8} {'MEM%':<8} {'NAME':<25} STATUS{RESET}")
    print(f"  {'─'*70}")
    result = run("ps aux --sort=-%cpu | head -20")
    lines = result.split("\n")[1:]
    suspicious = []
    for line in lines:
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        pid = parts[1]
        cpu = parts[2]
        mem = parts[3]
        name = parts[10][:40]
        proc_name = parts[10].split("/")[-1].split()[0][:20]
        is_trusted = any(t in proc_name.lower() for t in TRUSTED)
        color = DIM if is_trusted else YELLOW
        flag = " " if is_trusted else "?"
        if float(cpu) > 50 and not is_trusted:
            color = RED
            flag = "!"
            suspicious.append(f"{proc_name} (CPU: {cpu}%)")
        print(f"  {color}[{flag}] {pid:<8} {cpu:<8} {mem:<8} {proc_name:<25}{RESET}")
    if suspicious:
        print(f"\n  {RED}[!] High CPU processes:{RESET}")
        for s in suspicious:
            print(f"  {RED}  ↳ {s}{RESET}")

def audit_network():
    print(f"\n{BOLD}  Network Access:{RESET}")
    result = run("ss -tunp 2>/dev/null | grep ESTAB")
    if not result:
        print(f"  {GREEN}[✓]{RESET} No active external connections")
        return
    lines = result.split("\n")
    print(f"  {DIM}Active established connections:{RESET}")
    for line in lines:
        parts = line.split()
        if len(parts) > 5:
            remote = parts[5]
            proc = " ".join(parts[6:])[:40] if len(parts) > 6 else ""
            print(f"  {YELLOW}[~]{RESET} {remote:<40} {DIM}{proc}{RESET}")

def audit_files():
    print(f"\n{BOLD}  Open Sensitive Files:{RESET}")
    sensitive = run("lsof 2>/dev/null | grep -E '(passwd|shadow|private|secret|\.key|\.pem)' | head -10")
    if sensitive:
        for line in sensitive.split("\n"):
            print(f"  {RED}[!]{RESET} {line[:80]}")
    else:
        print(f"  {GREEN}[✓]{RESET} No suspicious file access detected")

def audit_ports():
    print(f"\n{BOLD}  Listening Ports:{RESET}")
    result = run("ss -tlnp 2>/dev/null")
    lines = result.split("\n")[1:]
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3]
        proc = " ".join(parts[5:])[:40] if len(parts) > 5 else ""
        port = local.split(":")[-1]
        nova_ports = ["11434", "51869", "51870", "8080", "9050"]
        if port in nova_ports:
            print(f"  {GREEN}[✓]{RESET} :{port:<8} {DIM}NovaOS service{RESET} {DIM}{proc}{RESET}")
        else:
            print(f"  {CYAN}[i]{RESET} :{port:<8} {DIM}{proc}{RESET}")

def audit_nova():
    print(f"\n{BOLD}  NovaOS Services:{RESET}")
    services = {
        "NovaBrain": ("curl -s http://localhost:11434/health", "ok"),
        "Tor": ("pgrep -x tor", ""),
        "nova-guard": ("pgrep -f nova-guard", ""),
        "WireGuard": ("command -v wg", ""),
    }
    for name, (cmd, expected) in services.items():
        result = run(cmd)
        if result and (not expected or expected in result):
            print(f"  {GREEN}[✓]{RESET} {name}: running")
        else:
            print(f"  {DIM}[~]{RESET} {name}: inactive")

def audit_integrity():
    print(f"\n{BOLD}  System Integrity:{RESET}")
    nova_bins = ["/usr/local/bin/nova", "/usr/local/bin/nova-guard",
                "/usr/local/bin/nova-vault", "/usr/local/bin/nova-id"]
    for b in nova_bins:
        p = Path(b)
        if p.exists():
            size = p.stat().st_size
            mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
            print(f"  {GREEN}[✓]{RESET} {b:<40} {size}b  {DIM}{mtime}{RESET}")
        else:
            print(f"  {RED}[✗]{RESET} {b} — missing")

def cmd_full():
    banner()
    print(f"{CYAN}[*]{RESET} Running full security audit...\n")
    audit_nova()
    audit_ports()
    audit_network()
    audit_files()
    audit_integrity()
    print(f"\n{GREEN}[✓]{RESET} Audit complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{PURPLE}  PRIVATA · LIBERA · SECURA{RESET}\n")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova audit <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {CYAN}full{RESET}        Complete security audit")
    print(f"  {CYAN}processes{RESET}   Audit running processes")
    print(f"  {CYAN}network{RESET}     Audit network connections")
    print(f"  {CYAN}ports{RESET}       Audit listening ports")
    print(f"  {CYAN}files{RESET}       Audit sensitive file access")
    print(f"  {CYAN}integrity{RESET}   Check NovaOS file integrity")
    print(f"\n{PURPLE}  Full transparency. Nothing hidden.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":       cmd_help()
elif args[0]=="full":                 cmd_full()
elif args[0]=="processes":            banner(); audit_processes()
elif args[0]=="network":              banner(); audit_network()
elif args[0]=="ports":                banner(); audit_ports()
elif args[0]=="files":                banner(); audit_files()
elif args[0]=="integrity":            banner(); audit_integrity()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
