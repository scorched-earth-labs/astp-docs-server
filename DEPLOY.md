# Deploying the open web-chat head

The web head (Clotho-lite) is the piece that needs hosting — a real box, off any
dev workstation. The retrieval engine rides inside it as a library, and the open
docs are **vendored into the package**, so the image is self-contained: no
sibling checkout, no runtime corpus mount, boots with zero secrets.

> The **MCP server** is a separate, *distributed* concern — adopters
> `pip install astp-docs-server[mcp]` and their coding tool runs it locally over
> stdio. It doesn't need hosting unless you decide to offer a hosted remote-MCP
> endpoint (a later choice).

## Build & run (Docker)

```bash
# 1. Refresh the vendored open docs from a protocol checkout (only when they change)
python scripts/vendor_corpus.py /path/to/ariadne-protocol

# 2. Build. astp-docs-core is a private sibling repo (not yet on PyPI), so it's
#    pulled in as a named build context:
docker build --build-context core=../astp-docs-core -t astp-docs-server .

# 3. Run
docker run -p 8080:8080 astp-docs-server        # http://localhost:8080
```

`GET /healthz`, `GET /search?q=…`, `GET /license-terms`, `POST /chat {query,k}`, and a demo widget at `/`.

Once `astp-docs-core` is published to PyPI (or made public), drop the
`--build-context` line and install straight from the index in the Dockerfile.

## Configuration (env vars)

| Var | Default (image) | Purpose |
|---|---|---|
| `ARIADNE_WEB_ENABLE_CHAT` | `false` | **`POST /chat` is not mounted unless this is `true`.** A public deployment should normally leave it off and serve `/search` + the MCP tools only; the Discord heads run the answerer in-process on the host that owns the model and do not use this endpoint. `/healthz` reports `chat`. |
| `ARIADNE_CHAT_MODE` | `extractive` | Only matters when chat is enabled. `extractive` (or unset) = keyless (no LLM). `claude` = synthesize with Claude — the **only** paid option, and only when asked for. `ollama` = synthesize with a local Ollama model (keyless, $0/call) — never point `ARIADNE_OLLAMA_URL` at a private host from a public deployment. |
| `ANTHROPIC_API_KEY` | — | Required when `ARIADNE_CHAT_MODE=claude`. |
| `ARIADNE_CHAT_MODEL` | `claude-opus-4-8` | Generation model (cost/quality knob) when mode is `claude`. |
| `ARIADNE_OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint when mode is `ollama`. |
| `ARIADNE_OLLAMA_MODEL` | `qwen3:14b` | Local model when mode is `ollama`. |
| `ARIADNE_CORS_ORIGINS` | `*` | Comma-separated allowed origins — **lock this to your docs domain in prod.** |
| `ARIADNE_PROTOCOL_DIR` | — | Override the vendored corpus with a live checkout (dev only). |
| `ARIADNE_WEB_HOST` / `ARIADNE_WEB_PORT` | `0.0.0.0` / `8080` | Bind address. |

The public default — search + MCP only, no chat, nothing that can spend:

```bash
docker run -p 8080:8080 \
  -e ARIADNE_CORS_ORIGINS=https://docs.example.com \
  astp-docs-server
```

Opting in to chat with Claude (paid — put a spend cap on the key's workspace
and rate-limit in front of it before exposing this publicly):

```bash
docker run -p 8080:8080 \
  -e ARIADNE_WEB_ENABLE_CHAT=true \
  -e ARIADNE_CHAT_MODE=claude \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e ARIADNE_CORS_ORIGINS=https://docs.example.com \
  astp-docs-server
```

## Where to host

The image is host-agnostic — any container runtime works: a small VM
(Hetzner/DigitalOcean/EC2) with `docker run` behind a reverse proxy for TLS, or a
managed container service (Cloud Run, Fly.io, ECS, a Nix/systemd box). It's
stateless (the index rebuilds from the vendored corpus at startup), so scaling is
just more replicas; no shared state, no database.

Provide `ANTHROPIC_API_KEY` as a runtime secret (never bake it into the image),
and terminate TLS at your proxy/platform.
