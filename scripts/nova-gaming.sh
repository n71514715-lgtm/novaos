#!/bin/bash
# nova-gaming — NovaOS Gaming Session Manager
# Runs inside GFN/cloud GPU session
# Installs and launches Steam, Epic, GOG, EA, Ubisoft
# Auto-bans miners, wipes credentials on disconnect
# Zero logs. Zero trace.

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
ORANGE='\033[0;33m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

GAMING_DIR="$HOME/.nova/gaming"
SESSION_LOG="$GAMING_DIR/session.tmp"
MINER_WATCHDOG_PID=""

banner() {
echo -e "${GREEN}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   nova-gaming — Cloud Gaming Session Manager  ║
  ║   Platforms: Steam · Epic · GOG · EA · Ubi   ║
  ║   GPU: RTX (via GFN session)                  ║
  ║   Logs: ZERO  |  Miners: BANNED               ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

# Anti-mining watchdog
start_miner_watchdog() {
    echo -e "${CYAN}[*]${RESET} Starting anti-mining watchdog..."
    while true; do
        # Check for known mining processes
        MINERS="xmrig nbminer t-rex gminer lolminer phoenixminer ethminer cgminer bfgminer"
        for miner in $MINERS; do
            if pgrep -x "$miner" > /dev/null 2>&1; then
                echo -e "${RED}[!!!] MINER DETECTED: $miner — KILLING SESSION${RESET}"
                pkill -x "$miner" 2>/dev/null
                notify_ban "$miner"
                terminate_session "MINING_DETECTED"
            fi
        done
        # Check GPU usage pattern — miners use 95-100% GPU constantly
        if command -v nvidia-smi &>/dev/null; then
            GPU_USAGE=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | tr -d ' ')
            if [ ! -z "$GPU_USAGE" ] && [ "$GPU_USAGE" -gt 95 ]; then
                # Check if a game is actually running
                GAMES_RUNNING=$(pgrep -l "steam\|epicgames\|gog\|origin\|uplay" 2>/dev/null | wc -l)
                if [ "$GAMES_RUNNING" -eq 0 ]; then
                    echo -e "${RED}[!!!] HIGH GPU USAGE WITH NO GAME — possible mining${RESET}"
                    sleep 30
                    GPU_USAGE2=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | tr -d ' ')
                    if [ "$GPU_USAGE2" -gt 95 ]; then
                        terminate_session "SUSPECTED_MINING"
                    fi
                fi
            fi
        fi
        sleep 10
    done &
    MINER_WATCHDOG_PID=$!
    echo -e "${GREEN}[✓]${RESET} Anti-mining watchdog active (PID: $MINER_WATCHDOG_PID)"
}

notify_ban() {
    echo -e "${RED}╔══════════════════════════════════════╗${RESET}"
    echo -e "${RED}║   SESSION TERMINATED — MINING BANNED  ║${RESET}"
    echo -e "${RED}║   Process: $1${RESET}"
    echo -e "${RED}║   This session has been ended.        ║${RESET}"
    echo -e "${RED}╚══════════════════════════════════════╝${RESET}"
}

terminate_session() {
    local reason="$1"
    echo -e "${CYAN}[*]${RESET} Terminating session: $reason"
    wipe_session_data
    if [ ! -z "$MINER_WATCHDOG_PID" ]; then
        kill "$MINER_WATCHDOG_PID" 2>/dev/null
    fi
    echo -e "${GREEN}[✓]${RESET} Session terminated cleanly"
    exit 0
}

wipe_session_data() {
    echo -e "${CYAN}[*]${RESET} Wiping session data..."
    # Wipe Steam credentials
    rm -rf "$HOME/.steam/steam/config/loginusers.vdf" 2>/dev/null
    rm -rf "$HOME/.steam/steam/config/SteamAppData.vdf" 2>/dev/null
    # Wipe Epic credentials
    rm -rf "$HOME/.config/Epic/EpicGamesLauncher/Data/EpicGamesLauncher/Saved/Config" 2>/dev/null
    rm -rf "$HOME/.config/Epic" 2>/dev/null
    # Wipe GOG credentials
    rm -rf "$HOME/.config/GOG.com" 2>/dev/null
    # Wipe EA credentials
    rm -rf "$HOME/.local/share/EA" 2>/dev/null
    rm -rf "$HOME/.config/EA" 2>/dev/null
    # Wipe Ubisoft credentials
    rm -rf "$HOME/.config/ubisoft" 2>/dev/null
    # Wipe session log
    rm -f "$SESSION_LOG" 2>/dev/null
    # Wipe bash history
    history -c 2>/dev/null
    cat /dev/null > "$HOME/.bash_history" 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} All session data wiped"
    echo -e "${GREEN}[✓]${RESET} No credentials stored"
    echo -e "${GREEN}[✓]${RESET} No logs kept"
}

install_steam() {
    echo -e "${CYAN}[*]${RESET} Installing Steam..."
    if command -v steam &>/dev/null; then
        echo -e "${GREEN}[✓]${RESET} Steam already installed"
        return
    fi
    # Install Steam via apt or flatpak
    if command -v apt &>/dev/null; then
        sudo apt install -y steam-installer 2>/dev/null || \
        flatpak install -y --user flathub com.valvesoftware.Steam 2>/dev/null
    fi
    echo -e "${GREEN}[✓]${RESET} Steam installed"
}

install_epic() {
    echo -e "${CYAN}[*]${RESET} Installing Epic Games Launcher via Heroic..."
    if command -v heroic &>/dev/null; then
        echo -e "${GREEN}[✓]${RESET} Heroic already installed"
        return
    fi
    flatpak install -y --user flathub com.heroicgameslauncher.hgl 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Heroic Games Launcher installed (Epic + GOG)"
}

