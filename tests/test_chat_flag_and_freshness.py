"""/chat is opt-in, and a deployment reports what it serves.

On a public host /chat can spend a model provider's credits for anyone (it
uses Claude whenever the SDK and a key are present), so it is off unless
ASTP_WEB_ENABLE_CHAT=true. /healthz reports the SPEC version and source
commit being served, and open_corpus_fingerprint lets a long-running process
(the Discord bot) notice the corpus changed — it served SPEC 5.1.0 for days
after 6.0.0 was vendored.
"""

import shutil

import pytest
from fastapi.testclient import TestClient

from astp_docs.core import Document, DocIndex, Retriever, chunk_corpus
from astp_docs_server.open_corpus import open_corpus_fingerprint, resolve_corpus_dir, served_corpus_info
from astp_docs_server.web.app import create_app


class _NeverBuilt:
    name = "must-not-be-used"

    def answer(self, *a, **k):
        raise AssertionError("the answerer was used while chat is off")


def _retriever():
    doc = Document(doc_id="SPEC", path="SPEC.md", text="## 5.2 Leaf hash\n\nThe leaf hash binds position.", title="SPEC")
    return Retriever(DocIndex(chunk_corpus([doc])))


def test_chat_is_off_by_default(monkeypatch):
    monkeypatch.delenv("ASTP_WEB_ENABLE_CHAT", raising=False)
    c = TestClient(create_app(retriever=_retriever(), answerer=_NeverBuilt()))
    assert c.post("/chat", json={"query": "leaf hash"}).status_code in (404, 405)
    h = c.get("/healthz").json()
    assert h["chat"] is False and h["generator"] is None
    assert c.get("/search", params={"q": "leaf hash"}).status_code == 200
    assert "const CHAT=false" in c.get("/").text


def test_env_opts_in(monkeypatch):
    monkeypatch.setenv("ASTP_WEB_ENABLE_CHAT", "true")
    from astp_docs_server.web.answerer import ExtractiveAnswerer
    c = TestClient(create_app(retriever=_retriever(), answerer=ExtractiveAnswerer()))
    assert c.post("/chat", json={"query": "leaf hash", "k": 1}).status_code == 200
    assert c.get("/healthz").json()["chat"] is True


def test_healthz_reports_what_is_served(monkeypatch):
    monkeypatch.delenv("ASTP_WEB_ENABLE_CHAT", raising=False)
    h = TestClient(create_app(retriever=_retriever(), answerer=_NeverBuilt())).get("/healthz").json()
    info = served_corpus_info()
    assert h["spec_version"] == info["spec_version"] and h["source_commit"] == info["source_commit"]
    assert info["spec_version"]  # vendored snapshot or live checkout — either way, a version


@pytest.fixture
def corpus_copy(tmp_path):
    src = resolve_corpus_dir()
    dst = tmp_path / "corpus"
    shutil.copytree(src, dst)
    return dst


def test_fingerprint_follows_served_content(corpus_copy):
    fp = open_corpus_fingerprint(str(corpus_copy))
    (corpus_copy / "VISION.md").write_text("excluded narrative — not served")
    assert open_corpus_fingerprint(str(corpus_copy)) == fp
    spec = corpus_copy / "SPEC.md"
    spec.write_text(spec.read_text() + "\n\nA new normative paragraph.\n")
    assert open_corpus_fingerprint(str(corpus_copy)) != fp


def test_served_info_for_a_live_checkout_reads_spec_md(corpus_copy):
    (corpus_copy / "vendor_manifest.json").unlink(missing_ok=True)
    info = served_corpus_info(str(corpus_copy))
    assert info["vendored"] is False and info["spec_version"]


@pytest.mark.parametrize("mode,expected", [(None, "ExtractiveAnswerer"), ("", "ExtractiveAnswerer"),
                                           ("extractive", "ExtractiveAnswerer"), ("ollama", "OllamaAnswerer")])
def test_a_paid_generator_is_opt_in(monkeypatch, mode, expected):
    """Unset used to mean Claude whenever the anthropic SDK was installed (it is,
    in the image). Only ASTP_CHAT_MODE=claude selects it now."""
    from astp_docs_server.web.answerer import default_answerer
    if mode is None:
        monkeypatch.delenv("ASTP_CHAT_MODE", raising=False)
    else:
        monkeypatch.setenv("ASTP_CHAT_MODE", mode)
    assert type(default_answerer()).__name__ == expected


def test_claude_only_when_asked(monkeypatch):
    from astp_docs_server.web.answerer import ClaudeAnswerer, default_answerer
    monkeypatch.setenv("ASTP_CHAT_MODE", "claude")
    assert isinstance(default_answerer(), ClaudeAnswerer)
