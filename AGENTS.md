# AGENTS.md — implementing ASTP

If you are an AI coding agent tasked with implementing (or conforming to) ASTP,
the AI State Tree Protocol, read this first.

## Ground rules

1. **The SPEC is authoritative. Do not infer normative behavior.** Hash
   preimages, field sets, field order, encodings, governance rules, and
   conformance vectors are exact. Guessing them yields a different digest and
   a non-conforming implementation — the single most common failure mode.
2. **Look it up, don't approximate.** Use the ASTP Docs MCP server for exact
   answers rather than semantic recall:
   - `get_governance_rule("G-2")` — a governance rule verbatim (G-1..G-43)
   - `get_conformance_vectors("RP-009")` or `("RP")` — a vector or a whole family
   - `get_section("5.7.1")` — a numbered spec section
   - `get_hash_preimage("witness commitment")` — which fields a hash binds, in order
   - `get_test_vectors()` — the machine-readable vector file with every expected digest
   - `search_spec("…")` — semantic search when you don't know the anchor
3. **Reproduce the vectors, from the text.** Every 5.0.0 seal construction has
   a pinned expected value in `vectors/5.0.0/seal-constructions.json`, and every
   6.0.0 context-commitment construction in `vectors/6.0.0/context-commitment.json`. Implement
   from the SPEC text and check your bytes against those digests before you
   trust your implementation; the reference tests do exactly that with a
   from-prose implementation that imports nothing from the reference package.
4. **Versions select constructions.** A record says which construction produced
   its hashes (`hash_version`, `spine_algorithm_version`, `ordering_version`,
   SPEC §5.8). Implement the current constructions for new records and the
   retained ones for verifying existing seals; never modify a construction in
   place.

## What ASTP is (and isn't)

- ASTP records **that** an agent reasoned, the resulting state, and a verifiable
  audit chain, and makes the record cryptographically verifiable and
  reproducible from stored state alone. It does **not** prescribe *how* the
  agent reasons — bring your own architecture (ReAct, BDI, CoT, …).
- Storage is an adapter concern: the protocol names storage *roles*, never
  providers. Conform to the protocol, not to the reference adapter.
- The protocol was developed under the internal name *Ariadne*; wire constants
  (`Ariadne*` graph labels, `ariadne.` HKDF info strings) keep that prefix
  because they feed derived keys and name stored data. Call the protocol ASTP.

## Where to start

Read SPEC §2 (terminology and the protocol/implementation boundary), §3
(layers), §5 (the hash chain: encoding, leaf hash, spine, manifests, Episode
root), §6 (governance), §8 (audit chain), §9 (verification). Then the surface
you need: §16 trust infrastructure, §19 branch/fork/merge and the side
channels, §20 cross-episode linking and grouping, §21 the Layer 3 DAG, §4.8–§4.9
and §5.7.3 context commitment and erasure (CONFORMANCE-CONTEXT.md, with an
IMPLEMENTATION-CONTEXT.md). Each has
a CONFORMANCE-*.md companion (§16 also an IMPLEMENTATION-PHASE3.md; the storage-layout
guides for §19–§21 ship with the reference deployment's adapter, not here); `GLOSSARY.md` defines
every term; `GOVERNANCE.md` and `VERSIONING.md` say how the protocol changes.
