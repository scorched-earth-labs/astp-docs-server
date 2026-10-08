"""The OPEN corpus spec: the public ASTP protocol documents.

This is the *only* corpus the open server ever sees. It is drawn from the
public ``astp`` repo: the normative SPEC, its CONFORMANCE companions (and the
one IMPLEMENTATION guide the protocol keeps, §16 trust infrastructure — the
storage-layout guides ship with the reference deployment's adapter), the
Episode of Record statements, plus GLOSSARY and CHANGELOG. Nothing proprietary. The enterprise corpus is a
separate spec in a separate (private) repo — never merged with this one.
"""
from __future__ import annotations

import os

from astp_docs.core.corpus import CorpusSpec, Visibility, docrefs_from_dir

# Dev fallback: a local checkout of the protocol repo.
DEFAULT_PROTOCOL_DIR = os.path.expanduser("~/projects/astp")

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
    "PROTOCOL-CONFORMANCE.md",  # the definition of a Conforming Implementation (6.0.2)
    "GLOSSARY.md",
    "CHANGELOG.md",
    "VERSIONING.md",
    "GOVERNANCE.md",
    "README.md",
    "docs/RATIFICATION-*.md",   # Episode of Record statements (5.0.0 onward), in a checkout
    "RATIFICATION-*.md",        # the same, as vendored: scripts/vendor_corpus.py flattens docs/ into the corpus root
]

# Machine-readable assets served verbatim (not chunked or indexed): the pinned
# expected digests every construction reproduces to. One file per protocol
# version, vendored under its repository-relative path so versions never
# collide: 5.0.0 seal-constructions, 6.0.0 context-commitment.
OPEN_ASSET_PATTERNS = [
    "vectors/*/seal-constructions.json",
    "vectors/*/context-commitment.json",
]

# The project's licensing documents, served verbatim by get_license_terms and
# never chunked or indexed. Legal text chunks badly, and a partial retrieval
# about a patent grant is worse than no answer — so none of these may ever
# appear in OPEN_DOC_PATTERNS. Exact names, not globs: NOTICE has no extension.
OPEN_VERBATIM_FILES = [
    "LICENSE.txt",   # Apache License 2.0
    "NOTICE",        # copyright, the protocol-name policy, the trademark position
    "PATENTS.md",    # the patent pledge to Conforming Implementations
]

LICENSE_TERMS_NOTICE = (
    "These are the full texts of the ASTP project's own licensing documents, "
    "exactly as published. This is not legal advice. Read the text itself "
    "rather than relying on a summary of it — including one you write."
)

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
    2. ``ASTP_PROTOCOL_DIR`` — dev override to serve a live checkout,
    3. the vendored corpus packaged into the server — the deploy default,
    4. ``~/projects/astp`` — dev fallback.
    """
    base = (
        protocol_dir
        or os.environ.get("ASTP_PROTOCOL_DIR")
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
            f"(python scripts/vendor_corpus.py) or set ASTP_PROTOCOL_DIR to a "
            f"checkout of the astp repository."
        )
    return CorpusSpec(name="astp-open", visibility=Visibility.OPEN, docs=docs)


def open_corpus_fingerprint(protocol_dir: str | None = None) -> str:
    """SHA-256 over the relative path and content of every file the open corpus
    serves — the documents the retriever indexes, the test-vector files and the
    verbatim licensing documents.

    Changes iff a freshly built retriever (or the vectors tool) would serve
    something different. A long-running process that built its retriever at
    startup (the Discord bot) compares this to decide when to rebuild — it had
    served SPEC 5.1.0 for days after 6.0.0 was vendored."""
    import hashlib

    from .vendor_manifest import file_digest

    base = resolve_corpus_dir(protocol_dir)
    paths = {d.path for d in docrefs_from_dir(base, OPEN_DOC_PATTERNS, exclude=OPEN_DOC_EXCLUDE)}
    paths.update(list_test_vector_files(base).values())
    paths.update(list_verbatim_files(base).values())
    h = hashlib.sha256()
    for path in sorted(paths):
        rel = os.path.relpath(path, base).replace(os.sep, "/")
        h.update(f"{rel}\0{file_digest(path)}\n".encode())
    return h.hexdigest()


def served_corpus_info(protocol_dir: str | None = None) -> dict:
    """What is being served: SPEC version, source commit, where from.

    From the vendor manifest for a vendored snapshot; for a live checkout
    (``ASTP_PROTOCOL_DIR``), from its SPEC.md and git HEAD. Reported on
    ``/healthz`` so a deployed server's freshness can be checked from outside."""
    import subprocess

    from .vendor_manifest import parse_spec_version, read_manifest

    base = resolve_corpus_dir(protocol_dir)
    manifest = read_manifest(base) or {}
    commit = manifest.get("source_commit")
    if not commit:
        try:
            commit = subprocess.check_output(["git", "-C", base, "rev-parse", "HEAD"], text=True,
                                             stderr=subprocess.DEVNULL).strip()
        except Exception:
            commit = None
    return {
        "spec_version": manifest.get("spec_version") or parse_spec_version(os.path.join(base, "SPEC.md")),
        "source_commit": commit,
        "vendored": bool(manifest),
    }


