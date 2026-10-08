"""Answer generation for the web-chat head ("Clotho-lite").

Pluggable behind the ``Answerer`` interface — same shape as the Embedder /
VectorStore seams — so the endpoint runs keyless (extractive) for local/dev and
testing, and swaps to a Claude-backed generator in deployment without touching
the routes.

Both heads (this and the MCP server) retrieve from the SAME core and cite the
SAME chunks, so the website assistant can't drift from what coding agents are
told. This module only *generates*; retrieval is the shared core.
"""
from __future__ import annotations

import dataclasses
import os
import re
from abc import ABC, abstractmethod

from astp_docs.core.models import Result

# Default generation model: Sonnet 5.5, the maintainers' choice for a docs
# chat head (scoped, grounded, latency-sensitive). Override with
# ASTP_CHAT_MODEL — which model a deployment pays for is its own decision.
DEFAULT_CHAT_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """\
You are Clotho-lite, the documentation assistant for ASTP, the AI State Tree \
Protocol — an open protocol for cognitive persistence and verifiable cognition in \
multi-agent systems. Some wire constants in the documents carry a historical \
`ariadne` prefix (for example `ariadne.seal.v…`); they are part of ASTP. Call the \
protocol ASTP.

Answer questions about ASTP using ONLY the numbered context \
passages provided in the user message. Each passage carries a citation like \
[1] SPEC §5.2. Rules:
- Ground every claim in the passages. If the passages don't contain the answer, \
say so plainly — do not invent protocol behavior, field names, hash preimages, \
governance rules, or conformance vectors.
- Cite the passages you used inline with their bracket numbers, e.g. "…as required \
by G-2 [1]." Prefer exact anchors (governance rule ids, conformance vector ids, \
section numbers) when the passages give them.
- Be concise and precise. This is a specification; exactness matters more than prose.
- Stay on the ASTP protocol. Decline unrelated requests briefly.
- Never state, summarise or paraphrase licensing, patent or trademark terms. The \
project's licensing documents are served verbatim by the get_license_terms tool; \
point there instead.\
"""

# Licensing is answered by the documents themselves, never by a generator. A
# paraphrase of a patent grant can be wrong in exactly the way that matters, and
# "it's Apache 2.0" — the best a retriever-fed model can assemble — misses the
# separate patent pledge. Enforced in Answerer.answer, not only in the prompt,
# because a head may bring its own system prompt.
LICENSING_REDIRECT = (
    "I don't answer licensing questions: a summary of legal terms can be wrong "
    "in exactly the way that matters. Read the terms themselves — LICENSE.txt "
    "(Apache License 2.0), NOTICE (the protocol-name policy and trademark "
    "position) and PATENTS.md (a patent pledge to Conforming Implementations, "
    "separate from the Apache license). The docs server serves all three "
    "verbatim: the get_license_terms MCP tool, or GET /license-terms. "
    "This is not legal advice."
)

# Asked about licensing. Over-matching is the safe direction: a false positive
# costs one redirect; a false negative is a generated legal summary.
_LICENSING_QUESTION_RE = re.compile(
    r"licen[cs]|patent|royalt|trademark|copyright|apache|pledge|infring|indemn"
    r"|(?-i:\bNOTICE\b)|\blegal|open[- ]?source|closed[- ]?source|commercial"
    # Permission phrasing counts only when its object is the protocol or its
    # code — "can we use SHA-256 here?" is a protocol question.
    r"|\b(?:may|can|could)\s+(?:we|i|you|they|one|anyone|companies)\s+"
    r"(?:use|ship|sell|fork|embed|redistribute|build on|implement)\s+"
    r"(?:astp|ariadne|this|it\b|the\s+(?:protocol|spec|specification|reference|code|software|package))"
    r"|\b(?:allowed|permitted|permission|free)\s+to\s+(?:use|ship|sell|implement|build|fork)",
    re.I,
)

