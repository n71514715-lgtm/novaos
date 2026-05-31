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

### Milestone 4 — Termux Android Bootstrap ✓
- nova-termux-install.sh — full guided installer
- nova-quick-install.sh — one-command install
- nova command with: start, update, status, brain, encrypt
- privacy.conf — telemetry disabled by default
- novaos-0.1-alpha.zip — distributable package
- Next: Test on Samsung Remote Test Lab

### Milestone 5 — Termux Installer Validated ✓
- Termux detection working correctly
- Android SDK version check working (requires 7.0+)
- Installer logic validated via mock environment
- Ready for real Termux deployment
- Next: GitHub release + real device test

### Milestone 6 — Desktop Shell ✓
- XFCE4 desktop running via WSLg X11 forwarding
- NovaOS identity showing in fastfetch
- GUI window rendering on Windows desktop
- AMD Ryzen 7 5700U + Radeon iGPU detected
- Next: NovaOS logo + custom theming

### Milestone 7 — Windows App Support ✓
- Wine 10.0 installed
- Windows apps run natively on NovaOS
- Notepad confirmed working via WSLg
- Next: Darling (macOS), nova-guard, WireGuard, boot splash

### Milestone 8 — nova-guard Real-time Encryption Watchdog ✓
- Monitors directories for new files in real-time
- Auto-encrypts files the moment they're created
- Original file deleted — only encrypted .nova version survives
- No other OS ships with this built in
- Next: WireGuard VPN + boot experience

### Milestone 9 — Boot Experience ✓
- Coat of arms renders on every terminal open
- Typewriter animation — "Private. Encrypted. Yours."
- Real-time system checks: NovaCrypt, NovaBrain, nova-guard, nova-vpn
- NovaBrain greeting with time of day
- Auto-runs via .bashrc on every session
- Next: Darling macOS layer + demo video

### Milestone 10 — Identity + Vault ✓
- nova-id: Ed25519 cryptographic identity (same as Signal/SSH)
- Sign and verify files with your NovaOS key
- Fingerprint: unique per device, cryptographically generated
- nova-vault: encrypted password manager
- AES-256 + PBKDF2 (600,000 iterations)
- Zero cloud, zero sync, zero breach risk
- Next: nova-chat encrypted messaging + nova-sync

### Milestone 11 — nova-chat Encrypted P2P Messaging ✓
- Direct device-to-device messaging
- No server, no account, no phone number
- Message delivered and displayed with timestamp
- Sender identity via nova-id fingerprint
- Port 51869 — works over LAN or WireGuard tunnel
- Next: nova-sync encrypted file sync