def list_test_vector_files(protocol_dir: str | None = None) -> dict[str, str]:
    """Repository-relative path -> absolute path of every vendored/available
    test-vector file, e.g. ``{"vectors/5.0.0/seal-constructions.json": ...,
    "vectors/6.0.0/context-commitment.json": ...}``."""
    import glob

    base = resolve_corpus_dir(protocol_dir)
    found: dict[str, str] = {}
    for pat in OPEN_ASSET_PATTERNS:
        for path in sorted(glob.glob(os.path.join(base, pat))):
            found[os.path.relpath(path, base).replace(os.sep, "/")] = path
    return found


def load_test_vectors(version: str | None = None, protocol_dir: str | None = None) -> dict:
    """The vector file for ``version`` (default: the newest available), parsed,
    with its path and SHA-256 so an adopter can cite exactly what they checked
    against. Raises ``FileNotFoundError`` with the versions on offer otherwise."""
    import hashlib
    import json

    files = list_test_vector_files(protocol_dir)
    versions = sorted({rel.split("/")[1] for rel in files}, key=lambda v: tuple(int(x) if x.isdigit() else 0 for x in v.split(".")))
    if not versions:
        raise FileNotFoundError("no test-vector files in the corpus; vendor them with scripts/vendor_corpus.py")
    chosen = version or versions[-1]
    matches = sorted(rel for rel in files if rel.split("/")[1] == chosen)
    if not matches:
        raise FileNotFoundError(f"no vectors for {chosen!r}; available: {versions}")
    rel = matches[0]
    raw = open(files[rel], "rb").read()
    return {"path": rel, "version": chosen, "sha256": hashlib.sha256(raw).hexdigest(),
            "available_versions": versions, "vectors": json.loads(raw)}


def list_verbatim_files(protocol_dir: str | None = None) -> dict[str, str]:
    """Name -> absolute path of each licensing document present, in
    ``OPEN_VERBATIM_FILES`` order."""
    base = resolve_corpus_dir(protocol_dir)
    found: dict[str, str] = {}
    for name in OPEN_VERBATIM_FILES:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            found[name] = path
    return found


def load_license_terms(protocol_dir: str | None = None) -> dict:
    """Every licensing document, whole and unaltered, with its SHA-256.

    All or nothing: if any one is missing this raises ``FileNotFoundError``
    rather than serve the rest. "Apache 2.0" without the patent pledge is true
    and materially incomplete — worse than no answer."""
    import hashlib

    files = list_verbatim_files(protocol_dir)
    missing = [name for name in OPEN_VERBATIM_FILES if name not in files]
    if missing:
        raise FileNotFoundError(
            f"licensing documents missing from the corpus: {missing}; "
            f"vendor them with scripts/vendor_corpus.py"
        )
    documents = []
    for name, path in files.items():
        raw = open(path, "rb").read()
        documents.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                          "text": raw.decode("utf-8")})
    return {"notice": LICENSE_TERMS_NOTICE, "documents": documents,
            "source_commit": served_corpus_info(protocol_dir)["source_commit"]}
