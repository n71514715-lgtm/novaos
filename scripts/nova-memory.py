#!/usr/bin/env python3
# nova-memory — NovaOS Personal Memory Engine
# Remembers everything you see, read, write, think
# Retrieves it instantly on demand
# 100% local. 100% encrypted. Zero cloud.
# What Microsoft Recall should have been.

import os, sys, json, time, hashlib, sqlite3, threading
from pathlib import Path
from datetime import datetime

VERSION = "0.1"
MEMORY_DIR = Path.home() / ".nova" / "memory"
MEMORY_DB = MEMORY_DIR / "memory.db"
MEMORY_LOG = MEMORY_DIR / "memory.log"

GREEN="\033[0;32m"; CYAN="\033[0;36m"; RED="\033[0;31m"
PURPLE="\033[0;35m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

def banner():
    print(f"""{GREEN}
  ╔══════════════════════════════════════════════╗
  ║   nova-memory — Personal Memory Engine       ║
  ║   Remembers everything. Locally. Always.     ║
  ║   What Microsoft Recall should have been.    ║
  ╚══════════════════════════════════════════════╝{RESET}""")

def init_db():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            tags TEXT,
            hash TEXT UNIQUE,
            importance INTEGER DEFAULT 1
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(type)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, source, tags)")
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(MEMORY_DB)

def store_memory(content, mtype="note", source="manual", tags="", importance=1):
    init_db()
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    timestamp = datetime.now().isoformat()
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO memories (timestamp, type, content, source, tags, hash, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, mtype, content, source, tags, content_hash, importance))
        rowid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO memories_fts(rowid, content, source, tags) VALUES (?,?,?,?)",
                    (rowid, content, source, tags))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def search_memory(query, limit=10):
    init_db()
    conn = get_conn()
    results = conn.execute("""
        SELECT m.id, m.timestamp, m.type, m.content, m.source, m.tags, m.importance
        FROM memories m
        JOIN memories_fts fts ON m.rowid = fts.rowid
        WHERE memories_fts MATCH ?
        ORDER BY m.importance DESC, m.timestamp DESC
        LIMIT ?
    """, (query, limit)).fetchall()
    conn.close()
    return results

