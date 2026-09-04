## 2025-01-01 - Prevent Information Disclosure of Scan Data via Restrictive Permissions
**Vulnerability:** Information Disclosure
**Learning:** The application writes sensitive output files (e.g. `scans/bugbounty.db`, `live_subdomains.txt`, `nuclei_results.json`) inside default permission directories. On shared environments or multi-user VPS (commonly used by bug bounty hunters), this exposes discovered vulnerabilities to other local users.
**Prevention:** Always use `os.chmod(dir, 0o700)` or strict `umask` configurations when creating local directories that will host sensitive vulnerability scan results or databases.
