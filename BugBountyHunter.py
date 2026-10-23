#!/usr/bin/env python3
"""
BugBountyHunter Pro - Beginner's Complete Toolkit v2.0
A comprehensive GUI-based tool for automating bug bounty hunting workflows

Features:
- Automated reconnaissance and vulnerability discovery
- Professional report generation (executive, technical, vulnerability, recon)
- Beginner-friendly program recommendations
- Essential tools guide and installation helper
- SQLite database for scan management
- Multiple scan types and workflows
- Graceful scan interruption

Author: AI Assistant
License: MIT
"""

import datetime
import json
import os
import re

# Make ProjectDiscovery / Go toolchain binaries discoverable when launched from a
# desktop environment that does not inherit the user's interactive PATH.
_gobin = os.path.expanduser("~/go/bin")
if os.path.isdir(_gobin):
    os.environ["PATH"] = _gobin + os.pathsep + os.environ.get("PATH", "")
import shutil
import sqlite3
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

APP_NAME = "BugBountyHunter Pro - Beginner's Complete Toolkit v2.0"
VERSION = "2.0"
# Resolved at runtime (see _resolve_base_dir) rather than at import time, so the
# app writes into the directory it was launched from and tests can relocate it.
BASE_DIR = Path.cwd()
OUTPUT_DIRS = ["outputs", "scans", "reports", "wordlists", "configs"]
DB_PATH = BASE_DIR / "scans" / "bugbounty.db"

TOOLS = [
    "subfinder",
    "httpx",
    "nuclei",
    "ffuf",
    "dalfox",
    "sqlmap",
    "assetfinder",
    "amass",
    "gau",
]

SCAN_TYPES = [
    ("Basic Recon (Subdomains + Live Check)", "basic"),
    ("Comprehensive Scan (Recon + Vulnerabilities)", "comprehensive"),
    ("Quick XSS Hunt", "xss"),
    ("SQLi Discovery", "sqli"),
    ("Directory Fuzzing", "dirfuzz"),
    ("Custom Workflow", "custom"),
]

TOOL_REQUIREMENTS = {
    "basic": ["subfinder", "httpx"],
    "comprehensive": ["subfinder", "httpx", "nuclei"],
    "xss": ["subfinder", "httpx", "dalfox"],
    "sqli": ["httpx", "sqlmap"],
    "dirfuzz": ["httpx", "ffuf"],
    "custom": ["subfinder", "httpx"],
}

HTTPX_STATUS = "200,301,302,403,500"
FUZZ_STATUS = "200,301,302,403"

REPORT_TEMPLATES = [
    ("Executive Summary Report", "executive"),
    ("Technical Findings Report", "technical"),
    ("Vulnerability Details Report", "vulnerability"),
    ("Recon Summary Report", "recon"),
]


class BugBountyHunter:
    def __init__(self, root):
        """Initialise the application: directories, database, tools, GUI."""
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x800")

        self.setup_directories()
        self.init_database()

        # Scan management state
        self.current_scan = None
        self.current_process = None
        self.stop_requested = False
        self.scan_results = {}

        self.available_tools = self.check_tool_availability()
        self.create_gui()
        self._log_tool_resolution()
        self.load_program_data()

        # Closing the window mid-scan would otherwise leave the child tool
        # running and the scan row stuck at status='running' forever.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _resolve_base_dir(self):
        """Resolve the writable base directory for this run.

        Prefers the current working directory, but falls back to the directory
        containing this file when the CWD is not writable (e.g. the app was
        launched from a read-only location). Called before any path is used so
        tests can relocate the app with chdir().
        """
        global BASE_DIR, DB_PATH
        for candidate in (Path.cwd(), Path(__file__).resolve().parent):
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                probe = candidate / ".bbh_write_probe"
                probe.touch(exist_ok=True)
                probe.unlink(missing_ok=True)
                BASE_DIR = candidate
                DB_PATH = BASE_DIR / "scans" / "bugbounty.db"
                return BASE_DIR
            except OSError:
                continue
        return BASE_DIR

    def setup_directories(self):
        """Create all directories required for scan output and data storage.

        Directories are created owner-only (0700). Scan output contains live
        target reconnaissance data, so it should not be world-readable on a
        shared machine.
        """
        self._resolve_base_dir()
        for name in OUTPUT_DIRS:
            path = BASE_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(path, 0o700)
            except OSError:
                pass  # e.g. a filesystem without POSIX permissions (Windows)

    def init_database(self):
        """Initialise the SQLite database that stores scan results."""
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
        # The scan history is target intelligence; keep it owner-only.
        try:
            os.chmod(str(DB_PATH), 0o600)
        except OSError:
            pass  # Windows, or a filesystem without POSIX permissions
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'running',
                results_path TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                subdomain TEXT NOT NULL,
                is_alive BOOLEAN DEFAULT FALSE,
                status_code INTEGER,
                technologies TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                vuln_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                url TEXT,
                proof TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (id)
            )
            """
        )
        self.conn.commit()

    def check_tool_availability(self):
        """Check which reconnaissance tools are installed and usable.

        Delegates to _tool_usable so the startup check and the pre-scan check
        can never disagree about whether a tool works.
        """
        self.tool_paths = {}
        return {tool: self._tool_usable(tool) for tool in TOOLS}

    def _tool_exe(self, name):
        """Resolve a tool name to its pinned absolute path (falls back to name)."""
        return self.tool_paths.get(name) or shutil.which(name) or name

    def _log_tool_resolution(self):
        """Log the resolved binary path for every tool at startup."""
        lines = ["Resolved tool paths:"]
        for tool in TOOLS:
            p = self.tool_paths.get(tool, "(not available)")
            lines.append(f"  {tool:<15} -> {p}")
        try:
            self.log("\n".join(lines), "INFO")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # GUI construction
    # ------------------------------------------------------------------
    def create_gui(self):
        """Create the main notebook interface with its four tabs."""
        notebook = ttk.Notebook(self.root)

        self.main_tab = ttk.Frame(notebook)
        notebook.add(self.main_tab, text="Scanner")

        self.guide_tab = ttk.Frame(notebook)
        notebook.add(self.guide_tab, text="Program Guide")

        self.tools_tab = ttk.Frame(notebook)
        notebook.add(self.tools_tab, text="Tools")

        self.reports_tab = ttk.Frame(notebook)
        notebook.add(self.reports_tab, text="Reports")

        notebook.pack(expand=True, fill="both")

        self.create_main_tab()
        self.create_guide_tab()
        self.create_tools_tab()
        self.create_reports_tab()

    def create_main_tab(self):
        """Create the main scanning interface."""
        # Target configuration
        target_frame = ttk.LabelFrame(self.main_tab, text="Target Configuration", padding="10")
        target_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(target_frame, text="Target Domain (e.g., example.com):").pack(anchor="w")
        self.target_entry = tk.Entry(target_frame, width=50, font=("Arial", 12))
        self.target_entry.pack(fill="x", pady=2)

        # Scan type selection
        scan_frame = ttk.LabelFrame(self.main_tab, text="Scan Configuration", padding="10")
        scan_frame.pack(fill="x", padx=10, pady=5)

        self.scan_type = tk.StringVar(value="basic")
        for text, value in SCAN_TYPES:
            tk.Radiobutton(
                scan_frame,
                text=text,
                variable=self.scan_type,
                value=value,
                font=("Arial", 10),
            ).pack(anchor="w")

        # Control buttons
        button_frame = ttk.Frame(self.main_tab)
        button_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            button_frame,
            text="🚀 Start Scan",
            command=self.start_scan,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
        ).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(
            button_frame,
            text="⏹️ Stop Scan",
            command=self.stop_scan,
            bg="#f44336",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
        ).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(
            button_frame,
            text="📊 Generate Report",
            command=self.generate_comprehensive_report,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Progress and status
        self.progress = ttk.Progressbar(self.main_tab, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.status_label = tk.Label(self.main_tab, text="Ready to scan...",
                                     font=("Arial", 11), fg="green")
        self.status_label.pack(pady=2)

        # Output area
        output_frame = ttk.LabelFrame(self.main_tab, text="Scan Output", padding="10")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_area = scrolledtext.ScrolledText(output_frame, height=20,
                                                     font=("Consolas", 10))
        self.output_area.pack(fill="both", expand=True)

    def create_guide_tab(self):
        """Create the program guide tab with recommendations, tools and tips."""
        guide_notebook = ttk.Notebook(self.guide_tab)

        programs_tab = ttk.Frame(guide_notebook)
        guide_notebook.add(programs_tab, text="Recommended Programs")

        tools_guide_tab = ttk.Frame(guide_notebook)
        guide_notebook.add(tools_guide_tab, text="Essential Tools")

        tips_tab = ttk.Frame(guide_notebook)
        guide_notebook.add(tips_tab, text="Beginner Tips")

        guide_notebook.pack(fill="both", expand=True)

        self.create_program_recommendations(programs_tab)
        self.create_tools_guide(tools_guide_tab)
        self.create_tips_guide(tips_tab)

    @staticmethod
    def _fill_readonly_text(parent, content):
        text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=("Arial", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
        return text

    def create_program_recommendations(self, parent):
        """Display curated recommendations for beginner-friendly programs."""
        content = """
