"""Open documentation server for ASTP — MCP + web-chat heads over the open corpus.

Two transports on one substrate: the FastMCP server (`mcp_server`) for adopters'
coding agents, and the web-chat head (`web/`) for the docs site. Both consume the
shared `astp_docs` core + `astp_docs.toolkit` and cite identical chunks. Serves
ONLY the open protocol corpus.

The package `__init__` stays import-light on purpose: it does NOT import the MCP
transport, so the web head runs without the `mcp` dependency installed. Import the
server explicitly where needed:  `from astp_docs_server.mcp_server import run`.
"""
__version__ = "0.1.0"
