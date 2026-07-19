"""Open Ariadne documentation server — MCP + web-chat heads over the open corpus.

Two transports on one substrate: the FastMCP server (`mcp_server`) for adopters'
coding agents, and the web-chat head (`web/`) for the docs site. Both consume the
shared `astp_docs` core + `astp_docs.toolkit` and cite identical chunks, so
they cannot drift. Serves ONLY the open protocol corpus.
"""
from .mcp_server import mcp, run

__version__ = "0.1.0"
__all__ = ["mcp", "run"]
