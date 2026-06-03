#!/bin/bash
# vukov-update — VukovOS Self-Updater v0.2
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'
YELLOW='\033[0;33m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
REPO_DIR="$HOME/NovaOS-git"
SCRIPTS_DST="/usr/local/bin"

banner() {
echo -e "${CYAN}"
cat << 'BANNER'
  ╔══════════════════════════════════════════════╗
  ║   vukov-update — Self-Updater v0.2          ║
  ║   Pulling latest VukovOS from GitHub         ║
  ╚══════════════════════════════════════════════╝
BANNER
echo -e "${RESET}"
}

backup_current() {
    BACKUP="$HOME/.vukov/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP"
    cp "$SCRIPTS_DST"/vukov* "$BACKUP/" 2>/dev/null
    echo -e "  ${GREEN}[✓]${RESET} Backed up to $BACKUP"
}

pull_latest() {
    cd "$REPO_DIR" || { echo -e "${RED}[!]${RESET} Repo not found at $REPO_DIR"; exit 1; }
    LOCAL=$(git rev-parse HEAD)
    git fetch origin 2>&1 | sed 's/^/  /'
    REMOTE=$(git rev-parse origin/main)
    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "  ${GREEN}[✓]${RESET} Already up to date."
        exit 0
    fi
    git pull origin main 2>&1 | sed 's/^/  /'
    echo -e "  ${GREEN}[✓]${RESET} Repository updated."
}

install_scripts() {
    COUNT=0
    for script in "$REPO_DIR/scripts"/vukov*; do
        name=$(basename "$script")
        sudo cp "$script" "$SCRIPTS_DST/$name"
        sudo chmod +x "$SCRIPTS_DST/$name"
        echo -e "  ${GREEN}[✓]${RESET} $name"
        COUNT=$((COUNT+1))
    done
    echo -e "  ${GREEN}[✓]${RESET} $COUNT scripts installed."
}

rollback() {
    LATEST=$(ls -td "$HOME/.vukov/backups"/*/ 2>/dev/null | head -1)
    [ -z "$LATEST" ] && echo -e "${RED}[!]${RESET} No backup found." && exit 1
    echo -e "${YELLOW}[*]${RESET} Rolling back to: $LATEST"
    for s in "$LATEST"vukov*; do
        sudo cp "$s" "$SCRIPTS_DST/$(basename $s)"
        sudo chmod +x "$SCRIPTS_DST/$(basename $s)"
    done
    echo -e "${GREEN}[✓]${RESET} Rollback complete."
}

case "${1:-update}" in
    update|"")
        banner
        curl -s --head https://github.com > /dev/null 2>&1 || { echo -e "${RED}[!]${RESET} No connection."; exit 1; }
        backup_current
        pull_latest
        install_scripts
        echo -e "\n${GREEN}${BOLD}[✓] VukovOS updated! 🐺${RESET}"
        echo -e "${DIM}    Run: source ~/.bashrc${RESET}"
        ;;
    rollback) banner; rollback ;;
    check)
        curl -s --head https://github.com > /dev/null 2>&1 || { echo -e "${RED}[!]${RESET} No connection."; exit 1; }
        cd "$REPO_DIR"
        git fetch origin -q
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main)
        [ "$LOCAL" = "$REMOTE" ] && echo -e "${GREEN}[✓]${RESET} Up to date." || echo -e "${YELLOW}[!]${RESET} Update available. Run: vukov update"
        ;;
    *) echo "Usage: vukov update [update|check|rollback]" ;;
esac
