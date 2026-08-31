import unittest
from unittest.mock import MagicMock
from BugBountyHunter import BugBountyHunter

class TestBugBountyHunter(unittest.TestCase):
    def setUp(self):
        # We need to mock Tkinter parts or just test the method directly if it doesn't rely on self state
        self.app = BugBountyHunter.__new__(BugBountyHunter)

    def test_get_required_tools(self):
        # Test basic scan
        self.assertEqual(self.app.get_required_tools('basic'), ['subfinder', 'httpx'])

        # Test comprehensive scan
        self.assertEqual(self.app.get_required_tools('comprehensive'), ['subfinder', 'httpx', 'nuclei'])

        # Test xss scan
        self.assertEqual(self.app.get_required_tools('xss'), ['httpx', 'dalfox'])

        # Test sqli scan
        self.assertEqual(self.app.get_required_tools('sqli'), ['httpx', 'sqlmap'])

        # Test dirfuzz scan
        self.assertEqual(self.app.get_required_tools('dirfuzz'), ['httpx', 'ffuf'])

        # Test custom scan
        self.assertEqual(self.app.get_required_tools('custom'), ['subfinder', 'httpx'])

        # Test unknown scan type fallback
        self.assertEqual(self.app.get_required_tools('unknown_scan_type'), ['subfinder', 'httpx'])

        # Test None scan type fallback
        self.assertEqual(self.app.get_required_tools(None), ['subfinder', 'httpx'])

if __name__ == '__main__':
    unittest.main()
