#!/usr/bin/env python3
# vukov-watch — VukovOS Process Monitor v0.2
import os, sys, time, subprocess, signal
from pathlib import Path
from datetime import datetime

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
YELLOW="\033[0;33m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

WHITELIST = ["systemd","bash","sh","python3","ssh","tor","vukov","wsl","init",
"dbus","NetworkManager","resolved","journald","logind","llama-server","wg",
"xfce","xfwm","ps","grep","top","htop","cat","ls","find","awk","sed","tee",
"sudo","su","login","sshd","cron","rsyslog","udev","kworker","watchdog"]

BLACKLIST = ["xmrig","minerd","cpuminer","ethminer","nmap","masscan","nikto",
"sqlmap","msfconsole","msfvenom","reverse_shell","backdoor","keylogger"]

SUSPICIOUS_PATTERNS = ["/dev/tcp","/dev/udp","base64 -d","base64 --decode",
"curl|bash","wget|bash","chmod 777","/tmp/.","exec /tmp","LD_PRELOAD","ptrace"]

def banner():
    print(f"""{CYAN}
  ╔══════════════════════════════════════════════╗
  ║   vukov-watch — Process Monitor v0.2        ║
  ║   Watching all processes in real-time        ║
  ║   Suspicious activity auto-killed            ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def get_processes():
    try:
        r = subprocess.run(["ps","aux","--no-headers"],capture_output=True,text=True)
        procs = []
        for line in r.stdout.strip().split('\n'):
            p = line.split(None,10)
            if len(p) >= 11:
                procs.append({"user":p[0],"pid":p[1],"cpu":p[2],"mem":p[3],"cmd":p[10]})
        return procs
    except: return []

def is_suspicious(proc):
    cmd = proc["cmd"].lower()
    for bad in BLACKLIST:
        if bad in cmd: return f"blacklisted: {bad}"
    for pat in SUSPICIOUS_PATTERNS:
        if pat.lower() in cmd: return f"suspicious pattern: {pat}"
    try:
        if float(proc["cpu"]) > 80 and cmd.split()[0].split("/")[-1] not in WHITELIST:
            return f"high CPU: {proc['cpu']}%"
    except: pass
    return None

def kill_process(pid, reason, auto=False):
    if auto:
        try:
            os.kill(int(pid), signal.SIGKILL)
            print(f"  {RED}[KILLED]{RESET} PID {pid} — {reason}")
            log_dir = Path.home()/".vukov"/"watch"
            log_dir.mkdir(parents=True,exist_ok=True)
            with open(log_dir/"killed.log","a") as f:
                f.write(f"[{datetime.now()}] KILLED PID {pid} — {reason}\n")
        except Exception as e: print(f"  {YELLOW}[!]{RESET} Could not kill {pid}: {e}")
    else:
        print(f"\n  {RED}[!] SUSPICIOUS:{RESET} PID {pid} — {reason}")
        if input(f"  Kill? [y/N]: ").strip().lower() == 'y':
            kill_process(pid, reason, auto=True)

def watch_once(auto=False):
    procs = get_processes()
    flagged = [(p,r) for p in procs if (r:=is_suspicious(p))]
    if not flagged:
        print(f"  {GREEN}[✓]{RESET} All clean — {len(procs)} processes checked")
        return
    print(f"  {YELLOW}[!]{RESET} {len(flagged)} suspicious process(es):")
    for p,r in flagged: kill_process(p["pid"],r,auto)

def watch_continuous(auto=False, interval=5):
    print(f"  {CYAN}[*]{RESET} Watching every {interval}s... (Ctrl+C to stop)")
    try:
        while True:
            for p in get_processes():
                r = is_suspicious(p)
                if r:
                    print(f"\n  {YELLOW}[!]{RESET} PID {p['pid']}: {p['cmd'][:60]}")
                    kill_process(p["pid"],r,auto)
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n  {GREEN}[✓]{RESET} Watch stopped.")

def list_processes():
    procs = get_processes()
    print(f"\n  {BOLD}{'PID':<8}{'CPU%':<6}{'MEM%':<6}{'USER':<12}COMMAND{RESET}")
    print(f"  {DIM}{'─'*65}{RESET}")
    for p in sorted(procs,key=lambda x: float(x['cpu']) if x['cpu'].replace('.','').isdigit() else 0,reverse=True)[:30]:
        try: color = RED if float(p['cpu'])>50 else YELLOW if float(p['cpu'])>20 else GREEN
        except: color = RESET
        print(f"  {p['pid']:<8}{color}{p['cpu']:<6}{RESET}{p['mem']:<6}{p['user']:<12}{p['cmd'][:45]}")

if __name__ == "__main__":
    banner()
    args = sys.argv[1:]
    if not args or args[0]=="scan": watch_once(auto=False)
    elif args[0]=="auto": watch_once(auto=True)
    elif args[0]=="watch": watch_continuous(auto="--auto" in args)
    elif args[0]=="list": list_processes()
    else:
        print("  Usage: vukov watch [scan|auto|watch|watch --auto|list]")
