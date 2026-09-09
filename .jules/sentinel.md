## 2024-05-19 - [Local Information Disclosure via Insecure Directory Permissions]
**Vulnerability:** Output directories containing sensitive bug bounty scan results (subdomains, vulnerability details, and reports) were created with default system permissions (often world-readable).
**Learning:** This is a localized Tkinter desktop application that manages sensitive scan data on the host machine. Failing to restrict permissions on dynamically generated directories can leak sensitive information to other users on a multi-user system.
**Prevention:** Always follow the principle of least privilege for local file storage by explicitly setting restrictive file permissions using `os.chmod(directory, 0o700)` immediately after creating local directories meant for sensitive data.
