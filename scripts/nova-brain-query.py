#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error

SERVER = "http://localhost:11434"
query = " ".join(sys.argv[1:])

prompt = f"<|system|>You are NovaBrain, the AI core of NovaOS. You run entirely on this device. Nothing leaves. Answer concisely in 2-3 sentences.<|end|><|user|>{query}<|end|><|assistant|>"

payload = json.dumps({
    "prompt": prompt,
    "n_predict": 150,
    "temperature": 0.7,
    "stop": ["<|end|>", "<|user|>"]
}).encode()

try:
    req = urllib.request.Request(
        f"{SERVER}/completion",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
        print(result["content"].strip())
except urllib.error.URLError:
    print("[!] NovaBrain server not running. Start it with: nova brain-start")
except Exception as e:
    print(f"[!] Error: {e}")
