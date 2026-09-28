"""The open web-chat head — a thin HTTP transport over the shared core.

Endpoints:
  POST /chat    {query, k}  → doc-grounded, cited answer (LLM or extractive)
                              OFF unless ARIADNE_WEB_ENABLE_CHAT=true (see below)
  GET  /search  ?q=&k=      → pure retrieval, no LLM (a docs search box)
  GET  /license-terms       → the licensing documents, verbatim (never indexed or generated)
  GET  /healthz             → liveness + what's being served (SPEC version, source commit)

/chat is off by default. On a public host it can spend a model provider's
credits for anyone who finds it (it uses Claude whenever the SDK and a key are
present), so a deployment must opt in. The Discord heads don't use this
endpoint — they run the answerer in-process on the host that owns the model.

Serves ONLY the open corpus. The generator is pluggable (see answerer.py); the
retriever is the same core the MCP server uses, so both heads cite identical
chunks. A reference demo page is mounted at / for local verification.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from astp_docs.core import Retriever
from astp_docs.toolkit import anchored_search
from ..open_corpus import build_open_corpus_spec, load_license_terms, served_corpus_info
from .answerer import Answerer, default_answerer


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=5, ge=1, le=20)


def chat_enabled_from_env() -> bool:
    return os.environ.get("ARIADNE_WEB_ENABLE_CHAT", "false").strip().lower() in ("1", "true", "yes")


def create_app(retriever: Retriever | None = None, answerer: Answerer | None = None,
               enable_chat: bool | None = None) -> FastAPI:
    """``enable_chat`` defaults to ``ARIADNE_WEB_ENABLE_CHAT`` (off). When off,
    ``/chat`` is not mounted and no answerer is ever built."""
    if enable_chat is None:
        enable_chat = chat_enabled_from_env()
    app = FastAPI(title="ASTP Docs Assistant", version="0.1.0")

    # Public read-only docs assistant: permissive CORS by default so the widget
    # can be embedded on the docs site. Lock down via ARIADNE_CORS_ORIGINS
    # (comma-separated) in production. Credentials are never used.
    origins = os.environ.get("ARIADNE_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins],
        allow_methods=["GET", "POST"] if enable_chat else ["GET"],
        allow_headers=["*"],
    )

    state: dict = {"retriever": retriever, "answerer": answerer}

    def get_retriever() -> Retriever:
        if state["retriever"] is None:
            state["retriever"] = Retriever.from_spec(build_open_corpus_spec())
        return state["retriever"]

    def get_answerer() -> Answerer:
        if state["answerer"] is None:
            state["answerer"] = default_answerer()
        return state["answerer"]

    @app.get("/healthz")
    def healthz() -> dict:
        r = get_retriever()
        return {"status": "ok", "corpus": r.corpus_name, "embedder": r.embedder_name,
                "chat": enable_chat, "generator": get_answerer().name if enable_chat else None,
                **served_corpus_info()}

    @app.get("/search")
    def search(q: str, k: int = 5) -> dict:
        results = get_retriever().search(q, k=max(1, min(k, 20)))
        return {"query": q, "count": len(results),
                "results": [res.to_dict() for res in results]}

    @app.get("/license-terms")
    def license_terms() -> dict:
        return load_license_terms()

    if enable_chat:
        @app.post("/chat")
        def chat(req: ChatRequest) -> dict:
            # Exact anchors named in the question resolve first (G-2, WF-001, §5.2),
            # vector search fills the rest — see astp_docs.toolkit.anchored_search.
            results = anchored_search(get_retriever(), req.query, k=req.k)
            out = get_answerer().answer(req.query, results)
            return {"query": req.query, **out}

    @app.get("/", response_class=HTMLResponse)
    def demo() -> str:
        return _DEMO_HTML.replace("__CHAT_ENABLED__", "true" if enable_chat else "false")

    return app


# Minimal self-contained reference widget — for local verification and as a
# starting point. The production widget lives in the website, not here.
_DEMO_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>ASTP Docs Assistant (demo)</title>
<style>
 body{font:15px/1.5 system-ui;max-width:720px;margin:40px auto;padding:0 16px}
 #a{white-space:pre-wrap;background:#f6f6f6;padding:12px;border-radius:8px;margin-top:12px}
 input{width:100%;padding:8px;font-size:15px} button{margin-top:8px;padding:8px 14px}
 .cite{color:#666;font-size:13px;margin-top:8px}
</style></head><body>
<h2>ASTP Docs Assistant <small>(reference demo)</small></h2>
<input id="q" placeholder="Ask about the ASTP protocol…"
 value="How is a WorkflowDeclaration content hash computed?">
<button onclick="ask()">Ask</button>
<div id="a"></div><div class="cite" id="c"></div>
<script>
const CHAT=__CHAT_ENABLED__;
async function ask(){
 const q=document.getElementById('q').value;
 document.getElementById('a').textContent='…';
 if(!CHAT){  // chat is off on this deployment: show the retrieval results instead
  const r=await fetch('/search?k=5&q='+encodeURIComponent(q)); const j=await r.json();
  document.getElementById('a').textContent=(j.results||[]).map((x,i)=>'['+(i+1)+'] '+(x.citation||x.doc_id||'')+'\n'+(x.text||'').slice(0,400)).join('\n\n');
  document.getElementById('c').textContent='(search only — chat is not enabled on this server)'; return;
 }
 const r=await fetch('/chat',{method:'POST',headers:{'content-type':'application/json'},
   body:JSON.stringify({query:q,k:5})});
 const j=await r.json();
 document.getElementById('a').textContent=j.answer;
 document.getElementById('c').textContent=(j.citations||[]).map(c=>'['+c.n+'] '+c.citation).join('   ');
}
</script></body></html>"""


def main() -> None:
    import uvicorn

    app = create_app()
    host = os.environ.get("ARIADNE_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("ARIADNE_WEB_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
