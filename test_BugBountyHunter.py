import pytest
import os
import sqlite3
import tkinter as tk
from pathlib import Path
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


def test_parse_nuclei_results_skips_malformed(app_instance, tmp_path):
    """Malformed JSON lines must be skipped without losing valid findings.

    nuclei emits JSONL; a truncated or non-JSON line must not abort the parse
    or silently drop the rows around it.
    """
    nuclei_output = tmp_path / "nuclei_results.json"
    nuclei_output.write_text(
        '{"template-id": "xss-vuln", "info": {"severity": "high", "name": "Reflected XSS"}, "matched-at": "http://example.com/xss"}\n'
        'This is not a json string\n'
        '{"missing_bracket": true\n'
        '{"template-id": "sqli-vuln", "info": {"severity": "critical", "name": "SQL Injection"}, "matched-at": "http://example.com/sqli"}\n'
    )

    cursor = app_instance.conn.cursor()
    cursor.execute(
        "INSERT INTO scans (target, scan_type, status) VALUES (?, ?, ?)",
        ("example.com", "comprehensive", "completed"),
    )
    scan_id = cursor.lastrowid
    app_instance.conn.commit()

    app_instance.parse_nuclei_results(str(nuclei_output), scan_id)

    rows = cursor.execute(
        "SELECT vuln_type, severity, description, url FROM vulnerabilities WHERE scan_id = ?",
        (scan_id,),
    ).fetchall()

    assert len(rows) == 2
    assert rows[0] == ("xss-vuln", "high", "Reflected XSS", "http://example.com/xss")
    assert rows[1] == ("sqli-vuln", "critical", "SQL Injection", "http://example.com/sqli")


def test_parse_nuclei_results_batching(app_instance, tmp_path):
    """The 1000-row insert batch boundary must not lose or duplicate rows."""
    for count in (0, 1, 999, 1000, 1001, 2500):
        nuclei_output = tmp_path / f"nuclei_{count}.json"
        with open(nuclei_output, "w") as f:
            for i in range(count):
                f.write(
                    '{"template-id": "t%d", "info": {"severity": "high", "name": "n%d"}, "matched-at": "https://x/%d"}\n'
                    % (i, i, i)
                )

        cursor = app_instance.conn.cursor()
        cursor.execute(
            "INSERT INTO scans (target, scan_type, status) VALUES (?, ?, ?)",
            ("example.com", "comprehensive", "running"),
        )
        scan_id = cursor.lastrowid
        app_instance.conn.commit()

        app_instance.parse_nuclei_results(str(nuclei_output), scan_id)

        stored = cursor.execute(
            "SELECT COUNT(*) FROM vulnerabilities WHERE scan_id = ?", (scan_id,)
        ).fetchone()[0]
        assert stored == count, f"input {count} stored {stored}"


def test_scan_output_permissions(app_instance, tmp_path):
    """Scan output holds live target data and must not be world-readable."""
    import stat

    if os.name == "nt":
        pytest.skip("POSIX permissions not applicable on Windows")

    for name in ("scans", "reports", "outputs"):
        mode = (tmp_path / name).stat().st_mode
        assert not (mode & stat.S_IROTH), f"{name} is world-readable"
        assert not (mode & stat.S_IWOTH), f"{name} is world-writable"


