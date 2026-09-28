"""The vendored corpus must be verifiable, and must not silently go stale.

`corpus/open/` is a physical copy of the protocol docs, refreshed by running
`scripts/vendor_corpus.py` and kept current by remembering to run it. A stale
copy is a fully valid corpus: the server answers confidently out of superseded
normative text and nothing reports a problem.

Two checks, deliberately separate because they need different things:

* Integrity — the snapshot matches its own manifest. Needs nothing but this
  repo, so it always runs. Catches partial vendoring, corruption, and hand
  edits to files that are supposed to be a faithful copy.

* Freshness — the snapshot matches the upstream protocol repo. Needs a source
  checkout, so it skips when one is absent. Set
  ASTP_REQUIRE_CORPUS_FRESHNESS=1 to make that skip an error, which is what a
  release or publish pipeline should do.
"""
from __future__ import annotations

import glob
import os

import pytest

from astp_docs_server.open_corpus import (
    DEFAULT_PROTOCOL_DIR,
    OPEN_ASSET_PATTERNS,
    OPEN_DOC_EXCLUDE,
    OPEN_DOC_PATTERNS,
    OPEN_VERBATIM_FILES,
)
from astp_docs_server.vendor_manifest import (
    MANIFEST_NAME,
    corpus_files,
    file_digest,
    parse_spec_version,
    read_manifest,
    verify,
)

CORPUS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "src", "astp_docs_server", "corpus", "open",
)
REVENDOR = "re-run `python scripts/vendor_corpus.py` and commit the result"


def _source_dir() -> str | None:
    src = os.environ.get("ARIADNE_PROTOCOL_DIR") or DEFAULT_PROTOCOL_DIR
    src = os.path.abspath(os.path.expanduser(src))
    return src if os.path.isdir(src) else None


def _source_files(src: str) -> dict[str, str]:
    """The files the vendor script would copy, by name -> digest."""
    excluded = set()
    for pat in OPEN_DOC_EXCLUDE:
        excluded.update(glob.glob(os.path.join(src, pat)))

    found: dict[str, str] = {}
    for pat in OPEN_DOC_PATTERNS:
        for path in sorted(glob.glob(os.path.join(src, pat))):
            name = os.path.basename(path)
            if path in excluded or not os.path.isfile(path) or name in found:
                continue
            found[name] = file_digest(path)
    for pat in OPEN_ASSET_PATTERNS:
        for path in sorted(glob.glob(os.path.join(src, pat))):
            found[os.path.relpath(path, src).replace(os.sep, "/")] = file_digest(path)
    for name in OPEN_VERBATIM_FILES:
        path = os.path.join(src, name)
        if os.path.isfile(path):
            found[name] = file_digest(path)
    return found


def _require_source() -> str:
    src = _source_dir()
    if src:
        return src
    reason = (
        "no protocol checkout found (set ARIADNE_PROTOCOL_DIR); freshness "
        "cannot be checked from this repo alone"
    )
    if os.environ.get("ASTP_REQUIRE_CORPUS_FRESHNESS") == "1":
        pytest.fail(reason + " — but ASTP_REQUIRE_CORPUS_FRESHNESS=1 was set")
    pytest.skip(reason)


class TestSnapshotIntegrity:
    """Always runs — needs only this repo."""

    def test_manifest_exists(self):
        assert read_manifest(CORPUS_DIR) is not None, (
            f"{MANIFEST_NAME} missing from the vendored corpus — {REVENDOR}"
        )

    def test_snapshot_matches_manifest(self):
        problems = verify(CORPUS_DIR)
        assert problems == [], (
            "vendored corpus does not match its manifest:\n  "
            + "\n  ".join(problems)
            + f"\n\n{REVENDOR}"
        )

    def test_manifest_records_a_spec_version(self):
        manifest = read_manifest(CORPUS_DIR) or {}
        assert manifest.get("spec_version"), (
            f"manifest records no SPEC version — {REVENDOR}"
        )

    def test_corpus_is_not_empty(self):
        assert corpus_files(CORPUS_DIR), "vendored corpus is empty"


class TestFreshnessAgainstSource:
    """Skips without a protocol checkout; strict when the pipeline demands it."""

    def test_no_document_is_stale(self):
        src = _require_source()
        vendored, source = corpus_files(CORPUS_DIR), _source_files(src)

        stale = sorted(
            name for name in set(vendored) & set(source)
            if vendored[name] != source[name]
        )
        assert stale == [], (
            "vendored documents differ from the protocol repo — the server "
            f"would serve superseded text for: {', '.join(stale)}\n\n{REVENDOR}"
        )

    def test_no_document_was_added_or_removed_upstream(self):
        src = _require_source()
        vendored, source = corpus_files(CORPUS_DIR), _source_files(src)

        missing = sorted(set(source) - set(vendored))
        extra = sorted(set(vendored) - set(source))
        assert not missing, f"upstream documents absent from the snapshot: {missing}\n\n{REVENDOR}"
        assert not extra, f"snapshot contains documents no longer upstream: {extra}\n\n{REVENDOR}"

    def test_spec_version_matches_source(self):
        src = _require_source()
        vendored = parse_spec_version(os.path.join(CORPUS_DIR, "SPEC.md"))
        upstream = parse_spec_version(os.path.join(src, "SPEC.md"))
        assert vendored == upstream, (
            f"serving SPEC {vendored}, upstream is {upstream} — {REVENDOR}"
        )

    def test_licensing_documents_are_checked_for_freshness(self):
        """LICENSE.txt, NOTICE and PATENTS.md are not indexed, but a stale copy
        of the patent pledge is as wrong as a stale SPEC."""
        src = _require_source()
        assert set(OPEN_VERBATIM_FILES) <= set(_source_files(src))
