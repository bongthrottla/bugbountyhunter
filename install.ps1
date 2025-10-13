# BugBountyHunter Pro - Windows Installation Script
# Run in PowerShell as Administrator

Write-Host "🚀 BugBountyHunter Pro - Windows Installation Script" -ForegroundColor Green
Write-Host "=" * 50

# Check if Python is installed
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://python.org and try again."
    exit 1
}

# Check if Go is installed
try {
    $goVersion = & go version 2>&1
    Write-Host "✅ Go found: $goVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Go language is required but not installed." -ForegroundColor Red  
    Write-Host "Please install Go from https://golang.org/dl/ and try again."
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path scans, reports, wordlists, configs, outputs | Out-Null

# Install essential reconnaissance tools
Write-Host "🛠️ Installing essential tools..." -ForegroundColor Yellow

Write-Host "Installing subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

Write-Host "Installing httpx..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

Write-Host "Installing nuclei..."
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

Write-Host "Installing ffuf..."
go install github.com/ffuf/ffuf@latest

Write-Host "Installing dalfox..."
go install github.com/hahwul/dalfox/v2@latest

Write-Host "Installing gau..."
go install github.com/lc/gau@latest

Write-Host "Installing assetfinder..."
go install github.com/tomnomnom/assetfinder@latest

# Update nuclei templates
Write-Host "📝 Updating nuclei templates..." -ForegroundColor Yellow
& nuclei -update-templates

# Verify installations
Write-Host "🔍 Verifying installations..." -ForegroundColor Yellow
$tools = @("subfinder", "httpx", "nuclei", "ffuf")
$allInstalled = $true

foreach ($tool in $tools) {
    try {
        & $tool --version > $null 2>&1
        Write-Host "✅ $tool`: installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ $tool`: not found in PATH" -ForegroundColor Red
        $allInstalled = $false
    }
}

if ($allInstalled) {
    Write-Host ""
    Write-Host "🎉 Installation completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next steps:"
    Write-Host "1. Run: python BugBountyHunter.py"
    Write-Host "2. Check tool status in the Tools tab" 
    Write-Host "3. Start with a basic reconnaissance scan"
    Write-Host ""
    Write-Host "🎯 Happy hunting!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  Some tools failed to install." -ForegroundColor Yellow
    Write-Host "Please ensure Go's bin directory is in your PATH."
    Write-Host "Typically: C:\Users\YourUser\go\bin"
}
