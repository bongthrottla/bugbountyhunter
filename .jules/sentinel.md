## 2024-05-18 - Restrict Output Directory Permissions
**Vulnerability:** Local information disclosure. Output directories for scan results, reports, and wordlists were created without explicit permission restrictions, potentially allowing other users on the same system to view sensitive data.
**Learning:** Even simple file system operations like `os.makedirs` should be paired with `os.chmod` to enforce the principle of least privilege.
**Prevention:** Ensure `os.chmod(..., 0o700)` is applied immediately after creating local output directories for security-sensitive data.
