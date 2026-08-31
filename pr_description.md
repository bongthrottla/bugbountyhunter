🎯 **What:** Removed `script.py` which is a duplicate of `BugBountyHunter.py`.
💡 **Why:** `script.py` was an older, redundant copy of the main application file. Removing it improves codebase maintainability, reduces confusion, and prevents potential issues with modifying the wrong file.
✅ **Verification:**
- Verified `BugBountyHunter.py` contains the complete application logic.
- Compiled `BugBountyHunter.py` and `bug_bounty_hunter.py` to ensure no syntax errors or missing dependencies.
- Verified removal of `script.py` does not break the application.
✨ **Result:** A cleaner codebase with a single source of truth for the main application.