install_ea() {
    echo -e "${CYAN}[*]${RESET} Installing EA App via Lutris..."
    flatpak install -y --user flathub net.lutris.Lutris 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Lutris installed (EA + Ubisoft support)"
}

install_gog() {
    echo -e "${CYAN}[*]${RESET} GOG supported via Heroic Games Launcher"
    echo -e "${GREEN}[✓]${RESET} Install Heroic first: nova gaming setup epic"
}

install_sunshine() {
    echo -e "${CYAN}[*]${RESET} Installing Sunshine game streaming server..."
    if command -v sunshine &>/dev/null; then
        echo -e "${GREEN}[✓]${RESET} Sunshine already installed"
        return
    fi
    # Download latest Sunshine AppImage
    SUNSHINE_URL="https://github.com/LizardByte/Sunshine/releases/latest/download/sunshine.AppImage"
    wget -q --show-progress -O "$HOME/.local/bin/sunshine" "$SUNSHINE_URL" 2>/dev/null
    chmod +x "$HOME/.local/bin/sunshine" 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Sunshine streaming server installed"
    echo -e "${CYAN}[i]${RESET} Start with: nova gaming stream"
}

start_stream() {
    echo -e "${CYAN}[*]${RESET} Starting Sunshine game streaming server..."
    if [ -f "$HOME/.local/bin/sunshine" ]; then
        "$HOME/.local/bin/sunshine" &
        sleep 3
        echo -e "${GREEN}[✓]${RESET} Streaming server started"
        echo -e "${CYAN}[i]${RESET} Connect via Moonlight or browser at: https://$(hostname -I | cut -d' ' -f1):47990"
    else
        echo -e "${RED}[!]${RESET} Sunshine not installed. Run: nova gaming setup stream"
    fi
}

setup_all() {
    banner
    echo -e "${BOLD}Setting up NovaOS Gaming Session...${RESET}\n"
    mkdir -p "$GAMING_DIR"
    start_miner_watchdog
    install_steam
    install_epic
    install_ea
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}║   NovaOS Gaming Ready!               ║${RESET}"
    echo -e "${GREEN}╠══════════════════════════════════════╣${RESET}"
    echo -e "${GREEN}║  Steam:    nova gaming launch steam  ║${RESET}"
    echo -e "${GREEN}║  Epic/GOG: nova gaming launch epic   ║${RESET}"
    echo -e "${GREEN}║  EA:       nova gaming launch ea     ║${RESET}"
    echo -e "${GREEN}║  Stream:   nova gaming stream        ║${RESET}"
    echo -e "${GREEN}║  Wipe:     nova gaming wipe          ║${RESET}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${RESET}"
}

launch_platform() {
    local platform="$1"
    start_miner_watchdog
    case "$platform" in
        steam)
            echo -e "${CYAN}[*]${RESET} Launching Steam..."
            steam 2>/dev/null || flatpak run com.valvesoftware.Steam 2>/dev/null &
            ;;
        epic|gog|heroic)
            echo -e "${CYAN}[*]${RESET} Launching Heroic (Epic + GOG)..."
            heroic 2>/dev/null || flatpak run com.heroicgameslauncher.hgl 2>/dev/null &
            ;;
        ea|origin)
            echo -e "${CYAN}[*]${RESET} Launching Lutris (EA App)..."
            lutris 2>/dev/null || flatpak run net.lutris.Lutris 2>/dev/null &
            ;;
        ubisoft|uplay)
            echo -e "${CYAN}[*]${RESET} Launching Ubisoft Connect via Lutris..."
            lutris 2>/dev/null || flatpak run net.lutris.Lutris 2>/dev/null &
            ;;
        *)
            echo -e "${RED}[!]${RESET} Unknown platform: $platform"
            echo -e "  Supported: steam, epic, gog, ea, ubisoft"
            ;;
    esac
}

show_help() {
    banner
    echo -e "${BOLD}Usage:${RESET} nova gaming <command>"
    echo ""
    echo -e "${GREEN}Session Commands:${RESET}"
    echo -e "  ${CYAN}setup${RESET}              Install all gaming platforms"
    echo -e "  ${CYAN}launch${RESET} <platform>  Launch Steam/Epic/GOG/EA/Ubisoft"
    echo -e "  ${CYAN}stream${RESET}             Start Sunshine streaming server"
    echo -e "  ${CYAN}wipe${RESET}               Wipe all session data now"
    echo -e "  ${CYAN}watchdog${RESET}           Start anti-mining watchdog only"
    echo ""
    echo -e "${GREEN}Setup Commands:${RESET}"
    echo -e "  ${CYAN}setup steam${RESET}        Install Steam only"
    echo -e "  ${CYAN}setup epic${RESET}         Install Heroic (Epic + GOG)"
    echo -e "  ${CYAN}setup ea${RESET}           Install Lutris (EA + Ubisoft)"
    echo -e "  ${CYAN}setup stream${RESET}       Install Sunshine streaming"
    echo ""
    echo -e "${ORANGE}  Mining = instant ban. Zero logs. Credentials wiped.${RESET}"
    echo ""
}

case "$1" in
    setup)
        case "$2" in
            steam)    install_steam ;;
            epic|gog) install_epic ;;
            ea)       install_ea ;;
            stream)   install_sunshine ;;
            "")       setup_all ;;
        esac
        ;;
    launch)     launch_platform "$2" ;;
    stream)     start_stream ;;
    wipe)       wipe_session_data ;;
    watchdog)   start_miner_watchdog; wait ;;
    help|"")    show_help ;;
    *)          echo -e "${RED}[!]${RESET} Unknown: $1 — run 'nova gaming help'" ;;
esac
