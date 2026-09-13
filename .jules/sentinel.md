## 2024-05-24 - SQLite Threads\n**Vulnerability:** SQLite multithreading\n**Learning:** SQLite connections initialized in main thread need `check_same_thread=False` to be accessed from background scan threads\n**Prevention:** Always add `check_same_thread=False` when opening SQLite connections in Tkinter apps that use threading.

## 2026-09-13 - Directory Permissions
**Vulnerability:** Local information disclosure
**Learning:** Scan outputs, databases, and reports created by the application may contain sensitive vulnerability data. If created with default permissions, other users on the system could access this data.
**Prevention:** Explicitly set restricted permissions (e.g., `os.chmod(directory, 0o700)`) immediately after creating directories that will store sensitive output files.
