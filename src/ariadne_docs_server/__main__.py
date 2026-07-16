"""Run the open MCP server:  python -m ariadne_docs_server

(For the web-chat head instead:  python -m ariadne_docs_server.web)
"""
from .mcp_server import run

if __name__ == "__main__":
    run()
