#!/usr/bin/env bash
# BugBountyHunter Pro — one-click installer.
#
#   curl -fsSL https://raw.githubusercontent.com/bongthrottla/bugbountyhunter/main/install.sh | bash
#
# Clones the repo, checks Python/tkinter, downloads the recon tools (no Go
# toolchain needed), verifies everything, and prints how to launch.
#
# Options (env vars):
#   BBH_DIR=/path        where to clone (default ~/bugbountyhunter)
#   BBH_BIN_DIR=/path    where to put tool binaries (default ~/.local/bin)
#   BBH_SKIP_TOOLS=1     skip tool download (app still runs, reports missing)
#   BBH_NO_PATH=1        don't touch your shell profile
#
# Safe to re-run: it updates an existing clone instead of failing.

set -euo pipefail

REPO_URL="https://github.com/bongthrottla/bugbountyhunter.git"
BBH_DIR="${BBH_DIR:-$HOME/bugbountyhunter}"
BBH_BIN_DIR="${BBH_BIN_DIR:-$HOME/.local/bin}"
SKIP_TOOLS="${BBH_SKIP_TOOLS:-0}"
NO_PATH="${BBH_NO_PATH:-0}"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
die()  { printf '  \033[31m✗\033[0m %s\n' "$1" >&2; exit 1; }

bold "BugBountyHunter Pro — installer"
echo

# --- 1. prerequisites -----------------------------------------------------
bold "1/5  Checking prerequisites"

PY=""
for candidate in python3 python; do
    if command -v "$candidate" > /dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,7) else 1)' 2>/dev/null; then
            PY="$candidate"; break
        fi
    fi
done
[ -n "$PY" ] || die "Python 3.7+ not found. Install it and re-run."
ok "Python: $($PY --version 2>&1)"

if ! "$PY" -c 'import tkinter' 2>/dev/null; then
    warn "tkinter is missing — the GUI cannot start without it."
    case "$(uname -s)" in
        Linux)
            echo "        Debian/Ubuntu:  sudo apt install python3-tk"
            echo "        Fedora:         sudo dnf install python3-tkinter"
            echo "        Arch:           sudo pacman -S tk"
            ;;
        Darwin) echo "        macOS:          brew install python-tk" ;;
    esac
    die "Install tkinter and re-run."
fi
ok "tkinter available"

command -v git > /dev/null 2>&1 || die "git not found. Install it and re-run."
ok "git available"

if ! command -v curl > /dev/null 2>&1; then
    warn "curl not found — the recon tools cannot be downloaded."
fi

# --- 2. clone or update ---------------------------------------------------
echo
bold "2/5  Getting the code"

if [ -d "$BBH_DIR/.git" ]; then
    ok "Existing install at $BBH_DIR — updating"
    git -C "$BBH_DIR" fetch --quiet origin
    git -C "$BBH_DIR" checkout --quiet main
    git -C "$BBH_DIR" pull --quiet --ff-only origin main || \
        warn "Could not fast-forward; leaving your local changes alone"
else
    git clone --quiet --depth 1 "$REPO_URL" "$BBH_DIR" || die "Clone failed."
    ok "Cloned to $BBH_DIR"
fi

# --- 3. tools -------------------------------------------------------------
echo
bold "3/5  Installing reconnaissance tools"

if [ "$SKIP_TOOLS" = "1" ]; then
    warn "Skipped (BBH_SKIP_TOOLS=1)"
elif [ ! -x "$BBH_DIR/scripts/install-tools.sh" ]; then
    warn "install-tools.sh not found in the repo — skipping"
elif ! command -v curl > /dev/null 2>&1; then
    warn "curl unavailable — skipping tool download"
else
    BBH_BIN_DIR="$BBH_BIN_DIR" "$BBH_DIR/scripts/install-tools.sh" || \
        warn "Some tools failed to install (the app still runs)"
fi

# --- 4. PATH --------------------------------------------------------------
echo
bold "4/5  Making the tools reachable"

TOOLS_OK=0
for t in subfinder httpx nuclei ffuf dalfox gau assetfinder; do
    if [ -x "$BBH_BIN_DIR/$t" ]; then TOOLS_OK=$((TOOLS_OK + 1)); fi
done

if [ "$TOOLS_OK" -eq 0 ]; then
    warn "No tools in $BBH_BIN_DIR — nothing to add to PATH"
elif [ "$NO_PATH" = "1" ]; then
    warn "Skipped (BBH_NO_PATH=1). Add manually:"
    echo "        export PATH=\"\$PATH:$BBH_BIN_DIR\""
else
    case ":$PATH:" in
        *":$BBH_BIN_DIR:"*) ok "$BBH_BIN_DIR already on PATH" ;;
        *)
            ADDED=0
            for profile in "$HOME/.bashrc" "$HOME/.zshrc"; do
                [ -e "$profile" ] || continue
                if ! grep -qF "$BBH_BIN_DIR" "$profile" 2>/dev/null; then
                    printf '\n# Added by BugBountyHunter Pro installer\nexport PATH="$PATH:%s"\n' \
                        "$BBH_BIN_DIR" >> "$profile"
                    ok "Updated $profile"
                    ADDED=1
                fi
            done
            if [ "$ADDED" -eq 0 ]; then
                warn "No shell profile updated. Add manually:"
                echo "        export PATH=\"\$PATH:$BBH_BIN_DIR\""
            fi
            export PATH="$PATH:$BBH_BIN_DIR"
            ;;
    esac
fi

# --- 5. verify ------------------------------------------------------------
echo
bold "5/5  Verifying"

"$PY" -m compileall -q "$BBH_DIR/BugBountyHunter.py" 2>/dev/null \
    && ok "Code compiles" || warn "Compile check failed"

FOUND=0
for t in subfinder httpx nuclei ffuf dalfox gau assetfinder; do
    if [ -x "$BBH_BIN_DIR/$t" ] || command -v "$t" > /dev/null 2>&1; then
        FOUND=$((FOUND + 1))
    fi
done
ok "$FOUND/7 recon tools available"

if [ "$FOUND" -ge 3 ]; then
    ok "Basic Recon will work"
else
    warn "Fewer than 3 tools found — scans will report missing tools"
fi

# --- done -----------------------------------------------------------------
echo
bold "Done."
echo
echo "  Start the app:"
echo "      cd $BBH_DIR && $PY BugBountyHunter.py"
echo
if [ "$FOUND" -ge 3 ]; then
    echo "  First run: the Scanner tab is already open. Type a domain you are"
    echo "  authorised to test, pick 'Basic Recon', and press Start Scan."
else
    echo "  Tools are missing. Re-run the tool installer once network is available:"
    echo "      $BBH_DIR/scripts/install-tools.sh"
fi
echo
echo "  Only scan systems you own or that are in scope for a program you have"
echo "  joined. See the Authorised Use section of the README."
echo
