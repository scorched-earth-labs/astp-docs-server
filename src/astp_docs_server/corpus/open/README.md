# ASTP — AI State Tree Protocol

**A cognitive persistence protocol for multi-agent AI systems.**

*Developed internally as Project Ariadne.*

Bring your own cognitive architecture. ASTP handles the persistence, integrity verification, and coordination of agent state transitions.

📖 **New to ASTP?** Start with the [Glossary](./GLOSSARY.md) — every term used in the spec and code, defined once with explicit structural relationships (e.g. how `EpisodeNode` relates to `CognitiveNode` + `EpisodePayload`).

**Current version:** the `**Version:**` field at the top of [`SPEC.md`](./SPEC.md) is the protocol version (it is not restated here, so it can't drift). Versioning policy: [`VERSIONING.md`](./VERSIONING.md). Change history: [`CHANGELOG.md`](./CHANGELOG.md).

---

## What It Is

Multi-agent AI systems have a memory problem. Agents reason across long episodes of work — architecture decisions, debugging sessions, collaborative exchanges — but the record of that reasoning is either lost between sessions or stored in ways that can't be verified, audited, or reliably retrieved.

ASTP is a protocol for solving that problem. It defines:

- A **hash-chained state tree** that provides cryptographic proof that the cognitive record hasn't been tampered with
- A **governance rule set** (the numbered `G-*` rules in `SPEC.md`) that any conforming implementation must enforce
- A **Write Intent Log (WIL)** that coordinates multi-store writes and guarantees recoverability
- A **Crystallization protocol** that captures point-in-time integrity snapshots as first-class state transitions
- A **Consultation record** that treats cross-agent exchanges as first-class protocol nodes, not implementation details

The protocol is **agnostic to cognitive architecture**. A system using BDI, ReAct, chain-of-thought, SOAR, or any other reasoning model can implement ASTP without inheriting assumptions about how agents think. ASTP records *that* agents reasoned and *what* resulted — not *how* they reasoned.

---

## What It Is Not

ASTP is not a vector database, a RAG system, or a session memory layer. It is a **verifiable cognitive record protocol** — closer in design philosophy to a distributed ledger than to a retrieval system. The integrity guarantees come from the hash chain and the Merkle tree, not from the storage backend.

---

## Structure

```
astp/
├── protocol/                # Node-generic layer — operates on CognitiveNode only
│   ├── node.py              # CognitiveNode + NodePayload abstraction
│   ├── leaf_hash.py         # Position-binding leaf hash
│   ├── merkle.py            # Adaptive Merkle tree (spine)
│   ├── governance.py        # Governance rule enforcement
│   ├── keys.py              # HKDF key hierarchy (workspace → node → seal)
│   ├── verification.py      # DeltaVerifier — the five-test gate
│   └── …                    # audit, chain_proof, delta, witness, registry, …
├── nodes/                   # Node-type instantiations (episode/, segment/)
├── core/                    # Episode-era schema, governance errors, WIL, BFM,
│   │                        #   cross-episode linking, Layer 3, coherence
│   ├── schema.py            # Episodes, Segments, Signals + inline governance
│   ├── wil.py               # Write Intent Log state machine
│   ├── branching.py         # Branch / fork / merge primitives
│   ├── workflow_execution.py# Layer 3 — Workflow & Execution DAG
│   └── hash_canonical.py    # Reference canonicalizer for content hashes
└── adapters/
    ├── base.py              # AriadneAdapter abstract interface (ASI)
    └── neo4j/               # Reference implementation
        ├── writer.py, queries.py, crystallization.py, wil.py
        └── rebalance.py, retrieval_audit.py
```

Two invariants shape the tree. The **namespace firewall**: `astp.protocol.*` never imports from `astp.nodes.*` (enforced by test). And the dependency is strictly one-directional: adapters import the protocol core; the protocol core has no database dependencies.

---

## Core Concepts

### Episode

A bounded unit of agent work. Episodes have a formal lifecycle:

```
CREATED → ACTIVE → CLOSING → CLOSING_PENDING_SEAL → SEALED → ARCHIVED
                 ↘ CRYSTALLIZATION_PENDING → CRYSTALLIZED ↗
```

### Segment

An ordered, immutable content unit within an episode. Each segment carries a `content_hash` (SHA3-256 of its content) and a `content_ref` (pointer to the full content in durable storage). The hash chain is over the pointers and hashes — not the content itself. Content scales independently of the integrity layer.

### Spine

The ordered hash chain of segments within an episode. The Merkle root of the spine is the episode's integrity fingerprint. The spine is the proof; the blobs are the payload.

### Crystallization

A state transition *in* the episode chain — not a receipt *about* it. Each crystallization produces a `CrystallizationDeltaNode` structurally analogous to a blockchain block header. Crystallizations are immutable after creation. Corrections flow forward through successor episodes; the original record is never amended.

### Write Intent Log (WIL)

A three-phase coordination protocol for multi-store writes. Writes proceed in strict durability order: durable content store → authoritative structural store → ephemeral coordinator → semantic search index. An interrupted write at any phase is recoverable. All writes are idempotent.

### Consultation

A cross-agent exchange recorded as a first-class protocol node, not an application-level convention. Consultations form their own hash chain of `ExchangeEntry` nodes. The branch point is recorded before any exchange occurs (G-8). Resolution requires at least one entry (G-9).

---

## Implementing an Adapter

Any database can serve as an ASTP backend by implementing the `AriadneAdapter` interface:

```python
from astp.adapters.base import AriadneAdapter

class MyDatabaseAdapter(AriadneAdapter):
    # Implement the ASI methods
    ...
```

A conforming adapter must:

1. Enforce every governance rule (`G-*`) defined in `SPEC.md`
2. Preserve hash chain integrity — never modify `content_hash`, `spine_hash`, or `episode_root_hash` after creation
3. Respect write ordering invariants across stores
4. Support idempotent writes for WIL recovery
5. Fail loudly on errors — never silently swallow writes

The Neo4j adapter in `astp/adapters/neo4j/` is the reference implementation. See `SPEC.md` for the full conformance requirements.

---

## Conformance Testing

What exists today:

- **Conformance requirement documents** — the `CONFORMANCE*.md` files listed under **Specification Documents** below. Each vector states its inputs and the property a conforming implementation must exhibit, by requirement class (REQUIRED / RECOMMENDED).
- **The reference test suite** — `tests/`, run with `pytest`. It exercises the reference implementation against those documents and guards the spec-to-code agreements (operation register, lifecycle states, namespace firewall, wire constants).

- **Machine-readable vectors** — [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json): pinned expected digests for every 5.0.0 construction (leaf hash, spine, sets, Episode root, inclusion proofs, canonical JSON, audit records, side-channel and link hashes, witness and anchor commitments), generated by `vectors/5.0.0/generate.py` and checked by the reference tests against a from-prose reference that imports nothing from the package.

What does not exist yet: an adapter-parameterized harness that a third-party implementation can run against those vectors. Until it does, conformance is demonstrated by reproducing the vector digests and showing the properties the `CONFORMANCE*.md` documents require.

---

## Installation

Requires Python >= 3.11. The distribution name and the import name are both `astp`.

The package is not yet published to a package index. Install from a checkout:

```bash
pip install -e ".[neo4j,dev]"   # editable install with the Neo4j reference adapter and test dependencies
pytest                          # run the reference test suite
```

```python
import astp
```

---

## Status

**Alpha.** The protocol core and Neo4j reference adapter are extracted and stable. Active development continues on branching, forking, merging, and agent tool-call retrieval interfaces. The protocol specification is in `SPEC.md`.

The first consumer of this protocol is Ignis OS, Scorched Earth Labs' agent runtime, and integration tests for the reference adapter run there rather than in this repository. Not recommended for production use elsewhere until the first stable release.

---

## Amendments

Protocol amendments are ratified in a designated Episode of Record and reference the Episode's spine hash for provenance. The Episode of Record is the cryptographic anchor; the document is the human-readable artifact. The Episode of Record for 4.0.0 is `458fb62b-faee-4e42-9f92-c63187c1b59a`; its sealed root reproduces from its stored nodes. The Episode of Record for 5.0.0 is `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`, sealed 2026-09-18; it ratifies `SPEC.md` by content digest ([`docs/RATIFICATION-5.0.0.md`](./docs/RATIFICATION-5.0.0.md)). Exported proofs of record — files a third party can verify with this package alone — are not yet published for any MAJOR release. As of the **v3.2.1 integration pass**, both prior amendments are folded into the SPEC body — the amendment documents are retained for provenance only and are no longer normative. Amendment documents retain their authoring numerals; the canonical SPEC version per [`VERSIONING.md`](./VERSIONING.md) is shown alongside.

| Amendment | SPEC version | Status | Now in SPEC | Document (historical) |
|-----------|--------------|--------|-------------|-----------------------|
| v2.0 — Cross-Episode Linking & Grouping Interface | v3.0.0 | Integrated into SPEC body (v3.2.1) | [§20](./SPEC.md) | [`AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`](./docs/history/AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md) |
| v3.0 — Layer 3 Workflow & Execution DAG Codification | v3.1.0 | Integrated into SPEC body (v3.2.1) | [§21](./SPEC.md) | [`AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`](./docs/history/AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md) |

**SPEC v3.0.0 (cross-episode linking, MAJOR)** introduces typed cross-episode links, an EpisodeGrouping interface (with `MembershipRecord` as the protocol-owned artifact), succession-chain governance for `MembershipRecord` and `ConformanceDeclaration`, audit-the-decision pattern for behavioral-tier implementation choices (§12), and a three-tier conformance taxonomy (wire / state / behavioral). Breaking hash preimage changes on three node types — see Appendix A of the amendment for the full breaking-change reference.

**SPEC v3.1.0 (Layer 3, MINOR)** formalizes the three-Merkle-layer model and codifies Layer 3 — `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation`. Layer 3 is cryptographically isolated from Spine integrity by construction (Layer 3 nodes reference Layers 1/2 by ID only; never participate in Spine hashing), so no future Layer-3 change can force a MAJOR bump on Spine grounds. Each Layer 3 node type has a designated Cognitive Implementation Authority (CIA) — sole-writer guarantee as a wire-tier conformance principle.

The SPEC integration pass landed in **v3.2.1**: this material is now normatively defined in the `SPEC.md` body (§20, §21), and each surface has a companion implementation guide and conformance-vector document (see **Specification Documents** below).

---

## Specification Documents

The protocol is one normative document (`SPEC.md`) plus, per feature surface, a non-normative implementation guide (reference Neo4j adapter) and a conformance document (test vectors stated as inputs and required properties; pinned expected digests are not yet published).

| Surface | SPEC | Implementation guide | Conformance vectors |
|---------|------|----------------------|---------------------|
| Branch / Fork / Merge + **Departure Fork** | §19 | [`IMPLEMENTATION-BFM.md`](./IMPLEMENTATION-BFM.md) | [`CONFORMANCE-BFM.md`](./CONFORMANCE-BFM.md) |
| Cross-Episode Linking & Grouping | §20 | [`IMPLEMENTATION-CROSS-EPISODE-LINKING.md`](./IMPLEMENTATION-CROSS-EPISODE-LINKING.md) | [`CONFORMANCE-CROSS-EPISODE-LINKING.md`](./CONFORMANCE-CROSS-EPISODE-LINKING.md) |
| Layer 3 — Workflow & Execution DAG | §21 | [`IMPLEMENTATION-LAYER3.md`](./IMPLEMENTATION-LAYER3.md) | [`CONFORMANCE-LAYER3.md`](./CONFORMANCE-LAYER3.md) |
| Reproducibility — spine leaf set, episode root, version identifiers | §5.6–§5.8, §9.3, G-1 | — | [`CONFORMANCE-REPRODUCIBILITY.md`](./CONFORMANCE-REPRODUCIBILITY.md) |
| Trust Infrastructure (Phase 3) | §16 | [`IMPLEMENTATION-PHASE3.md`](./IMPLEMENTATION-PHASE3.md) | [`CONFORMANCE.md`](./CONFORMANCE.md) |

Supporting: [`VERSIONING.md`](./VERSIONING.md) (canonical version policy), [`GLOSSARY.md`](./GLOSSARY.md), [`CHANGELOG.md`](./CHANGELOG.md).

Historical, retained for provenance only and not to be implemented from: [`docs/history/`](./docs/history/) — prior major-version specifications (`SPEC-v1.md`, `SPEC-v3.md`), the two former amendment documents, and the original architecture vision (`VISION.md`).

---

## Versioning

ASTP follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`:

- **MAJOR** — changes to canonical form (hash preimages, serialization, required fields). Conformance-breaking.
- **MINOR** — additive surface (new optional node types, new query surface, new fields with safe defaults). Existing implementations remain conformant.
- **PATCH** — errata, clarifications, ambiguity resolution. No semantic change.

`SPEC.md` is the canonical version source — the `Version:` field at the top of that file IS the protocol version. Implementation guides, conformance documents, and amendments are versioned-against (they describe behavior at a specific protocol version), not versioned-independently.

Full policy: [`VERSIONING.md`](./VERSIONING.md). Change history: [`CHANGELOG.md`](./CHANGELOG.md).

---

## License

Apache-2.0. Copyright 2026 Scorched Earth Labs, LLC.

The specification text and the code in this repository are both licensed under Apache-2.0; see [`LICENSE.txt`](./LICENSE.txt).

The Apache license was chosen deliberately: it includes a patent grant clause, which matters for a protocol with novel cryptographic data structures at its core.

---

## Developed By

[Scorched Earth Labs](https://scorchedearthlabs.com)
