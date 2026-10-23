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
    # xss enumerates subdomains first, so it needs subfinder too
    assert app_instance.get_required_tools("xss") == ["subfinder", "httpx", "dalfox"]
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


def test_tool_usable_rejects_missing(app_instance):
    """A tool that is not on PATH must be reported unusable."""
    assert app_instance._tool_usable("definitely-not-a-real-tool-xyz") is False


def test_tool_usable_accepts_flagless_tool(app_instance, tmp_path, monkeypatch):
    """Regression: assetfinder has no version flag and exits non-zero on every
    probe, so it was reported missing even when installed and working.

    A tool that rejects unknown flags but prints usage must count as usable.
    """
    import os
    import stat

    fake = tmp_path / "flagless-tool"
    fake.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        "  -h|--help) echo 'Usage: flagless-tool [-subs-only]'; exit 0 ;;\n"
        '  *) echo "flag provided but not defined: $1" >&2; exit 2 ;;\n'
        "esac\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    monkeypatch.setattr(
        "BugBountyHunter.shutil.which", lambda name: str(fake) if name == "flagless-tool" else None
    )
    app_instance.tool_paths.pop("flagless-tool", None)
    assert app_instance._tool_usable("flagless-tool") is True


def test_check_tool_availability_matches_tool_usable(app_instance):
    """The startup check and the pre-scan check must never disagree."""
    fresh = app_instance.check_tool_availability()
    for tool, reported in fresh.items():
        assert reported == app_instance._tool_usable(tool), tool


def test_hostname_of(app_instance):
    """URLs and bare hostnames must normalise to the same bare hostname."""
    h = app_instance._hostname_of
    assert h("https://api.example.com") == "api.example.com"
    assert h("http://api.example.com") == "api.example.com"
    assert h("https://api.example.com/path?q=1#frag") == "api.example.com"
    assert h("https://api.example.com:8443/x") == "api.example.com"
    assert h("https://user:pw@api.example.com/x") == "api.example.com"
    assert h("API.Example.COM") == "api.example.com"
    assert h("api.example.com") == "api.example.com"
    assert h("") == ""
    assert h(None) == ""


def test_live_host_matching(app_instance, tmp_path):
    """Regression: httpx emits full URLs, subfinder emits bare hostnames.

    A plain `subdomain in live_hosts` test never matched, so every host was
    recorded as dead and reports claimed 'Live Hosts: 0' / 'Success Rate: 0%'
    even when live hosts were found.
    """
    scan_dir = tmp_path / "scan_x"
    scan_dir.mkdir()
    (scan_dir / "subdomains.txt").write_text(
        "api.example.com\nwww.example.com\ndead.example.com\n"
    )
    (scan_dir / "live_subdomains.txt").write_text(
        "https://api.example.com\nhttp://www.example.com\n"
    )

    cursor = app_instance.conn.cursor()
    cursor.execute(
        "INSERT INTO scans (target, scan_type, status) VALUES (?, ?, ?)",
        ("example.com", "basic", "running"),
    )
    scan_id = cursor.lastrowid
    app_instance.conn.commit()

    # Drive just the persistence half of run_basic_scan.
    subdomains = app_instance._read_lines(str(scan_dir / "subdomains.txt"))
    live_hosts = app_instance._read_lines(str(scan_dir / "live_subdomains.txt"))
    live_names = {app_instance._hostname_of(h) for h in live_hosts}
    live_names.discard("")
    for subdomain in subdomains:
        cursor.execute(
            "INSERT INTO subdomains (scan_id, subdomain, is_alive) VALUES (?, ?, ?)",
            (scan_id, subdomain, app_instance._hostname_of(subdomain) in live_names),
        )
    app_instance.conn.commit()

    alive = dict(cursor.execute(
        "SELECT subdomain, is_alive FROM subdomains WHERE scan_id = ?", (scan_id,)
    ).fetchall())

    assert alive["api.example.com"] == 1
    assert alive["www.example.com"] == 1
    assert alive["dead.example.com"] == 0
