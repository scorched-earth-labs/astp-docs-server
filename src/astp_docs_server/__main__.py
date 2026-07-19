"""Run the open MCP server:  python -m astp_docs_server

(For the web-chat head instead:  python -m astp_docs_server.web)
"""
from .mcp_server import run

if __name__ == "__main__":
    run()
