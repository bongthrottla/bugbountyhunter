#!/bin/bash
# BugBountyHunter Pro - Quick Installation Script
# For Linux and macOS systems

set -e

echo "BugBountyHunter Pro - Installation Script"
echo "========================================="

# --- Python 3 -------------------------------------------------------------
if ! command -v python3 > /dev/null 2>&1; then
    echo "Python 3 is required but was not found."
    echo "Install Python 3.7+ (including tkinter) and re-run this script."
    exit 1
fi
echo "Python 3 found: $(python3 --version)"

# tkinter is required for the GUI
if ! python3 -c "import tkinter" 2> /dev/null; then
    echo "tkinter is missing. Install it with your package manager, e.g.:"
    echo "  Debian/Ubuntu : sudo apt install python3-tk"
    echo "  Fedora        : sudo dnf install python3-tkinter"
    echo "  macOS (brew)  : brew install python-tk"
    exit 1
fi
echo "tkinter OK"

# --- Directories ----------------------------------------------------------
echo "Creating directories..."
mkdir -p scans reports wordlists configs outputs data

# --- Go + recon tools -----------------------------------------------------
if ! command -v go > /dev/null 2>&1; then
    echo "Go was not found. The recon tools cannot be installed automatically."
    echo "Install Go from https://go.dev/dl/ and re-run this script."
    echo "(The GUI itself still works; scans will report missing tools.)"
else
    echo "Go found: $(go version)"
    echo "Installing reconnaissance tools..."

    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    go install github.com/ffuf/ffuf@latest
    go install github.com/hahwul/dalfox/v2@latest
    go install github.com/lc/gau@latest
    go install github.com/tomnomnom/assetfinder@latest

    echo "Updating nuclei templates..."
    nuclei -update-templates || echo "nuclei template update skipped"

    # Make ~/go/bin reachable in this shell and persist it
    GOPATH_BIN="$(go env GOPATH 2> /dev/null || echo "$HOME/go")/bin"
    case ":$PATH:" in
        *":$GOPATH_BIN:"*) ;;
        *) export PATH="$PATH:$GOPATH_BIN" ;;
    esac
    if [ -d "$GOPATH_BIN" ]; then
        echo "Adding $GOPATH_BIN to PATH"
        grep -qF "$GOPATH_BIN" "$HOME/.profile" 2> /dev/null || \
            echo "export PATH=\"\$PATH:$GOPATH_BIN\"" >> "$HOME/.profile"
    fi
fi

# --- Verify ---------------------------------------------------------------
echo "Verifying installations..."
MISSING=0
for tool in subfinder httpx nuclei ffuf dalfox; do
    if command -v "$tool" > /dev/null 2>&1; then
        echo "  OK      $tool"
    else
        echo "  MISSING $tool"
        MISSING=1
    fi
done

echo
if [ "$MISSING" -eq 0 ]; then
    echo "All tools installed. Run the app with: python3 BugBountyHunter.py"
else
    echo "Some tools are missing. Add ~/go/bin to your PATH and re-run:"
    echo "  export PATH=\"\$PATH:\$HOME/go/bin\""
    echo "The app will still start and report which tools are unavailable."
fi
