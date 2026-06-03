#!/bin/bash
# nova-vpn — NovaOS WireGuard VPN Manager
# One command encrypted VPN tunnel
# Zero logs. Zero tracking. Zero trust.

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

VPN_DIR="$HOME/.nova/vpn"
CONFIG_FILE="$VPN_DIR/nova0.conf"
KEYS_FILE="$VPN_DIR/keys.json"

banner() {
echo -e "${GREEN}"
cat << 'BANNER'
  ╔═══════════════════════════════════════╗
  ║   nova-vpn — Encrypted Tunnel         ║
  ║   Protocol: WireGuard (ChaCha20)      ║
  ║   Logs: none  |  Tracking: none       ║
  ╚═══════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

generate_keys() {
    echo -e "${CYAN}[*]${RESET} Generating WireGuard keypair..."
    mkdir -p "$VPN_DIR"
    PRIVATE_KEY=$(wg genkey)
    PUBLIC_KEY=$(echo "$PRIVATE_KEY" | wg pubkey)
    echo -e "${GREEN}[✓]${RESET} Private key generated"
    echo -e "${GREEN}[✓]${RESET} Public key: ${BOLD}$PUBLIC_KEY${RESET}"
    cat > "$KEYS_FILE" << KEYS
{
  "private_key": "$PRIVATE_KEY",
  "public_key": "$PUBLIC_KEY",
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
KEYS
    chmod 600 "$KEYS_FILE"
    echo -e "${GREEN}[✓]${RESET} Keys saved to: $KEYS_FILE"
    echo ""
    echo -e "${CYAN}[*]${RESET} Your public key (share with VPN server):"
    echo -e "${BOLD}$PUBLIC_KEY${RESET}"
}

create_config() {
    if [ ! -f "$KEYS_FILE" ]; then
        echo -e "${RED}[!]${RESET} No keys found. Run: nova vpn genkeys"
        exit 1
    fi
    PRIVATE_KEY=$(python3 -c "import json; print(json.load(open('$KEYS_FILE'))['private_key'])")
    echo -e "${CYAN}[*]${RESET} Creating WireGuard config..."
    cat > "$CONFIG_FILE" << WGCONF
[Interface]
PrivateKey = $PRIVATE_KEY
Address = 10.0.0.2/24
DNS = 1.1.1.1, 1.0.0.1

# Add your server peer below
# [Peer]
# PublicKey = SERVER_PUBLIC_KEY
# Endpoint = SERVER_IP:51820
# AllowedIPs = 0.0.0.0/0
# PersistentKeepalive = 25
WGCONF
    chmod 600 "$CONFIG_FILE"
    echo -e "${GREEN}[✓]${RESET} Config created: $CONFIG_FILE"
    echo -e "${CYAN}[!]${RESET} Edit the [Peer] section with your server details"
}

show_status() {
    banner
    echo -e "  ${CYAN}Keys:${RESET}   $([ -f "$KEYS_FILE" ] && echo "${GREEN}generated${RESET}" || echo "${RED}not generated${RESET}")"
    echo -e "  ${CYAN}Config:${RESET} $([ -f "$CONFIG_FILE" ] && echo "${GREEN}ready${RESET}" || echo "${RED}not created${RESET}")"
    if command -v wg &>/dev/null; then
        echo -e "  ${CYAN}WireGuard:${RESET} ${GREEN}available${RESET} ($(wg --version))"
    else
        echo -e "  ${CYAN}WireGuard:${RESET} ${RED}not found${RESET}"
    fi
    echo ""
    if [ -f "$KEYS_FILE" ]; then
        PUB=$(python3 -c "import json; print(json.load(open('$KEYS_FILE'))['public_key'])" 2>/dev/null)
        echo -e "  ${CYAN}Public key:${RESET} $PUB"
    fi
}

show_help() {
    banner
    echo -e "${BOLD}Usage:${RESET} nova vpn <command>"
    echo ""
    echo -e "${GREEN}Commands:${RESET}"
    echo -e "  ${CYAN}genkeys${RESET}     Generate WireGuard keypair"
    echo -e "  ${CYAN}config${RESET}      Create VPN config file"
    echo -e "  ${CYAN}status${RESET}      Show VPN status and keys"
    echo -e "  ${CYAN}start${RESET}       Start VPN tunnel (requires root + server)"
    echo -e "  ${CYAN}stop${RESET}        Stop VPN tunnel"
    echo ""
    echo -e "${CYAN}Quick start:${RESET}"
    echo -e "  1. nova vpn genkeys"
    echo -e "  2. nova vpn config"
    echo -e "  3. Edit ~/.nova/vpn/nova0.conf with server details"
    echo -e "  4. nova vpn start"
    echo ""
}

case "$1" in
    genkeys)    generate_keys ;;
    config)     create_config ;;
    status)     show_status ;;
    start)
        echo -e "${CYAN}[*]${RESET} Starting VPN tunnel..."
        sudo wg-quick up "$CONFIG_FILE" 2>&1 || echo -e "${RED}[!]${RESET} Need server config — run: nova vpn config"
        ;;
    stop)
        echo -e "${CYAN}[*]${RESET} Stopping VPN tunnel..."
        sudo wg-quick down "$CONFIG_FILE" 2>&1
        ;;
    help|"")    show_help ;;
    *)          echo -e "${RED}[!]${RESET} Unknown: $1 — run 'nova vpn help'" ;;
esac
