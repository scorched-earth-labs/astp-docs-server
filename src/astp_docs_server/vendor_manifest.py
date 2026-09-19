"""Provenance for the vendored open-docs snapshot.

The server ships a physical copy of the protocol docs (``corpus/open/``) so a
deployment is self-contained. That copy is produced by
``scripts/vendor_corpus.py`` and kept current by remembering to re-run it.

Remembering is not a mechanism. A stale snapshot is byte-for-byte a valid
corpus — the server answers confidently from superseded normative text, and
nothing anywhere reports a problem. For a server whose entire purpose is
telling external implementers what the protocol says, that is the worst
available failure mode: wrong, confident, and silent.

The manifest closes that hole by recording what was vendored and from where,
so the snapshot can be checked rather than trusted. See
``tests/test_vendor_freshness.py``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

MANIFEST_NAME = "vendor_manifest.json"

_SPEC_VERSION_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)", re.M)


def file_digest(path: str) -> str:
    """SHA-256 of a file's bytes. Newline-sensitive on purpose — a corpus that
    differs only by line endings is still not the corpus that was reviewed."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_spec_version(spec_path: str) -> str | None:
    """The ``**Version:**`` field from a SPEC.md. None if absent/unreadable."""
    try:
        with open(spec_path, encoding="utf-8") as handle:
            match = _SPEC_VERSION_RE.search(handle.read(4096))
    except OSError:
        return None
    return match.group(1) if match else None


def manifest_path(corpus_dir: str) -> str:
    return os.path.join(corpus_dir, MANIFEST_NAME)


def write_manifest(corpus_dir: str, manifest: dict[str, Any]) -> str:
    """Write the manifest deterministically.

    Sorted keys and no timestamp: re-vendoring unchanged docs must produce an
    empty diff, or the manifest becomes noise reviewers learn to skip.
    """
    path = manifest_path(corpus_dir)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def read_manifest(corpus_dir: str) -> dict[str, Any] | None:
    """The recorded manifest, or None when the snapshot predates one."""
    try:
        with open(manifest_path(corpus_dir), encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def corpus_files(corpus_dir: str) -> dict[str, str]:
    """Digest of every vendored file, keyed by corpus-relative path (documents
    at the top level; assets such as ``vectors/5.0.0/seal-constructions.json``
    under theirs). The manifest itself is excluded — it cannot contain its own
    digest."""
    out: dict[str, str] = {}
    for root, _dirs, names in os.walk(corpus_dir):
        for name in names:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, corpus_dir).replace(os.sep, "/")
            if rel == MANIFEST_NAME:
                continue
            out[rel] = file_digest(path)
    return dict(sorted(out.items()))


def verify(corpus_dir: str) -> list[str]:
    """Check the snapshot against its manifest. Returns human-readable problems.

    An empty list means the vendored files are exactly what was recorded. It
    does NOT mean they match the upstream protocol repo — that requires the
    source checkout, and is a separate test.
    """
    manifest = read_manifest(corpus_dir)
    if manifest is None:
        return [f"no {MANIFEST_NAME} in {corpus_dir} — re-run scripts/vendor_corpus.py"]

    recorded: dict[str, str] = manifest.get("files") or {}
    actual = corpus_files(corpus_dir)
    problems: list[str] = []

    for name in sorted(set(recorded) - set(actual)):
        problems.append(f"{name}: in manifest but missing from the snapshot")
    for name in sorted(set(actual) - set(recorded)):
        problems.append(f"{name}: present in the snapshot but not in the manifest")
    for name in sorted(set(recorded) & set(actual)):
        if recorded[name] != actual[name]:
            problems.append(f"{name}: content differs from the manifest digest")

    spec = os.path.join(corpus_dir, "SPEC.md")
    if os.path.isfile(spec):
        declared, recorded_version = parse_spec_version(spec), manifest.get("spec_version")
        if declared != recorded_version:
            problems.append(
                f"SPEC.md declares version {declared!r} but the manifest records "
                f"{recorded_version!r}"
            )

    return problems
