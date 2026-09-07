## 2025-02-14 - Fix local information disclosure via overly permissive directories
**Vulnerability:** The application was creating output directories (`outputs`, `scans`, `reports`, `wordlists`, `configs`) with default permissions, which could allow unauthorized local users to access sensitive bug bounty scan results and findings.
**Learning:** In desktop applications or tools creating local output, any sensitive data must be protected using appropriate file permissions. Default `os.makedirs` permissions are often too permissive.
**Prevention:** Use `os.chmod(directory, 0o700)` immediately after creating directories intended for sensitive data to ensure only the owner has read, write, and execute permissions.
