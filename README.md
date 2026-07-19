# astp-docs-server

The **open** documentation server for Project Ariadne — two transports on one
substrate, over the public protocol corpus:

- an **MCP server** adopters' coding agents (Claude Code / Codex / Copilot) point
  at to implement the protocol from its normative text, and
- a **web-chat head** ("Clotho-lite") backing a docs-site assistant.

Both consume the shared [`astp-docs`](../astp-docs) core and cite identical
chunks, so the two heads can't drift. This repo serves **only** the open corpus;
the proprietary corpus is a separate, private server.

## Layout

```
src/astp_docs_server/
  open_corpus.py     # the OPEN CorpusSpec (points at the ariadne-protocol docs)
  mcp_server.py      # FastMCP transport — search_spec / get_governance_rule /
                     #   get_conformance_vectors / get_section / get_hash_preimage / corpus_info
  atlas_manifest.py  # Atlas registration (read-only)
  web/               # HTTP transport: /chat, /search, /healthz + a reference demo
```

The retrieval engine, chunker, index, vector search, and the shared tool logic
(`astp_docs.toolkit`) live in the core library — this repo is a thin transport
layer on top. `mcp` (MCP transport) and `fastapi`/`uvicorn`/`anthropic` (web head)
are **separate extras**, so the web head deploys without the MCP SDK and vice-versa.

## The corpus is vendored

The open docs are copied into the package (`src/astp_docs_server/corpus/open/`) by
`scripts/vendor_corpus.py`, and ship in the wheel/image — so a built server is
**self-contained** (no sibling `ariadne-protocol` checkout at runtime). Corpus
resolution precedence: explicit arg → `ARIADNE_PROTOCOL_DIR` (dev override) →
vendored package corpus → `~/projects/ariadne-protocol` (dev fallback).

Refresh the snapshot when the protocol docs change:
```bash
python scripts/vendor_corpus.py /path/to/ariadne-protocol
```

## Run (dev)

```bash
pip install -e ../astp-docs-core          # the core library (editable)
pip install -e '.[mcp,web,dev]'           # this server + both transports

python -m astp_docs_server                # MCP server (stdio)  [needs .[mcp]]
python -m astp_docs_server.web            # web-chat head (http://127.0.0.1:8080)  [needs .[web]]
ARIADNE_CHAT_MODE=extractive python -m astp_docs_server.web   # keyless (no LLM)
python -m pytest tests/ -q                # self-contained (runs off the vendored corpus)
```

The web head answers with Claude by default (`ANTHROPIC_API_KEY` or an
`ant auth login` profile; model via `ARIADNE_CHAT_MODEL`, default `claude-opus-4-8`);
`ARIADNE_CHAT_MODE=extractive` runs without an LLM.

## Deploy

The web head containerizes — see **[DEPLOY.md](DEPLOY.md)**. Short version:
```bash
python scripts/vendor_corpus.py /path/to/ariadne-protocol
docker build --build-context core=../astp-docs-core -t astp-docs-server .
docker run -p 8080:8080 astp-docs-server
```
Stateless (index rebuilds from the vendored corpus at startup) → host-agnostic,
scales by replicas. `llms.txt` and `AGENTS.md` (repo root) point coding agents at
the corpus and these tools.
