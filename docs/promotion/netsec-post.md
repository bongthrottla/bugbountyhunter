# r/netsec post — DRAFT

**Do not post this without reading the rules section at the bottom.**

r/netsec has low tolerance for promotion and removes vendor content. This post
must be about the *problem*, with the tool mentioned in a comment.

---

## Title

Silent scan failures: your recon report may be telling you a target is clean when it isn't

## Body

### The problem

Most recon wrappers treat "the tool produced no output" and "the target has
nothing" as the same fact. They are not the same fact, and in a
subfinder → httpx → nuclei pipeline the tool cannot tell them apart:

- subfinder hits a rate limit → empty file → "0 subdomains found"
- httpx fails on a bad resolver → empty file → "0 live hosts"
- nuclei can't load templates → empty file → "0 vulnerabilities"

In each case the pipeline exits, the scan is marked complete, and the report is
byte-for-byte identical to a genuinely clean target.

### What this cost me

I went back through my own scan history. 11 scans, of which 2 failed outright
and were recorded as failed. That part is fine — the failures were loud.

The problem is the other 9. They were recorded as `completed`, and with the
code as it was there is **no way to tell now which of them actually ran**. A
"completed" scan whose nuclei silently died looks exactly like a completed scan
that ran cleanly. Those 9 reports are unfalsifiable after the fact.

That is the actual defect. Not that scans fail — scans fail constantly, that is
normal — but that a failed scan and a clean scan are indistinguishable in the
output.

### Why checking the output file is not enough

The obvious fix is "check that the output file exists". It does not work. I
tested it:

```bash
$ subfinder -d definitely-not-a-real-domain-xyz123.com -o /tmp/s1.txt -silent
exit: 0
$ ls -la /tmp/s1.txt
-rw-r--r-- 1 root root 0 /tmp/s1.txt     # exists, zero bytes
```

A **successful** run against a target with no results writes an empty file. So
does a run that produced nothing for any other reason. Checking the file exists
tells you nothing, and checking it is non-empty tells you nothing either.

I also found that a *fatal* error can look clean if you read the wrong signal.
`nuclei` with a bad template path prints a fatal error and writes an empty
output file:

```bash
$ nuclei -l /dev/null -o /tmp/n1.jsonl -t /nonexistent-templates -silent
[FTL] Could not run nuclei: no templates provided for scan
$ ls -la /tmp/n1.jsonl
-rw-r--r-- 1 root root 0 /tmp/n1.jsonl
```

It does exit non-zero, so the exit code catches it — but only if you capture
stderr do you learn *why*, and only if you look at the exit code rather than
the output file do you catch it at all.

You need both signals: **exit code and stderr contents.** And you need to know
the binary you ran was the right one.

### The fix I settled on

Three parts:

1. **Preflight.** Before a scan starts, check every required tool actually
   executes. If one cannot, refuse to start and say which. This prevents the
   worst case — a scan that was never going to work being recorded as done.

2. **Record every invocation.** Exit code and first stderr line, per tool, per
   scan. Not a boolean "success", the actual code.

3. **Put it in the output.** Every report states its own confidence and lists
   each tool's outcome. A reader can tell a clean target from a scan that
   didn't run.

```
**Scan Confidence:** PARTIAL

## Scan Integrity

- `subfinder`: ok (exit 0)
- `httpx`: ok (exit 0)
- `nuclei`: **FAILED** — exit 1: no templates installed
```

### The generalisable point

This is not specific to recon tooling. Any pipeline that shells out to external
binaries and treats empty output as a negative result has this bug. If your
scanner, linter, or CI job can report "nothing found" when the underlying tool
crashed, it can report a clean pass on a broken run, and you will believe it.

The test is simple: break the tool deliberately and see what your pipeline
says. If it says "no findings", you have this bug.

### Code

I built this into a small beginner-focused tool. Comment, per subreddit norms:
`github.com/bongthrottla/bugbountyhunter`

Happy to go into the specific failure modes I saw per tool.

---

## Rules for this post

- **Lead with the measured finding.** The 11/2/9 breakdown is real, taken from
  an actual scan database. Do not inflate it. If asked for more data, say the
  sample is small and you are not claiming a population rate.
- **The tool link goes in a comment**, not the body. r/netsec removes tool
  announcements.
- **Disclose authorship.** "I built this" in the comment. Hiding it gets you
  banned.
- **Do not ask for upvotes**, here or anywhere.
- **Skip this channel entirely** if the post would be the first thing you've
  ever contributed to r/netsec. Post the r/bugbounty one first.
