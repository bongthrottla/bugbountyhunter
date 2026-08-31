import pytest
import os
import sqlite3
import tkinter as tk
from BugBountyHunter import BugBountyHunter

@pytest.fixture
def app_instance(monkeypatch, tmp_path):
    # Change working directory to tmp_path so directories and db are created there
    monkeypatch.chdir(tmp_path)

    # We need a Tk root for the app
    root = tk.Tk()

    # Instantiate the app
    app = BugBountyHunter(root)

    yield app

    # Teardown: close DB connection and destroy root
    if hasattr(app, 'conn') and app.conn:
        app.conn.close()
    root.destroy()

def test_validate_target(app_instance):
    # Test valid targets
    assert app_instance.validate_target("example.com") is True
    assert app_instance.validate_target("sub.example.com") is True
    assert app_instance.validate_target("http://example.com") is True
    assert app_instance.validate_target("https://example.com") is True
    assert app_instance.validate_target("example-domain.com") is True

    # Test invalid targets
    assert app_instance.validate_target("invalid_domain.com") is False
    assert app_instance.validate_target("-invalid.com") is False
    assert app_instance.validate_target("invalid-.com") is False
    assert app_instance.validate_target("") is False

def test_get_required_tools(app_instance):
    # Test valid scan types
    assert app_instance.get_required_tools("basic") == ["subfinder", "httpx"]
    assert app_instance.get_required_tools("comprehensive") == ["subfinder", "httpx", "nuclei"]
    assert app_instance.get_required_tools("xss") == ["httpx", "dalfox"]
    assert app_instance.get_required_tools("dirfuzz") == ["httpx", "ffuf"]

    # Test invalid scan type
    assert app_instance.get_required_tools("unknown") == ["subfinder", "httpx"]

def test_setup_directories(app_instance, tmp_path):
    # setup_directories is called in __init__, so directories should exist in tmp_path
    directories = ['outputs', 'scans', 'reports', 'wordlists', 'configs']
    for directory in directories:
        assert (tmp_path / directory).is_dir()

def test_init_database(app_instance, tmp_path):
    # init_database is called in __init__, so db should exist
    db_path = tmp_path / 'scans' / 'bugbounty.db'
    assert db_path.is_file()

    # Verify tables exist
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    assert "scans" in tables
    assert "subdomains" in tables
    assert "vulnerabilities" in tables

    conn.close()

from unittest.mock import MagicMock, patch

def test_run_scan_os_exception(app_instance):
    # This exception will occur in os.makedirs since cursor.execute completes
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 123

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    app_instance.conn = mock_conn
    app_instance.log = MagicMock()

    with patch('os.makedirs', side_effect=OSError("Disk full")):
        app_instance.run_scan("example.com", "basic")

        app_instance.log.assert_called_with("Scan failed: Disk full", "ERROR")
        mock_cursor.execute.assert_any_call("UPDATE scans SET status = 'failed' WHERE id = ?", (123,))

def test_run_scan_db_exception(app_instance):
    # Create a mock cursor
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.OperationalError("Database is locked")

    # Mock the conn property rather than the instance method directly
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Replace app_instance's conn with the mock
    app_instance.conn = mock_conn

    # Mock the log method to verify it's called
    app_instance.log = MagicMock()

    # Run the scan
    app_instance.run_scan("example.com", "basic")

    # Verify that the log method was called with the error
    app_instance.log.assert_called_with("Scan failed: Database is locked", "ERROR")

    # Because it fails before scan_id is assigned (or even cursor in some cases depending on where the error throws),
    # the failure recovery doesn't attempt to use the undefined scan_id
    # We verify it doesn't crash here with an UnboundLocalError by just ensuring the method finishes without error
