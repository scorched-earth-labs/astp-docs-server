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
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))

from astp_docs_server.open_corpus import (  # noqa: E402
    DEFAULT_PROTOCOL_DIR,
    OPEN_DOC_EXCLUDE,
    OPEN_DOC_PATTERNS,
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

    os.makedirs(DEST, exist_ok=True)
    for old in glob.glob(os.path.join(DEST, "*")):  # clean prior snapshot
        os.remove(old)

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

    if not copied:
        print(f"ERROR: no docs matched under {src!r}", file=sys.stderr)
        return 1

    print(f"Vendored {len(copied)} open docs\n  from: {src}\n  into: {os.path.relpath(DEST, os.path.join(_HERE, '..'))}")
    for name in copied:
        print("   -", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
