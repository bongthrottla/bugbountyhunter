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
