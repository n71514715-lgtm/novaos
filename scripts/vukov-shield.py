#!/usr/bin/env python3
# nova-shield — NovaOS Real-time Network Monitor
# Shows exactly who is connecting to you and what's phoning home
# No other OS ships this as a built-in command
# Your network. Your control. Zero surprises.

import os, sys, json, time, socket, subprocess
from pathlib import Path
from datetime import datetime

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
YELLOW="\033[0;33m"; PURPLE="\033[0;35m"; BOLD="\033[1m"
DIM="\033[2m"; RESET="\033[0m"

VERSION = "0.1"

SUSPICIOUS_PORTS = {
    4444: "Metasploit", 5555: "Android ADB", 6666: "IRC/malware",
    6667: "IRC", 31337: "Elite/backdoor", 12345: "NetBus",
    27374: "SubSeven", 1234: "Ultors Trojan", 7777: "Tini backdoor"
}

TELEMETRY_DOMAINS = [
    "telemetry", "analytics", "tracking", "metrics", "stats",
    "collect", "monitor", "report", "crash", "diagnostic",
    "google-analytics", "doubleclick", "facebook.com", "amazon-adsystem"
]

def banner():
    print(f"""{GREEN}
  ╔══════════════════════════════════════════════╗
  ║   nova-shield — Network Monitor              ║
  ║   Real-time visibility into your network     ║
  ║   No surprises. No hidden connections.       ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def get_connections():
    try:
        result = subprocess.run(["ss", "-tunp"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")[1:]
        connections = []
        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                continue
            proto = parts[0]
            state = parts[1] if len(parts) > 1 else ""
            local = parts[4] if len(parts) > 4 else ""
            remote = parts[5] if len(parts) > 5 else ""
            process = " ".join(parts[6:]) if len(parts) > 6 else ""
            connections.append({
                "proto": proto, "state": state,
                "local": local, "remote": remote,
                "process": process
            })
        return connections
    except:
        return []

def resolve_ip(ip):
    try:
        ip_clean = ip.split(":")[0].strip("[]")
        if ip_clean in ("0.0.0.0", "127.0.0.1", "*", "[::]", "0"):
            return ip_clean
        return socket.gethostbyaddr(ip_clean)[0]
    except:
        return ip

def is_suspicious(conn):
    remote = conn.get("remote", "")
    if not remote or remote in ("*", "0.0.0.0:*"):
        return False, ""
    port_str = remote.split(":")[-1]
    try:
        port = int(port_str)
        if port in SUSPICIOUS_PORTS:
            return True, f"Known malware port: {SUSPICIOUS_PORTS[port]}"
    except:
        pass
    for domain in TELEMETRY_DOMAINS:
        if domain in remote.lower():
            return True, f"Telemetry/tracking: {domain}"
    return False, ""

def cmd_watch():
    banner()
    print(f"{CYAN}[*]{RESET} Monitoring network connections in real-time...")
    print(f"{CYAN}[*]{RESET} Press Ctrl+C to stop\n")
    seen = set()
    while True:
        try:
            connections = get_connections()
            for conn in connections:
                remote = conn.get("remote", "")
                process = conn.get("process", "")
                key = f"{remote}:{process}"
                if remote in ("*", "0.0.0.0:*", "[::]*") or not remote:
                    continue
                suspicious, reason = is_suspicious(conn)
                if key not in seen:
                    seen.add(key)
                    ts = datetime.now().strftime("%H:%M:%S")
                    if suspicious:
                        print(f"  {RED}[!!!]{RESET} {DIM}{ts}{RESET} {RED}SUSPICIOUS{RESET} {remote}")
                        print(f"        {RED}Reason: {reason}{RESET}")
                        print(f"        Process: {process}")
                    else:
                        print(f"  {GREEN}[+]{RESET} {DIM}{ts}{RESET} {remote} {DIM}{process}{RESET}")
            time.sleep(2)
        except KeyboardInterrupt:
            print(f"\n{GREEN}[✓]{RESET} Shield monitoring stopped")
            break

def cmd_scan():
    banner()
    print(f"{CYAN}[*]{RESET} Scanning all active connections...\n")
    connections = get_connections()
    suspicious_count = 0
    clean_count = 0
    print(f"{BOLD}  {'PROTO':<6} {'STATE':<12} {'LOCAL':<25} {'REMOTE':<30} {'PROCESS'}{RESET}")
    print(f"  {'─'*100}")
    for conn in connections:
        remote = conn.get("remote","")
        suspicious, reason = is_suspicious(conn)
        if suspicious:
            suspicious_count += 1
            color = RED
            flag = "⚠"
        else:
            clean_count += 1
            color = DIM
            flag = " "
        print(f"  {flag} {color}{conn['proto']:<6}{RESET} {conn['state']:<12} "
              f"{conn['local']:<25} {color}{remote:<30}{RESET} {DIM}{conn['process'][:30]}{RESET}")
        if suspicious:
            print(f"    {RED}↳ {reason}{RESET}")
    print(f"\n  {GREEN}[✓]{RESET} Clean connections: {clean_count}")
    if suspicious_count > 0:
        print(f"  {RED}[!]{RESET} Suspicious: {suspicious_count}")
    else:
        print(f"  {GREEN}[✓]{RESET} No suspicious connections detected")

def cmd_block(ip):
    print(f"{CYAN}[*]{RESET} Blocking: {ip}")
    result = subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                           capture_output=True)
    if result.returncode == 0:
        print(f"{GREEN}[✓]{RESET} Blocked: {ip}")
    else:
        print(f"{RED}[!]{RESET} Could not block {ip} — try with sudo")

def cmd_listening():
    banner()
    print(f"{CYAN}[*]{RESET} Services listening for incoming connections:\n")
    result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")[1:]
    print(f"{BOLD}  {'PORT':<10} {'ADDRESS':<25} {'PROCESS'}{RESET}")
    print(f"  {'─'*60}")
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        local = parts[3] if len(parts) > 3 else ""
        process = " ".join(parts[5:]) if len(parts) > 5 else ""
        port = local.split(":")[-1]
        suspicious = int(port) in SUSPICIOUS_PORTS if port.isdigit() else False
        color = RED if suspicious else GREEN
        flag = "⚠" if suspicious else "✓"
        print(f"  {color}[{flag}]{RESET} {port:<10} {local:<25} {DIM}{process}{RESET}")
        if suspicious:
            print(f"        {RED}↳ {SUSPICIOUS_PORTS.get(int(port),'Unknown')}{RESET}")

def cmd_stats():
    result = subprocess.run(["ss", "-s"], capture_output=True, text=True)
    print(f"\n{GREEN}Network Statistics:{RESET}")
    print(result.stdout)

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova shield <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {CYAN}scan{RESET}          Scan all active connections now")
    print(f"  {CYAN}watch{RESET}         Real-time connection monitor")
    print(f"  {CYAN}listening{RESET}     Show all listening services")
    print(f"  {CYAN}block{RESET} <ip>    Block an IP address")
    print(f"  {CYAN}stats{RESET}         Network statistics")
    print(f"\n{GREEN}What it detects:{RESET}")
    print(f"  {RED}✗{RESET} Known malware ports (Metasploit, NetBus, SubSeven...)")
    print(f"  {RED}✗{RESET} Telemetry and tracking connections")
    print(f"  {RED}✗{RESET} Unexpected listening services")
    print(f"  {GREEN}✓{RESET} Clean connections")
    print(f"\n{PURPLE}  Your network. Your control. Zero surprises.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":   cmd_help()
elif args[0]=="scan":             cmd_scan()
elif args[0]=="watch":            cmd_watch()
elif args[0]=="listening":        cmd_listening()
elif args[0]=="block":            cmd_block(args[1] if len(args)>1 else "")
elif args[0]=="stats":            cmd_stats()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
