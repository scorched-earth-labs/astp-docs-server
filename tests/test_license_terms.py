"""The licensing documents are served whole, tracked like the rest of the
corpus, and never reach a generator.

LICENSE.txt, NOTICE and PATENTS.md are a third category beside the indexed
documents and the test vectors: vendored, fingerprinted and manifest-checked,
but never chunked. An implementer's agent asking "may we use this" must get the
text — including the patent pledge that "Apache 2.0" alone misses — and the
chat head must not be able to paraphrase it.
"""
from __future__ import annotations

import fnmatch
import re
import shutil

import pytest
from fastapi.testclient import TestClient

from astp_docs.core import DocIndex, Document, Retriever, chunk_corpus
from astp_docs_server.open_corpus import (
    OPEN_DOC_PATTERNS,
    OPEN_VERBATIM_FILES,
    build_open_corpus_spec,
    list_verbatim_files,
    load_license_terms,
    open_corpus_fingerprint,
    resolve_corpus_dir,
)
from astp_docs_server.vendor_manifest import file_digest, read_manifest, verify
from astp_docs_server.web.answerer import (
    LICENSING_REDIRECT,
    Answerer,
    ExtractiveAnswerer,
    is_licensing_question,
    withhold_licensing_text,
)
from astp_docs_server.web.app import create_app


@pytest.fixture
def corpus_copy(tmp_path):
    dst = tmp_path / "corpus"
    shutil.copytree(resolve_corpus_dir(), dst)
    return dst


# --- served verbatim, never indexed ------------------------------------------

def test_no_licensing_file_matches_a_document_pattern():
    for name in OPEN_VERBATIM_FILES:
        assert not any(fnmatch.fnmatch(name, pat) for pat in OPEN_DOC_PATTERNS), name


def test_no_licensing_file_is_indexed():
    indexed = {d.path.replace("\\", "/").rsplit("/", 1)[-1] for d in build_open_corpus_spec().docs}
    assert indexed.isdisjoint(OPEN_VERBATIM_FILES)


def test_license_terms_are_whole_and_unaltered():
    out = load_license_terms()
    assert [d["path"] for d in out["documents"]] == OPEN_VERBATIM_FILES
    files = list_verbatim_files()
    for d in out["documents"]:
        assert d["text"] == open(files[d["path"]], encoding="utf-8").read()
        assert d["sha256"] == file_digest(files[d["path"]])
    assert "not legal advice" in out["notice"]


def test_the_patent_pledge_and_name_policy_are_served():
    """The two things "Apache 2.0" alone leaves out."""
    texts = {d["path"]: d["text"] for d in load_license_terms()["documents"]}
    assert "Conforming Implementation" in texts["PATENTS.md"]
    assert "PROTOCOL NAME" in texts["NOTICE"] and "TRADEMARK NOTICE" in texts["NOTICE"]


def test_a_missing_licensing_file_serves_none_of_them(corpus_copy):
    (corpus_copy / "NOTICE").unlink()
    with pytest.raises(FileNotFoundError, match="NOTICE"):
        load_license_terms(str(corpus_copy))


# --- manifest and fingerprint ------------------------------------------------

def test_manifest_records_each_licensing_file():
    recorded = (read_manifest(resolve_corpus_dir()) or {}).get("files", {})
    for name, path in list_verbatim_files().items():
        assert recorded.get(name) == file_digest(path), name
    assert set(list_verbatim_files()) == set(OPEN_VERBATIM_FILES)


@pytest.mark.parametrize("name", OPEN_VERBATIM_FILES)
def test_editing_a_licensing_file_moves_the_fingerprint(corpus_copy, name):
    """The Discord bot rebuilds when the fingerprint moves. NOTICE has no
    extension, so it is the case a suffix-based walk would miss."""
    before = open_corpus_fingerprint(str(corpus_copy))
    with open(corpus_copy / name, "a", encoding="utf-8") as fh:
        fh.write("\nAmended.\n")
    assert open_corpus_fingerprint(str(corpus_copy)) != before


