#!/bin/bash
# nova-id — NovaOS Cryptographic Identity System
# Your identity. Your keys. Your proof.
# Algorithm: Ed25519 (256-bit) — same as Signal, SSH
# Zero central authority. Zero servers. Zero trust required.

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

ID_DIR="$HOME/.nova/identity"
PRIVATE_KEY="$ID_DIR/nova-id.pem"
PUBLIC_KEY="$ID_DIR/nova-id.pub"
IDENTITY_FILE="$ID_DIR/identity.json"

banner() {
echo -e "${GREEN}"
cat << 'BANNER'
  ╔═══════════════════════════════════════════╗
  ║   nova-id — Cryptographic Identity        ║
  ║   Algorithm: Ed25519 (256-bit)            ║
  ║   Authority: YOU — no servers, no CA      ║
  ╚═══════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

generate_identity() {
    local name="$1"
    local email="$2"
    [ -z "$name" ] && echo -e "${RED}[!] Usage: nova id generate \"Name\" \"email\"${RESET}" && exit 1
    mkdir -p "$ID_DIR" && chmod 700 "$ID_DIR"
    echo -e "${CYAN}[*]${RESET} Generating Ed25519 identity keypair..."
    openssl genpkey -algorithm ed25519 -out "$PRIVATE_KEY" 2>/dev/null
    openssl pkey -in "$PRIVATE_KEY" -pubout -out "$PUBLIC_KEY" 2>/dev/null
    chmod 600 "$PRIVATE_KEY" && chmod 644 "$PUBLIC_KEY"
    FINGERPRINT=$(openssl pkey -in "$PUBLIC_KEY" -pubin -outform DER 2>/dev/null | sha256sum | cut -d' ' -f1 | fold -w4 | paste -sd':' | head -c 47)
    cat > "$IDENTITY_FILE" << IDEOF
{
  "name": "$name",
  "email": "$email",
  "fingerprint": "$FINGERPRINT",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "os": "NovaOS 0.1 (Spectre)",
  "algorithm": "Ed25519"
}
IDEOF
    chmod 600 "$IDENTITY_FILE"
    echo -e "${GREEN}[✓]${RESET} Identity created: ${BOLD}$name${RESET}"
    echo -e "${GREEN}[✓]${RESET} Algorithm: Ed25519 (256-bit)"
    echo -e "${GREEN}[✓]${RESET} Fingerprint: ${BOLD}$FINGERPRINT${RESET}"
}

sign_file() {
    local file="$1"
    [ -z "$file" ] || [ ! -f "$file" ] && echo -e "${RED}[!] Usage: nova id sign <file>${RESET}" && exit 1
    [ ! -f "$PRIVATE_KEY" ] && echo -e "${RED}[!] No identity. Run: nova id generate${RESET}" && exit 1
    openssl pkeyutl -sign -inkey "$PRIVATE_KEY" -in "$file" -out "$file.novasig" 2>/dev/null
    NAME=$(python3 -c "import json; print(json.load(open('$IDENTITY_FILE'))['name'])" 2>/dev/null)
    FP=$(python3 -c "import json; print(json.load(open('$IDENTITY_FILE'))['fingerprint'])" 2>/dev/null)
    echo -e "${GREEN}[✓]${RESET} Signed: ${BOLD}$file${RESET}"
    echo -e "${GREEN}[✓]${RESET} Signature: ${BOLD}$file.novasig${RESET}"
    echo -e "${CYAN}[i]${RESET} Signer: $NAME | Fingerprint: $FP"
}

verify_file() {
    local file="$1"
    local sigfile="${2:-$file.novasig}"
    local pubkey="${3:-$PUBLIC_KEY}"
    [ -z "$file" ] && echo -e "${RED}[!] Usage: nova id verify <file> [sig] [pubkey]${RESET}" && exit 1
    [ ! -f "$sigfile" ] && echo -e "${RED}[!] Signature not found: $sigfile${RESET}" && exit 1
    openssl pkeyutl -verify -pubin -inkey "$pubkey" \
        -in "$file" -sigfile "$sigfile" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] VERIFIED — signature is valid${RESET}"
        echo -e "${GREEN}[✓] File has not been tampered with${RESET}"
    else
        echo -e "${RED}[✗] INVALID — signature verification failed${RESET}"
        echo -e "${RED}[✗] File may have been tampered with${RESET}"
    fi
}

show_identity() {
    [ ! -f "$IDENTITY_FILE" ] && echo -e "${RED}[!] No identity. Run: nova id generate${RESET}" && exit 1
    banner
    NAME=$(python3 -c "import json; d=json.load(open('$IDENTITY_FILE')); print(d['name'])" 2>/dev/null)
    EMAIL=$(python3 -c "import json; d=json.load(open('$IDENTITY_FILE')); print(d['email'])" 2>/dev/null)
    FP=$(python3 -c "import json; d=json.load(open('$IDENTITY_FILE')); print(d['fingerprint'])" 2>/dev/null)
    CREATED=$(python3 -c "import json; d=json.load(open('$IDENTITY_FILE')); print(d['created'])" 2>/dev/null)
    echo -e "  ${CYAN}Name:${RESET}        $NAME"
    echo -e "  ${CYAN}Email:${RESET}       $EMAIL"
    echo -e "  ${CYAN}Created:${RESET}     $CREATED"
    echo -e "  ${CYAN}Algorithm:${RESET}   Ed25519 (256-bit)"
    echo -e "  ${CYAN}Fingerprint:${RESET} ${BOLD}$FP${RESET}"
    echo ""
}

export_pubkey() {
    [ ! -f "$PUBLIC_KEY" ] && echo -e "${RED}[!] No identity. Run: nova id generate${RESET}" && exit 1
    echo -e "${CYAN}[*]${RESET} Your NovaOS public key:"
    echo ""
    cat "$PUBLIC_KEY"
}

show_help() {
    banner
    echo -e "${BOLD}Usage:${RESET} nova id <command> [args]"
    echo ""
    echo -e "${GREEN}Commands:${RESET}"
    echo -e "  ${CYAN}generate${RESET} \"Name\" \"email\"   Create identity keypair"
    echo -e "  ${CYAN}show${RESET}                     Show your identity"
    echo -e "  ${CYAN}sign${RESET} <file>              Sign a file"
    echo -e "  ${CYAN}verify${RESET} <file> [sig]      Verify a signature"
    echo -e "  ${CYAN}export${RESET}                   Export public key"
    echo ""
    echo -e "${PURPLE}  Your identity. Your keys. Your proof.${RESET}"
}

case "$1" in
    generate)  generate_identity "$2" "$3" ;;
    show)      show_identity ;;
    sign)      sign_file "$2" ;;
    verify)    verify_file "$2" "$3" "$4" ;;
    export)    export_pubkey ;;
    help|"")   show_help ;;
    *)         echo -e "${RED}[!]${RESET} Unknown: $1 — run 'nova id help'" ;;
esac