🎯 BEST BEGINNER-FRIENDLY BUG BOUNTY PROGRAMS (2025)

🏆 TOP TIER PLATFORMS:

1. HackerOne (★★★★★)
   • Open registration - no invitation needed
   • Excellent Hacker101 training resources
   • Strong triage team and clear communication
   • Recommended programs for beginners:
     - Shopify (XSS, CSRF, business logic)
     - Uber (wide scope, accepts low severity)
     - WordPress.org (open source, learning friendly)
     - Malwarebytes (good for recon findings)
   • Average beginner payouts: $50-$500

2. Bugcrowd (★★★★☆)
   • Good beginner support and documentation
   • Clear vulnerability classification
   • Recommended programs:
     - Tesla (accepts informational findings)
     - Fitbit (good for mobile app testing)
     - Western Union (broad scope)
   • Average beginner payouts: $100-$750

3. Intigriti (★★★★☆)
   • European platform with personal touch
   • Good for beginners in EU timezone
   • Regular competitions and challenges
   • Growing community of researchers
   • Focus on quality over quantity

🎯 SPECIALTY PLATFORMS:

4. Open Bug Bounty (★★★☆☆)
   • Completely FREE for companies
   • Great for building initial reputation
   • Focus on XSS and CSRF vulnerabilities
   • Non-monetary rewards but excellent for learning

5. HackenProof (★★★☆☆)
   • Best for Web3/DeFi bug hunting
   • Cryptocurrency rewards (USDT, ETH, BTC)
   • Excellent educational materials for blockchain security
   • Growing rapidly with high payouts

💡 BEGINNER STRATEGY:

PHASE 1 (Months 1-3): Learning Foundation
→ Start with Open Bug Bounty (free practice)
→ Complete HackerOne Hacker101 courses
→ Focus on ONE vulnerability type (recommend XSS)

PHASE 2 (Months 3-6): Building Reputation
→ Target "Easy" tagged programs on HackerOne
→ Submit quality reports even for low severity
→ Build consistent submission pattern

PHASE 3 (Months 6+): Scaling Up
→ Apply for private program invitations
→ Diversify vulnerability hunting (SQLi, SSRF, etc.)
→ Develop automation and custom methodologies

🎯 EASIEST TARGETS FOR BEGINNERS:

HIGH SUCCESS RATE PROGRAMS:
• Government programs (.gov domains)
• Educational institutions (.edu domains)
• Small-medium businesses with new programs
• Programs with "Accepts: Informational" scope

VULNERABILITY TYPES TO START WITH:
1. Cross-Site Scripting (XSS) - Easiest to find and verify
2. Information Disclosure - Exposed files, debug info
3. Missing Security Headers - Quick automated findings
4. Open Redirects - Common in authentication flows
5. CSRF - Often overlooked by other hunters

📊 REALISTIC EARNING EXPECTATIONS:

Month 1-3: $0-$200 (Learning phase)
Month 4-6: $200-$1,000 (Building skills)
Month 7-12: $500-$3,000 (Consistent findings)
Year 2+: $1,000-$10,000+ (Experienced hunter)

Remember: Focus on learning first, money second! 🚀
        """
        self._fill_readonly_text(parent, content)

    def create_tools_guide(self, parent):
        """Display the essential tools installation guide."""
        content = """
🛠️ ESSENTIAL BUG BOUNTY TOOLS FOR BEGINNERS (2025)

🎯 MUST-HAVE TOOLS (Install These First):

1. RECONNAISSANCE TOOLS:
   📡 Subfinder - Fast subdomain enumeration
   📡 httpx - HTTP service discovery and probing
   📡 Amass - Advanced subdomain enumeration
   📡 Assetfinder - Find related domains and assets

   Installation:
   go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
   go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

2. VULNERABILITY SCANNERS:
   🔍 Nuclei - YAML-based vulnerability scanner (4000+ templates)
   🔍 Dalfox - Advanced XSS scanner
   🔍 SQLMap - SQL injection automation

   Installation:
   go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
   go install github.com/hahwul/dalfox/v2@latest

