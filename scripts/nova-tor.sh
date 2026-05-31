#!/bin/bash
# nova-tor — NovaOS Tor Anonymity Layer
# Route all traffic through Tor with one command
# Beats Tails on ease of use
# Zero configuration needed

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

banner() {
echo -e "${PURPLE}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   nova-tor — Anonymity Layer                 ║
  ║   All traffic routed through Tor             ║
  ║   IP hidden. Location hidden. You hidden.    ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

start_tor() {
    banner
    echo -e "${CYAN}[*]${RESET} Starting Tor daemon..."
    sudo service tor start 2>/dev/null || sudo tor --RunAsDaemon 1 2>/dev/null
    sleep 3
    if pgrep -x tor > /dev/null; then
        echo -e "${GREEN}[✓]${RESET} Tor is running"
        echo -e "${GREEN}[✓]${RESET} SOCKS5 proxy: 127.0.0.1:9050"
        echo -e "${GREEN}[✓]${RESET} Control port: 127.0.0.1:9051"
        echo ""
        echo -e "${CYAN}[*]${RESET} To route a command through Tor:"
        echo -e "    ${BOLD}torsocks curl https://check.torproject.org/api/ip${RESET}"
        echo ""
        echo -e "${CYAN}[*]${RESET} To check your Tor IP:"
        echo -e "    ${BOLD}nova tor ip${RESET}"
    else
        echo -e "${RED}[!]${RESET} Failed to start Tor"
    fi
}

stop_tor() {
    sudo service tor stop 2>/dev/null || sudo pkill tor 2>/dev/null
    echo -e "${GREEN}[✓]${RESET} Tor stopped"
}

check_ip() {
    echo -e "${CYAN}[*]${RESET} Checking your Tor IP..."
    REAL_IP=$(curl -s https://api.ipify.org 2>/dev/null)
    TOR_IP=$(torsocks curl -s https://api.ipify.org 2>/dev/null)
    echo -e "  ${RED}Real IP:${RESET}  $REAL_IP"
    echo -e "  ${GREEN}Tor IP:${RESET}   ${BOLD}$TOR_IP${RESET}"
    if [ "$REAL_IP" != "$TOR_IP" ] && [ ! -z "$TOR_IP" ]; then
        echo -e "\n  ${GREEN}[✓] Your real IP is hidden${RESET}"
    else
        echo -e "\n  ${RED}[!] Tor may not be routing correctly${RESET}"
    fi
}

new_identity() {
    echo -e "${CYAN}[*]${RESET} Requesting new Tor identity..."
    echo -e 'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT' | \
        nc 127.0.0.1 9051 2>/dev/null && \
        echo -e "${GREEN}[✓]${RESET} New identity assigned — new IP" || \
        echo -e "${RED}[!]${RESET} Could not signal Tor — is it running?"
}

run_with_tor() {
    shift
    echo -e "${CYAN}[*]${RESET} Running through Tor: $@"
    torsocks "$@"
}

show_status() {
    banner
    if pgrep -x tor > /dev/null; then
        echo -e "  ${GREEN}[✓]${RESET} Tor: running"
        echo -e "  ${GREEN}[✓]${RESET} SOCKS5: 127.0.0.1:9050"
    else
        echo -e "  ${RED}[✗]${RESET} Tor: not running — run: nova tor start"
    fi
}

show_help() {
    banner
    echo -e "${BOLD}Usage:${RESET} nova tor <command>"
    echo ""
    echo -e "${GREEN}Commands:${RESET}"
    echo -e "  ${PURPLE}start${RESET}         Start Tor daemon"
    echo -e "  ${PURPLE}stop${RESET}          Stop Tor daemon"
    echo -e "  ${PURPLE}status${RESET}        Show Tor status"
    echo -e "  ${PURPLE}ip${RESET}            Compare real vs Tor IP"
    echo -e "  ${PURPLE}new${RESET}           Get new Tor identity"
    echo -e "  ${PURPLE}run${RESET} <cmd>     Run command through Tor"
    echo ""
    echo -e "${GREEN}Examples:${RESET}"
    echo -e "  nova tor start"
    echo -e "  nova tor ip"
    echo -e "  nova tor run curl https://example.com"
    echo -e "  nova tor new"
    echo ""
    echo -e "${PURPLE}  Your location. Hidden. Always.${RESET}"
}

case "$1" in
    start)   start_tor ;;
    stop)    stop_tor ;;
    status)  show_status ;;
    ip)      check_ip ;;
    new)     new_identity ;;
    run)     run_with_tor "$@" ;;
    help|"") show_help ;;
    *)       echo -e "${RED}[!]${RESET} Unknown: $1" ;;
esac
