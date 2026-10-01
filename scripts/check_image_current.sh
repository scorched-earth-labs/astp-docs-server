#!/usr/bin/env bash
# Refuse to deploy an image whose corpus was checked against anything but the
# current head of astp main.
#
# The Dockerfile's freshness stage checks the vendored corpus against the
# protocol checkout passed as the `protocol` build context, and records that
# checkout's commit in /app/CORPUS-FRESHNESS. It trusts whatever checkout it is
# given, so an image built against a stale checkout passes the build. This
# script closes that gap at deploy time: the recorded commit must BE astp main's
# current head. Exact equality, not "not behind": an image checked against an
# older commit is refused even if the later commits did not touch the corpus.
# That refusal is harmless (rebuild, about a minute), and it needs no checkout.
#
#   scripts/check_image_current.sh astp-docs-server:latest
#
# Exit 0: current. Exit 1: refuse (stale, unmarked, or main unreachable).
# ASTP_MAIN_COMMIT overrides the ls-remote lookup (tests only).
set -euo pipefail

image="${1:?usage: $0 IMAGE}"
repo="${ASTP_REPO_URL:-https://github.com/scorched-earth-labs/astp.git}"

marker="$(docker run --rm --entrypoint cat "$image" /app/CORPUS-FRESHNESS 2>/dev/null)" || {
    echo "REFUSE: $image has no /app/CORPUS-FRESHNESS; it was not built through the freshness gate" >&2
    exit 1
}
recorded="$(grep -oE '[0-9a-f]{40}' <<<"$marker" | head -1)"
[[ -n "$recorded" ]] || { echo "REFUSE: no commit in $image's marker: $marker" >&2; exit 1; }

main="${ASTP_MAIN_COMMIT:-$(git ls-remote "$repo" refs/heads/main 2>/dev/null | cut -f1 || true)}"
[[ -n "$main" ]] || { echo "REFUSE: could not read astp main from $repo" >&2; exit 1; }

if [[ "$recorded" != "$main" ]]; then
    echo "REFUSE: $image's corpus was checked against astp ${recorded:0:7}; astp main is ${main:0:7}." >&2
    echo "        Pull the protocol checkout, re-vendor if it changed, and rebuild." >&2
    exit 1
fi
echo "OK: $image — $marker (astp main ${main:0:7})"
