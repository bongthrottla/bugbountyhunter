# Show HN — DRAFT

Show HN is for something people can try, that you made, and that you are
around to discuss. No signup. No marketing language. Never ask for upvotes.

---

## Title

Show HN: Recon tool that reports its own scan confidence

## Body

I kept getting burned by recon wrappers that report "0 findings" when actually
a tool had failed. A tool that ran fine on an empty target writes a 0-byte
output file, and so does a run that produced nothing for any other reason — so
"the scan found nothing" and "the scan never ran" produce identical reports.

I went through my own scan history: 11 scans, 2 recorded as failed, and the
other 9 marked "completed" with no way to tell retroactively which had actually
run. That's the bug. Not that scans fail, but that a failed scan and a clean
scan look the same.

This tool records every tool's exit code and puts a confidence level at the top
of every report:

    **Scan Confidence:** PARTIAL

    ## Scan Integrity

    - `subfinder`: ok (exit 0)
    - `httpx`: ok (exit 0)
    - `nuclei`: **FAILED** — exit 1: no templates installed

It also refuses to start a scan whose required tools can't execute, so you
never get a "completed" scan that was never going to work.

Install is one command, no Go toolchain needed:

    curl -fsSL https://raw.githubusercontent.com/bongthrottla/bugbountyhunter/main/install.sh | bash

Repo: https://github.com/bongthrottla/bugbountyhunter

It's deliberately small — subfinder, httpx, nuclei, ffuf, dalfox behind a
desktop GUI. It is not trying to beat reNgine or reconftw on coverage; it's
trying to be honest about its own limits. It also detects what changed between
scans of the same target, which is the thing that makes re-running worthwhile.

Happy to answer anything about the failure modes, or about why checking that
the output file exists is not sufficient (a failed tool writes the file too).

## First comment (post immediately after)

Author here. Two things I'd flag:

The confidence levels are FULL / PARTIAL / NONE. PARTIAL means at least one
tool failed, so the finding list is incomplete in a way you can't see from the
findings alone.

The most useful test is to deliberately break a tool and see what your own
pipeline says. Point it at a tool that exits non-zero and check whether the
report says "no findings" or "this tool failed". If it says the former, the
bug is there.

---

## Rules for this post

- Post when you can sit in the thread all day. HN rewards author presence.
- Answer criticism directly. "You're right, that's a limitation" beats
  defending.
- The likely top objection is "why not just use reNgine". Answer honestly: you
  should, if you want coverage. This is for people who want to understand each
  step and trust the output.
- Do not ask for upvotes, and do not post it more than once.
