# DEV.to build log — DRAFT

Longer technical post. Highest-effort, highest-credibility channel because it
teaches rather than announces. Structure: the bug I found in my own tool → how
I reproduced it → the fix → what I learned.

---

## Title

I found a silent failure bug in my own recon tool, and it's probably in yours too

## Tags

`security` `python` `programming` `opensource`

---

## The report that lied to me

I built a recon tool that wraps `subfinder`, `httpx` and `nuclei` behind a GUI.
It stores results in SQLite and generates markdown reports.

One day I noticed something odd. A scan of a target I know has plenty of
subdomains came back with a clean report:

```
- **Total Subdomains Found:** 0
- **Live Hosts:** 0
- **Success Rate:** 0.0%
```

The scan was marked `completed`. The report looked exactly like a genuinely
empty target.

subfinder was rate-limited. It wrote an empty `subdomains.txt` and exited. My
code read the file, found zero lines, and reported success.

## Why this is the worst possible bug for this tool

The tool is aimed at beginners. A beginner who sees "0 subdomains" concludes
the target has no attack surface and moves to the next one. They don't know to
be suspicious. I didn't.

The general shape: **any pipeline that shells out to a binary and treats empty
output as a negative result has this bug.** Scanners, linters, CI jobs. If the
underlying tool can fail in a way that produces no output, and you only check
the output, you can't distinguish "nothing found" from "never ran".

## Reproducing it

I reproduced it with a stand-in tool so I could control the failure:

```bash
# a "subfinder" that fails like a rate limit does: exit non-zero, no output
cat > /tmp/fake-tools/subfinder <<'EOF'
#!/bin/sh
echo "rate limited" >&2
exit 1
EOF
chmod +x /tmp/fake-tools/subfinder
```

Point the scanner at it with the fake first on PATH. The old code produced a
`completed` scan with zero findings. Exactly what a clean target looks like.

## The fix that doesn't work

My first attempt was to check the output file exists. That fails immediately:
**a tool that ran fine on a target with no results writes the same empty
file.** A crash and a genuinely empty target are indistinguishable from the
output alone.

Second attempt: check the file is non-empty. Also wrong — a tool that ran
successfully against a target with no results *also* writes an empty file.

The exit code is the only signal that separates the two cases.

## The fix that does work

Three parts.

**1. Preflight.** Before starting, verify every required tool actually
executes. If one can't, refuse to start and name it.

```python
def _tool_usable(self, tool):
    """True only if the tool is on PATH AND actually executes."""
    path = self.tool_paths.get(tool) or shutil.which(tool)
    if path is None:
        return False
    for flag in ("--version", "-version", "version", "-V", "-h", "--help"):
        try:
            r = subprocess.run([path, flag], capture_output=True,
                               text=True, timeout=8)
        except (subprocess.TimeoutExpired, OSError):
            continue
        combined = f"{r.stdout or ''}{r.stderr or ''}".lower()
        if "flag provided but not defined" in combined:
            continue
        if r.returncode == 0 or "usage" in combined:
            self.tool_paths[tool] = path
            return True
    return False
```

**2. Record every invocation.** Exit code and first stderr line, per tool.

```python
ok = proc.returncode in (0, -15)
self._record_integrity(
    os.path.basename(command[0]),
    ok=ok,
    detail=f"exit {proc.returncode}",
)
```

**3. Put it in the output.** Every report states its confidence:

```
**Scan Confidence:** PARTIAL

## Scan Integrity

- `subfinder`: ok (exit 0)
- `httpx`: ok (exit 0)
- `nuclei`: **FAILED** — exit 1: no templates installed
```

A reader can now tell a clean target from a scan that didn't run.

## Two traps I hit on the way

**Tool name collisions.** `httpx` is both a Python HTTP library CLI and
ProjectDiscovery's probe. I had both on PATH. The Python one shadowed the real
one, rejected `-l`, and exited non-zero — which looked exactly like a network
failure. If you resolve tools by name, assert the resolved binary is the one
you expect.

**Tools with no version flag.** My `_tool_usable` probe tried four version
flags. `assetfinder` has none of them and exits non-zero on all of them, so a
perfectly good install was reported missing. Falling back to `-h` and treating
a usage dump as proof-of-life fixed it.

## What I'd tell you to do

Break a tool on purpose and see what your pipeline reports:

```bash
# rename your scanner's binary and run a scan
mv /usr/local/bin/yourtool /usr/local/bin/yourtool.bak
# run your pipeline
# if it says "no findings" instead of "tool missing", you have this bug
```

That's a two-minute test that could save you weeks.

The code is MIT licensed: https://github.com/bongthrottla/bugbountyhunter

---

## Notes

- Every code sample above is from the actual implementation and has been run.
- The 11-scan / 2-failed / 9-unverifiable figure is from a real scan database,
  not an estimate. Keep the framing honest: the sample is small.
- This post is the one that should be genuinely useful even to someone who
  never installs the tool.
