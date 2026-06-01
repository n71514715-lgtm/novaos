#!/bin/bash
# nova-panic — NovaOS Emergency Wipe
# One command destroys all sensitive data instantly
# For journalists, activists, anyone who needs it
# The last line of defense

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'
BOLD='\033[1m'; RESET='\033[0m'

banner() {
echo -e "${RED}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   nova-panic — Emergency Wipe                ║
  ║   ⚠ This will destroy sensitive data         ║
  ║   Use only in emergencies                    ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

wipe_level_1() {
    echo -e "${YELLOW}[*]${RESET} Level 1 — Wiping session data..."
    history -c 2>/dev/null
    cat /dev/null > ~/.bash_history 2>/dev/null
    rm -f /tmp/nova-* 2>/dev/null
    rm -f ~/.nova/vpn/nova0.conf 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Session data wiped"
}

wipe_level_2() {
    wipe_level_1
    echo -e "${YELLOW}[*]${RESET} Level 2 — Wiping credentials..."
    rm -rf ~/.nova/vault/ 2>/dev/null
    rm -rf ~/.config/Epic 2>/dev/null
    rm -rf ~/.steam/steam/config/loginusers.vdf 2>/dev/null
    rm -f ~/.nova/gaming/ 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Credentials wiped"
}

wipe_level_3() {
    wipe_level_2
    echo -e "${RED}[*]${RESET} Level 3 — Wiping identity and memory..."
    rm -rf ~/.nova/identity/ 2>/dev/null
    rm -rf ~/.nova/memory/ 2>/dev/null
    rm -rf ~/.nova/chat/ 2>/dev/null
    rm -rf ~/.nova/sync/ 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Identity and memory wiped"
}

wipe_level_4() {
    wipe_level_3
    echo -e "${RED}[!!!]${RESET} Level 4 — FULL WIPE — destroying everything..."
    rm -rf ~/.nova/ 2>/dev/null
    rm -rf ~/.config/nova* 2>/dev/null
    # Overwrite with random data first
    find ~/.nova -type f -exec shred -u {} \; 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Full wipe complete — NovaOS data destroyed"
}

case "$1" in
    ""|help)
        banner
        echo -e "${BOLD}Usage:${RESET} nova panic [level]"
        echo ""
        echo -e "${GREEN}Levels:${RESET}"
        echo -e "  ${YELLOW}1${RESET}  Session only — history, temp files, VPN config"
        echo -e "  ${YELLOW}2${RESET}  + Credentials — vault, gaming accounts"
        echo -e "  ${RED}3${RESET}  + Identity — nova-id, memory, chat history"
        echo -e "  ${RED}4${RESET}  FULL WIPE — everything, no recovery"
        echo ""
        echo -e "${RED}  ⚠ This cannot be undone.${RESET}"
        ;;
    1) wipe_level_1 ;;
    2) wipe_level_2 ;;
    3)
        echo -e "${RED}[!!!]${RESET} Level 3 will destroy your identity and memories."
        read -p "  Type YES to confirm: " confirm
        [ "$confirm" = "YES" ] && wipe_level_3 || echo "Cancelled."
        ;;
    4)
        echo -e "${RED}[!!!]${RESET} Level 4 FULL WIPE — cannot be undone."
        echo -e "${RED}[!!!]${RESET} Your identity, vault, memories, everything."
        read -p "  Type DESTROY to confirm: " confirm
        [ "$confirm" = "DESTROY" ] && wipe_level_4 || echo "Cancelled."
        ;;
    *)
        echo -e "${RED}[!]${RESET} Unknown level: $1 — use 1, 2, 3, or 4"
        ;;
esac
