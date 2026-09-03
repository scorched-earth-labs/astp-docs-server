"""Web-chat head tests.

Prompt assembly + the extractive answerer + the ClaudeAnswerer request shape
run with no network. The FastAPI route tests use the extractive answerer (no
key) and skip if fastapi/httpx or the corpus is unavailable.
"""
import pytest

from astp_docs.core import Document, DocIndex, Retriever, chunk_corpus
from astp_docs_server.web.answerer import (
    ClaudeAnswerer,
    ExtractiveAnswerer,
    build_context,
    build_user_prompt,
)

MINI = Document(
    doc_id="SPEC",
    path="SPEC.md",
    text="# Spec\n\n## 5. Hash Chain\n\n### 5.2 Leaf Hash\n\n"
         "The leaf hash binds identity, type, and position into a SHA3-256 commitment.\n",
)


def _results():
    r = Retriever(DocIndex(chunk_corpus([MINI])))
    return r.search("leaf hash commitment", k=3)


def test_build_context_numbers_and_cites():
    ctx = build_context(_results())
    assert "[1]" in ctx and "SPEC §5.2" in ctx
    assert "SHA3-256" in ctx


def test_user_prompt_handles_empty_results():
    p = build_user_prompt("anything", [])
    assert "No documentation passages" in p


def test_extractive_answerer_grounds_and_cites():
    out = ExtractiveAnswerer().answer("leaf hash", _results())
    assert out["generator"] == "extractive"
    assert out["grounded"] is True
    assert out["citations"][0]["citation"].startswith("SPEC §5.2")
    assert "SHA3-256" in out["answer"]


def test_extractive_empty_is_ungrounded():
    out = ExtractiveAnswerer().answer("unrelated", [])
    assert out["grounded"] is False and out["citations"] == []


def test_claude_answerer_builds_correct_request():
    """Stub the client; assert the request shape follows the API guidance
    (Opus 4.8 default, adaptive thinking, no sampling params)."""
    captured = {}

    class _Block:
        type = "text"
        text = "Grounded answer [1]."

    class _Resp:
        stop_reason = "end_turn"
        content = [_Block()]

    class _Messages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _Resp()

    class _Client:
        messages = _Messages()

    ans = ClaudeAnswerer(client=_Client())
    out = ans.answer("How is the leaf hash built?", _results())

    assert out["answer"] == "Grounded answer [1]."
    assert out["generator"] == "claude:claude-opus-4-8"
    assert captured["model"] == "claude-opus-4-8"
    assert captured["thinking"] == {"type": "adaptive"}
    assert "temperature" not in captured and "top_p" not in captured
    assert captured["system"].startswith("You are Clotho-lite")
    assert captured["messages"][0]["role"] == "user"


def test_claude_answerer_handles_refusal():
    class _Resp:
        stop_reason = "refusal"
        content = []

    class _Client:
        class messages:
            @staticmethod
            def create(**kwargs):
                return _Resp()

    out = ClaudeAnswerer(client=_Client()).answer("x", _results())
    assert out["grounded"] is False and out["citations"] == []


# -- route tests -----------------------------------------------------------
fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

try:
    from astp_docs_server.open_corpus import build_open_corpus_spec

    _spec = build_open_corpus_spec()
except FileNotFoundError:
    _spec = None


@pytest.fixture(scope="module")
def client():
    from astp_docs_server.web.app import create_app

    retriever = Retriever.from_spec(_spec) if _spec else Retriever(DocIndex(chunk_corpus([MINI])))
    app = create_app(retriever=retriever, answerer=ExtractiveAnswerer())
    return TestClient(app)


def test_healthz(client):
    j = client.get("/healthz").json()
    assert j["status"] == "ok"
    assert j["generator"] == "extractive"
    assert j["embedder"] == "tfidf-local"


def test_search_route(client):
    j = client.get("/search", params={"q": "leaf hash", "k": 3}).json()
    assert j["count"] >= 1
    assert all("citation" in r for r in j["results"])


def test_chat_route(client):
    j = client.post("/chat", json={"query": "leaf hash", "k": 3}).json()
    assert j["generator"] == "extractive"
    assert j["answer"]
    assert j["citations"]


def test_demo_page_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Ariadne Docs Assistant" in r.text


# --- OllamaAnswerer (local inference) ----------------------------------------

from astp_docs_server.web.answerer import OllamaAnswerer, SYSTEM_PROMPT  # noqa: E402


def test_ollama_answerer_builds_correct_request():
    """No network: capture the payload the answerer would POST to /api/chat."""
    captured = {}

    def transport(payload):
        captured.update(payload)
        return {"message": {"role": "assistant", "content": "The leaf hash binds position [1]."}}

    ans = OllamaAnswerer(model="qwen3:14b", transport=transport)
    out = ans.answer("leaf hash", _results())

    assert captured["model"] == "qwen3:14b"
    assert captured["stream"] is False
    assert captured["think"] is False
    assert captured["options"]["temperature"] == 0.2
    assert captured["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "Context passages" in captured["messages"][1]["content"]
    assert "SHA3-256" in captured["messages"][1]["content"]
    assert out["generator"] == "ollama:qwen3:14b"
    assert out["grounded"] is True
    assert out["answer"] == "The leaf hash binds position [1]."
    assert out["citations"][0]["citation"].startswith("SPEC §5.2")


def test_ollama_answerer_strips_leaked_thinking_and_uses_custom_prompt():
    seen = {}

    def transport(payload):
        seen.update(payload)
        return {"message": {"content": "<think>hmm\nlots</think>\nAnswer here."}}

    ans = OllamaAnswerer(model="m", transport=transport, system_prompt="You are Bob.")
    out = ans.answer("q", _results())
    assert out["answer"] == "Answer here."
    assert seen["messages"][0]["content"] == "You are Bob."


def test_ollama_answerer_empty_completion_is_ungrounded():
    out = OllamaAnswerer(model="m", transport=lambda p: {"message": {"content": ""}}).answer("q", _results())
    assert out["grounded"] is False and out["citations"] == []
    assert "try again" in out["answer"]


def test_default_answerer_ollama_mode(monkeypatch):
    from astp_docs_server.web.answerer import default_answerer

    monkeypatch.setenv("ARIADNE_CHAT_MODE", "ollama")
    monkeypatch.setenv("ARIADNE_OLLAMA_MODEL", "phi3:3.8b")
    monkeypatch.setenv("ARIADNE_OLLAMA_URL", "http://gpu-box:11434/")
    a = default_answerer()
    assert isinstance(a, OllamaAnswerer)
    assert a.model == "phi3:3.8b" and a.base_url == "http://gpu-box:11434"


def test_claude_answerer_accepts_custom_system_prompt():
    captured = {}

    class _Block:
        type = "text"
        text = "ok"

    class _Resp:
        stop_reason = "end_turn"
        content = [_Block()]

    class _Messages:
        def create(self, **kw):
            captured.update(kw)
            return _Resp()

    class _Client:
        messages = _Messages()

    ClaudeAnswerer(client=_Client(), system_prompt="You are Bob.").answer("q", _results())
    assert captured["system"] == "You are Bob."


def test_chat_route_resolves_named_anchor_exactly(client):
    r = client.post("/chat", json={"query": "what does G-1 require?", "k": 3})
    assert r.status_code == 200
    assert r.json()["citations"][0]["anchor"] == "G-1"
