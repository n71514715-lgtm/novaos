#!/bin/bash
# NovaOS Master Build Script
# Builds the rootfs for both PC and Android/Termux targets

set -e

NOVA_ROOT="/mnt/d/NovaOS"
ROOTFS="$NOVA_ROOT/rootfs"
BUILD="$NOVA_ROOT/build"
TERMUX="$NOVA_ROOT/termux"
ARCH="aarch64"

echo "================================================"
echo "  NovaOS Build System v0.1"
echo "  Target: $ARCH (Android/Termux + bare metal)"
echo "================================================"

echo "[1/5] Checking build dependencies..."
for cmd in proot qemu-aarch64 git curl wget; do
    if command -v $cmd &>/dev/null; then
        echo "  [OK] $cmd"
    else
        echo "  [MISSING] $cmd — run setup first"
        exit 1
    fi
done

echo "[2/5] Creating rootfs structure..."
mkdir -p $ROOTFS/{bin,etc,home,lib,proc,sys,tmp,usr,var,dev}
mkdir -p $ROOTFS/etc/nova
mkdir -p $ROOTFS/usr/{bin,lib,share}
mkdir -p $ROOTFS/home/user

echo "[3/5] Writing NovaOS identity..."
cat > $ROOTFS/etc/nova/release << 'RELEASE'
NAME="NovaOS"
VERSION="0.1-alpha"
ENCRYPTION="LUKS2+AES256+ChaCha20"
AI="NovaBrain/llama.cpp"
PRIVACY="maximum"
TELEMETRY="none"
RELEASE

echo "[4/5] Writing OS release file..."
cat > $ROOTFS/etc/os-release << 'OSREL'
NAME="NovaOS"
VERSION="0.1"
ID=novaos
ID_LIKE=arch
PRETTY_NAME="NovaOS 0.1 (Spectre)"
HOME_URL="https://github.com/nova/novaos"
OSREL

echo "[5/5] Done. NovaOS rootfs skeleton ready."
echo "  Location: $ROOTFS"
echo "  Next: Download Arch Linux ARM base"
