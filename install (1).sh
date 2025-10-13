#!/bin/bash
# BugBountyHunter Pro - Quick Installation Script
# For Linux and macOS systems

echo "🚀 BugBountyHunter Pro - Installation Script"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if Go is installed  
if ! command -v go &> /dev/null; then
    echo "❌ Go language is required but not installed."
    echo "Please install Go from https://golang.org/dl/ and try again."
    exit 1
fi

echo "✅ Go found: $(go version)"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p scans reports wordlists configs outputs

# Install essential reconnaissance tools
echo "🛠️ Installing essential tools..."

echo "Installing subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

echo "Installing httpx..."  
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

echo "Installing nuclei..."
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

echo "Installing ffuf..."
go install github.com/ffuf/ffuf@latest

echo "Installing dalfox..."
go install github.com/hahwul/dalfox/v2@latest

echo "Installing gau..."
go install github.com/lc/gau@latest

echo "Installing assetfinder..."
go install github.com/tomnomnom/assetfinder@latest

# Update nuclei templates
echo "📝 Updating nuclei templates..."
nuclei -update-templates

# Verify installations
echo "🔍 Verifying installations..."
tools=("subfinder" "httpx" "nuclei" "ffuf")
all_installed=true

for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo "✅ $tool: installed"
    else
        echo "❌ $tool: not found in PATH"
        all_installed=false
    fi
done

if [ "$all_installed" = true ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Run: python3 BugBountyHunter.py"
    echo "2. Check tool status in the Tools tab"
    echo "3. Start with a basic reconnaissance scan"
    echo ""
    echo "🎯 Happy hunting!"
else
    echo ""
    echo "⚠️  Some tools failed to install."
    echo "Please ensure ~/go/bin is in your PATH:"
    echo "export PATH=\$PATH:~/go/bin"
    echo ""
    echo "Add this line to your ~/.bashrc or ~/.zshrc for persistence."
fi
