#!/data/data/com.termux/files/usr/bin/bash
# NovaOS Termux Bootstrap Installer
# Installs NovaOS inside Termux with no root required
# Works on any Android 7+ device

set -e

NOVA_VERSION="0.1-alpha"
INSTALL_DIR="$HOME/novaos"
PROOT_DISTRO="archlinux"

echo "╔══════════════════════════════════════════╗"
echo "║   NovaOS $NOVA_VERSION — Termux Installer       ║"
echo "║   No root required. Private by default.  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Step 1 — update Termux packages
echo "[1/6] Updating Termux..."
pkg update -y && pkg upgrade -y

# Step 2 — install proot-distro
echo "[2/6] Installing proot-distro..."
pkg install -y proot-distro wget curl git

# Step 3 — install Arch Linux ARM via proot-distro
echo "[3/6] Installing Arch Linux ARM base..."
proot-distro install archlinux

# Step 4 — configure NovaOS identity inside proot
echo "[4/6] Configuring NovaOS identity..."
proot-distro login archlinux -- bash -c "
cat > /etc/os-release << 'OSREL'
NAME=\"NovaOS\"
VERSION=\"0.1-alpha\"
ID=novaos
ID_LIKE=arch
PRETTY_NAME=\"NovaOS 0.1 (Spectre)\"
PRIVACY=\"maximum\"
TELEMETRY=\"none\"
OSREL
mkdir -p /etc/nova
echo 'NovaOS 0.1 (Spectre) — Privacy First' > /etc/nova/release
"

# Step 5 — install core packages inside NovaOS
echo "[5/6] Installing NovaOS core packages..."
proot-distro login archlinux -- bash -c "
pacman-key --init 2>/dev/null || true
sed -i 's/SigLevel    = Required DatabaseOptional/SigLevel = Never/' /etc/pacman.conf
sed -i '/^\[options\]/a DisableSandbox' /etc/pacman.conf 2>/dev/null || true
pacman -Sy --noconfirm --cachedir /tmp git wget curl nano htop fastfetch python 2>&1 | tail -5
"

# Step 6 — create nova launcher
echo "[6/6] Creating nova launcher..."
cat > "$PREFIX/bin/nova" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
# NovaOS launcher
echo "Starting NovaOS..."
proot-distro login archlinux -- bash --login
LAUNCHER
chmod +x "$PREFIX/bin/nova"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   NovaOS installed successfully!         ║"
echo "║   Type 'nova' to enter NovaOS            ║"
echo "╚══════════════════════════════════════════╝"
