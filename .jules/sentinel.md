
## 2024-05-24 - Secure Directory Creation
**Vulnerability:** Insecure local directory creation. Creating directories using default permissions (like `os.makedirs(dir, exist_ok=True)`) could allow local users on the same machine to view or alter sensitive files such as scans, reports, or database outputs.
**Learning:** Python's `os.makedirs` respects system umask by default. If a script operates on sensitive data in an environment with a permissive umask, directories can be created with overly broad access (e.g. read permissions for all users).
**Prevention:** Explicitly pass restrictive modes (e.g., `mode=0o700`) to `os.makedirs` to restrict permissions. Because of potential TOCTOU vulnerabilities and varied handling of umask across Python versions, follow up with `os.chmod(dir, 0o700)` to ensure permissions are strictly enforced.
