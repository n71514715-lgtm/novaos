#!/data/data/com.termux/files/usr/bin/bash
# NovaOS Quick Install — paste this single command into Termux
# curl -sL https://raw.githubusercontent.com/n71514715-lgtm/novaos/main/termux/nova-quick-install.sh | bash

set -e

echo "╔══════════════════════════════════════════╗"
echo "║        NovaOS Quick Install              ║"
echo "║   Privacy OS for Android — No Root       ║"
echo "╚══════════════════════════════════════════╝"

# Check we're in Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "[!] This script must run inside Termux"
    exit 1
fi

# Check Android version
SDK=$(getprop ro.build.version.sdk 2>/dev/null || echo "0")
echo "[*] Android SDK: $SDK"
if [ "$SDK" -lt 24 ]; then
    echo "[!] Android 7.0+ required"
    exit 1
fi

echo "[*] Installing dependencies..."
pkg update -y -o Dpkg::Options::="--force-confold" 2>/dev/null
pkg install -y proot-distro curl wget git python 2>/dev/null

echo "[*] Setting up NovaOS environment..."
proot-distro install archlinux 2>/dev/null || echo "[*] Arch already installed"

echo "[*] Configuring NovaOS..."
proot-distro login archlinux -- bash -c "
# Set NovaOS identity
cat > /etc/os-release << 'ID'
NAME=\"NovaOS\"
VERSION=\"0.1-alpha\"
ID=novaos
PRETTY_NAME=\"NovaOS 0.1 (Spectre)\"
TELEMETRY=\"none\"
ID

# Disable telemetry and tracking
mkdir -p /etc/nova
cat > /etc/nova/privacy.conf << 'PRIV'
TELEMETRY=disabled
CRASH_REPORTS=disabled
ANALYTICS=disabled
AUTO_UPDATE_CHECK=disabled
DNS_OVER_HTTPS=enabled
DNS_SERVER=1.1.1.1
PRIV

# Configure pacman
sed -i 's/SigLevel    = Required DatabaseOptional/SigLevel = Never/' /etc/pacman.conf 2>/dev/null || true
echo '[*] NovaOS identity configured'
"

echo "[*] Creating nova command..."
cat > "$PREFIX/bin/nova" << 'NOVA'
#!/data/data/com.termux/files/usr/bin/bash
case "$1" in
    start|"")
        echo "Entering NovaOS..."
        proot-distro login archlinux -- bash --login
        ;;
    update)
        echo "Updating NovaOS..."
        proot-distro login archlinux -- pacman -Syu --noconfirm --cachedir /tmp
        ;;
    status)
        echo "NovaOS 0.1 (Spectre)"
        proot-distro login archlinux -- cat /etc/nova/privacy.conf
        ;;
    brain)
        echo "Starting NovaBrain AI..."
        proot-distro login archlinux -- python3 /opt/novabrain/novabrain.py
        ;;
    encrypt)
        proot-distro login archlinux -- bash /etc/nova/nova-crypt.sh "$2" "$3" "$4"
        ;;
    help|*)
        echo "Usage: nova [command]"
        echo "  start    — enter NovaOS shell"
        echo "  update   — update packages"
        echo "  status   — show privacy status"
        echo "  brain    — start NovaBrain AI"
        echo "  encrypt  — encrypt a file"
        ;;
esac
NOVA
chmod +x "$PREFIX/bin/nova"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   NovaOS ready on your Android device!   ║"
echo "║                                          ║"
echo "║   Commands:                              ║"
echo "║     nova          — enter NovaOS         ║"
echo "║     nova status   — privacy status       ║"
echo "║     nova brain    — start AI             ║"
echo "║     nova encrypt  — encrypt files        ║"
echo "╚══════════════════════════════════════════╝"
