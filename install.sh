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
for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
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

# Check Node.js / npm (optional, for generated web apps)
if command -v npm >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Node.js & npm found (npm $(npm --version))"
else
    echo -e "  ${YELLOW}! Node.js / npm not found. (Optional, recommended for generated React apps)${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Clone or Update Aztec Source (Optimized with Sparse-Checkout)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[2/5] Setting up Aztec source in ${AZTEC_HOME}...${NC}"
mkdir -p "$AZTEC_HOME"

# Check if running inside local source repository
IS_LOCAL=false
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    CANDIDATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$CANDIDATE_DIR/pyproject.toml" ] && [ -f "$CANDIDATE_DIR/aztec_circle/__init__.py" ]; then
        IS_LOCAL=true
        REPO_DIR="$CANDIDATE_DIR"
    fi
fi

if [ "$IS_LOCAL" = false ] && [ -f "$PWD/pyproject.toml" ] && [ -f "$PWD/aztec_circle/__init__.py" ]; then
    IS_LOCAL=true
    REPO_DIR="$PWD"
fi

if [ "$IS_LOCAL" = true ]; then
    echo -e "  ${CYAN}●${NC} Installing from local repository: ${REPO_DIR}"
else
    if [ -d "$REPO_DIR/.git" ]; then
        echo -e "  ${CYAN}●${NC} Updating existing repository in ${REPO_DIR}..."
        (cd "$REPO_DIR" && git pull --rebase origin main 2>/dev/null || git pull origin main 2>/dev/null || true)
    else
        echo -e "  ${CYAN}●${NC} Downloading Aztec core package (shallow sparse clone)..."
        # Use shallow sparse-checkout to skip downloading examples and heavy test projects
        if git clone --help 2>&1 | grep -q -- '--sparse'; then
            git clone --depth 1 --filter=blob:none --sparse "$GIT_REPO_URL" "$REPO_DIR"
            (
                cd "$REPO_DIR"
                git sparse-checkout set aztec_circle
            )
            echo -e "  ${GREEN}✓${NC} Core package sparse-cloned (omitted test projects)"
        else
            git clone --depth 1 "$GIT_REPO_URL" "$REPO_DIR"
            echo -e "  ${GREEN}✓${NC} Core package cloned"
        fi
    fi
fi

# ------------------------------------------------------------------------------
# 4. Provision Isolated Virtual Environment
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[3/5] Provisioning isolated Python virtualenv...${NC}"
if [ ! -f "$VENV_DIR/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo -e "  ${GREEN}✓${NC} Virtualenv created at ${VENV_DIR}"
else
    echo -e "  ${GREEN}✓${NC} Existing virtualenv found at ${VENV_DIR}"
fi

echo -e "  ${CYAN}●${NC} Upgrading packaging tools (pip, setuptools, wheel)..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel

echo -e "  ${CYAN}●${NC} Installing Aztec dependencies..."
"$VENV_DIR/bin/pip" install --quiet -e "$REPO_DIR"
echo -e "  ${GREEN}✓${NC} Dependencies installed successfully"

# ------------------------------------------------------------------------------
# 5. Create Symlink and Configure Shell PATH
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[4/5] Configuring global binary launcher...${NC}"
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/aztec" "$BIN_DIR/aztec"
chmod +x "$BIN_DIR/aztec"
echo -e "  ${GREEN}✓${NC} Linked ${BIN_DIR}/aztec -> ${VENV_DIR}/bin/aztec"

# Check if BIN_DIR is in active PATH
PATH_IN_SESSION=false
case ":$PATH:" in
    *":$BIN_DIR:"*) PATH_IN_SESSION=true ;;
    *) PATH_IN_SESSION=false ;;
esac

# Append to shell rc files if missing
SHELL_CONFIG_UPDATED=false
for rcfile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ -f "$rcfile" ]; then
        if ! grep -q '\.local/bin' "$rcfile" 2>/dev/null; then
            echo -e '\n# Aztec CLI Path\nexport PATH="$HOME/.local/bin:$PATH"' >> "$rcfile"
            echo -e "  ${GREEN}✓${NC} Added ~/.local/bin to ${rcfile}"
            SHELL_CONFIG_UPDATED=true
        fi
    fi
done

# Fish shell configuration
FISH_CONF="$HOME/.config/fish/config.fish"
if [ -d "$HOME/.config/fish" ]; then
    mkdir -p "$(dirname "$FISH_CONF")"
    if [ -f "$FISH_CONF" ]; then
        if ! grep -q 'fish_add_path.*\.local/bin' "$FISH_CONF" 2>/dev/null; then
            echo -e '\n# Aztec CLI Path\nfish_add_path $HOME/.local/bin' >> "$FISH_CONF"
            echo -e "  ${GREEN}✓${NC} Added ~/.local/bin to ${FISH_CONF}"
            SHELL_CONFIG_UPDATED=true
        fi
    else
        echo -e '# Aztec CLI Path\nfish_add_path $HOME/.local/bin' > "$FISH_CONF"
        echo -e "  ${GREEN}✓${NC} Created ${FISH_CONF} with ~/.local/bin"
        SHELL_CONFIG_UPDATED=true
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
if [ "$PATH_IN_SESSION" = false ]; then
    echo -e "  ${BOLD}1.${NC} Run: ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC} (or reload your terminal)"
    echo -e "  ${BOLD}2.${NC} Launch interactive TUI:  ${CYAN}aztec${NC}"
else
    echo -e "  ${BOLD}1.${NC} Launch interactive TUI:  ${CYAN}aztec${NC}"
fi
echo -e "  ${BOLD}•${NC} Run single prompt:       ${CYAN}aztec run \"Build a 3D robot studio\" --auto-build${NC}"
echo -e "  ${BOLD}•${NC} Run multimodal vision:   ${CYAN}aztec run \"Match this UI\" --image mockup.png${NC}"
echo -e "  ${BOLD}•${NC} Incremental edit:        ${CYAN}aztec edit \"Add dark mode\" --path ./examples/cellular_automata_app${NC}"
echo -e "  ${BOLD}•${NC} Update anytime:          ${CYAN}aztec update${NC} (or ${CYAN}/update${NC} inside TUI)\n"
