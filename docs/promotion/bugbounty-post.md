# r/bugbounty post — DRAFT

r/bugbounty allows medium self-promotion but prefers writeups and tips. Frame
this as a lesson learned. The tool goes at the end.

**Post this first**, before Show HN or r/netsec.

---

## Title

PSA: check your recon tool's exit codes before you trust "0 findings"

## Body

I wasted a few weeks early on concluding targets were clean when my tooling was
actually failing. Sharing in case it saves someone else the time.

**The bug:** most recon wrappers treat "the tool produced no output" and "the
target has nothing" as the same thing. They aren't. A tool that ran fine on a
target with no results writes an empty file — and so does a run that produced
nothing for any other reason. Your report can't tell them apart.

Quick check on your own workflow:

```bash
subfinder -d example.com -o subs.txt
echo "exit code: $?"
ls -la subs.txt        # a failed tool still creates this file, just empty
```

If your wrapper marks the scan "complete" without looking at the exit code,
then a rate-limited subfinder and a genuinely empty domain look identical in
your results. You move on to the next target and never find out.

**Why "check the file isn't empty" doesn't fix it:** a tool that ran fine on a
target with no results also writes an empty file. I tested it — subfinder
against a domain with no subdomains exits 0 and writes a 0-byte file. The exit
code plus stderr is what tells the two apart.

**What I did about it:** I got annoyed enough to build the check into a tool I
use. It refuses to start a scan if a required tool can't run, and every report
states which tools actually executed and what each exited with:

```
**Scan Confidence:** PARTIAL

## Scan Integrity

- `subfinder`: ok (exit 0)
- `httpx`: ok (exit 0)
- `nuclei`: **FAILED** — exit 1: no templates installed
```

It's a desktop GUI, one-command install, no Go toolchain needed:

```
curl -fsSL https://raw.githubusercontent.com/bongthrottla/bugbountyhunter/main/install.sh | bash
```

https://github.com/bongthrottla/bugbountyhunter

**Two specific traps worth knowing about:**

1. `httpx` is both a Python library CLI and ProjectDiscovery's probe. If you
   have both on PATH the wrong one shadows the real one, and it fails in a way
   that looks like a network problem. I hit this and spent an hour on it.

2. Some tools suppress stderr under `-silent`, so when they fail you get an
   exit code and no reason. Capture stderr anyway — some failures still write
   it.

Curious whether others have hit this, and what you use to catch it. I don't
think it's specific to recon — any pipeline that shells out and treats empty
output as a negative result has this.

---

## Rules for this post

- Disclose authorship: "I built this" in the body, which it already does.
- Lead with the tip, not the tool. The tool is the last third.
- Answer "why not reNgine" honestly if it comes up: reNgine is more capable,
  and you should use it if you want coverage. This is for people who want to
  see each step.
- Do not cross-post the same text to r/netsec. That post is different and
  research-framed (see `netsec-post.md`).
