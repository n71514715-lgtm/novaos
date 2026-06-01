#!/usr/bin/env python3
# nova-ai-train — Fine-tune NovaBrain on your own data
# Train the AI on YOUR documents, notes, knowledge
# Runs entirely locally — your data never leaves
# Makes NovaBrain smarter about YOUR life

import os, sys, json, time, subprocess
from pathlib import Path
from datetime import datetime

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

TRAIN_DIR = Path.home() / ".nova" / "ai-train"
DATA_DIR = TRAIN_DIR / "data"
MODEL_DIR = Path("/opt/novabrain/models")
BASE_MODEL = MODEL_DIR / "phi3-mini.gguf"

def banner():
    print(f"""{PURPLE}
  ╔══════════════════════════════════════════════╗
  ║   nova-ai-train — Train NovaBrain            ║
  ║   Fine-tune on your own documents            ║
  ║   Your data. Your model. Local only.         ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def prepare_data(source_dir):
    banner()
    source = Path(source_dir)
    if not source.exists():
        print(f"{RED}[!]{RESET} Directory not found: {source_dir}")
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{CYAN}[*]{RESET} Preparing training data from: {source_dir}")
    files_processed = 0
    training_data = []
    for ext in ["*.txt", "*.md", "*.py", "*.json", "*.csv"]:
        for f in source.rglob(ext):
            try:
                content = f.read_text(errors='ignore')
                if len(content) > 50:
                    chunks = [content[i:i+512] for i in range(0, len(content), 512)]
                    for chunk in chunks:
                        training_data.append({
                            "source": str(f),
                            "content": chunk.strip(),
                            "timestamp": datetime.now().isoformat()
                        })
                    files_processed += 1
                    print(f"  {GREEN}[+]{RESET} {f.name} ({len(chunks)} chunks)")
            except Exception as e:
                print(f"  {RED}[!]{RESET} Failed: {f.name}")
    output = DATA_DIR / "training_data.json"
    output.write_text(json.dumps(training_data, indent=2))
    print(f"\n{GREEN}[✓]{RESET} Prepared {len(training_data)} training samples from {files_processed} files")
    print(f"{GREEN}[✓]{RESET} Saved to: {output}")
    return len(training_data)

def add_to_memory(source_dir):
    banner()
    source = Path(source_dir)
    if not source.exists():
        print(f"{RED}[!]{RESET} Directory not found: {source_dir}")
        return
    print(f"{CYAN}[*]{RESET} Adding documents to NovaBrain memory...")
    count = 0
    for ext in ["*.txt", "*.md"]:
        for f in source.rglob(ext):
            try:
                content = f.read_text(errors='ignore')[:500]
                if len(content) > 30:
                    result = subprocess.run(
                        [sys.executable, "/usr/local/bin/nova-memory",
                         "remember", content, "document", f.stem],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        count += 1
                        print(f"  {GREEN}[+]{RESET} Memorized: {f.name}")
            except:
                pass
    print(f"\n{GREEN}[✓]{RESET} Added {count} documents to NovaBrain memory")
    print(f"{CYAN}[i]{RESET} Query with: nova memory recall \"topic\"")

def create_system_prompt(name, description, personality):
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    prompt = {
        "name": name,
        "description": description,
        "personality": personality,
        "created": datetime.now().isoformat(),
        "system_prompt": f"""You are {name}. {description}
Personality: {personality}
You run on NovaOS — a privacy-first operating system.
You never send data to the cloud. You are local, private, and trusted.
Always be helpful, concise, and honest."""
    }
    prompt_file = TRAIN_DIR / "custom_prompt.json"
    prompt_file.write_text(json.dumps(prompt, indent=2))
    print(f"{GREEN}[✓]{RESET} Custom AI personality created: {name}")
    print(f"{GREEN}[✓]{RESET} Saved to: {prompt_file}")
    print(f"{CYAN}[i]{RESET} NovaBrain will use this personality on next start")

def show_stats():
    banner()
    data_file = DATA_DIR / "training_data.json"
    prompt_file = TRAIN_DIR / "custom_prompt.json"
    print(f"\n{BOLD}  Training Status:{RESET}\n")
    if data_file.exists():
        data = json.loads(data_file.read_text())
        print(f"  {GREEN}[✓]{RESET} Training data: {len(data)} samples")
        sources = set(d['source'] for d in data)
        print(f"  {GREEN}[✓]{RESET} Source files: {len(sources)}")
    else:
        print(f"  {DIM}[~]{RESET} No training data yet")
    if prompt_file.exists():
        prompt = json.loads(prompt_file.read_text())
        print(f"  {GREEN}[✓]{RESET} Custom personality: {prompt['name']}")
    else:
        print(f"  {DIM}[~]{RESET} No custom personality")
    if BASE_MODEL.exists():
        size = BASE_MODEL.stat().st_size // (1024**3)
        print(f"  {GREEN}[✓]{RESET} Base model: phi3-mini.gguf ({size}GB)")
    memory_db = Path.home() / ".nova" / "memory" / "memory.db"
    if memory_db.exists():
        import sqlite3
        conn = sqlite3.connect(memory_db)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        print(f"  {GREEN}[✓]{RESET} Memory entries: {count}")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova ai-train <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {PURPLE}prepare{RESET} <dir>              Prepare training data from directory")
    print(f"  {PURPLE}memorize{RESET} <dir>             Add documents to NovaBrain memory")
    print(f"  {PURPLE}personality{RESET} <name> <desc>  Create custom AI personality")
    print(f"  {PURPLE}stats{RESET}                      Show training status")
    print(f"\n{GREEN}Examples:{RESET}")
    print(f"  nova ai-train memorize ~/Documents")
    print(f"  nova ai-train memorize ~/notes")
    print(f"  nova ai-train personality \"Alex\" \"My personal assistant\"")
    print(f"  nova memory recall \"what did I write about privacy\"")
    print(f"\n{PURPLE}  Your data. Your model. Zero cloud.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":      cmd_help()
elif args[0]=="prepare":             prepare_data(args[1] if len(args)>1 else ".")
elif args[0]=="memorize":            add_to_memory(args[1] if len(args)>1 else ".")
elif args[0]=="personality":         create_system_prompt(
                                        args[1] if len(args)>1 else "NovaBrain",
                                        args[2] if len(args)>2 else "Personal AI assistant",
                                        args[3] if len(args)>3 else "Helpful, honest, private")
elif args[0]=="stats":               show_stats()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