3. DIRECTORY/FILE DISCOVERY:
   📁 ffuf - Fast web fuzzer written in Go
   📁 dirsearch - Web path scanner
   📁 gobuster - URI/DNS/VHost brute forcer

   Installation:
   go install github.com/ffuf/ffuf@latest

4. MANUAL TESTING TOOLS:
   🕷️ Burp Suite Community (Free) - Web application security testing
   🕷️ OWASP ZAP - Free security testing proxy
   🕷️ Browser Developer Tools - Built-in testing capabilities

🚀 AUTOMATION WORKFLOW TOOLS:

5. URL DISCOVERY:
   🔗 gau (GetAllURLs) - Fetch known URLs from AlienVault, Wayback, etc.
   🔗 waybackurls - Fetch URLs from Wayback Machine
   🔗 katana - Fast web crawler

   Installation:
   go install github.com/lc/gau@latest

6. CONTENT ANALYSIS:
   📝 gf - Pattern matching for sensitive data
   📝 anew - Append new lines to files (deduplication)
   📝 unfurl - Extract domains, paths, queries from URLs

🔧 BEGINNER-FRIENDLY WORKFLOW:

STEP 1: Subdomain Discovery
→ subfinder -d target.com -o subdomains.txt
→ amass enum -d target.com >> subdomains.txt

STEP 2: Live Host Discovery
→ httpx -l subdomains.txt -o live_hosts.txt

STEP 3: Vulnerability Scanning
→ nuclei -l live_hosts.txt -t ~/nuclei-templates/

STEP 4: XSS Hunting
→ dalfox url https://target.com/vulnerable-endpoint

STEP 5: Directory Fuzzing
→ ffuf -u https://target.com/FUZZ -w wordlist.txt

💡 TOOL INSTALLATION GUIDE:

Prerequisites:
1. Install Go language: https://golang.org/dl/
2. Add ~/go/bin to your PATH
3. Install Git for version control

One-Command Setup:
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest && go install github.com/ffuf/ffuf@latest && go install github.com/lc/gau@latest

📚 LEARNING RESOURCES:

Official Documentation:
• ProjectDiscovery: https://docs.projectdiscovery.io/
• OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
• HackerOne Hacker101: https://www.hacker101.com/

YouTube Channels:
• NahamSec - Bug bounty methodology and tools
• STÖK - Practical bug hunting techniques
• InsiderPHD - Beginner-friendly tutorials

🎯 BEGINNER TOOL PRIORITIES:

Week 1-2: Master Burp Suite basics
Week 3-4: Learn subfinder + httpx workflow
Week 5-6: Understand Nuclei templates
Week 7-8: Practice with ffuf directory fuzzing
Month 2+: Advanced tool customization and automation

