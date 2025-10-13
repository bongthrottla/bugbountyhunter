
import tkinter as tk
import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bug_bounty_hunter import BugBountyHunter

    if __name__ == "__main__":
        root = tk.Tk()
        app = BugBountyHunter(root)
        root.mainloop()

except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available.")
    sys.exit(1)
