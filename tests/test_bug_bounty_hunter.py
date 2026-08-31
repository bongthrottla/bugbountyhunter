import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BugBountyHunter import BugBountyHunter
from tkinter import Tk

class TestBugBountyHunter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need a root window for Tkinter, but we only create it once
        cls.root = Tk()
        cls.root.withdraw() # Hide the window

    def setUp(self):
        # Initialize the app with the hidden root
        self.app = BugBountyHunter(self.root)

    def test_validate_target(self):
        # Valid domain names
        self.assertTrue(self.app.validate_target("example.com"))
        self.assertTrue(self.app.validate_target("sub.example.com"))
        self.assertTrue(self.app.validate_target("sub-domain.example.com"))
        self.assertTrue(self.app.validate_target("example.co.uk"))
        self.assertTrue(self.app.validate_target("localhost"))
        self.assertTrue(self.app.validate_target("123example.com"))
        self.assertTrue(self.app.validate_target("example123.com"))

        # IP Addresses
        self.assertTrue(self.app.validate_target("192.168.1.1"))
        self.assertTrue(self.app.validate_target("10.0.0.1"))

        # Protocol stripping (http/https should be stripped and then validated)
        self.assertTrue(self.app.validate_target("http://example.com"))
        self.assertTrue(self.app.validate_target("https://example.com"))
        self.assertTrue(self.app.validate_target("http://sub.example.com"))
        self.assertTrue(self.app.validate_target("https://192.168.1.1"))

        # Invalid domain names - Format issues
        self.assertFalse(self.app.validate_target("-example.com")) # Starts with hyphen
        self.assertFalse(self.app.validate_target("example-.com")) # Ends with hyphen before dot
        self.assertFalse(self.app.validate_target("example.-com")) # Starts with hyphen after dot
        self.assertFalse(self.app.validate_target("example.com-")) # Ends with hyphen

        # Invalid domain names - Invalid characters
        self.assertFalse(self.app.validate_target("example.com/path")) # Paths not allowed
        self.assertFalse(self.app.validate_target("example.com?query=1")) # Query params not allowed
        self.assertFalse(self.app.validate_target("example com")) # Spaces not allowed
        self.assertFalse(self.app.validate_target("ex!ample.com")) # Special chars not allowed
        self.assertFalse(self.app.validate_target("example.com#anchor")) # Anchors not allowed

        # Invalid formats
        self.assertFalse(self.app.validate_target("example..com"))

        # Empty or very short
        self.assertFalse(self.app.validate_target(""))
        # Note: 'a' is actually valid under the regex `^[a-zA-Z0-9]$`
        self.assertTrue(self.app.validate_target("a"))

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

if __name__ == '__main__':
    unittest.main()