Remember: Tools are just helpers - understanding vulnerabilities is key! 🧠
        """
        self._fill_readonly_text(parent, content)

    @staticmethod
    def _read_data_file(relative_path, fallback):
        """Read a bundled data file, trying repo layout then installed layout.

        Works both when running from a clone (BASE_DIR/data/...) and when
        installed via pip (sys.prefix/share/bugbountyhunter/...).
        """
        candidates = [
            BASE_DIR / relative_path,
            Path(__file__).resolve().parent / relative_path,
            Path(sys.prefix) / "share" / "bugbountyhunter" / relative_path,
        ]
        for path in candidates:
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                continue
        return fallback

    def create_tips_guide(self, parent):
        """Display beginner tips loaded from data/tips_guide.txt."""
        content = self._read_data_file(
            "data/tips_guide.txt",
            "Tips guide not found. Please ensure data/tips_guide.txt exists.",
        )
        self._fill_readonly_text(parent, content)

    def create_tools_tab(self):
        """Create the tools management tab."""
        # Tool status section
        status_frame = ttk.LabelFrame(self.tools_tab, text="Tool Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)

        self.tool_status_text = scrolledtext.ScrolledText(status_frame, height=8,
                                                          font=("Consolas", 10))
        self.tool_status_text.pack(fill="both", expand=True)
        self.update_tool_status()

        # Installation helper
        install_frame = ttk.LabelFrame(self.tools_tab, text="Tool Installation Helper",
                                       padding="10")
        install_frame.pack(fill="both", expand=True, padx=10, pady=5)

        install_content = self._read_data_file(
            "data/install_guide.txt",
            "Install guide not found. Please ensure data/install_guide.txt exists.",
        )

        install_text = scrolledtext.ScrolledText(install_frame, wrap=tk.WORD,
                                                 font=("Arial", 11))
        install_text.pack(fill="both", expand=True)
        install_text.insert(tk.END, install_content)
        install_text.config(state=tk.DISABLED)

        tk.Button(
            self.tools_tab,
            text="🔄 Refresh Tool Status",
            command=self.refresh_tools,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12),
        ).pack(pady=10)

    def create_reports_tab(self):
        """Create the reports management tab."""
        # Recent scans table
        scans_frame = ttk.LabelFrame(self.reports_tab, text="Recent Scans", padding="10")
        scans_frame.pack(fill="x", padx=10, pady=5)

        columns = ("ID", "Target", "Type", "Date", "Status")
        self.scan_tree = ttk.Treeview(scans_frame, columns=columns,
                                      show="headings", height=6)
        for col in columns:
            self.scan_tree.heading(col, text=col)
            self.scan_tree.column(col, width=100)
        self.scan_tree.pack(fill="x", pady=5)
        self.load_scan_history()

        # Report templates
        report_frame = ttk.LabelFrame(self.reports_tab, text="Report Templates", padding="10")
        report_frame.pack(fill="both", expand=True, padx=10, pady=5)

        generators = {
            "executive": self.generate_executive_report,
            "technical": self.generate_technical_report,
            "vulnerability": self.generate_vulnerability_report,
            "recon": self.generate_recon_report,
        }
        for label, key in REPORT_TEMPLATES:
            tk.Button(
                report_frame,
                text=f"📊 {label}",
                command=generators[key],
                bg="#2196F3",
                fg="white",
                font=("Arial", 11),
                height=2,
            ).pack(fill="x", pady=2)

    # ------------------------------------------------------------------
    # Tool status
    # ------------------------------------------------------------------
    def update_tool_status(self):
        """Refresh the tool availability display."""
        self.tool_status_text.delete(1.0, tk.END)

        lines = ["🛠️  TOOL AVAILABILITY STATUS", "=" * 50, ""]
        for tool, available in self.available_tools.items():
            status = "✅ INSTALLED" if available else "❌ NOT FOUND"
            lines.append(f"{tool:<15} : {status}")

        installed = sum(self.available_tools.values())
        total = len(self.available_tools)
        lines.append(f"\n📊 SUMMARY: {installed}/{total} tools installed")
        lines.append("\n⚠️  Some tools are missing. Check installation guide below."
                     if installed < total
                     else "\n🎉 All essential tools are installed! Ready to hunt!")

        self.tool_status_text.insert(tk.END, "\n".join(lines))

    def refresh_tools(self):
        """Re-run the tool availability check and refresh the display."""
        self.available_tools = self.check_tool_availability()
        self.update_tool_status()
        self.log("Tool status refreshed", "INFO")

    # ------------------------------------------------------------------
    # Logging / UI helpers (thread-safe)
    # ------------------------------------------------------------------
    def log(self, message, level="INFO"):
        """Log a message to the output area with a timestamp and colour."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        color_map = {"INFO": "black", "SUCCESS": "green",
                     "WARNING": "orange", "ERROR": "red"}
        formatted = f"[{timestamp}] {level}: {message}\n"

        def _write():
            self.output_area.insert(tk.END, formatted)
            self.output_area.see(tk.END)
            if level in ("SUCCESS", "ERROR"):
                self.status_label.config(text=message, fg=color_map.get(level, "black"))

        self._schedule(_write)

    def _schedule(self, func):
        """Run a GUI action on the main thread (safe from worker threads)."""
        if threading.current_thread() is threading.main_thread():
            func()
        else:
            self.root.after(0, func)

    # ------------------------------------------------------------------
    # Scan workflow
    # ------------------------------------------------------------------
    def start_scan(self):
        """Validate input and launch the selected scan type in a thread."""
        target = self.target_entry.get().strip()
        if not target:
            messagebox.showwarning("Input Required", "Please enter a target domain.")
            return

        if not self.validate_target(target):
            messagebox.showerror(
                "Invalid Target",
                "Please enter a valid domain name (e.g., example.com)",
            )
            return

        scan_type = self.scan_type.get()

        # Ensure required tools are installed
        required_tools = self.get_required_tools(scan_type)
        missing = [t for t in required_tools if not self.available_tools.get(t, False)]
        if missing:
            messagebox.showerror(
                "Missing Tools",
                f"Required tools not found: {', '.join(missing)}\n\n"
                "Please install missing tools using the Tools tab.",
            )
            return

        self.stop_requested = False
        self.current_scan = threading.Thread(
            target=self.run_scan, args=(target, scan_type), daemon=True
        )
        self.current_scan.start()

        self._schedule(lambda: self.progress.start(10))
        self.log(f"Starting {scan_type} scan on {target}", "INFO")

    def stop_scan(self):
        """Request the running scan to stop and terminate its active process."""
        proc = self.current_process
        if proc and proc.poll() is None:
            proc.terminate()
        self.stop_requested = True

        def _ui():
            if proc and proc.poll() is None:
                self.progress.stop()
                self.status_label.config(text="Stop requested...", fg="orange")
                self.log("Scan stop requested... (terminating active process)", "WARNING")
            elif self.current_scan and self.current_scan.is_alive():
                self.log("Scan stop requested... (waiting for clean exit)", "WARNING")
            else:
                self.stop_requested = False
                self.log("No scan is currently running", "INFO")

        self._schedule(_ui)

    @staticmethod
    def validate_target(target):
        """Return True if the target looks like a valid domain name."""
        clean = target.replace("http://", "").replace("https://", "").strip("/")
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return re.match(pattern, clean) is not None

    @staticmethod
    def get_required_tools(scan_type):
        """Return the list of tools required for a given scan type."""
        return TOOL_REQUIREMENTS.get(scan_type, TOOL_REQUIREMENTS["basic"])

    def run_scan(self, target, scan_type):
        """Execute the selected scan pipeline and record results."""
        # Preflight FIRST: refuse to start a scan whose tools cannot run.
        # Otherwise a tool that exists but fails yields an empty result file,
        # which is indistinguishable from "no findings" and gets recorded as a
        # completed scan that never actually ran.
        missing = self._require_tools(scan_type)
        if missing:
            self.log(
                f"Cannot run '{scan_type}' scan — required tool(s) not usable: "
                f"{', '.join(missing)}. Install them (see Tools tab) and retry.",
                "ERROR",
            )
            self._schedule(lambda: self.progress.stop())
            self._schedule(lambda: self.status_label.config(
                text="Scan not started — missing tools", fg="red"))
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO scans (target, scan_type, status) VALUES (?, ?, ?)",
                (target, scan_type, "running"),
            )
            scan_id = cursor.lastrowid
            self.conn.commit()

            scan_dir = BASE_DIR / "scans" / f"scan_{scan_id}_{target}"
            scan_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(scan_dir, 0o700)
            except OSError:
                pass  # Windows, or a filesystem without POSIX permissions

            handlers = {
                "basic": self.run_basic_scan,
                "comprehensive": self.run_comprehensive_scan,
                "xss": self.run_xss_scan,
                "sqli": self.run_sqli_scan,
                "dirfuzz": self.run_dirfuzz_scan,
                "custom": self.run_basic_scan,
            }
            handler = handlers.get(scan_type, self.run_basic_scan)
            handler(target, str(scan_dir), scan_id)

            status = "stopped" if self.stop_requested else "completed"
            cursor.execute(
                "UPDATE scans SET status = ?, results_path = ? WHERE id = ?",
                (status, str(scan_dir), scan_id),
            )
            self.conn.commit()

            if status == "completed":
                self.log(f"Scan completed! Results saved to {scan_dir}", "SUCCESS")
            else:
                self.log("Scan stopped by user.", "WARNING")

        except FileNotFoundError as exc:
            self.log(f"Required tool not found: {exc.filename}", "ERROR")
            self._mark_scan_failed(scan_id if "scan_id" in locals() else None)
        except Exception as exc:  # noqa: BLE001 - surface all tool failures to the UI
            self.log(f"Scan failed: {exc}", "ERROR")
            self._mark_scan_failed(scan_id if "scan_id" in locals() else None)

        finally:
            self.stop_requested = False
            self.current_process = None
            self._schedule(lambda: self.progress.stop())
            self._schedule(lambda: self.status_label.config(
                text="Scan completed", fg="green"))

    def on_close(self):
        """Handle window close: stop any running scan, then tear down cleanly.

        Without this, closing the window mid-scan orphans the child tool
        process and leaves the scan row at status='running' forever.
        """
        scan_alive = self.current_scan is not None and self.current_scan.is_alive()
        if scan_alive:
            if not messagebox.askokcancel(
                "Quit",
                "A scan is still running. Quit anyway?\n\n"
                "The running tool will be terminated and the scan marked stopped.",
            ):
                return
            self.stop_requested = True

        # Terminate the active child tool so it does not outlive the GUI.
        proc = self.current_process
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

        # Give the scan thread a moment to unwind and record its final status.
        if scan_alive and self.current_scan is not None:
            self.current_scan.join(timeout=5)

        self._mark_scan_stopped()

        try:
            if self.conn is not None:
                self.conn.close()
        except sqlite3.Error:
            pass

        self.root.destroy()

    def _mark_scan_stopped(self):
        """Mark any scan left in 'running' as 'stopped' so history stays honest."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE scans SET status = 'stopped' WHERE status = 'running'"
            )
            self.conn.commit()
        except sqlite3.Error:
            pass

    def _mark_scan_failed(self, scan_id):
        if scan_id is None:
            return
        cursor = self.conn.cursor()
        cursor.execute("UPDATE scans SET status = 'failed' WHERE id = ?", (scan_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Command execution helper
    # ------------------------------------------------------------------
    def _run_command(self, command, cwd=None):
        """Run a command, returning a dict with returncode/stdout/stderr.

        ``ok`` is False whenever the tool could not be run OR exited non-zero.
        Callers MUST check it: a tool that exists but fails (bad API key, rate
        limit, no network) produces an empty output file, and treating that as
        "zero findings" silently reports a clean scan that never happened.
        """
        if self.stop_requested:
            return {"returncode": -1, "stdout": "", "stderr": "stopped", "ok": False}
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(getattr(exc, "filename", None) or str(command[0]))

        self.current_process = proc
        try:
            stdout, stderr = proc.communicate()
        finally:
            if self.current_process is proc:
                self.current_process = None

        ok = proc.returncode in (0, -15)
        if not ok and stderr.strip():
            self.log(f"[{' '.join(command)}] stderr: {stderr.strip()[:500]}", "WARNING")
        return {
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "ok": ok,
        }

    def _require_tools(self, scan_type):
        """Preflight: return the list of required tools that are not usable.

        Checked BEFORE a scan row is created, so an unrunnable scan never gets
        recorded as 'completed'.
        """
        missing = []
        for tool in self.get_required_tools(scan_type):
            if not self._tool_usable(tool):
                missing.append(tool)
        return missing

    def _tool_usable(self, tool):
        """True only if the tool is on PATH AND actually executes.

        Most tools answer a version probe, but some (assetfinder) have no
        version flag at all and exit non-zero on every probe. Falling back to
        the tool's own help flag distinguishes "installed but flagless" from
        "not installed" — without it, a perfectly good binary is reported
        missing and the user is told to install something they already have.
        """
        path = self.tool_paths.get(tool) or shutil.which(tool)
        if path is None:
            return False

        # A probe "succeeds" if the process runs and does not report an
        # unknown-flag error. Some tools print help to stderr and exit 2.
        unknown_flag_markers = (
            "flag provided but not defined",
            "unknown flag",
            "unrecognized option",
            "invalid option",
        )
        for flag in ("--version", "-version", "version", "-V", "-h", "--help"):
            try:
                r = subprocess.run(
                    [path, flag],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=8,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue

            combined = f"{r.stdout or ''}{r.stderr or ''}".lower()
            if any(m in combined for m in unknown_flag_markers):
                continue  # this flag is not supported; try the next one

            # Either a clean exit, or a help dump (which some tools exit 2 on).
            if r.returncode == 0 or "usage" in combined:
                self.tool_paths[tool] = path
                return True
        return False

    # ------------------------------------------------------------------
    # Scan implementations
    # ------------------------------------------------------------------
    def run_basic_scan(self, target, scan_dir, scan_id):
        """Run subdomain enumeration followed by live host discovery."""
        self.log("Phase 1: Subdomain enumeration with subfinder...", "INFO")
        subfinder_output = f"{scan_dir}/subdomains.txt"
        r = self._run_command([self._tool_exe("subfinder"), "-d", target, "-o", subfinder_output, "-silent"])
        if not r.get("ok"):
            raise RuntimeError(
                f"subfinder failed (exit {r.get('returncode')}): "
                f"{r.get('stderr', '').strip()[:200] or 'no output'}"
            )

        subdomains = self._read_lines(subfinder_output)
        self.log(f"Found {len(subdomains)} subdomains", "SUCCESS")

        self.log("Phase 2: Checking live hosts with httpx...", "INFO")
        live_output = f"{scan_dir}/live_subdomains.txt"
        r = self._run_command([
            self._tool_exe("httpx"), "-l", subfinder_output, "-o", live_output,
            "-silent", "-mc", HTTPX_STATUS,
        ])
        if not r.get("ok"):
            raise RuntimeError(
                f"httpx failed (exit {r.get('returncode')}): "
                f"{r.get('stderr', '').strip()[:200] or 'no output'}"
            )

        live_hosts = self._read_lines(live_output)
        self.log(f"Found {len(live_hosts)} live hosts", "SUCCESS")

        # httpx emits full URLs (https://host/path) while subfinder emits bare
        # hostnames, so a plain membership test never matches. Normalise both
        # sides to a bare hostname before comparing.
        live_names = {self._hostname_of(h) for h in live_hosts}
        live_names.discard("")

        cursor = self.conn.cursor()
        for subdomain in subdomains:
            cursor.execute(
                "INSERT INTO subdomains (scan_id, subdomain, is_alive) VALUES (?, ?, ?)",
                (scan_id, subdomain, self._hostname_of(subdomain) in live_names),
            )
        self.conn.commit()

    @staticmethod
    def _hostname_of(value):
        """Reduce a URL or hostname to a bare, lowercased hostname.

        'https://api.example.com:443/x' -> 'api.example.com'
        'API.Example.com'               -> 'api.example.com'
        """
        if not value:
            return ""
        text = value.strip()
        if "://" in text:
            text = text.split("://", 1)[1]
        # strip path, query and fragment
        for sep in ("/", "?", "#"):
            if sep in text:
                text = text.split(sep, 1)[0]
        # strip userinfo and port
        if "@" in text:
            text = text.rsplit("@", 1)[1]
        if ":" in text:
            text = text.split(":", 1)[0]
        return text.strip().lower()

    def run_comprehensive_scan(self, target, scan_dir, scan_id):
        """Run the basic recon pipeline then a Nuclei vulnerability scan."""
        self.run_basic_scan(target, scan_dir, scan_id)
        if self.stop_requested:
            return

        self.log("Phase 3: Running Nuclei vulnerability scan...", "INFO")
        live_hosts_file = f"{scan_dir}/live_subdomains.txt"
        nuclei_output = f"{scan_dir}/nuclei_results.json"
        if os.path.exists(live_hosts_file):
            r = self._run_command([
                self._tool_exe("nuclei"), "-l", live_hosts_file, "-o", nuclei_output,
                "-jsonl", "-silent",
            ])
            # nuclei exits 1 when it finds nothing in some versions; only treat
            # a missing results file plus a non-zero exit as a real failure.
            if not r.get("ok") and not os.path.exists(nuclei_output):
                raise RuntimeError(
                    f"nuclei failed (exit {r.get('returncode')}): "
                    f"{r.get('stderr', '').strip()[:200] or 'no output'}"
                )
            self.parse_nuclei_results(nuclei_output, scan_id)

    def parse_nuclei_results(self, nuclei_output, scan_id):
        """Parse Nuclei JSON lines and store findings in the database."""
        if not os.path.exists(nuclei_output):
            self.log("No nuclei results file produced", "INFO")
            return

        cursor = self.conn.cursor()
        vuln_count = 0
        # Batch inserts: a comprehensive scan can return thousands of findings,
        # and one INSERT per row is needlessly slow. Flush every 1000 rows.
        records = []
        with open(nuclei_output, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    result = json.loads(line)
                except json.JSONDecodeError:
                    continue

                vuln_type = result.get("template-id", "unknown")
                severity = result.get("info", {}).get("severity", "info")
                description = result.get("info", {}).get("name", "No description")
                url = result.get("matched-at", "")

                records.append((scan_id, vuln_type, severity, description, url))
                vuln_count += 1

                if len(records) >= 1000:
                    cursor.executemany(
                        """
                        INSERT INTO vulnerabilities (scan_id, vuln_type, severity,
                                                     description, url)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        records,
                    )
                    records = []

        if records:
            cursor.executemany(
                """
                INSERT INTO vulnerabilities (scan_id, vuln_type, severity,
                                             description, url)
                VALUES (?, ?, ?, ?, ?)
                """,
                records,
            )

        self.conn.commit()
        self.log(f"Found {vuln_count} potential vulnerabilities", "SUCCESS")

    def run_xss_scan(self, target, scan_dir, scan_id):
        """Enumerate live hosts and pass each through dalfox for XSS checks."""
        self.log("XSS hunting scan starting...", "INFO")

        subdomain_file = f"{scan_dir}/subdomains.txt"
        live_file = f"{scan_dir}/live_subdomains.txt"

        r = self._run_command([self._tool_exe("subfinder"), "-d", target, "-silent", "-o", subdomain_file])
        if not r.get("ok"):
            raise RuntimeError(f"subfinder failed (exit {r.get('returncode')}): {r.get('stderr','').strip()[:200] or 'no output'}")

        r = self._run_command([self._tool_exe("httpx"), "-l", subdomain_file, "-o", live_file, "-silent"])
        if not r.get("ok"):
            raise RuntimeError(f"httpx failed (exit {r.get('returncode')}): {r.get('stderr','').strip()[:200] or 'no output'}")

        for url in self._read_lines(live_file):
            if self.stop_requested:
                return
            self.log(f"Scanning {url} for XSS...", "INFO")
            r = self._run_command([self._tool_exe("dalfox"), "url", url, "-silence"])
            if not r.get("ok"):
                self.log(f"dalfox failed on {url}: exit {r.get('returncode')}", "WARNING")

    def run_sqli_scan(self, target, scan_dir, scan_id):
        """Explain the SQLi workflow; parameter selection is inherently manual."""
        self.log("SQL injection scan starting...", "INFO")
        self.log("SQL injection scanning requires manual parameter identification", "WARNING")
        self.log("Please use Burp Suite to identify potential injection points", "INFO")

    def run_dirfuzz_scan(self, target, scan_dir, scan_id):
        """Fuzz common paths on the target using ffuf."""
        self.log("Directory fuzzing scan starting...", "INFO")
        if not self.available_tools.get("ffuf", False):
            self.log("ffuf not installed - skipping directory fuzzing", "WARNING")
            return

        wordlist_path = self._pick_wordlist()
        if wordlist_path is None:
            fallback = BASE_DIR / "wordlists" / "common.txt"
            self.create_basic_wordlist(str(fallback))
            wordlist_path = fallback
        self.log(f"Directory fuzzing with {wordlist_path.name} "
                 f"({self._count_lines(wordlist_path)} entries)", "INFO")

        dirfuzz_output = f"{scan_dir}/directories.json"
        r = self._run_command([
            self._tool_exe("ffuf"), "-u", f"https://{target}/FUZZ",
            "-w", str(wordlist_path),
            "-o", dirfuzz_output,
            "-of", "json",
            "-mc", FUZZ_STATUS,
            "-s",
        ])
        if not r.get("ok") and not os.path.exists(dirfuzz_output):
            raise RuntimeError(f"ffuf failed (exit {r.get('returncode')}): {r.get('stderr','').strip()[:200] or 'no output'}")

        count = 0
        if os.path.exists(dirfuzz_output):
            try:
                with open(dirfuzz_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results = data.get("results", [])
                count = len(results)
                for item in results:
                    self.log(
                        f"Found: {item.get('status')} {item.get('url', '')}",
                        "SUCCESS",
                    )
            except (json.JSONDecodeError, OSError):
                pass
        self.log(f"Directory fuzzing completed - {count} paths found", "SUCCESS")

    @staticmethod
    def _count_lines(path):
        """Count non-empty lines in a wordlist, without loading it all."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for line in f if line.strip())
        except OSError:
            return 0

    def _pick_wordlist(self):
        """Choose the best available directory-fuzzing wordlist.

        Prefers a user-supplied or system-installed list over the bundled one,
        then the bundled SecLists-derived lists. Returns None if nothing is
        available, so the caller can generate a minimal fallback.
        """
        candidates = []

        # 1. Explicit override in config.ini, if set.
        configured = self._configured_wordlist()
        if configured:
            candidates.append(Path(configured).expanduser())

        # 2. System SecLists / dirb installs (what Kali ships).
        candidates += [
            Path("/usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt"),
            Path("/usr/share/seclists/Discovery/Web-Content/common.txt"),
            Path("/usr/share/wordlists/dirb/common.txt"),
            Path("/usr/share/dirb/wordlists/common.txt"),
            Path("/usr/share/wfuzz/wordlist/general/common.txt"),
        ]

        # 3. Bundled lists (shipped in the repo and in the wheel).
        candidates += [
            BASE_DIR / "wordlists" / "raft-small-directories.txt",
            BASE_DIR / "wordlists" / "common.txt",
            Path(__file__).resolve().parent / "wordlists" / "raft-small-directories.txt",
            Path(__file__).resolve().parent / "wordlists" / "common.txt",
            Path(sys.prefix) / "share" / "bugbountyhunter" / "wordlists" / "raft-small-directories.txt",
            Path(sys.prefix) / "share" / "bugbountyhunter" / "wordlists" / "common.txt",
        ]

        for path in candidates:
            try:
                if path.is_file() and path.stat().st_size > 0:
                    return path
            except OSError:
                continue
        return None

    def _configured_wordlist(self):
        """Read wordlist_path from config.ini if present, else empty string."""
        import configparser
        try:
            parser = configparser.ConfigParser()
            for cfg in (BASE_DIR / "config.ini", Path(__file__).resolve().parent / "config.ini"):
                if cfg.is_file():
                    parser.read(cfg)
                    if parser.has_option("scanning", "wordlist_path"):
                        return parser.get("scanning", "wordlist_path").strip()
                    break
        except (OSError, configparser.Error):
            pass
        return ""

    @staticmethod
    def create_basic_wordlist(path):
        """Write a minimal directory wordlist used for ffuf."""
        common_dirs = [
            "admin", "administrator", "login", "wp-admin", "backup",
            "test", "dev", "staging", "api", "v1", "v2", "docs",
            "config", "uploads", "images", "css", "js", "assets",
            "tmp", "temp", "cache", "log", "logs", "database",
        ]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("\n".join(common_dirs) + "\n", encoding="utf-8")

    @staticmethod
    def _read_lines(path):
        """Read non-empty, whitespace-stripped lines from a text file."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return [line.strip() for line in f if line.strip()]
        except OSError:
            return []

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load_program_data(self):
        """Load curated program recommendation data."""
        self.program_data = {
            "beginner_friendly": [
                {
                    "name": "HackerOne - Shopify",
                    "platform": "HackerOne",
                    "difficulty": "Beginner",
                    "scope": "Wide (*.shopify.com)",
                    "common_bugs": ["XSS", "CSRF", "Business Logic"],
                    "avg_payout": "$150",
                    "tips": "Focus on admin panel functionality and partner integrations",
                },
                {
                    "name": "Bugcrowd - Tesla",
                    "platform": "Bugcrowd",
                    "difficulty": "Beginner",
                    "scope": "Vehicle systems excluded",
                    "common_bugs": ["Info Disclosure", "XSS", "CSRF"],
                    "avg_payout": "$200",
                    "tips": "Check charging network and mobile app endpoints",
                },
            ]
        }

    def load_scan_history(self):
        """Populate the recent-scans treeview from the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, target, scan_type, timestamp, status
            FROM scans
            ORDER BY timestamp DESC
            LIMIT 20
            """
        )
        scans = cursor.fetchall()

        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)

        for scan in scans:
            scan_id, target, scan_type, timestamp, status = scan
            try:
                formatted = datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                formatted = str(timestamp)
            self.scan_tree.insert(
                "", "end", values=(scan_id, target, scan_type, formatted, status)
            )

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------
    def _get_scan(self, scan_id=None):
        """Return the selected scan row, falling back to the newest finished scan."""
        cursor = self.conn.cursor()
        if scan_id is not None:
            cursor.execute(
                "SELECT id, target, scan_type, timestamp, results_path FROM scans WHERE id = ?",
                (scan_id,),
            )
        else:
            cursor.execute(
                """
                SELECT id, target, scan_type, timestamp, results_path
                FROM scans WHERE status IN ('completed', 'stopped')
                ORDER BY timestamp DESC LIMIT 1
                """
            )
        return cursor.fetchone()

    def _selected_scan_id(self):
        selection = self.scan_tree.selection()
        if selection:
            item = self.scan_tree.item(selection[0], "values")
            try:
                return int(item[0])
            except (ValueError, IndexError):
                return None
        return None

    def _write_report(self, filename, content):
        report_dir = BASE_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / filename
        path.write_text(content, encoding="utf-8")
        self.log(f"Report generated: {path}", "SUCCESS")
        messagebox.showinfo("Report Generated", f"Report saved to:\n{path}")

    def generate_comprehensive_report(self):
        """Generate a full markdown report for the most recent scan."""
        scan = self._get_scan(self._selected_scan_id())
        if not scan:
            messagebox.showinfo("No Data", "No completed scans found. Please run a scan first.")
            return

        scan_id, target, scan_type, timestamp, _ = scan
        filename = f"comprehensive_report_{target}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_report(filename, self.generate_markdown_report(
            scan_id, target, scan_type, timestamp))

    def generate_markdown_report(self, scan_id, target, scan_type, timestamp):
        """Build the comprehensive markdown report content."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) as total, COUNT(CASE WHEN is_alive = 1 THEN 1 END) as live
            FROM subdomains WHERE scan_id = ?
            """,
            (scan_id,),
        )
        total, live = cursor.fetchone()

        cursor.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM vulnerabilities WHERE scan_id = ?
            GROUP BY severity
            """,
            (scan_id,),
        )
        severity_stats = cursor.fetchall()

        cursor.execute(
            """
            SELECT vuln_type, severity, description, url
            FROM vulnerabilities WHERE scan_id = ?
            ORDER BY severity, vuln_type
            """,
            (scan_id,),
        )
        vulnerabilities = cursor.fetchall()

        total = total or 0
        live = live or 0
        success_rate = (live / max(total, 1) * 100)

        report = f"""# Bug Bounty Reconnaissance Report

