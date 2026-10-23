#!/usr/bin/env bash
# Delete the stale Jules / agent branches on bongthrottla/bugbountyhunter.
#
# Defaults to a DRY RUN — it prints what it would delete and changes nothing.
# Pass --apply to actually delete.
#
# Requires: gh authenticated as the repo owner (bongthrottla).
#
# Usage:
#   ./scripts/cleanup-branches.sh            # dry run
#   ./scripts/cleanup-branches.sh --apply    # delete

set -euo pipefail

REPO="bongthrottla/bugbountyhunter"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

if ! gh auth status > /dev/null 2>&1; then
    echo "gh is not authenticated. Run: gh auth login" >&2
    exit 1
fi

OWNER=$(gh api user --jq .login)
echo "Authenticated as: $OWNER"
echo "Target repo:      $REPO"
echo

if [ "$OWNER" != "bongthrottla" ]; then
    echo "WARNING: you are not authenticated as the repo owner." >&2
    echo "Deleting branches will fail with 403 unless $OWNER has write access." >&2
    echo
fi

# Branches to keep. main is the default branch and is never touched.
KEEP_RE='^(main|HEAD)$'

# Every other branch in this repo is a stale agent branch. Listed explicitly so
# the script is reviewable rather than a blind wildcard.
BRANCHES=$(gh api "repos/$REPO/branches" --paginate --jq '.[].name' \
    | grep -Ev "$KEEP_RE" || true)

COUNT=$(printf '%s\n' "$BRANCHES" | grep -c . || true)
echo "Found $COUNT branch(es) to delete."
echo

if [ "$APPLY" -eq 0 ]; then
    printf '%s\n' "$BRANCHES" | sed 's/^/  would delete: /'
    echo
    echo "DRY RUN — nothing was deleted. Re-run with --apply to delete."
    exit 0
fi

DELETED=0
FAILED=0
while IFS= read -r branch; do
    [ -z "$branch" ] && continue
    if gh api -X DELETE "repos/$REPO/git/refs/heads/$branch" > /dev/null 2>&1; then
        echo "  deleted: $branch"
        DELETED=$((DELETED + 1))
    else
        echo "  FAILED:  $branch" >&2
        FAILED=$((FAILED + 1))
    fi
done <<< "$BRANCHES"

echo
echo "Deleted $DELETED branch(es), $FAILED failure(s)."
[ "$FAILED" -eq 0 ] || exit 1
