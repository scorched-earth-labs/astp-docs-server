"""The OPEN ASTP documentation MCP server (FastMCP transport).

Serves ONLY the open protocol corpus (see ``corpora/open_corpus.py``). Adopters
point their coding agents (Claude Code / Codex / Copilot) at this to implement
the protocol from its docs. The enterprise server is a separate deployment with
a separate corpus spec; this module never imports it.

Follows the research-mcp-server FastMCP pattern + .claude/rules/mcp-servers.md.
"""
from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from astp_docs.core import Retriever
from .open_corpus import build_open_corpus_spec
from astp_docs import toolkit as tools

logger = logging.getLogger(__name__)

mcp = FastMCP("astp-docs-open")

_retriever: Retriever | None = None


def retriever() -> Retriever:
    """Lazily build the open-corpus retriever (once per process)."""
    global _retriever
    if _retriever is None:
        protocol_dir = os.environ.get("ASTP_PROTOCOL_DIR")
        _retriever = Retriever.from_spec(build_open_corpus_spec(protocol_dir))
        logger.info("Open corpus loaded: %s", _retriever.stats())
    return _retriever


# -- tools: thin wrappers over the pure functions in tools.py ---------------
@mcp.tool()
def search_spec(query: str, k: int = 5) -> dict:
    """Search the ASTP protocol docs for passages relevant to a query.

    Args:
        query: What you want to find (a concept, symbol, or question).
        k: Max passages to return (default 5).
    """
    return tools.search_spec(retriever(), query, k)


@mcp.tool()
def get_governance_rule(rule_id: str) -> dict:
    """Get a governance rule (G-1 .. G-43) verbatim, with its citation.

    Args:
        rule_id: Rule id in any form — "G-2", "g2", "2".
    """
    return tools.get_governance_rule(retriever(), rule_id)


@mcp.tool()
def get_conformance_vectors(id_or_family: str) -> dict:
    """Get a conformance test vector by id, or a whole family by prefix.

    Args:
        id_or_family: A vector id ("WF-004") or a family prefix ("WF", "CEL").
    """
    return tools.get_conformance_vectors(retriever(), id_or_family)


@mcp.tool()
def get_section(section_id: str, doc: str | None = None) -> dict:
    """Fetch a numbered spec section verbatim (e.g. "5.2", "21").

    Args:
        section_id: The section number, with or without a leading "§".
        doc: Optional document id to disambiguate (e.g. "SPEC"); section
             numbers are per-document.
    """
    return tools.get_section(retriever(), section_id, doc)


@mcp.tool()
def get_hash_preimage(type_name: str, k: int = 5) -> dict:
    """Find how a node/record type's content hash is built (which fields, order).

    Args:
        type_name: e.g. "WorkflowDeclaration", "EpisodeLink", "leaf hash".
        k: Max passages to return (default 5).
    """
    return tools.get_hash_preimage(retriever(), type_name, k)


@mcp.tool()
def get_test_vectors(version: str | None = None) -> dict:
    """The machine-readable conformance vector file for a protocol version:
    5.0.0 pins every seal construction (leaf hash, spine root, sets, Episode
    root, inclusion proofs, canonical JSON, audit records, side-channel and link
    hashes, witness and anchor commitments); 6.0.0 pins the context-commitment
    constructions (context entries, salted content, context manifest, Episode
    root v3, erasure tombstones). Reproduce these from the SPEC text before
    trusting an implementation.

    Args:
        version: Protocol version, e.g. "5.0.0" or "6.0.0" (default: the newest available).
    """
    from astp_docs_server.open_corpus import load_test_vectors

    return load_test_vectors(version, os.environ.get("ASTP_PROTOCOL_DIR"))


@mcp.tool()
def get_license_terms() -> dict:
    """The text of the ASTP project's own licensing documents, verbatim and in
    full: LICENSE.txt (Apache License 2.0), NOTICE (copyright, the
    protocol-name policy, the trademark position) and PATENTS.md (a patent
    pledge to Conforming Implementations, separate from and in addition to the
    Apache license). Each comes whole — never an excerpt — with its SHA-256.

    This is not legal advice. Read the text itself rather than relying on a
    summary of it, and do not answer "may we use this" from the Apache license
    alone: the patent pledge and the NOTICE are separate documents.
    """
    from astp_docs_server.open_corpus import load_license_terms

    return load_license_terms(os.environ.get("ASTP_PROTOCOL_DIR"))


@mcp.tool()
def corpus_info() -> dict:
    """Report what this server serves: doc count, governance rules, vector families."""
    return tools.corpus_info(retriever())


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting ASTP Open Docs MCP Server")
    retriever()  # build eagerly so a bad corpus fails at startup, not first call
    mcp.run()


if __name__ == "__main__":
    run()