# Licensing language inside a retrieved passage. The paragraph is withheld from
# the generator, so it has nothing to paraphrase. Narrower than the question
# pattern: "copyright" in SPEC §4.8.4 is about retaining fetched content, not
# about this project's terms.
_LICENSING_TEXT_RE = re.compile(
    r"patent|royalt|trademark|\blicen[cs](?:e|es|ed|ing|or|ee)\b|sublicens|(?-i:\bNOTICE\b)|PATENTS\.md",
    re.I,
)
_REDACTED = ("[Licensing text withheld. Read LICENSE.txt, NOTICE and PATENTS.md "
             "verbatim via get_license_terms.]")


def is_licensing_question(query: str) -> bool:
    return bool(_LICENSING_QUESTION_RE.search(query))


def withhold_licensing_text(results: list[Result]) -> list[Result]:
    """Copies of ``results`` with every paragraph that speaks to licensing
    replaced by a pointer to the verbatim terms. The retriever's chunks are not
    modified."""
    out = []
    for r in results:
        paras = r.chunk.text.split("\n\n")
        kept = [_REDACTED if _LICENSING_TEXT_RE.search(p) else p for p in paras]
        if kept == paras:
            out.append(r)
        else:
            chunk = dataclasses.replace(r.chunk, text="\n\n".join(kept))
            out.append(dataclasses.replace(r, chunk=chunk))
    return out


def build_context(results: list[Result]) -> str:
    """Render retrieved chunks as numbered, citation-tagged context."""
    blocks = []
    for i, r in enumerate(results, start=1):
        c = r.chunk
        blocks.append(f"[{i}] {c.citation()}\n{c.text}")
    return "\n\n".join(blocks)


def build_user_prompt(query: str, results: list[Result]) -> str:
    if not results:
        return (
            f"Question: {query}\n\n"
            "No documentation passages were retrieved. Tell the user you don't have "
            "anything in the docs on this and suggest they rephrase."
        )
    return f"Context passages:\n\n{build_context(results)}\n\n---\nQuestion: {query}"


def _citations(results: list[Result]) -> list[dict]:
    out = []
    for i, r in enumerate(results, start=1):
        c = r.chunk
        out.append({
            "n": i,
            "doc_id": c.doc_id,
            "anchor": str(c.primary),
            "citation": str(c.citation()),
            "heading_path": c.heading_path,
        })
    return out


class Answerer(ABC):
    name: str = "answerer"

    def answer(self, query: str, results: list[Result]) -> dict:
        """Return {answer, citations, generator, grounded}.

        Licensing never reaches a generator: a licensing question gets a fixed
        pointer to the verbatim terms, and licensing paragraphs are withheld
        from the passages any other question is answered from."""
        if is_licensing_question(query):
            return {"answer": LICENSING_REDIRECT, "citations": [],
                    "generator": self.name, "grounded": False}
        return self._answer(query, withhold_licensing_text(results))

    @abstractmethod
    def _answer(self, query: str, results: list[Result]) -> dict:
        """Generate from passages already cleared of licensing text."""


class ExtractiveAnswerer(Answerer):
    """Keyless fallback: no LLM, just return the top passages as the answer.

    Honest and useful for a docs *search* box, and it keeps /chat working (and
    testable) with no credentials. Not a real conversational assistant — the
    Claude generator is that.
    """

    name = "extractive"

    def _answer(self, query: str, results: list[Result]) -> dict:
        if not results:
            return {"answer": "Nothing in the ASTP docs matches that query.",
                    "citations": [], "generator": self.name, "grounded": False}
        top = results[0].chunk
        answer = (
            f"Most relevant passage — {top.citation()}:\n\n{top.text.strip()}"
        )
        return {"answer": answer, "citations": _citations(results),
                "generator": self.name, "grounded": True}


