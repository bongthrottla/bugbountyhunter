# Wordlists

Directory-fuzzing wordlists used by the Directory Fuzzing scan type.

## Bundled lists

| File | Entries | Source |
|---|---|---|
| `raft-small-directories.txt` | ~20,110 | [SecLists](https://github.com/danielmiessler/SecLists) `Discovery/Web-Content/raft-small-directories.txt` |
| `common.txt` | ~4,751 | [SecLists](https://github.com/danielmiessler/SecLists) `Discovery/Web-Content/common.txt` |

Both are from SecLists, which is MIT licensed (Copyright © 2018 Daniel
Miessler) — the same license as this project. The raw files are committed so a
scan works without network access.

They are sanitised on fetch: CRLF stripped, control characters and zero-width
spaces removed, leading slashes dropped (a leading `/` produces a doubled
`//path` request and false negatives), blanks removed, and entries deduped.

## Refreshing them

```bash
./scripts/fetch-wordlists.sh
```

## Which list gets used

At scan time the app picks the first available of:

1. `wordlist_path` from `config.ini`, if set
2. A system install — `/usr/share/seclists/...`, `/usr/share/wordlists/dirb/...`,
   `/usr/share/wfuzz/wordlist/...` (what Kali ships)
3. The bundled lists above

If none exist it generates a minimal 24-entry fallback so a scan still runs.
The chosen list and its entry count are logged at the start of the scan.

## Using a bigger list

The bundled lists are deliberately small so they stay in the repo. For serious
work, install SecLists and point at a larger list:

```bash
sudo apt install seclists          # Kali / Debian
```

then set it in `config.ini`:

```ini
[scanning]
wordlist_path = /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
```

`raft-medium-directories.txt` is ~30k entries and `directory-list-2.3-medium.txt`
is ~220k. Larger lists take proportionally longer and generate more traffic —
respect the target's rate limits.