**Target:** {target}  
**Scan Type:** {scan_type}  
**Date:** {timestamp}  
**Generated By:** {APP_NAME}

## Executive Summary

This report contains the findings from an automated reconnaissance and vulnerability assessment of {target}. The scan was conducted using industry-standard tools and methodologies.

## Reconnaissance Summary

### Subdomain Discovery
- **Total Subdomains Found:** {total}
- **Live Hosts:** {live}
- **Success Rate:** {success_rate:.1f}%

## Vulnerability Assessment

### Summary by Severity
"""
        if severity_stats:
            for severity, count in severity_stats:
                report += f"- **{severity.upper()}:** {count} findings\n"
        else:
            report += "- No vulnerabilities detected\n"

        if vulnerabilities:
            report += "\n### Detailed Findings\n\n"
            for vuln_type, severity, description, url in vulnerabilities:
                report += f"#### {description}\n"
                report += f"- **Type:** {vuln_type}\n"
                report += f"- **Severity:** {severity.upper()}\n"
                report += f"- **URL:** {url}\n"
                report += "- **Recommendation:** Manual verification required\n\n"

        report += """
## Methodology

This assessment utilized the following tools and techniques:

1. **Subdomain Enumeration**
   - Tool: Subfinder
   - Method: DNS enumeration and passive sources

