"""The OPEN corpus spec: the public Project Ariadne protocol documents.

This is the *only* corpus the open server ever sees. It is drawn from the
public ``ariadne-protocol`` repo: the normative SPEC, its IMPLEMENTATION /
CONFORMANCE companions, the amendments still referenced for Layer-3 semantics,
plus GLOSSARY and CHANGELOG. Nothing proprietary. The enterprise corpus is a
separate spec in a separate (private) repo — never merged with this one.
"""
from __future__ import annotations

import os

from astp_docs.core.corpus import CorpusSpec, Visibility, docrefs_from_dir

# Dev fallback: a local checkout of the protocol repo.
DEFAULT_PROTOCOL_DIR = os.path.expanduser("~/projects/ariadne-protocol")

# Normative + reference documents that make up the open corpus. Glob patterns
# keep new companion docs picked up automatically; historical/marketing docs
# are excluded so adopters' agents only see the *current* normative surface.
#
# AMENDMENT-*.md are deliberately excluded: the v3.2.1 integration pass folded
# them into the SPEC body (§20 cross-episode, §21 Layer 3) and retired them to
# historical-reference banners. They retain their *authoring* governance
# numbering (e.g. CIA = G-19, since renumbered to G-36), which would pollute
# exact lookup with superseded anchors. The SPEC body is authoritative.
OPEN_DOC_PATTERNS = [
    "SPEC.md",
    "IMPLEMENTATION-*.md",
    "CONFORMANCE*.md",
    "GLOSSARY.md",
    "CHANGELOG.md",
    "VERSIONING.md",
    "README.md",
]

OPEN_DOC_EXCLUDE = [
    "SPEC-v1.md",   # superseded by SPEC.md
    "VISION.md",    # narrative, not normative
]


def _vendored_corpus_dir() -> str | None:
    """The open-docs snapshot packaged with the server (populated by
    ``scripts/vendor_corpus.py``). Present in built wheels and Docker images, so
    a deployed server is self-contained — no sibling protocol checkout needed."""
    try:
        from importlib.resources import files

        path = files("astp_docs_server") / "corpus" / "open"
        if path.is_dir() and any(path.iterdir()):
            return str(path)
    except Exception:
        pass
    return None


def resolve_corpus_dir(protocol_dir: str | None = None) -> str:
    """Where the open docs come from, in precedence order:

    1. an explicit ``protocol_dir`` argument,
    2. ``ARIADNE_PROTOCOL_DIR`` — dev override to serve a live checkout,
    3. the vendored corpus packaged into the server — the deploy default,
    4. ``~/projects/ariadne-protocol`` — dev fallback.
    """
    base = (
        protocol_dir
        or os.environ.get("ARIADNE_PROTOCOL_DIR")
        or _vendored_corpus_dir()
        or DEFAULT_PROTOCOL_DIR
    )
    return os.path.abspath(os.path.expanduser(base))


def build_open_corpus_spec(protocol_dir: str | None = None) -> CorpusSpec:
    base = resolve_corpus_dir(protocol_dir)
    docs = docrefs_from_dir(base, OPEN_DOC_PATTERNS, exclude=OPEN_DOC_EXCLUDE)
    if not docs:
        raise FileNotFoundError(
            f"No open protocol docs found under {base!r}. Vendor them "
            f"(python scripts/vendor_corpus.py) or set ARIADNE_PROTOCOL_DIR to a "
            f"checkout of the ariadne-protocol repo."
        )
    return CorpusSpec(name="ariadne-open", visibility=Visibility.OPEN, docs=docs)
