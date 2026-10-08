# ASTP — AI State Tree Protocol

**A cognitive persistence protocol for multi-agent AI systems.**

*Developed internally as Project Ariadne.*

Bring your own cognitive architecture. ASTP handles the persistence, integrity verification, and coordination of agent state transitions.

📖 **New to ASTP?** Start with the [Glossary](https://github.com/scorched-earth-labs/astp/blob/main/GLOSSARY.md) — every term used in the spec and code, defined once with explicit structural relationships (e.g. how `EpisodeNode` relates to `CognitiveNode` + `EpisodePayload`).

**Current version:** the `**Version:**` field at the top of [`SPEC.md`](https://github.com/scorched-earth-labs/astp/blob/main/SPEC.md) is the protocol version (it is not restated here, so it can't drift). Versioning policy: [`VERSIONING.md`](https://github.com/scorched-earth-labs/astp/blob/main/VERSIONING.md). Change history: [`CHANGELOG.md`](https://github.com/scorched-earth-labs/astp/blob/main/CHANGELOG.md).

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
    ├── base.py              # ASTPAdapter + StructuralStore contracts
    └── memory.py            # InMemoryStore — the reference implementation of both
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

Any database can serve as an ASTP backend by implementing the `ASTPAdapter` interface:

```python
from astp.adapters.base import ASTPAdapter

class MyDatabaseAdapter(ASTPAdapter):
    # Implement the ASI methods
    ...
```

A conforming adapter must:

1. Enforce every governance rule (`G-*`) defined in `SPEC.md`
2. Preserve hash chain integrity — never modify `content_hash`, `spine_hash`, or `episode_root_hash` after creation
3. Respect write ordering invariants across stores
4. Support idempotent writes for WIL recovery
5. Fail loudly on errors — never silently swallow writes

The operations layer — branch, fork, merge, aside, soliloquy, cross-episode linking, grouping, coherence, the audit chain — reads and writes through a second, synchronous contract, `StructuralStore` (also in `astp.adapters.base`), and names no store of its own. An implementation supplies one. `astp.adapters.memory.InMemoryStore` implements both contracts over plain dicts — the reference implementation, and the store the protocol's own tests run the operations against. The protocol names no storage provider: a graph database, a relational store or anything else is a deployment's choice behind these two contracts. See `SPEC.md` for the full conformance requirements.

---

## Conformance Testing

What exists today:

- **Conformance requirement documents** — the `CONFORMANCE*.md` files listed under **Specification Documents** below. Each vector states its inputs and the property a conforming implementation must exhibit, by requirement class (REQUIRED / RECOMMENDED).
- **The reference test suite** — `tests/`, run with `pytest`. It exercises the reference implementation against those documents and guards the spec-to-code agreements (operation register, lifecycle states, namespace firewall, wire constants).

- **Machine-readable vectors** — [`vectors/6.0.0/context-commitment.json`](https://github.com/scorched-earth-labs/astp/blob/main/vectors/6.0.0/context-commitment.json): pinned expected digests for every 6.0.0 context-commitment construction (entry hash, content commitments, manifest, Episode root version 3, inclusion proofs, erasure tombstone), generated over the ratified 5.0.0 Episode; and [`vectors/5.0.0/seal-constructions.json`](https://github.com/scorched-earth-labs/astp/blob/main/vectors/5.0.0/seal-constructions.json): pinned expected digests for every 5.0.0 construction (leaf hash, spine, sets, Episode root, inclusion proofs, canonical JSON, audit records, side-channel and link hashes, witness and anchor commitments), generated by `vectors/5.0.0/generate.py` and checked by the reference tests against a from-prose reference that imports nothing from the package.

What does not exist yet: an adapter-parameterized harness that a third-party implementation can run against those vectors. Until it does, conformance is demonstrated by reproducing the vector digests and showing the properties the `CONFORMANCE*.md` documents require.

---

## Installation

Requires Python >= 3.11. The distribution name and the import name are both `astp`.

The package is not yet published to a package index. Install from a checkout:

```bash
pip install -e ".[dev]"         # editable install with test dependencies
pytest                          # run the reference test suite
```

```python
import astp
```

---

## Status

**6.0.0.** The protocol is ratified at 6.0.0 (Episode of Record `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8`, [`docs/RATIFICATION-6.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-6.0.0.md)): a sealed Episode now proves what its agents were *given* — a context manifest as the sixth field of the Episode root under `spine_algorithm_version` 3 — and the seal proves history, not retention: content behind a sealed pointer can be lawfully erased with a witnessed tombstone and no sealed value moves. The reference package implements the constructions (`astp.core.context_v1`), the store contract and operations (`astp.core.context_operations`, package 2.1.0) and the proof of record's sixth field; the reference deployment writes context entries and has sealed under version 3 since 2026-09-23 ([`IMPLEMENTATION-CONTEXT.md`](https://github.com/scorched-earth-labs/astp/blob/main/IMPLEMENTATION-CONTEXT.md) §7).

**5.1.0.** The protocol was ratified at 5.0.0 (Episode of Record `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`) and at 5.1.0 the reference deployment (Ignis OS, cutover 2026-09-19) seals under `spine_algorithm_version` 2 — `astp.core.seal_v2.compute_episode_seal_v2` over the adapter's `seal_inputs` reader — with no feature flag and nothing swallowed. A version 2 seal takes its identifiers from the `SealV2` result; `astp.core.schema.SPINE_ALGORITHM_VERSION_CURRENT` names the retained version 1 construction and reads `1` by design. Every construction has machine-readable vectors. The protocol specification is in `SPEC.md`.

The first consumer of this protocol is Ignis OS, Scorched Earth Labs' agent runtime, and integration tests for the reference adapter run there rather than in this repository. Not recommended for production use elsewhere until the first stable release.

---

## Amendments

Protocol amendments are ratified in a designated Episode of Record and reference the Episode's spine hash for provenance. The Episode of Record is the cryptographic anchor; the document is the human-readable artifact. The Episode of Record for 4.0.0 is `458fb62b-faee-4e42-9f92-c63187c1b59a`; its sealed root reproduces from its stored nodes. The Episode of Record for 5.0.0 is `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`, sealed 2026-09-18; it ratifies `SPEC.md` by content digest ([`docs/RATIFICATION-5.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-5.0.0.md)). The Episode of Record for 6.0.0 is `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8`, sealed 2026-09-22; it ratifies the context-commitment amendment and its vectors by content digest ([`docs/RATIFICATION-6.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-6.0.0.md)). The Episode of Record for `PROTOCOL-CONFORMANCE.md` 1.0.0 is `19d4390f-ac46-4840-bc9a-f419c6626fb4`, sealed 2026-10-01 under `spine_algorithm_version` 3; it ratifies the conformance definition by content digest and is itself a conforming record under it ([`docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md)). The Episode of Record for `SPEC.md` 6.0.2 as a whole document is `46490010-e8a7-4d79-8092-a1a82de3c93f`, sealed 2026-10-01 under `spine_algorithm_version` 3; it ratifies the specification by the same digest `PATENTS.md` §4.1 pledges against, together with `PROTOCOL-CONFORMANCE.md` 1.0.1 ([`docs/RATIFICATION-SPEC-6.0.2.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-SPEC-6.0.2.md)). The Episode of Record for `PATENTS.md` 1.0.0, the first versioned text of the patent policy, is `df3434bd-6936-441c-a896-254149f2bd48`, sealed 2026-10-01 under `spine_algorithm_version` 3 ([`docs/RATIFICATION-PATENTS-1.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-PATENTS-1.0.0.md)). Exported proofs of record for all six — files a third party verifies with this package alone (`python -m astp.core.proof_of_record verify <file>`) — are published under [`docs/proofs/`](https://github.com/scorched-earth-labs/astp/tree/main/docs/proofs/). As of the **v3.2.1 integration pass**, both prior amendments are folded into the SPEC body — the amendment documents are retained for provenance only and are no longer normative. Amendment documents retain their authoring numerals; the canonical SPEC version per [`VERSIONING.md`](https://github.com/scorched-earth-labs/astp/blob/main/VERSIONING.md) is shown alongside.

| Amendment | SPEC version | Status | Now in SPEC | Document (historical) |
|-----------|--------------|--------|-------------|-----------------------|
| v2.0 — Cross-Episode Linking & Grouping Interface | v3.0.0 | Integrated into SPEC body (v3.2.1) | [§20](https://github.com/scorched-earth-labs/astp/blob/main/SPEC.md) | [`AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/history/AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md) |
| v3.0 — Layer 3 Workflow & Execution DAG Codification | v3.1.0 | Integrated into SPEC body (v3.2.1) | [§21](https://github.com/scorched-earth-labs/astp/blob/main/SPEC.md) | [`AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/history/AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md) |

**SPEC v3.0.0 (cross-episode linking, MAJOR)** introduces typed cross-episode links, an EpisodeGrouping interface (with `MembershipRecord` as the protocol-owned artifact), succession-chain governance for `MembershipRecord` and `ConformanceDeclaration`, audit-the-decision pattern for behavioral-tier implementation choices (§12), and a three-tier conformance taxonomy (wire / state / behavioral). Breaking hash preimage changes on three node types — see Appendix A of the amendment for the full breaking-change reference.

**SPEC v3.1.0 (Layer 3, MINOR)** formalizes the three-Merkle-layer model and codifies Layer 3 — `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation`. Layer 3 is cryptographically isolated from Spine integrity by construction (Layer 3 nodes reference Layers 1/2 by ID only; never participate in Spine hashing), so no future Layer-3 change can force a MAJOR bump on Spine grounds. Each Layer 3 node type has a designated Cognitive Implementation Authority (CIA) — sole-writer guarantee as a wire-tier conformance principle.

Each feature surface (§19, §20, §21) has a companion implementation guide and conformance document, listed below. Ratification history: 4.0.0 (`458fb62b-faee-4e42-9f92-c63187c1b59a`), 5.0.0 (`ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`, [`docs/RATIFICATION-5.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-5.0.0.md)), 6.0.0 (`80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8`, [`docs/RATIFICATION-6.0.0.md`](https://github.com/scorched-earth-labs/astp/blob/main/docs/RATIFICATION-6.0.0.md)).

---

## Specification Documents

The protocol is one normative document (`SPEC.md`) plus, per feature surface, a conformance document (test vectors stated as inputs and required properties, with pinned expected digests in `vectors/`).

| Surface | SPEC | Implementation guide | Conformance vectors |
|---------|------|----------------------|---------------------|
| Branch / Fork / Merge + **Departure Fork** | §19 | — | [`CONFORMANCE-BFM.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-BFM.md) |
| Cross-Episode Linking & Grouping | §20 | — | [`CONFORMANCE-CROSS-EPISODE-LINKING.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-CROSS-EPISODE-LINKING.md) |
| Layer 3 — Workflow & Execution DAG | §21 | — | [`CONFORMANCE-LAYER3.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-LAYER3.md) |
| Reproducibility — spine leaf set, episode root, version identifiers | §5.6–§5.8, §9.3, G-1 | — | [`CONFORMANCE-REPRODUCIBILITY.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-REPRODUCIBILITY.md) |
| Trust Infrastructure — keys, anchoring, witnesses, chain proofs | §16 | [`IMPLEMENTATION-PHASE3.md`](https://github.com/scorched-earth-labs/astp/blob/main/IMPLEMENTATION-PHASE3.md) | [`CONFORMANCE-TRUST.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-TRUST.md) |
| Seal constructions — encoding, leaf hash, spine, manifests, Episode root, inclusion proofs | §5, §9.2 | — | [`CONFORMANCE-REPRODUCIBILITY.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-REPRODUCIBILITY.md) RP-009–011, [`vectors/5.0.0/`](https://github.com/scorched-earth-labs/astp/tree/main/vectors/5.0.0/) |
| Context commitment — context entries, content commitments, context manifest, Episode root version 3, erasure | §4.8, §4.9, §5.7.3, G-41–G-43 | [`IMPLEMENTATION-CONTEXT.md`](https://github.com/scorched-earth-labs/astp/blob/main/IMPLEMENTATION-CONTEXT.md) | [`CONFORMANCE-CONTEXT.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONFORMANCE-CONTEXT.md) CM-001–010, [`vectors/6.0.0/`](https://github.com/scorched-earth-labs/astp/tree/main/vectors/6.0.0/) |

What a Conforming Implementation is — the profiles, the governance rules each carries, and how conformance is demonstrated and claimed: [`PROTOCOL-CONFORMANCE.md`](https://github.com/scorched-earth-labs/astp/blob/main/PROTOCOL-CONFORMANCE.md) 1.0.1, ratified in Episode of Record `46490010-e8a7-4d79-8092-a1a82de3c93f`.

Supporting: [`VERSIONING.md`](https://github.com/scorched-earth-labs/astp/blob/main/VERSIONING.md) (canonical version policy), [`GLOSSARY.md`](https://github.com/scorched-earth-labs/astp/blob/main/GLOSSARY.md), [`CHANGELOG.md`](https://github.com/scorched-earth-labs/astp/blob/main/CHANGELOG.md).

Historical, retained for provenance only and not to be implemented from: [`docs/history/`](https://github.com/scorched-earth-labs/astp/tree/main/docs/history/) — prior major-version specifications (`SPEC-v1.md`, `SPEC-v3.md`, `SPEC-v4.md`, `SPEC-v5.md`), the two former amendment documents, the ratified amendment drafts from which 5.0.0 and 6.0.0 were folded, and the original architecture vision (`VISION.md`).

---

## Versioning

ASTP follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`:

- **MAJOR** — changes to canonical form (hash preimages, serialization, required fields). Conformance-breaking.
- **MINOR** — additive surface (new optional node types, new query surface, new fields with safe defaults). Existing implementations remain conformant.
- **PATCH** — errata, clarifications, ambiguity resolution. No semantic change.

`SPEC.md` is the canonical version source — the `Version:` field at the top of that file IS the protocol version. Implementation guides, conformance documents, and amendments are versioned-against (they describe behavior at a specific protocol version), not versioned-independently.

Full policy: [`VERSIONING.md`](https://github.com/scorched-earth-labs/astp/blob/main/VERSIONING.md). Change history: [`CHANGELOG.md`](https://github.com/scorched-earth-labs/astp/blob/main/CHANGELOG.md).

---

## License

Apache-2.0. Copyright 2026 Scorched Earth Labs, LLC.

The specification text and the code in this repository are both licensed under Apache-2.0; see [`LICENSE.txt`](https://github.com/scorched-earth-labs/astp/blob/main/LICENSE.txt).

The Apache license was chosen deliberately for its explicit grant terms. Attribution notices are in [`NOTICE`](https://github.com/scorched-earth-labs/astp/blob/main/NOTICE).

A patent pledge to Conforming Implementations, separate from the Apache license, is set out in [`PATENTS.md`](https://github.com/scorched-earth-labs/astp/blob/main/PATENTS.md); that document, not this summary, states its terms. Contributions are made under the Developer Certificate of Origin ([`CONTRIBUTING.md`](https://github.com/scorched-earth-labs/astp/blob/main/CONTRIBUTING.md#certificate-of-origin)).

---

## Developed By

[Scorched Earth Labs](https://scorchedearthlabs.com)
