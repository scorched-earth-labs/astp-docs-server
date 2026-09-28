#!/usr/bin/env python3
"""Copy the open protocol docs into the packaged corpus, so the built server is
self-contained — no sibling `ariadne-protocol` checkout needed at deploy time.

Run this before building the wheel or Docker image (and whenever the protocol
docs change). Uses the same include/exclude patterns as the corpus loader, so
the vendored snapshot matches what the server serves.

    python scripts/vendor_corpus.py                      # from ARIADNE_PROTOCOL_DIR or ~/projects/ariadne-protocol
    python scripts/vendor_corpus.py /path/to/ariadne-protocol
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

from astp_docs_server.open_corpus import (  # noqa: E402
    DEFAULT_PROTOCOL_DIR,
    OPEN_DOC_EXCLUDE,
    OPEN_ASSET_PATTERNS,
    OPEN_DOC_PATTERNS,
    OPEN_VERBATIM_FILES,
)

from astp_docs_server.vendor_manifest import (  # noqa: E402
    MANIFEST_NAME,
    file_digest,
    parse_spec_version,
    write_manifest,
)

DEST = os.path.join(_HERE, "..", "src", "astp_docs_server", "corpus", "open")


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else (
        os.environ.get("ARIADNE_PROTOCOL_DIR") or DEFAULT_PROTOCOL_DIR
    )
    src = os.path.abspath(os.path.expanduser(src))
    if not os.path.isdir(src):
        print(f"ERROR: source protocol dir not found: {src}", file=sys.stderr)
        return 1

    excluded = set()
    for pat in OPEN_DOC_EXCLUDE:
        excluded.update(glob.glob(os.path.join(src, pat)))

    if os.path.isdir(DEST):  # clean prior snapshot, assets included
        shutil.rmtree(DEST)
    os.makedirs(DEST, exist_ok=True)

    copied: list[str] = []
    seen: set[str] = set()
    for pat in OPEN_DOC_PATTERNS:
        for path in sorted(glob.glob(os.path.join(src, pat))):
            name = os.path.basename(path)
            if path in excluded or not os.path.isfile(path) or name in seen:
                continue
            seen.add(name)
            shutil.copy2(path, os.path.join(DEST, name))
            copied.append(name)
    for pat in OPEN_ASSET_PATTERNS:
        for path in sorted(glob.glob(os.path.join(src, pat))):
            rel = os.path.relpath(path, src).replace(os.sep, "/")
            os.makedirs(os.path.dirname(os.path.join(DEST, rel)), exist_ok=True)
            shutil.copy2(path, os.path.join(DEST, rel))
            copied.append(rel)
    # Licensing documents: copied whole, never indexed. All or none — a
    # snapshot with the Apache license but not the patent pledge would serve
    # an incomplete answer to "may we use this".
    missing = [n for n in OPEN_VERBATIM_FILES if not os.path.isfile(os.path.join(src, n))]
    if missing:
        print(f"ERROR: licensing documents missing from {src!r}: {missing}", file=sys.stderr)
        return 1
    for name in OPEN_VERBATIM_FILES:
        shutil.copy2(os.path.join(src, name), os.path.join(DEST, name))
        copied.append(name)

    if not copied:
        print(f"ERROR: no docs matched under {src!r}", file=sys.stderr)
        return 1

    # Record provenance alongside the snapshot. Without it a stale vendored
    # corpus is indistinguishable from a current one, and the server would
    # serve superseded normative text with nothing to notice — see
    # tests/test_vendor_freshness.py.
    spec_path = os.path.join(DEST, "SPEC.md")
    manifest = {
        "spec_version": parse_spec_version(spec_path) if os.path.isfile(spec_path) else None,
        "source_commit": _source_commit(src),
        "files": {name: file_digest(os.path.join(DEST, name)) for name in sorted(copied)},
    }
    write_manifest(DEST, manifest)

    print(f"Vendored {len(copied)} open docs\n  from: {src}\n  into: {os.path.relpath(DEST, os.path.join(_HERE, '..'))}")
    for name in copied:
        print("   -", name)
    print(f"  SPEC version: {manifest['spec_version']}")
    print(f"  source commit: {manifest['source_commit'] or '(not a git checkout)'}")
    print(f"  manifest: {MANIFEST_NAME}")
    return 0


def _source_commit(src: str) -> str | None:
    """Best-effort commit id of the source checkout. None if unavailable —
    provenance is a convenience here; the per-file digests are the real check."""
    try:
        out = subprocess.run(
            ["git", "-C", src, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None if out.returncode == 0 else None
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
