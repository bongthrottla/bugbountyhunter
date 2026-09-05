## 2025-01-20 - Local Information Disclosure via Insecure Directory Permissions
**Vulnerability:** Newly created local directories for storing sensitive data (e.g., outputs, scans, reports) were created with default permissions, potentially allowing other users on the system to access bug bounty scan results.
**Learning:** In desktop applications that handle sensitive information, local data directories must be restricted. The `os.makedirs()` function creates directories with default permissions (often `0o777` modified by umask, resulting in `0o755`).
**Prevention:** Explicitly set strict directory permissions (e.g., `os.chmod(directory, 0o700)`) after creating directories that will store sensitive application data.

## 2025-01-20 - SQLite ProgrammingError Threading Crash (Denial of Service)
**Vulnerability:** The application crashed when background scanning threads attempted to access the SQLite database, which was initialized in the main thread.
**Learning:** The Python `sqlite3` module restricts connection objects from being shared across threads by default to prevent data corruption.
**Prevention:** Initialize `sqlite3.connect()` with `check_same_thread=False` when using background threads, but ensure that any concurrent writes are properly synchronized (SQLite generally handles concurrent thread access gracefully if thread-safe).