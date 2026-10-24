# Promotion plan

Post in this order, one per day. Do not post everywhere at once — each channel
needs you present in the thread.

## Order and rules

| # | Channel | Audience | Rules that matter | Post file |
|---|---|---|---|---|
| 1 | r/bugbounty | 80–140k | Medium self-promo OK; prefers writeups and tips | `bugbounty-post.md` |
| 2 | Show HN | large | Must be tryable, no signup; author in thread all day; never ask for upvotes | `show-hn.md` |
| 3 | DEV.to | devs | Build logs welcome; teach, don't announce | `devto-build-log.md` |
| 4 | r/netsec | 550k | **Low self-promo tolerance**; research only; tool link in a comment | `netsec-post.md` |
| 5 | LibHunt | devs | Open-source repos only, auto-indexed from GitHub | nothing to post |
| 6 | Product Hunt | broad | Launch morning, maker comment | reuse `show-hn.md` body |

## Before posting anything

1. Confirm the one-click install works on a clean machine:
   ```bash
   rm -rf /tmp/promo-test && mkdir -p /tmp/promo-test && touch /tmp/promo-test/.bashrc
   env -i HOME=/tmp/promo-test PATH="/usr/bin:/bin" \
     bash -c 'curl -fsSL https://raw.githubusercontent.com/bongthrottla/bugbountyhunter/main/install.sh | BBH_DIR=/tmp/promo-test/bbh bash' 2>&1 | tail -12
   ```
   Expected: `5/5 Verifying ✓ 7/7 recon tools available ✓ Basic Recon will work`

2. Confirm the screenshot in the README is current (the Reports tab gained an
   Export JSON button, the status bar now shows confidence).

3. Confirm every number you quote is one you measured. The current real figures
   from the scan database: **11 scans, 2 failed, 9 completed-but-unverifiable**.
   Do not round up. Do not present a sample of 11 as a rate.

## Skip r/netsec if

- the post would be your first contribution there, or
- you can't sit in the thread answering questions, or
- someone else has posted the same angle recently.

A removed post burns the account's standing. It is the one channel where
posting badly is worse than not posting.

## Do not

- Ask for upvotes or stars, anywhere.
- Post the same text to r/netsec and r/bugbounty. They are framed differently
  for a reason.
- Claim the tool beats reNgine, reconftw or bbot on coverage. It doesn't, and
  the audience knows it.
- Quote a failure rate you haven't measured.