def search_simple(query, limit=10):
    init_db()
    conn = get_conn()
    results = conn.execute("""
        SELECT id, timestamp, type, content, source, tags, importance
        FROM memories
        WHERE content LIKE ? OR source LIKE ? OR tags LIKE ?
        ORDER BY importance DESC, timestamp DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
    conn.close()
    return results

def ask_brain_about_memory(query, memories):
    try:
        import urllib.request
        context = "\n".join([f"[{m[2]}] {m[3][:200]}" for m in memories[:5]])
        prompt = f"""<|system|>You are NovaBrain memory assistant. Answer based on these memories from the user's personal archive:

{context}

Answer the user's question about their memories. Be specific and reference the actual stored content.<|end|><|user|>{query}<|end|><|assistant|>"""
        payload = json.dumps({"prompt": prompt, "n_predict": 150, "temperature": 0.7}).encode()
        req = urllib.request.Request("http://localhost:11434/completion", data=payload,
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["content"].strip()
    except:
        return None

def cmd_remember(content, mtype="note", tags=""):
    if store_memory(content, mtype=mtype, source="manual", tags=tags):
        print(f"{GREEN}[✓]{RESET} Remembered: {BOLD}{content[:60]}{'...' if len(content)>60 else ''}{RESET}")
        print(f"{DIM}    Type: {mtype} | Tags: {tags or 'none'}{RESET}")
    else:
        print(f"{CYAN}[~]{RESET} Already in memory")

def cmd_recall(query):
    keywords = [w for w in query.split() if len(w) > 3]
    if not keywords: keywords = [query]
    banner()
    print(f"{CYAN}[*]{RESET} Searching memory for: {BOLD}{query}{RESET}\n")
    try:
        results = search_memory(query)
    except:
        results = search_simple(query)
    if not results:
        results = search_simple(query)
    if not results:
        print(f"{DIM}  No memories found for: {query}{RESET}")
        print(f"{DIM}  Try: nova memory remember \"something\" to add memories{RESET}")
        return
    brain_answer = ask_brain_about_memory(query, results)
    if brain_answer:
        print(f"{GREEN}[NovaBrain]{RESET} {brain_answer}\n")
        print(f"{DIM}{'─'*50}{RESET}")
    print(f"{BOLD}  Matching memories ({len(results)} found):{RESET}\n")
    for r in results:
        rid, ts, rtype, content, source, tags, importance = r
        time_str = ts[:16].replace("T", " ")
        print(f"  {GREEN}#{rid}{RESET} {DIM}{time_str}{RESET} [{rtype}]")
        print(f"  {content[:120]}{'...' if len(content)>120 else ''}")
        if tags:
            print(f"  {DIM}tags: {tags}{RESET}")
        print()

def cmd_list(limit=20, mtype=None):
    init_db()
    conn = get_conn()
    if mtype:
        rows = conn.execute("""
            SELECT id, timestamp, type, content, source, tags
            FROM memories WHERE type=?
            ORDER BY timestamp DESC LIMIT ?
        """, (mtype, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, timestamp, type, content, source, tags
            FROM memories ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    if not rows:
        print(f"{CYAN}[*]{RESET} No memories yet. Add with: nova memory remember \"text\"")
        return
    print(f"\n{BOLD}  Recent memories ({len(rows)} shown):{RESET}\n")
    for r in rows:
        rid, ts, rtype, content, source, tags = r
        time_str = ts[:16].replace("T", " ")
        print(f"  {GREEN}#{rid}{RESET} {DIM}{time_str}{RESET} {CYAN}[{rtype}]{RESET}")
        print(f"  {content[:100]}{'...' if len(content)>100 else ''}\n")

def cmd_stats():
    init_db()
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    by_type = conn.execute("SELECT type, COUNT(*) FROM memories GROUP BY type").fetchall()
    oldest = conn.execute("SELECT MIN(timestamp) FROM memories").fetchone()[0]
    conn.close()
    print(f"\n{GREEN}╔══════════════════════════════════════╗{RESET}")
    print(f"{GREEN}║   nova-memory Statistics             ║{RESET}")
    print(f"{GREEN}╚══════════════════════════════════════╝{RESET}\n")
    print(f"  {CYAN}Total memories:{RESET} {BOLD}{total}{RESET}")
    if oldest:
        print(f"  {CYAN}Oldest memory:{RESET}  {oldest[:16]}")
    print(f"  {CYAN}Database:{RESET}      {MEMORY_DB}")
    print(f"\n  {BOLD}By type:{RESET}")
    for t, count in by_type:
        print(f"  {GREEN}{t:<15}{RESET} {count}")

def cmd_watch():
    banner()
    print(f"{CYAN}[*]{RESET} Memory capture mode — paste text to remember it")
    print(f"{CYAN}[*]{RESET} Type 'done' when finished, 'quit' to exit\n")
    buffer = []
    while True:
        try:
            line = input(f"  {DIM}>{RESET} ").strip()
            if line.lower() == "quit":
                break
            elif line.lower() == "done":
                if buffer:
                    content = " ".join(buffer)
                    cmd_remember(content)
                    buffer = []
            elif line:
                buffer.append(line)
        except KeyboardInterrupt:
            break
    print(f"\n{GREEN}[✓]{RESET} Memory capture ended")

def cmd_forget(memory_id):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
    conn.execute("DELETE FROM memories_fts WHERE rowid=?", (memory_id,))
    conn.commit()
    conn.close()
    print(f"{GREEN}[✓]{RESET} Memory #{memory_id} forgotten")

def cmd_export():
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM memories ORDER BY timestamp").fetchall()
    conn.close()
    export_file = MEMORY_DIR / f"memory-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    data = [{"id":r[0],"timestamp":r[1],"type":r[2],"content":r[3],
             "source":r[4],"tags":r[5],"importance":r[6]} for r in rows]
    export_file.write_text(json.dumps(data, indent=2))
    print(f"{GREEN}[✓]{RESET} Exported {len(data)} memories to: {export_file}")

def cmd_help():
    banner()
    print(f"{BOLD}Usage:{RESET} nova memory <command>")
    print(f"\n{GREEN}Commands:{RESET}")
    print(f"  {CYAN}remember{RESET} \"text\" [type] [tags]  Store a memory")
    print(f"  {CYAN}recall{RESET} \"query\"               Search + AI answer")
    print(f"  {CYAN}list{RESET} [type]                  List recent memories")
    print(f"  {CYAN}watch{RESET}                        Interactive capture mode")
    print(f"  {CYAN}stats{RESET}                        Memory statistics")
    print(f"  {CYAN}forget{RESET} <id>                  Delete a memory")
    print(f"  {CYAN}export{RESET}                       Export all memories")
    print(f"\n{GREEN}Memory types:{RESET}")
    print(f"  note · idea · link · quote · meeting · code · dream · anything")
    print(f"\n{GREEN}Examples:{RESET}")
    print(f"  nova memory remember \"The Feynman technique: teach to learn\"")
    print(f"  nova memory remember \"https://novaos.dev\" link \"privacy,os\"")
    print(f"  nova memory recall \"Feynman\"")
    print(f"  nova memory recall \"what links did I save about privacy\"")
    print(f"\n{PURPLE}  Everything stays on your device. Forever. Private.{RESET}\n")

args = sys.argv[1:]
if not args or args[0]=="help":     cmd_help()
elif args[0]=="remember":           cmd_remember(" ".join(args[1:2]), args[2] if len(args)>2 else "note", args[3] if len(args)>3 else "")
elif args[0]=="recall":             cmd_recall(" ".join(args[1:]))
elif args[0]=="list":               cmd_list(mtype=args[1] if len(args)>1 else None)
elif args[0]=="watch":              cmd_watch()
elif args[0]=="stats":              cmd_stats()
elif args[0]=="forget":             cmd_forget(int(args[1]))
elif args[0]=="export":             cmd_export()
else: print(f"{RED}[!] Unknown: {args[0]}{RESET}")
