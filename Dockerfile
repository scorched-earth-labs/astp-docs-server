# syntax=docker/dockerfile:1
#
# Container for the OPEN web-chat head (Clotho-lite). The retrieval engine rides
# inside it as a library; the open docs are vendored into the package, so the
# image is self-contained — no sibling checkout, no runtime corpus mount.
#
# The core library (astp-docs-core) is a private sibling repo, not yet on PyPI,
# so it's pulled in as a named build context. Build from THIS repo dir:
#
#   python scripts/vendor_corpus.py ../ariadne-protocol   # refresh the packaged docs first
#   docker build --build-context core=../astp-docs-core \
#                --build-context protocol=../ariadne-protocol -t astp-docs-server .
#   docker run -p 8080:8080 astp-docs-server   # -> http://localhost:8080
#
# The build REFUSES to produce an image from a stale corpus. The `freshness`
# stage runs tests/test_vendor_freshness.py against the protocol checkout passed
# as the `protocol` context, with ASTP_REQUIRE_CORPUS_FRESHNESS=1, so a missing
# or out-of-date source fails the build instead of skipping. The final image
# copies a marker out of that stage, so BuildKit cannot skip it. Pass a checkout
# of astp's main, clean and up to date: freshness is checked against whatever
# you pass.
#
# (Once astp-docs-core is published to PyPI / made public, drop the build-context
# line and install straight from the index.)
# -- freshness gate (I6) --------------------------------------------------------
FROM python:3.12-slim AS freshness
COPY --from=core . /opt/astp-docs-core
COPY . /opt/astp-docs-server
COPY --from=protocol . /opt/astp-protocol
RUN pip install --no-cache-dir "/opt/astp-docs-core" "/opt/astp-docs-server" "pytest>=7.0.0" \
 && cd /opt/astp-docs-server \
 && ARIADNE_PROTOCOL_DIR=/opt/astp-protocol ASTP_REQUIRE_CORPUS_FRESHNESS=1 \
    python -m pytest tests/test_vendor_freshness.py -q -p no:cacheprovider \
 && python -c "import json; m=json.load(open('src/astp_docs_server/corpus/open/vendor_manifest.json')); print('corpus fresh: SPEC', m['spec_version'], 'from', m['source_commit'])" \
      > /corpus-fresh

# -- the image ------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Depend on the gate: without this COPY, BuildKit would skip the freshness stage.
COPY --from=freshness /corpus-fresh /app/CORPUS-FRESHNESS

# Core library (from the named build context) then this server's WEB extra only
# — no `mcp` SDK in the web image (the MCP transport is a separate, distributed
# concern: adopters `pip install astp-docs-server[mcp]` and run it locally).
COPY --from=core . /opt/astp-docs-core
COPY . /opt/astp-docs-server
RUN pip install --no-cache-dir "/opt/astp-docs-core[embeddings]" \
 && pip install --no-cache-dir "/opt/astp-docs-server[web]"

# Bind to all interfaces inside the container. Default to the keyless extractive
# generator so the container boots with ZERO secrets; enable Claude answers by
# setting ANTHROPIC_API_KEY and ARIADNE_CHAT_MODE=claude at run time.
ENV ARIADNE_WEB_HOST=0.0.0.0 \
    ARIADNE_WEB_PORT=8080 \
    ARIADNE_CHAT_MODE=extractive

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4).status==200 else 1)"

# create_app() is a factory; uvicorn builds the app (retriever loads lazily on
# first request / the healthcheck warms it).
CMD ["uvicorn", "astp_docs_server.web.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
