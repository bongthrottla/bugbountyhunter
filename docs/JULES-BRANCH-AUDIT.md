# Jules branch audit — 2026-10-24

Audit of all 53 remote branches on `bongthrottla/bugbountyhunter`, against
`main` at `e6ceb95`.

## Summary

| Category | Count | Verdict |
|---|---|---|
| Already merged into `main` | 5 | Safe to delete |
| Duplicate fixes (same change, many branches) | 34 | Keep one, delete rest |
| Genuinely useful, not in `main` | 5 | Worth cherry-picking |
| Superseded by the local hardened branch | 9 | Drop |
| **Total** | **53** | |

The dominant pattern: Jules ran the same three or four tasks repeatedly and
opened a fresh branch each time. There are **12 near-identical security
branches** all doing `os.chmod(dir, 0o700)`, and **14 near-identical "Palette"
UX branches** all adding an Enter-key binding and autofocus to the target
entry. Neither was ever merged.

## Already merged (delete)

```
jules-15335525467432086967-2c03bdff
jules-5340483742144300422-69802388
jules-8176853340041219663-31a10a65
jules-testing-improvement-11418208824179922215
```

## Genuinely useful — not in `main`, worth cherry-picking

These are the only branches with real, non-duplicated value.

### 1. `perf/nuclei-batch-insert-13836630051281275876`
Batches vulnerability inserts with `executemany` in chunks of 1000 instead of
one `execute` per row. Real win on large nuclei result sets. **Recommended.**

### 2. `jules-optimize-nuclei-insert-13649143585306733195`
Same idea as above, slightly different implementation. Pick one of the two —
this one also touches 4 files, the other only 1.

### 3. `jules-7649827511964934412-2d869c0d`
`executemany` for the subdomain insert path plus a set-based lookup. Overlaps
with the live-host fix already applied locally.

### 4. `jules-17899839927857073476-60d8c528`
Fixes an N+1 query and an O(N) lookup in the subdomain database path.

### 5. `jules-12764389097893428524-336fb140`
Extracts the large literal guide strings out of `BugBountyHunter.py` into data
files (215 insertions, 382 deletions). This is the same direction the local
branch already took by moving `tips_guide.txt` / `install_guide.txt` into
`data/`. Partially superseded, but the extraction of the *remaining* inline
strings is still worth doing.

## Duplicate clusters (keep one, delete the rest)

### Security — `os.chmod(dir, 0o700)`, 12 branches
```
sentinel-security-fix-10508705435339884357        (HIGH)
sentinel-security-fix-12463192884621262627        (HIGH)
sentinel/fix-local-info-disclosure-15050027978344751598  (HIGH)
fix/secure-file-permissions-14349712744320234263  (adds db 0o600 — best of the set)
sentinel-directory-permissions-11079373791881768117
sentinel-fix-dir-permissions-1130550412329662010
sentinel-fix-local-file-permissions-3560434093968595401
sentinel-fix-local-info-disclosure-13310238437237584119
sentinel-local-info-disclosure-fix-13672901617279920033
sentinel-secure-os-makedirs-2599514209451008951
sentinel/fix-local-info-disclosure-1325099771915664590
security/sentinel-fix-information-disclosure-14167324213960057048
```
`fix/secure-file-permissions-14349712744320234263` is the most complete — it
also chmods the SQLite file to `0o600`. The rest are subsets.

**Note:** the local hardened branch already adds a `.gitignore` covering
`scans/`, `reports/` and `*.db`, which addresses the same disclosure risk at
the source. The chmod is still worth having as defence in depth.

### Palette / UX — Enter key + autofocus on target entry, 14 branches
```
palette-keyboard-a11y-14925258253651780058
palette-target-input-ux-16605832121361168456
palette-ux-enter-key-support-8012514824038976722
palette-ux-improvements-15612809865633679967
palette-ux-improvements-8789427591268149628
palette-ux-improvements-9241660565158197162
palette-ux-improvements-9583370798582421217
palette-ux-improvements-9721446533263911752
palette-ux-keyboard-accessibility-802700321118117008
palette/keyboard-accessibility-entry-15144676019122954391
palette/tkinter-keyboard-a11y-12398582557482845294
palette/ux-enhancements-8390685445927303531
palette/ux-keyboard-a11y-8276749011955109046
ux-focus-return-bind-1716601180540856140
```
All do the same thing. `palette-ux-improvements-9721446533263911752` is the
largest (23 insertions) and the most complete.

### Test additions, 4 branches
```
add-get-required-tools-tests-10822125985408620846
jules-2118641704301925861-225116d8   (validate_target)
jules-12251730200791767246-59cfb2f7  (parse_nuclei_results)
jules-add-parse-nuclei-tests-fix-16329626685535749799
jules-10624300378845167173-cd308d9c  (check_tool_availability)
```
The local branch already has a 9-test suite covering all of these areas. These
are superseded — but `jules-add-parse-nuclei-tests-fix-16329626685535749799`
tests the JSONDecodeError path specifically, which the local suite does not.

### Cleanup branches, 3
```
jules-7681197575296431522-89403922   remove duplicate script.py
jules-8691816616439708836-d18cab1a   remove unused bug_bounty_hunter.py
jules-15335525467432086967-2c03bdff-4497330893901571797  remove dupes + fix requirements
fix/rename-install-sh-4259962312054674194  rename install (1).sh
```
All four changes are already applied on the local hardened branch (junk files
dropped, `install.sh` renamed, `requirements.txt` fixed).

### Refactor branches, 3
```
jules-2044956745291275854-a08f9fb4   refactor create_main_tab
refactor-create-main-tab-14156841550133504712  same
jules-17450071675527418744-5633868c  remove unused imports
```
Low value. The unused-imports one is worth a look if doing a lint pass.

### Other
```
jules-4838195617058976815-fa6506c9   set-based live_hosts lookup — superseded
jules-13354751847745388638-c4d0789e  report string concat — micro-opt
jules-5653256857438590558-75ef7b75   report string concat — duplicate of above
testing-improvement-run-scan-exception-18334321089662839254  run_scan exception handling
```

## Recommendation

1. Cherry-pick `perf/nuclei-batch-insert-13836630051281275876` — the one clear
   performance win not already applied.
2. Cherry-pick the `0o600` SQLite chmod from
   `fix/secure-file-permissions-14349712744320234263`.
3. Cherry-pick the JSONDecodeError test from
   `jules-add-parse-nuclei-tests-fix-16329626685535749799`.
4. Delete all 53 branches.

Everything else is either merged, duplicated, or already done better on the
local hardened branch.
