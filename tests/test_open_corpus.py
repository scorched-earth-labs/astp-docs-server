"""Integration test against the real astp open corpus.

Skipped automatically when the sibling repo isn't resolvable, so unit tests
still run anywhere. This is the guard that the engine keeps matching the live
spec — the same invariants the build script prints.
"""
import pytest

from astp_docs.core import Retriever

try:
    from astp_docs_server.open_corpus import build_open_corpus_spec

    _spec = build_open_corpus_spec()
except FileNotFoundError:
    _spec = None

pytestmark = pytest.mark.skipif(
    _spec is None, reason="astp open docs not resolvable (set ASTP_PROTOCOL_DIR)"
)


@pytest.fixture(scope="module")
def retriever():
    return Retriever.from_spec(_spec)


def test_governance_contiguous(retriever):
    """Governance rules run G-1..G-N with no gaps and no duplicates.

    Contiguity is the invariant — a gap means a rule failed to parse out of the
    corpus, a duplicate means two rules collided (see the G-19/G-36 case in the
    next test). N is derived rather than pinned: the count grows whenever the
    protocol adds a rule, and hardcoding it only guarantees this repo breaks on
    every upstream governance addition without catching anything the contiguity
    check does not already catch.
    """
    nums = sorted(int(g["id"].split("-")[1]) for g in retriever.list_governance_rules())
    assert nums, "no governance rules parsed out of the corpus"
    assert nums == list(range(1, max(nums) + 1)), (
        f"governance not contiguous G-1..G-{max(nums)}: {nums}"
    )


def test_no_stale_amendment_governance_collision(retriever):
    # G-19 must be the SPEC fork rule, not the retired amendment's CIA (now G-36).
    g19 = retriever.get_governance_rule("G-19")
    assert len(g19) == 1
    assert g19[0].chunk.doc_id == "SPEC"
    assert "fork_objective" in g19[0].chunk.text
    assert all("AMENDMENT" not in r.chunk.doc_id for r in retriever.get_governance_rule("G-36"))


def test_known_conformance_vector_resolves(retriever):
    wf4 = retriever.get_conformance_vectors("WF-004")
    assert wf4 and "transition legality" in wf4[0].chunk.text.lower()


def test_spec_section_ranked_first(retriever):
    res = retriever.get_section("5.2")
    assert res[0].chunk.doc_id == "SPEC"
