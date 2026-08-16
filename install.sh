#!/usr/bin/env bash
# ==============================================================================
# Aztec Decision Circle: Universal Self-Installing Script
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/JUANITOTELO/aztec-cirlce-llm/main/install.sh | bash
#   OR
#   ./install.sh
# ==============================================================================

set -euo pipefail

# Visual Colors
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
DIM="\033[2m"
NC="\033[0m"

AZTEC_HOME="${AZTEC_HOME:-$HOME/.aztec}"
REPO_DIR="$AZTEC_HOME/repo"
VENV_DIR="$AZTEC_HOME/venv"
BIN_DIR="${HOME}/.local/bin"
GIT_REPO_URL="https://github.com/JUANITOTELO/aztec-cirlce-llm.git"

echo -e "${CYAN}${BOLD}"
echo "  ██████╗ ███████╗████████╗███████╗ ██████╗ "
echo "  ██╔══██╗╚════██║╚══██╔══╝██╔════╝██╔════╝ "
echo "  ███████║    ██╔╝   ██║   █████╗  ██║      "
echo "  ██╔══██║   ██╔╝    ██║   ██╔══╝  ██║      "
echo "  ██║  ██║   ██║     ██║   ███████╗╚██████╗ "
echo "  ╚═╝  ╚═╝   ╚═╝     ╚═╝   ╚══════╝ ╚═════╝ "
echo "   Multi-Generational Adversarial LLM Debate Framework"
echo -e "${NC}"
echo -e "${BOLD}▶ Starting Aztec Self-Installation...${NC}\n"

# ------------------------------------------------------------------------------
# 1. System & Architecture Detection
# ------------------------------------------------------------------------------
OS="$(uname -s)"
ARCH="$(uname -m)"
echo -e "  ${DIM}OS: ${OS} | Architecture: ${ARCH}${NC}"

case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=macos;;
    *)          PLATFORM=unknown;;
esac

# ------------------------------------------------------------------------------
# 2. Check Prerequisites (Python 3.10+, Git, Node.js)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[1/5] Checking prerequisites...${NC}"

# Find Python 3.10+
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN=$(command -v "$cmd")
            echo -e "  ${GREEN}✓${NC} Python ${VER} found (${PYTHON_BIN})"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "  ${RED}✗ Python 3.10 or higher is required but not found.${NC}"
    echo -e "  Please install Python 3.10+ using your package manager (e.g. pyenv, apt, brew) and re-run."
    exit 1
fi

# Check Git
if command -v git >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Git found ($(git --version | head -n1))"
else
    echo -e "  ${RED}✗ Git is required to clone and update Aztec.${NC}"
    exit 1
fi

# Check Node.js / npm (recommended for Vite + React generation)
if command -v npm >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Node.js & npm found (npm $(npm --version))"
else
    echo -e "  ${YELLOW}! Node.js / npm not found. (Optional, but recommended for generated React apps)${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Clone or Update Aztec Source Repository
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[2/5] Setting up Aztec source in ${AZTEC_HOME}...${NC}"
mkdir -p "$AZTEC_HOME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If running directly inside the cloned repo, sync from local directory
if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/aztec_circle" ]; then
    echo -e "  ${CYAN}●${NC} Installing from local repository: ${SCRIPT_DIR}"
    REPO_DIR="$SCRIPT_DIR"
else
    if [ -d "$REPO_DIR/.git" ]; then
        echo -e "  ${CYAN}●${NC} Updating existing repository in ${REPO_DIR}..."
        (cd "$REPO_DIR" && git pull --rebase origin main || git pull origin main)
    else
        echo -e "  ${CYAN}●${NC} Cloning repository into ${REPO_DIR}..."
        git clone "$GIT_REPO_URL" "$REPO_DIR"
    fi
fi

# ------------------------------------------------------------------------------
# 4. Provision Isolated Virtual Environment
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[3/5] Provisioning isolated Python virtualenv...${NC}"
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo -e "  ${GREEN}✓${NC} Virtualenv created at ${VENV_DIR}"
else
    echo -e "  ${GREEN}✓${NC} Existing virtualenv found at ${VENV_DIR}"
fi

echo -e "  ${CYAN}●${NC} Upgrading pip and installing Aztec dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install --quiet -e "$REPO_DIR"

# ------------------------------------------------------------------------------
# 5. Create Symlink and Configure Shell PATH
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[4/5] Configuring global binary launcher...${NC}"
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/aztec" "$BIN_DIR/aztec"
echo -e "  ${GREEN}✓${NC} Linked ${BIN_DIR}/aztec -> ${VENV_DIR}/bin/aztec"

# Check if BIN_DIR is in PATH
PATH_CONFIGURED=false
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    PATH_CONFIGURED=true
else
    # Auto-append to shell config files
    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [ -f "$rcfile" ]; then
            if ! grep -q 'export PATH="\$HOME/.local/bin:\$PATH"' "$rcfile" 2>/dev/null; then
                echo -e '\n# Aztec CLI Path\nexport PATH="$HOME/.local/bin:$PATH"' >> "$rcfile"
                echo -e "  ${GREEN}✓${NC} Added ~/.local/bin to ${rcfile}"
                PATH_CONFIGURED=true
            fi
        fi
    done

    # Fish shell support
    FISH_CONF="$HOME/.config/fish/config.fish"
    if [ -d "$HOME/.config/fish" ]; then
        mkdir -p "$(dirname "$FISH_CONF")"
        if ! grep -q 'fish_add_path $HOME/.local/bin' "$FISH_CONF" 2>/dev/null; then
            echo -e '\n# Aztec CLI Path\nfish_add_path $HOME/.local/bin' >> "$FISH_CONF"
            echo -e "  ${GREEN}✓${NC} Added ~/.local/bin to ${FISH_CONF}"
            PATH_CONFIGURED=true
        fi
    fi
fi

# ------------------------------------------------------------------------------
# 6. Verify Installation & Print Welcome
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[5/5] Verifying installation...${NC}"
if "$BIN_DIR/aztec" --help >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Aztec CLI verified successfully!${NC}\n"
else
    echo -e "  ${YELLOW}! Binary installed, but initial execution returned non-zero.${NC}"
fi

echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 Aztec is ready to use!${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}\n"

echo -e "To start using Aztec:"
if [ "$PATH_CONFIGURED" = true ]; then
    echo -e "  ${BOLD}1.${NC} Run: ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC} (or restart your terminal)"
fi
echo -e "  ${BOLD}2.${NC} Launch interactive TUI:  ${CYAN}aztec${NC}"
echo -e "  ${BOLD}3.${NC} Run single prompt:       ${CYAN}aztec run \"Build a 3D robot studio\" --auto-build${NC}"
echo -e "  ${BOLD}4.${NC} Run multimodal vision:   ${CYAN}aztec run \"Match this UI\" --image mockup.png${NC}"
echo -e "  ${BOLD}5.${NC} Incremental edit:        ${CYAN}aztec edit \"Add dark mode\" --path ./my_app${NC}"
echo -e "  ${BOLD}6.${NC} Update in future:        ${CYAN}aztec update${NC} (or ${CYAN}/update${NC} inside TUI)\n"
