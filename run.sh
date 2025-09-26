#!/bin/bash

set -Eeo pipefail

die() {
    echo "$@"
    exit 1;
}

[ -n "$MERGE_QUEUE_PR_URL" ] || die "MERGE_QUEUE_PR_URL is not set"
[ -n "$REPOSITORY_URL" ] || die "REPOSITORY_URL is not set"

MERGE_QUEUE_METADATA="$(gh pr view --json body -q ".body" "$MERGE_QUEUE_PR_URL" | sed -n -e "/\`\`\`yaml/,/\`\`\`/p" | sed -e '1d;$d')"

# Extract checking_base_sha from the metadata
CHECKING_BASE_SHA="$(echo "$MERGE_QUEUE_METADATA" | yq -r '.checking_base_sha')"

if [ -n "$CHECKING_BASE_SHA" ] && [ "$CHECKING_BASE_SHA" != "null" ]; then
    echo "checking_base_sha=$CHECKING_BASE_SHA" >> "$GITHUB_OUTPUT"
    echo "Extracted checking_base_sha: $CHECKING_BASE_SHA"
else
    die "checking_base_sha not found in merge queue metadata"
fi