@pytest.mark.parametrize("name", OPEN_VERBATIM_FILES)
def test_editing_a_licensing_file_fails_manifest_verification(corpus_copy, name):
    with open(corpus_copy / name, "a", encoding="utf-8") as fh:
        fh.write("\nAmended.\n")
    assert f"{name}: content differs from the manifest digest" in verify(str(corpus_copy))


# --- the chat head never generates about licensing ---------------------------

class _Recording(Answerer):
    name = "recording"

    def __init__(self):
        self.seen: list | None = None

    def _answer(self, query, results):
        self.seen = results
        return {"answer": "generated", "citations": [], "generator": self.name, "grounded": True}


def _results(text: str):
    doc = Document(doc_id="PROTOCOL-CONFORMANCE", path="PROTOCOL-CONFORMANCE.md",
                   text=f"## 1 Scope\n\n{text}", title="PROTOCOL-CONFORMANCE")
    r = Retriever(DocIndex(chunk_corpus([doc])))
    return r.search("scope", k=1)


@pytest.mark.parametrize("query", [
    "May we use ASTP in a commercial product?",
    "What license is this under?",
    "Is there a patent grant for implementers?",
    "Can we fork the reference implementation?",
    "What does the NOTICE file say about the name?",
])
def test_a_licensing_question_never_reaches_the_generator(query):
    a = _Recording()
    out = a.answer(query, _results("Anything at all."))
    assert out["answer"] == LICENSING_REDIRECT and out["grounded"] is False
    assert a.seen is None


@pytest.mark.parametrize("query", [
    "Can we use SHA-256 instead of SHA3-256?",
    "What is a Conforming Implementation?",
    "how does a reader notice a stale seal",
    "what makes an illegal state transition",
])
def test_protocol_questions_are_not_redirected(query):
    assert not is_licensing_question(query)


def test_licensing_paragraphs_are_withheld_from_the_generator():
    results = _results(
        "A conforming implementation meets every REQUIRED provision.\n\n"
        "PATENTS.md §4.2 grants a royalty-free patent license to a Conforming Implementation."
    )
    original = results[0].chunk.text
    a = _Recording()
    a.answer("What is a Conforming Implementation?", results)
    passed = a.seen[0].chunk.text
    assert "every REQUIRED provision" in passed
    assert "royalty" not in passed and "get_license_terms" in passed
    assert results[0].chunk.text == original  # the retriever's chunk is untouched


def test_no_served_passage_carries_patent_terms_to_a_generator():
    """Over the real corpus: after withholding, nothing a generator is given
    mentions a patent, royalty or trademark."""
    r = Retriever.from_spec(build_open_corpus_spec())
    from astp_docs.core.models import Result
    from astp_docs_server.web.answerer import _REDACTED

    cleared = withhold_licensing_text([Result(chunk=c) for c in r.index.chunks])
    leaks = [str(x.chunk.citation()) for x in cleared
             if re.search(r"patent|royalt|trademark", x.chunk.text.replace(_REDACTED, ""), re.I)]
    assert leaks == []


def test_web_chat_redirects_and_license_terms_route_serves_verbatim():
    doc = Document(doc_id="SPEC", path="SPEC.md", text="## 5.2 Leaf hash\n\nBinds position.", title="SPEC")
    retriever = Retriever(DocIndex(chunk_corpus([doc])))
    c = TestClient(create_app(retriever=retriever, answerer=ExtractiveAnswerer(), enable_chat=True))
    assert c.post("/chat", json={"query": "is ASTP open source?"}).json()["answer"] == LICENSING_REDIRECT
    served = c.get("/license-terms").json()
    assert [d["path"] for d in served["documents"]] == OPEN_VERBATIM_FILES

    off = TestClient(create_app(retriever=retriever, answerer=ExtractiveAnswerer(), enable_chat=False))
    assert off.get("/license-terms").status_code == 200  # no generator involved; always served


def test_mcp_tool_returns_the_full_files():
    pytest.importorskip("mcp")
    from astp_docs_server import mcp_server

    out = mcp_server.get_license_terms()
    assert [d["path"] for d in out["documents"]] == OPEN_VERBATIM_FILES
    doc = mcp_server.get_license_terms.__doc__
    assert "not legal advice" in doc and "verbatim" in doc and "never an excerpt" in doc
