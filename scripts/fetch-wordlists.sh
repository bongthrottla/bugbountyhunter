#!/usr/bin/env bash
# Fetch and sanitise the directory-fuzzing wordlists.
#
# Source: SecLists (MIT, https://github.com/danielmiessler/SecLists)
# Re-run this to update the bundled lists. The output is committed so users do
# not need network access to run a scan.
#
# Usage:
#   ./scripts/fetch-wordlists.sh          # write into wordlists/
#   ./scripts/fetch-wordlists.sh /tmp/x   # write somewhere else

set -euo pipefail

DEST="${1:-$(cd "$(dirname "$0")/.." && pwd)/wordlists}"
BASE="https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content"
mkdir -p "$DEST"

# name:source-file
LISTS="
common.txt:$BASE/common.txt
raft-small-directories.txt:$BASE/raft-small-directories.txt
"

echo "Fetching wordlists into $DEST"
while IFS=: read -r name url; do
    [ -z "$name" ] && continue
    raw=$(mktemp)
    out="$DEST/$name"

    echo -n "  $name ... "
    curl -fsSL --max-time 120 -o "$raw" "$url" || {
        echo "FAILED to download $url" >&2
        rm -f "$raw"
        continue
    }

    # Sanitise:
    #  - drop CR (CRLF -> LF)
    #  - drop control chars and zero-width spaces that break ffuf requests
    #  - drop entries with a leading slash (would produce //path)
    #  - drop whitespace-only lines
    #  - dedupe, preserving sort order
    LC_ALL=C sed -e 's/\r$//' "$raw" \
        | LC_ALL=C tr -d '\000-\010\013\014\016-\037\200-\377\342\200\213' \
        | grep -v '^[[:space:]]*$' \
        | grep -v '^/' \
        | LC_ALL=C sort -u \
        > "$out"

    before=$(wc -l < "$raw")
    after=$(wc -l < "$out")
    echo "$after entries (was $before)"
    rm -f "$raw"
done <<< "$LISTS"

echo
echo "Done. Remember to update wordlists/README.md if you change the list set."
