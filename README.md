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
layer on top.

## Run

```bash
pip install -e ../astp-docs        # the core library (editable, dev)
pip install -e '.[web]'               # this server + web extra

export ARIADNE_PROTOCOL_DIR=~/projects/ariadne-protocol   # the open docs source

python -m astp_docs_server                      # MCP server (stdio)
python -m astp_docs_server.web                  # web-chat head (http://127.0.0.1:8080)
ARIADNE_CHAT_MODE=extractive python -m astp_docs_server.web   # keyless (no LLM)

PYTHONPATH=src python scripts/build_open_index.py  # build + sample lookups
python -m pytest tests/ -q                         # tests (skip if the corpus is absent)
```

The web head answers with Claude by default (`ANTHROPIC_API_KEY` or an
`ant auth login` profile; model via `ARIADNE_CHAT_MODEL`, default `claude-opus-4-8`);
`ARIADNE_CHAT_MODE=extractive` runs without an LLM. `llms.txt` and `AGENTS.md`
(repo root) point coding agents at the corpus and these tools.
