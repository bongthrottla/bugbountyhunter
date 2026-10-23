# Agent instructions

Guidance for automated coding agents (Jules, Copilot, Claude Code, Codex, or
similar) working on this repository.

## Read this first

This is a **security tool that sends live traffic to third-party hosts**. A
change that makes it scan more aggressively, retry harder, or hide its origin
is a behaviour change with legal consequences for the user. Treat scan
behaviour as sensitive.

## Before you open a branch

1. **Check whether the work already exists.** Run:
   ```bash
   git fetch --all
   git branch -r | grep -i <keyword>
   git diff main...origin/<branch> --stat
   ```
   This repo accumulated 53 branches where the same fix was opened repeatedly.
   Duplicate branches waste review time and clutter the branch list.

2. **Check whether `main` already does it.** Several branches were opened
   against code that had already been fixed. Diff before you write.

## What is genuinely useful here

- **Correctness bugs in the scan pipeline.** The highest-value class. A tool
  that fails silently and reports a clean scan is worse than one that crashes.
- **Tests for existing behaviour.** Especially failure paths: tool exits
  non-zero, output file missing, malformed JSON, empty results.
- **Cross-platform fixes.** The app must work on Linux, macOS and Windows.
- **Performance on large result sets.** Scans can return thousands of rows.

## What is not useful

- **Cosmetic churn.** Reformatting, renaming, or reordering code that works.
- **Repeated UX micro-tweaks.** One Enter-key binding and autofocus is enough;
  do not open a new branch per variation.
- **Speculative hardening** that changes scan behaviour without a stated threat.
- **Adding dependencies.** The GUI, database and process handling are stdlib
  only, deliberately. Keep it that way unless there is a strong reason.

## Rules for scan behaviour

- **Never** make a scan report success when a tool failed. Empty output from a
  failed tool must be distinguishable from "no findings".
- **Never** add retry loops that hammer a target. Respect rate limits.
- **Never** add code that obscures the scanner's origin or identity.
- **Never** add a scan type that runs without a preflight tool check.
- Do not weaken the authorised-use constraints in the README.

## Code conventions

- Python 3.7+ compatible. No walrus in a way that breaks 3.7, no `match`.
- Standard library only for core functionality.
- `tkinter` for all GUI work.
- Every new behaviour needs a test in `test_BugBountyHunter.py`.
- Tests must not require network access or real recon tools. Use `tmp_path` and
  fakes. The suite runs under `xvfb-run` in CI, so it needs a display but no
  network.

## Before you open a PR

```bash
python -m compileall -q BugBountyHunter.py script.py
xvfb-run -a python -m pytest test_BugBountyHunter.py -v
```

Both must pass. State in the PR description:

- what was broken (with a reproduction if it is a bug fix)
- what you changed
- how you verified it — actual command output, not a description of intent

Do not claim a fix works without having run it.

## Commits

One logical change per commit. Conventional-commit prefixes are welcome
(`fix:`, `test:`, `perf:`, `docs:`). Do not commit:

- `scans/`, `reports/`, `outputs/` — these hold real target data
- `*.db`, `*.sqlite` — scan history
- `__pycache__/`, `*.pyc`
- editor or OS files

`.gitignore` covers these. If you find yourself needing `git add -f` on one of
them, stop — you are about to publish someone's reconnaissance data.
