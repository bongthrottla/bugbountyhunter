#!/usr/bin/env bash
# Install the reconnaissance tools without needing a Go toolchain.
#
# Downloads prebuilt release binaries for the tools that publish them and drops
# them in ~/.local/bin (or $BBH_BIN_DIR). Only assetfinder lacks prebuilt
# binaries, so it is built from source if Go happens to be present; if not, it
# is skipped — the app runs fine without it.
#
# Usage:
#   ./scripts/install-tools.sh              # install to ~/.local/bin
#   BBH_BIN_DIR=/opt/bbh/bin ./scripts/install-tools.sh
#
# Supported platforms: linux x86_64/aarch64, darwin x86_64/arm64.

set -euo pipefail

BIN_DIR="${BBH_BIN_DIR:-$HOME/.local/bin}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$BIN_DIR"

# --- platform detection ---------------------------------------------------
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
    x86_64|amd64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH_RAW" >&2; exit 1 ;;
esac

case "$OS" in
    linux|darwin) ;;
    *) echo "Unsupported OS: $OS (Windows: use install.ps1)" >&2; exit 1 ;;
esac

echo "Installing recon tools into $BIN_DIR"
echo "Platform: ${OS}/${ARCH}"
echo

FAILED=()

# Fetch the latest release asset URL for a repo, matching a name pattern.
asset_url() {
    local repo="$1" pattern="$2"
    curl -fsSL --max-time 60 "https://api.github.com/repos/$repo/releases/latest" \
        | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
pat = re.compile(sys.argv[1])
for a in d.get('assets', []):
    if pat.search(a['name']):
        print(a['browser_download_url']); break
" "$pattern"
}

install_from_release() {
    local name="$1" repo="$2" pattern="$3"
    echo -n "  $name ... "
    local url
    url="$(asset_url "$repo" "$pattern" || true)"
    if [ -z "$url" ]; then
        echo "no matching release asset"
        FAILED+=("$name")
        return
    fi
    local file="$TMP/$(basename "$url")"
    if ! curl -fsSL --max-time 300 -o "$file" "$url"; then
        echo "download failed"
        FAILED+=("$name")
        return
    fi
    case "$file" in
        *.zip) unzip -qo "$file" -d "$TMP/$name" ;;
        *.tar.gz|*.tgz) mkdir -p "$TMP/$name" && tar -xzf "$file" -C "$TMP/$name" ;;
        *) echo "unknown archive type"; FAILED+=("$name"); return ;;
    esac
    # Find the executable: prefer a file named exactly like the tool.
    local exe
    exe="$(find "$TMP/$name" -type f -name "$name" -perm -u+x | head -1)"
    [ -z "$exe" ] && exe="$(find "$TMP/$name" -type f -name "$name" | head -1)"
    if [ -z "$exe" ]; then
        echo "binary not found in archive"
        FAILED+=("$name")
        return
    fi
    install -m 0755 "$exe" "$BIN_DIR/$name"
    echo "ok"
}

echo "Downloading prebuilt binaries..."
install_from_release subfinder projectdiscovery/subfinder "subfinder_.*_${OS}_${ARCH}\.zip$"
install_from_release httpx     projectdiscovery/httpx     "httpx_.*_${OS}_${ARCH}\.zip$"
install_from_release nuclei    projectdiscovery/nuclei    "nuclei_.*_${OS}_${ARCH}\.zip$"
install_from_release ffuf      ffuf/ffuf                  "ffuf_.*_${OS}_${ARCH}\.tar\.gz$"
install_from_release gau       lc/gau                     "gau_.*_${OS}_${ARCH}\.tar\.gz$"
# dalfox names its assets linux-x86_64 / darwin-arm64, not linux_amd64.
DALFOX_ARCH="$ARCH_RAW"
[ "$ARCH" = "amd64" ] && DALFOX_ARCH="x86_64"
install_from_release dalfox    hahwul/dalfox              "dalfox-v.*-${OS}-${DALFOX_ARCH}\.tar\.gz$"

# --- assetfinder: source only --------------------------------------------
echo -n "  assetfinder ... "
if command -v go > /dev/null 2>&1; then
    if GOBIN="$BIN_DIR" go install github.com/tomnomnom/assetfinder@latest 2> /dev/null; then
        echo "built from source"
    else
        echo "build failed (optional tool, continuing)"
        FAILED+=("assetfinder")
    fi
else
    echo "skipped (no prebuilt binaries, Go not installed — optional)"
fi

# --- nuclei templates ----------------------------------------------------
if [ -x "$BIN_DIR/nuclei" ]; then
    echo -n "  nuclei templates ... "
    if "$BIN_DIR/nuclei" -update-templates > /dev/null 2>&1; then
        echo "updated"
    else
        echo "update failed (run '$BIN_DIR/nuclei -update-templates' later)"
    fi
fi

# --- PATH hint -----------------------------------------------------------
echo
echo "Installed:"
for t in subfinder httpx nuclei ffuf dalfox gau assetfinder; do
    if [ -x "$BIN_DIR/$t" ]; then
        printf "  %-14s %s\n" "$t" "$BIN_DIR/$t"
    else
        printf "  %-14s not installed\n" "$t"
    fi
done

echo
case ":$PATH:" in
    *":$BIN_DIR:"*)
        echo "$BIN_DIR is already on your PATH."
        ;;
    *)
        echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
        echo
        echo "    export PATH=\"\$PATH:$BIN_DIR\""
        echo
        ;;
esac

if [ "${#FAILED[@]}" -gt 0 ]; then
    echo "Failed: ${FAILED[*]}"
    echo "The app still starts and reports which tools are unavailable."
    exit 1
fi

echo "Done. Start the app with: python3 BugBountyHunter.py"
