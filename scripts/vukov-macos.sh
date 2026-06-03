#!/bin/bash
# vukov-macos — VukovOS macOS Emulation Layer v0.2
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'
YELLOW='\033[0;33m'; PURPLE='\033[0;35m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
VUKOV_MACOS_DIR="$HOME/.vukov/macos"
QEMU_IMG="$VUKOV_MACOS_DIR/macos.qcow2"

banner() {
echo -e "${PURPLE}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   vukov-macos — macOS Emulation Layer       ║
  ║   Darling + QEMU + VukovSyscall             ║
  ║   Stronger than stock Darling               ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

check_deps() {
    for dep in git cmake make gcc python3 curl qemu-system-x86_64; do
        command -v "$dep" > /dev/null 2>&1 || MISSING+=("$dep")
    done
    [ ${#MISSING[@]} -gt 0 ] && \
        echo -e "${CYAN}[*]${RESET} Installing: ${MISSING[*]}" && \
        sudo apt-get install -y "${MISSING[@]}" 2>&1 | grep -E "^(Get|Inst)" | sed 's/^/  /'
}

install_darling() {
    echo -e "${CYAN}[1/4]${RESET} Checking Darling..."
    if command -v darling > /dev/null 2>&1; then
        echo -e "${GREEN}[✓]${RESET} Darling already installed."
        return
    fi
    echo -e "${CYAN}[*]${RESET} Installing Darling dependencies..."
    sudo apt-get install -y cmake clang bison flex xz-utils libfuse-dev \
        libudev-dev pkg-config libc6-dev-i386 libcairo2-dev libgl1-mesa-dev \
        libglu1-mesa-dev libtiff5-dev libfreetype6-dev libpulse-dev \
        libavformat-dev libavcodec-dev libswresample-dev git 2>&1 | grep -E "^(Get|Inst)" | sed 's/^/  /'
    echo -e "${CYAN}[*]${RESET} Cloning Darling (this takes a while)..."
    git clone --recursive https://github.com/darlinghq/darling.git "$VUKOV_MACOS_DIR/darling-src" 2>&1 | tail -3
    cd "$VUKOV_MACOS_DIR/darling-src"
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -3
    make -j$(nproc) 2>&1 | tail -5
    sudo make install 2>&1 | tail -3
    echo -e "${GREEN}[✓]${RESET} Darling installed."
}

apply_patches() {
    echo -e "${CYAN}[2/4]${RESET} Applying VukovOS patches..."
    mkdir -p "$VUKOV_MACOS_DIR/patches"

    # Display bridge for WSLg
    cat > "$VUKOV_MACOS_DIR/patches/display-bridge.sh" << 'PATCH'
#!/bin/bash
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
[ -S "/tmp/.X11-unix/X0" ] && echo "  [vukov-macos] Display: X11/WSLg" && return
[ -n "$WAYLAND_DISPLAY" ] && echo "  [vukov-macos] Display: Wayland/WSLg" && return
echo "  [vukov-macos] Warning: no display found"
PATCH
    chmod +x "$VUKOV_MACOS_DIR/patches/display-bridge.sh"

    # Syscall shim
    cat > "$VUKOV_MACOS_DIR/patches/syscall-shim.py" << 'SHIM'
#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime
SYSCALL_MAP = {
    "getentropy":"getrandom","mach_absolute_time":"clock_gettime",
    "kqueue":"epoll_create1","kevent":"epoll_wait","kevent64":"epoll_pwait",
    "pthread_jit_write_protect_np":"mprotect","SecRandomCopyBytes":"getrandom",
}
LOG = Path.home()/".vukov"/"macos"/"syscall.log"
LOG.parent.mkdir(parents=True,exist_ok=True)
def translate(name):
    mapped = SYSCALL_MAP.get(name)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG,"a") as f:
        f.write(f"[{ts}] {name} -> {mapped or 'UNHANDLED'}\n")
    return mapped
if len(sys.argv)>1:
    r = translate(sys.argv[1])
    print(f"  [vukov-syscall] {sys.argv[1]} -> {r or 'no mapping'}")
SHIM
    chmod +x "$VUKOV_MACOS_DIR/patches/syscall-shim.py"
    echo -e "${GREEN}[✓]${RESET} Patches applied."
}

setup_qemu() {
    echo -e "${CYAN}[3/4]${RESET} Setting up QEMU VM path..."
    mkdir -p "$VUKOV_MACOS_DIR"
    cat > "$VUKOV_MACOS_DIR/launch-qemu.sh" << 'QEMU'
#!/bin/bash
VUKOV_MACOS_DIR="$HOME/.vukov/macos"
QEMU_IMG="$VUKOV_MACOS_DIR/macos.qcow2"
[ ! -f "$QEMU_IMG" ] && echo "[!] No macOS image at $QEMU_IMG" && echo "    Create with: qemu-img create -f qcow2 $QEMU_IMG 64G" && exit 1
[ ! -f "$VUKOV_MACOS_DIR/OVMF_VARS.fd" ] && cp /usr/share/OVMF/OVMF_VARS.fd "$VUKOV_MACOS_DIR/"
echo "[vukov-macos] Starting QEMU macOS VM..."
qemu-system-x86_64 \
    -enable-kvm -m 4096 -smp 4,cores=2 \
    -cpu Penryn,kvm=on,vendor=GenuineIntel,+invtsc \
    -machine q35 \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \
    -drive if=pflash,format=raw,file="$VUKOV_MACOS_DIR/OVMF_VARS.fd" \
    -device isa-applesmc,osk="ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc" \
    -drive file="$QEMU_IMG",if=virtio \
    -vga vmware -display gtk \
    -device usb-kbd -device usb-mouse \
    -netdev user,id=net0 -device vmxnet3,netdev=net0
QEMU
    chmod +x "$VUKOV_MACOS_DIR/launch-qemu.sh"
    echo -e "${GREEN}[✓]${RESET} QEMU path ready."
}

setup_shell() {
    echo -e "${CYAN}[4/4]${RESET} Setting up macOS shell environment..."
    cat > "$VUKOV_MACOS_DIR/macos-env.sh" << 'ENV'
#!/bin/bash
export VUKOV_MACOS=1
export TERM_PROGRAM="Apple_Terminal"
export LANG="${LANG:-en_US.UTF-8}"
export HOMEBREW_PREFIX="/usr/local"
echo "  [vukov-macos] macOS environment loaded — type 'exit' to leave"
exec bash --rcfile <(echo "PS1='macos@vukovos % '")
ENV
    chmod +x "$VUKOV_MACOS_DIR/macos-env.sh"
    echo -e "${GREEN}[✓]${RESET} Shell ready."
}

show_status() {
    command -v darling > /dev/null 2>&1 && \
        echo -e "  ${GREEN}[✓]${RESET} Darling: installed" || \
        echo -e "  ${RED}[✗]${RESET} Darling: not installed"
    command -v qemu-system-x86_64 > /dev/null 2>&1 && \
        echo -e "  ${GREEN}[✓]${RESET} QEMU: installed" || \
        echo -e "  ${YELLOW}[!]${RESET} QEMU: not installed"
    [ -f "$QEMU_IMG" ] && \
        echo -e "  ${GREEN}[✓]${RESET} macOS image: $(du -h $QEMU_IMG | cut -f1)" || \
        echo -e "  ${YELLOW}[!]${RESET} macOS image: not found"
    [ -d "$VUKOV_MACOS_DIR/patches" ] && \
        echo -e "  ${GREEN}[✓]${RESET} VukovOS patches: applied" || \
        echo -e "  ${YELLOW}[!]${RESET} Patches: not applied"
    [ -S "/tmp/.X11-unix/X0" ] || [ -n "$WAYLAND_DISPLAY" ] && \
        echo -e "  ${GREEN}[✓]${RESET} Display: available" || \
        echo -e "  ${YELLOW}[!]${RESET} Display: not detected"
}

case "${1:-status}" in
    install)
        banner; check_deps; install_darling
        apply_patches; setup_qemu; setup_shell
        echo "" && echo -e "${GREEN}${BOLD}[✓] vukov-macos ready! 🐺${RESET}"
        echo -e "  ${DIM}vukov macos shell — enter macOS shell"
        echo -e "  vukov macos run <app> — run macOS binary"
        echo -e "  vukov macos vm — launch full QEMU VM${RESET}"
        sudo cp "$0" /usr/local/bin/vukov-macos.sh
        sudo chmod +x /usr/local/bin/vukov-macos.sh
        ;;
    run)
        shift
        [ -z "$1" ] && echo -e "${RED}[!]${RESET} Usage: vukov macos run <app>" && exit 1
        source "$VUKOV_MACOS_DIR/patches/display-bridge.sh" 2>/dev/null
        command -v darling > /dev/null 2>&1 && darling shell "$@" || \
            { echo -e "${RED}[!]${RESET} Darling not installed. Run: vukov macos install"; exit 1; }
        ;;
    shell)
        banner
        command -v darling > /dev/null 2>&1 && \
            { source "$VUKOV_MACOS_DIR/patches/display-bridge.sh" 2>/dev/null; darling shell; } || \
            source "$VUKOV_MACOS_DIR/macos-env.sh"
        ;;
    vm)     banner; bash "$VUKOV_MACOS_DIR/launch-qemu.sh" ;;
    status) banner; show_status ;;
    logs)   tail -50 "$VUKOV_MACOS_DIR/syscall.log" 2>/dev/null || echo "No log." ;;
    *)
        echo "Usage: vukov macos [install|run <app>|shell|vm|status|logs]"
        ;;
esac