def test_bundled_wordlists_present_and_sane(app_instance):
    """The shipped wordlists must exist, be non-trivial, and be clean.

    A leading slash in an entry produces a doubled '//path' request and a false
    negative, so it is checked explicitly.
    """
    wl_dir = Path(__file__).resolve().parent / "wordlists"
    for name, minimum in (("common.txt", 1000), ("raft-small-directories.txt", 5000)):
        path = wl_dir / name
        assert path.is_file(), f"{name} missing from the repo"
        entries = [
            line.strip()
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
        assert len(entries) >= minimum, f"{name} only has {len(entries)} entries"
        assert not [e for e in entries if e.startswith("/")], f"{name} has leading slashes"
        assert len(entries) == len(set(entries)), f"{name} has duplicate entries"
        assert not [e for e in entries if any(ord(c) > 126 for c in e)], f"{name} has non-ASCII"


def test_pick_wordlist_prefers_bundled(app_instance):
    """With no system install and no config override, the bundled list is used."""
    picked = app_instance._pick_wordlist()
    assert picked is not None
    assert picked.is_file()
    assert app_instance._count_lines(picked) > 1000


def test_pick_wordlist_honours_config(app_instance, tmp_path, monkeypatch):
    """A wordlist_path in config.ini takes precedence."""
    custom = tmp_path / "custom.txt"
    custom.write_text("alpha\nbeta\n")

    monkeypatch.setattr(
        app_instance, "_configured_wordlist", lambda: str(custom)
    )
    assert app_instance._pick_wordlist() == custom


def test_count_lines_handles_missing(app_instance, tmp_path):
    assert app_instance._count_lines(tmp_path / "nope.txt") == 0
    real = tmp_path / "wl.txt"
    real.write_text("a\n\nb\n  \nc\n")
    assert app_instance._count_lines(real) == 3


def test_parse_httpx_jsonl_captures_status_and_tech(app_instance, tmp_path):
    """httpx -jsonl output must populate status_code and technologies.

    These columns exist in the schema but were never written, so reports could
    not show a status code or tech stack.
    """
    httpx_out = tmp_path / "live.jsonl"
    httpx_out.write_text(
        '{"url":"https://api.example.com","status_code":200,'
        '"tech":["nginx","React"],"host":"api.example.com"}\n'
        '{"url":"https://dead.example.com","status_code":403,'
        '"tech":["Cloudflare"],"host":"dead.example.com"}\n'
        'not json\n'
    )

    rows = app_instance.parse_httpx_jsonl(str(httpx_out))

    assert len(rows) == 2
    assert rows[0]["host"] == "api.example.com"
    assert rows[0]["status_code"] == 200
    assert rows[0]["technologies"] == "nginx, React"
    assert rows[1]["status_code"] == 403


def test_scan_integrity_records_tool_outcomes(app_instance):
    """Every scan must record which tools ran and which failed.

    This is the feature no competitor has: a scan that cannot prove it ran is
    indistinguishable from a clean target, which is the worst outcome for a
    beginner.
    """
    app_instance.scan_integrity = {}

    app_instance._record_integrity("subfinder", ok=True, detail="exit 0")
    app_instance._record_integrity("httpx", ok=True, detail="exit 0")
    app_instance._record_integrity("nuclei", ok=False, detail="exit 1: no templates")

    lines = app_instance.format_integrity_lines()

    assert any("subfinder" in l and "ok" in l.lower() for l in lines)
    assert any("nuclei" in l and "FAILED" in l for l in lines)
    assert app_instance.integrity_confidence() == "PARTIAL"


def test_scan_integrity_full_when_all_ok(app_instance):
    app_instance.scan_integrity = {}
    app_instance._record_integrity("subfinder", ok=True, detail="exit 0")
    app_instance._record_integrity("httpx", ok=True, detail="exit 0")
    assert app_instance.integrity_confidence() == "FULL"


def test_scan_integrity_none_when_all_failed(app_instance):
    app_instance.scan_integrity = {}
    app_instance._record_integrity("subfinder", ok=False, detail="not found")
    assert app_instance.integrity_confidence() == "NONE"


def test_diff_scans_reports_new_and_removed_hosts(app_instance):
    """Comparing two scans must surface what changed since last time."""
    cur = app_instance.conn.cursor()

    cur.execute("INSERT INTO scans (target,scan_type,status) VALUES (?,?,?)",
                ("example.com", "basic", "completed"))
    old = cur.lastrowid
    cur.execute("INSERT INTO scans (target,scan_type,status) VALUES (?,?,?)",
                ("example.com", "basic", "completed"))
    new = cur.lastrowid

    for host in ("a.example.com", "b.example.com", "gone.example.com"):
        cur.execute("INSERT INTO subdomains (scan_id,subdomain,is_alive) VALUES (?,?,?)",
                    (old, host, 1))
    for host in ("a.example.com", "b.example.com", "new.example.com"):
        cur.execute("INSERT INTO subdomains (scan_id,subdomain,is_alive) VALUES (?,?,?)",
                    (new, host, 1))
    app_instance.conn.commit()

    d = app_instance.diff_scans(old, new)

    assert d["added"] == ["new.example.com"]
    assert d["removed"] == ["gone.example.com"]
    assert d["unchanged"] == ["a.example.com", "b.example.com"]


def test_previous_scan_id_finds_earlier_completed_scan(app_instance):
    cur = app_instance.conn.cursor()
    cur.execute("INSERT INTO scans (target,scan_type,status) VALUES (?,?,?)",
                ("example.com", "basic", "completed"))
    first = cur.lastrowid
    cur.execute("INSERT INTO scans (target,scan_type,status) VALUES (?,?,?)",
                ("example.com", "basic", "failed"))
    cur.execute("INSERT INTO scans (target,scan_type,status) VALUES (?,?,?)",
                ("example.com", "basic", "completed"))
    third = cur.lastrowid
    app_instance.conn.commit()

    # A failed scan must not be used as a comparison baseline.
    assert app_instance.previous_scan_id("example.com", third) == first
    assert app_instance.previous_scan_id("example.com", first) is None
    assert app_instance.previous_scan_id("other.com", third) is None
