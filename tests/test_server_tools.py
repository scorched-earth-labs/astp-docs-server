"""Tests for the MCP tool logic (pure functions, no `mcp` dependency).

Run against the real open corpus; skipped if it isn't resolvable.
"""
import pytest

from astp_docs.core import Retriever
from astp_docs import toolkit as tools

try:
    from astp_docs_server.open_corpus import build_open_corpus_spec

    _spec = build_open_corpus_spec()
except FileNotFoundError:
    _spec = None

pytestmark = pytest.mark.skipif(
    _spec is None, reason="ariadne-protocol open docs not resolvable (set ARIADNE_PROTOCOL_DIR)"
)


@pytest.fixture(scope="module")
def r():
    return Retriever.from_spec(_spec)


def test_search_spec_returns_hits(r):
    out = tools.search_spec(r, "position-binding leaf hash preimage", k=5)
    assert out["search_method"] == "tfidf-local"   # default offline embedder
    assert out["count"] > 0
    assert all("citation" in hit for hit in out["results"])
    assert all(hit["score"] is not None for hit in out["results"])


def test_get_governance_rule_tool(r):
    out = tools.get_governance_rule(r, "G-2")
    assert out["count"] == 1
    assert "Reparenting" in out["results"][0]["text"]


def test_get_conformance_family_tool(r):
    out = tools.get_conformance_vectors(r, "WF")
    ids = {hit["anchor"]["id"] for hit in out["results"]}
    assert "WF-004" in ids and out["count"] >= 3


def test_get_section_prefers_spec(r):
    out = tools.get_section(r, "5.2")
    assert out["results"][0]["doc_id"] == "SPEC"


def test_get_hash_preimage_tool(r):
    out = tools.get_hash_preimage(r, "WorkflowDeclaration", k=5)
    assert out["count"] > 0
    # every returned passage actually discusses a hash
    assert all("hash" in hit["text"].lower() for hit in out["results"])


def test_corpus_info_tool(r):
    info = tools.corpus_info(r)
    # Assert the tool reports what the retriever holds, not a pinned count —
    # this is a test of corpus_info, not of how many rules the protocol has.
    assert len(info["governance_rules"]) == len(r.list_governance_rules())
    assert info["governance_rules"], "corpus_info reported no governance rules"
    # Derived, not restated: the corpus grows with the spec (4.3.0 added
    # CONFORMANCE-REPRODUCIBILITY.md and this line was hard-coded to 13).
    from astp_docs_server.open_corpus import build_open_corpus_spec
    assert info["docs"] == len(build_open_corpus_spec().docs) >= 13


def test_get_test_vectors_returns_the_vendored_file_with_its_digest():
    """The vector file is served verbatim, parsed, with the path and SHA-256 an
    adopter cites, and the newest version is the default."""
    from astp_docs_server.open_corpus import load_test_vectors, list_test_vector_files

    files = list_test_vector_files()
    if not files:
        pytest.skip("no vendored test vectors (run scripts/vendor_corpus.py)")
    out = load_test_vectors()
    assert out["path"].startswith("vectors/") and out["path"].endswith("seal-constructions.json")
    assert len(out["sha256"]) == 64 and out["version"] in out["available_versions"]
    v = out["vectors"]
    assert "episode_root_v2" in v and "witness_and_anchor_v2" in v and "audit_records_v2" in v
    with pytest.raises(FileNotFoundError, match="available"):
        load_test_vectors("0.0.1")