2. **Live Host Discovery**
   - Tool: httpx
   - Method: HTTP/HTTPS probing

3. **Vulnerability Scanning**
   - Tool: Nuclei
   - Method: Template-based vulnerability detection

## Recommendations

### Immediate Actions
1. Manually verify all identified vulnerabilities
2. Prioritize findings based on business impact
3. Implement security headers on all web applications

### Long-term Security Improvements
1. Implement automated security scanning in CI/CD pipeline
2. Regular security assessments and penetration testing
3. Security awareness training for development teams

## Disclaimer

This report is generated by automated tools and requires manual verification. False positives are possible. All testing should be conducted within the scope of approved bug bounty programs only.

---
*Report generated by BugBountyHunter Pro - Beginner's Complete Toolkit*
"""
        return report

    def generate_executive_report(self):
        """Generate a high-level executive summary report."""
        scan = self._get_scan(self._selected_scan_id())
        if not scan:
            messagebox.showinfo("No Data", "No completed scans found.")
            return
        scan_id, target, scan_type, timestamp, _ = scan

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM subdomains WHERE scan_id = ? AND is_alive = 1",
            (scan_id,),
        )
        live = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM vulnerabilities WHERE scan_id = ?", (scan_id,))
        vulns = cursor.fetchone()[0] or 0
        cursor.execute("SELECT severity, COUNT(*) FROM vulnerabilities WHERE scan_id = ? GROUP BY severity",
                       (scan_id,))
        by_severity = cursor.fetchall()

        lines = [f"# Executive Summary - {target}", ""]
        lines.append(f"- **Scan Type:** {scan_type}")
        lines.append(f"- **Scan Date:** {timestamp}")
        lines.append(f"- **Live Hosts:** {live}")
        lines.append(f"- **Vulnerabilities Found:** {vulns}")
        lines.append("")
        lines.append("## Severity Breakdown")
        lines.append("")
        if by_severity:
            for severity, count in by_severity:
                lines.append(f"- **{severity.upper()}:** {count}")
        else:
            lines.append("- No vulnerabilities detected.")
        lines.append("")
        lines.append("## Recommendation")
        lines.append("")
        lines.append("Prioritise remediation of high and critical findings, then verify "
                     "all medium findings manually. Re-scan after fixes are deployed.")

        filename = f"executive_report_{target}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_report(filename, "\n".join(lines))

    def generate_technical_report(self):
        """Generate a technical findings report (vulnerability table)."""
        scan = self._get_scan(self._selected_scan_id())
        if not scan:
            messagebox.showinfo("No Data", "No completed scans found.")
            return
        scan_id, target, scan_type, timestamp, _ = scan

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT vuln_type, severity, description, url
            FROM vulnerabilities WHERE scan_id = ? ORDER BY severity, vuln_type
            """,
            (scan_id,),
        )
        findings = cursor.fetchall()

        lines = [f"# Technical Findings - {target}", ""]
        lines.append(f"- **Scan Type:** {scan_type}")
        lines.append(f"- **Scan Date:** {timestamp}")
        lines.append("")
        lines.append("| Severity | Type | Description | URL |")
        lines.append("|---|---|---|---|")
        for vuln_type, severity, description, url in findings:
            lines.append(f"| {severity.capitalize()} | {vuln_type} | {description} | {url} |")
        if not findings:
            lines.append("| - | None | No vulnerabilities found | - |")
        lines.append("")
        lines.append("*Automated scan results - requires manual verification.*")

        filename = f"technical_report_{target}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_report(filename, "\n".join(lines))

    def generate_vulnerability_report(self):
        """Generate a detailed per-vulnerability report with remediation hints."""
        scan = self._get_scan(self._selected_scan_id())
        if not scan:
            messagebox.showinfo("No Data", "No completed scans found.")
            return
        scan_id, target, scan_type, timestamp, _ = scan

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT vuln_type, severity, description, url
            FROM vulnerabilities WHERE scan_id = ? ORDER BY severity, vuln_type
            """,
            (scan_id,),
        )
        findings = cursor.fetchall()

        lines = [f"# Vulnerability Details - {target}", ""]
        lines.append(f"- **Scan Type:** {scan_type}")
        lines.append(f"- **Scan Date:** {timestamp}")
        lines.append("")
        if not findings:
            lines.append("No vulnerabilities were identified.")
        for i, (vuln_type, severity, description, url) in enumerate(findings, 1):
            lines.append(f"## {i}. {description}")
            lines.append("")
            lines.append(f"- **CWE/Type:** {vuln_type}")
            lines.append(f"- **Severity:** {severity.capitalize()}")
            lines.append(f"- **Affected URL:** {url}")
            lines.append(f"- **Evidence:** captured during automated scan")
            lines.append(f"- **Remediation:** Manual verification and targeted testing required")
            lines.append("")

        filename = f"vulnerability_report_{target}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_report(filename, "\n".join(lines))

    def generate_recon_report(self):
        """Generate a reconnaissance summary report (subdomains / live hosts)."""
        scan = self._get_scan(self._selected_scan_id())
        if not scan:
            messagebox.showinfo("No Data", "No completed scans found.")
            return
        scan_id, target, scan_type, timestamp, _ = scan

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT subdomain, is_alive FROM subdomains WHERE scan_id = ?
            ORDER BY is_alive DESC, subdomain
            """,
            (scan_id,),
        )
        rows = cursor.fetchall()

        lines = [f"# Reconnaissance Summary - {target}", ""]
        lines.append(f"- **Scan Date:** {timestamp}")
        lines.append(f"- **Total Subdomains:** {len(rows)}")
        lines.append(f"- **Live Hosts:** {sum(1 for _, alive in rows if alive)}")
        lines.append("")
        lines.append("## Discovered Hosts")
        lines.append("")
        if rows:
            lines.append("| Subdomain | Status |")
            lines.append("|---|---|")
            for subdomain, alive in rows:
                lines.append(f"| {subdomain} | {'🟢 LIVE' if alive else '⚪ offline'} |")
        else:
            lines.append("No subdomains discovered for this scan.")

        filename = f"recon_report_{target}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._write_report(filename, "\n".join(lines))


def main():
    """Entry point for the application."""
    root = tk.Tk()
    BugBountyHunter(root)
    root.mainloop()


if __name__ == "__main__":
    main()