class ClaudeAnswerer(Answerer):
    """Doc-grounded RAG answers via Claude. The deployment default."""

    def __init__(self, model: str | None = None, client=None,
                 system_prompt: str | None = None):
        self.model = model or os.environ.get("ASTP_CHAT_MODEL", DEFAULT_CHAT_MODEL)
        self.name = f"claude:{self.model}"
        self._client = client  # injected for tests; else built lazily
        # Another head (e.g. a differently-named community bot over a different
        # corpus) can supply its own persona; the grounding rules travel with it.
        self.system_prompt = system_prompt or SYSTEM_PROMPT

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic  # lazy: optional dep, resolves creds itself

            self._client = Anthropic()
        return self._client

    def _answer(self, query: str, results: list[Result]) -> dict:
        resp = self._get_client().messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            thinking={"type": "adaptive"},        # low effort: scoped, latency-sensitive
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": build_user_prompt(query, results)}],
        )
        # Safety classifiers can decline (HTTP 200) — check before reading content.
        if getattr(resp, "stop_reason", None) == "refusal":
            return {"answer": "I can't help with that request.",
                    "citations": [], "generator": self.name, "grounded": False}
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return {"answer": text.strip(), "citations": _citations(results),
                "generator": self.name, "grounded": bool(results)}


# Local-inference defaults. qwen3:14b is the strongest model that fits a 16GB
# consumer GPU; override per deployment.
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:14b"

# Reasoning models sometimes leak their scratchpad even with thinking disabled.
_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class OllamaAnswerer(Answerer):
    """Doc-grounded RAG answers via a local Ollama model. Keyless, $0 per call.

    Same prompt assembly as the Claude generator, so the answer is grounded in
    the same cited passages — only the generator differs. Deliberately stdlib-
    only (urllib) so the server gains no dependency for a local deployment.
    A ``transport`` callable ``(payload: dict) -> dict`` can be injected for
    tests; the default POSTs to ``/api/chat``.
    """

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 system_prompt: str | None = None, transport=None,
                 timeout: float = 120.0, num_predict: int = 700,
                 keep_alive: str = "30m"):
        self.model = model or os.environ.get("ASTP_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.base_url = (base_url or os.environ.get("ASTP_OLLAMA_URL", DEFAULT_OLLAMA_URL)).rstrip("/")
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.name = f"ollama:{self.model}"
        self._transport = transport
        self.timeout = timeout
        self.num_predict = num_predict
        self.keep_alive = keep_alive

    def _post(self, payload: dict) -> dict:
        if self._transport is not None:
            return self._transport(payload)
        import json
        from urllib.request import Request, urlopen

        req = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def build_payload(self, query: str, results: list[Result]) -> dict:
        return {
            "model": self.model,
            "stream": False,
            "think": False,                 # answer, don't deliberate (qwen3 et al.)
            "keep_alive": self.keep_alive,  # stay resident between questions
            "options": {"temperature": 0.2, "num_predict": self.num_predict},
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": build_user_prompt(query, results)},
            ],
        }

    def _answer(self, query: str, results: list[Result]) -> dict:
        data = self._post(self.build_payload(query, results))
        text = (data.get("message") or {}).get("content") or ""
        text = _THINK_BLOCK_RE.sub("", text).strip()
        if not text:
            # A silent empty completion must not look like "the docs say nothing".
            return {"answer": "I couldn't produce an answer just now — please try again.",
                    "citations": [], "generator": self.name, "grounded": False}
        return {"answer": text, "citations": _citations(results),
                "generator": self.name, "grounded": bool(results)}


def default_answerer() -> Answerer:
    """Pick a generator from ``ASTP_CHAT_MODE``: ``claude`` (paid — must be
    asked for), ``ollama`` (keyless, local model), or anything else / unset →
    ``extractive`` (keyless, no LLM).

    Unset used to mean Claude whenever the anthropic SDK was importable — and
    the ``[web]`` extra the image installs includes it, so a deployment that set
    nothing would spend a provider's credits. A paid generator is now opt-in,
    matching DEPLOY.md."""
    mode = os.environ.get("ASTP_CHAT_MODE", "").strip().lower()
    if mode == "claude":
        return ClaudeAnswerer()
    if mode == "ollama":
        return OllamaAnswerer()
    return ExtractiveAnswerer()
