# NovaOS
A privacy-first, encrypted, AI-native operating system.
Runs on bare metal, WSL2, and Android via Termux (rootless).
No telemetry. No cloud. No surveillance.
Encryption: LUKS2 + AES-256 + ChaCha20 (stronger than Telegram)
AI: Local llama.cpp + Phi-3 Mini (never leaves your device)
Built on Arch Linux ARM + proot (rootless Android support)

## Build Log
### Milestone 1 — First Boot ✓
- Date: 2026-05-30
- NovaOS 0.1 (Spectre) aarch64 boots successfully
- Running inside WSL2 via arch-chroot + QEMU translation
- Core packages: cryptsetup 2.8.6, WireGuard, Python 3.14.5, Git 2.54.0
- 180 packages installed via pacman
- Next: Encryption layer (LUKS2 + AES-256 + ChaCha20)

### Milestone 2 — NovaCrypt Encryption Engine ✓
- ChaCha20-Poly1305 file encryption working
- AES-256-XTS disk cipher configured
- Argon2id key derivation (memory-hard, bruteforce resistant)
- 512-bit keyfile generation working
- Encrypt/decrypt/secure-delete all functional
- Next: NovaBrain local AI daemon

### Milestone 3 — NovaBrain AI Daemon ✓
- llama.cpp compiled natively on Ryzen 7 5700U
- Phi-3 Mini 3.8B model running at 3.1 tokens/sec
- Zero cloud, zero telemetry, fully local
- First words: "I am NovaBrain, the AI core of NovaOS"
- Use llama-completion for single-shot queries
- Next: Termux Android bootstrap
