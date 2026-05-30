#!/bin/bash
# nova-boot — NovaOS Boot Experience
# Runs on every terminal open
# Makes NovaOS feel alive

GREEN='\033[0;32m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Typewriter effect
type_text() {
    text="$1"
    color="$2"
    delay="${3:-0.03}"
    echo -ne "${color}"
    for ((i=0; i<${#text}; i++)); do
        echo -ne "${text:$i:1}"
        sleep "$delay"
    done
    echo -e "${RESET}"
}

clear

# Draw coat of arms
echo -e "${GREEN}"
cat << 'BANNER'
        .·:+++++++++++++++++++:·.
      ·'  ╔══════════════════╗  '·
    ·'    ║  \   ·|·   /  ║    '·
   /      ║   \  ·N·  /   ║      \
  |    ✦  ╠────[✦ N ✦]────╣  ✦   |
  |       ║  /  ·|·   \   ║       |
  |  ·····╬·················╬·····  |
  |  ✦    ║  ⊗─────────))) ║   ✦  |
  |  star  ║  ⊗  eye  (🔒) ║  wave |
  |  burst ║  ⊗─────────))) ║  sig  |
  |  ·····╬·················╬·····  |
  |       ║   circuit  [N]  ║       |
   \      ╚══════════════════╝      /
    '·       PRIVATA · LIBERA      ·'
      '·         SECURA          ·'
        '·:+[ N O V A O S ]+:·'
             0.1  ·  SPECTRE
BANNER
echo -e "${RESET}"

sleep 0.3

# Typewriter intro
type_text "  Welcome to NovaOS 0.1 (Spectre)" "$BOLD$GREEN" 0.04
type_text "  Private. Encrypted. Yours." "$CYAN" 0.05
echo ""
sleep 0.2

# Quick system check
echo -e "${DIM}  Initializing systems...${RESET}"
sleep 0.3

# Encryption
echo -ne "  ${GREEN}[✓]${RESET} NovaCrypt  "
echo -e "${GREEN}online${RESET} ${DIM}— ChaCha20 + AES-256 + Argon2id${RESET}"
sleep 0.1

# AI Brain
if curl -s http://localhost:11434/health 2>/dev/null | grep -q "ok"; then
    echo -ne "  ${GREEN}[✓]${RESET} NovaBrain  "
    echo -e "${GREEN}online${RESET} ${DIM}— Phi-3 Mini ready${RESET}"
else
    echo -ne "  ${CYAN}[~]${RESET} NovaBrain  "
    echo -e "${CYAN}standby${RESET} ${DIM}— run: nova brain-start${RESET}"
fi
sleep 0.1

# Guard
echo -ne "  ${GREEN}[✓]${RESET} nova-guard "
echo -e "${GREEN}ready${RESET} ${DIM}— real-time encryption watchdog${RESET}"
sleep 0.1

# VPN
if [ -f "$HOME/.nova/vpn/keys.json" ]; then
    echo -ne "  ${GREEN}[✓]${RESET} nova-vpn   "
    echo -e "${GREEN}configured${RESET} ${DIM}— WireGuard keys ready${RESET}"
else
    echo -ne "  ${CYAN}[~]${RESET} nova-vpn   "
    echo -e "${CYAN}unconfigured${RESET} ${DIM}— run: nova vpn genkeys${RESET}"
fi
sleep 0.2

echo ""
echo -e "  ${DIM}$(date '+%A, %B %d %Y  %H:%M:%S')${RESET}"
echo ""

# NovaBrain greeting
HOUR=$(date +%H)
if [ "$HOUR" -lt 12 ]; then
    GREETING="Good morning. NovaOS is ready."
elif [ "$HOUR" -lt 18 ]; then
    GREETING="Good afternoon. NovaOS is ready."
else
    GREETING="Good evening. NovaOS is ready."
fi

type_text "  [NovaBrain] $GREETING" "$CYAN" 0.03
type_text "  [NovaBrain] Type 'nova help' to see all commands." "$DIM" 0.02
echo ""
echo -e "  ${PURPLE}${BOLD}PRIVATA · LIBERA · SECURA${RESET}"
echo ""
