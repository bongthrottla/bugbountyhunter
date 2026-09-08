## 2025-02-18 - [Insecure Local File Permissions]
**Vulnerability:** Local information disclosure due to newly created scan output directories lacking restrictive permissions.
**Learning:** Default permissions created by `os.makedirs` may be too broad depending on the umask setting, which could allow unauthorized local users to access sensitive vulnerability scan results and subdomain lists.
**Prevention:** Always follow up `os.makedirs` for sensitive data directories with `os.chmod(directory_path, 0o700)` to ensure only the owner has read/write/execute permissions.
