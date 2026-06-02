# 🐺 VukovOS

> *PRIVATA · LIBERA · SECURA*

**VukovOS** is a privacy-first, AI-native operating system built from scratch for people who believe surveillance is theft and that technology should serve its user — not the other way around.

Named after **Vuk** (вук) — wolf in Serbian — and in the spirit of Vuk Stefanović Karadžić, who fought to give ordinary people a language they could actually use. VukovOS fights to give ordinary people an OS they actually control.

---

## Current Release: v0.1-alpha "Spectre"

| Component | Status |
|---|---|
| Base (Arch Linux ARM / aarch64) | ✅ Live |
| VukovCrypt (ChaCha20-Poly1305 + AES-256-XTS + Argon2id) | ✅ Live |
| VukovBrain (llama.cpp + Phi-3 Mini 3.8B, local AI) | ✅ Live |
| vukov-guard (encryption watchdog) | ✅ Live |
| vukov-vpn (WireGuard) | ✅ Live |
| vukov-id (Ed25519 identity) | ✅ Live |
| vukov-vault (encrypted password manager) | ✅ Live |
| vukov-chat (P2P messaging, port 51869) | ✅ Live |
| vukov-sync (P2P file sync, port 51870) | ✅ Live |
| vukov-gaming (Steam / Epic / GOG / EA / Ubisoft) | ✅ Live |
| Desktop (XFCE via WSLg + Wine 10.0) | ✅ Live |
| Android (Termux bootstrap) | ✅ Live |

---

## Philosophy

Most operating systems are built for convenience. VukovOS is built for **sovereignty**.

- **No telemetry.** Nothing leaves your machine unless you choose.
- **Local AI first.** VukovBrain runs entirely on-device. No cloud, no API keys, no logs.
- **Encrypted by default.** VukovCrypt wraps your data before it ever touches disk.
- **P2P native.** vukov-chat and vukov-sync work without central servers.
- **Built for the underserved.** Designed with users in mind who live under surveillance-heavy regimes and have limited access to privacy tools.

---

## Quick Start

```bash
# Boot into VukovOS environment
vukov-boot

# Check system status
vukov status

# Start local AI
vukov-brain start

# Encrypt a file
vukov-crypt encrypt myfile.txt

# Connect VPN
vukov-vpn up

# Open encrypted vault
vukov-vault open
```

---

## Architecture

```
VukovOS
├── Base: Arch Linux ARM (aarch64, QEMU-translated in WSL2)
├── Crypto: VukovCrypt
│   ├── ChaCha20-Poly1305 (stream encryption)
│   ├── AES-256-XTS (disk encryption)
│   └── Argon2id (key derivation)
├── AI: VukovBrain
│   ├── llama.cpp backend
│   ├── Phi-3 Mini 3.8B model
│   └── llama-server (persistent, port 11434)
├── Network: vukov-vpn (WireGuard)
├── Identity: vukov-id (Ed25519)
├── Comms: vukov-chat (P2P, port 51869)
├── Sync: vukov-sync (P2P, port 51870)
├── Desktop: XFCE + WSLg + Wine 10.0
└── Gaming: Steam, Epic, GOG, EA, Ubisoft
```

---

## Hardware Reference Build

Tested and developed on:
- **Device:** Acer Aspire (Ryzen 7 5700U, integrated Radeon)
- **Host:** Windows 11 + WSL2 (Ubuntu)
- **Storage:** D:\WSL + D:\VukovOS
- **AI speed:** ~3 tokens/second (CPU only)

---

## Roadmap

- [ ] v0.2 — vukov-shield (network intrusion detection)
- [ ] v0.2 — improved VukovBrain context persistence
- [ ] v0.3 — vukov-mesh (multi-node encrypted network)
- [ ] v0.3 — native ARM image (no QEMU layer)
- [ ] v1.0 — full installable ISO

---

## Contributing

VukovOS is built for people who need it most. If you're from a region where privacy tools are scarce or restricted, you're exactly who this is for.

PRs welcome. Issues welcome. Forks welcome.

---

## License

MIT

---

*PRIVATA · LIBERA · SECURA* 🐺
