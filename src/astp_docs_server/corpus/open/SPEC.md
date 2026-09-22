# ASTP — AI State Tree Protocol Specification

**Version:** 5.2.0
**Status:** Stable — ratified in Episode of Record `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28` (below)
**Authors:** Scorched Earth Labs
**Date:** 2026-09-22
**Supersedes:** [`SPEC-v4.md`](./docs/history/SPEC-v4.md) (4.5.0); earlier, [`SPEC-v3.md`](./docs/history/SPEC-v3.md) (3.5.1) and [`SPEC-v1.md`](./docs/history/SPEC-v1.md) (0.1.0-draft)
**Change history:** [`CHANGELOG.md`](./CHANGELOG.md)
**Versioning policy:** [`VERSIONING.md`](./VERSIONING.md)
**Term definitions:** [`GLOSSARY.md`](./GLOSSARY.md)

The full normative protocol is defined in this document's body. The `Version` field above is the protocol version; what changed in each release is recorded in `CHANGELOG.md` and is not restated here.

**Former amendment documents.** Cross-episode linking and grouping, and the Layer 3 Workflow & Execution DAG, were first written as standalone amendments and were folded into this document at 3.2.1 as §20 and §21. §20 and §21 are normative. The amendment documents ([`AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`](./docs/history/AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md), [`AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`](./docs/history/AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md)) are retained under `docs/history/` for provenance only; do not implement from them. Their filenames keep their authoring numerals; under `VERSIONING.md` they correspond to SPEC 3.0.0 and 3.1.0 respectively.

**What 5.0.0 is.** Every construction the 4.x line built — leaf hash, spine, Episode root, inclusion proof, audit record, the side-channel and cross-Episode content hashes, witness and anchor commitments — is replaced by a **new versioned construction**, and every rule written for a human reader is restated as one a verifier can execute against stored state. The discipline the constructions now share: **every commitment binds exactly its claim, and every rule is executable against stored state.** Nothing sealed under 4.x becomes unverifiable: the 4.x constructions are retained in this document as the definitions of the versions that produced those seals, selected by the §5.8 identifiers. The deliberation is recorded in design Episode `4b9a779e-be46-4d61-872e-fd76545aa901`; the reference vectors are [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json).

**Episode of Record.** `VERSIONING.md` requires a ratifying Episode of Record for each MAJOR release. The Episode of Record for 5.0.0 is `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28` ("5.0.0 Episode of Record", sealed 2026-09-18 under `spine_algorithm_version` 1, `episode_root_hash` `3649bff4b96a17c99bb108ec23f4e6f8e41a455d9d38c98d6f32111800afe48a`). It ratifies the text of this document at commit `44f764e` by content digest — SHA3-256 `c2e13d0ee60f7db95d185ec2f8079d38c9f087f7168a3b613aada6bc0a6b8a8d` of the `-draft`-suffixed file; the suffix was stripped and this paragraph written after the seal, and no normative sentence changed ([`docs/RATIFICATION-5.0.0.md`](./docs/RATIFICATION-5.0.0.md)). The Episode of Record for 4.0.0 is `458fb62b-faee-4e42-9f92-c63187c1b59a` ("Episode of Record — ASTP 4.0.0 ledgering obligations (G-39)", sealed 2026-08-22 under `spine_algorithm_version` 1, `ordering_version` 1). Its sealed root reproduces from its stored nodes. Exported proofs of record for both Episodes, verifiable with this package alone, are published under [`docs/proofs/`](./docs/proofs/).

**Conventions.** The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119] [RFC 8174] when, and only when, they appear in all capitals, as shown here.

## 1. Abstract

ASTP (the AI State Tree Protocol) is a cognitive persistence protocol for multi-agent AI systems. It provides a standardized, verifiable record of agent state transitions — what agents did, what state resulted, and cryptographic proof that the record hasn't been tampered with. ASTP is developed internally as Project Ariadne; that name persists in the reference implementation's code and identifiers.

The protocol is agnostic to both cognitive architecture and node type. A system using BDI, ReAct, chain-of-thought, SOAR, or any other reasoning model can implement ASTP without inheriting assumptions about how agents think. ASTP records *that* agents reasoned and *what* resulted — not *how* they reasoned.

**v2 core change:** The protocol primitive is `CognitiveNode`, not `Episode`. Episodes are the first *parameterization* of the protocol, not a precondition of it. Future node types (signals, agents, artifacts) slot into the same framework with zero protocol-layer changes.

## 2. Terminology

| Term | Definition |
|------|-----------|
| **CognitiveNode** | The universal protocol primitive. All cognitive state is represented as CognitiveNodes with type-specific payloads. |
| **NodePayload** | Abstract interface for node-type-specific data. The protocol calls `validate()` and `to_content_hash_input()` — never inspects internals. |
| **Episode** | A bounded unit of agent work. The Phase 1 node type. Implemented as `CognitiveNode` with `node_type="episode"` and `EpisodePayload`. |
| **Segment** | An ordered, immutable content unit within an episode. |
| **Spine** | The ordered hash chain of leaf hashes within a cognitive node tree. The Merkle root of the spine is the node's integrity fingerprint. |
| **Seal** | A cryptographic commitment that freezes a cognitive node. |
| **Crystallization** | A protocol-level state transition that captures a point-in-time integrity snapshot. Immutable once written. |
| **WIL** | Write Intent Log. A coordination protocol for multi-store writes that guarantees ordering and recoverability. |
| **Dual Index** | The separation of `sequence_index` (immutable temporal position, in hash) from `tree_leaf_index` (mutable structural position, NOT in hash). The epistemological core of v2. |
| **HITLEventNode** | A first-class node representing a human-in-the-loop decision gate. Two-phase lifecycle: INVOKED (gate raised) → RESOLVED/TIMED_OUT/ESCALATED (concluded). Its `node_hash` commits the decision (§4.6); it is not a spine leaf, and in a terminal state it is a structural-manifest member (§5.7.1). |
| **HITL Gate** | An edge from an Episode to an HITLEventNode. Typed as BLOCKS (approval required) or FOLLOWS (advisory review). |
| **Causal Anchor** | A node whose hash records an authorization that later Segments rely on. A resolved `HITLEventNode` is a causal anchor: its `node_hash` binds the invocation context to the human decision (§4.6), and Segments written under a pending gate reference it by ID. A causal anchor is not a spine leaf. Under `spine_algorithm_version` 2 a concluded HITL event is a structural-manifest member (§5.7.1), so the anchor is committed into the Episode root; under `spine_algorithm_version` 0 and 1 no sealed root commits to it (§5.6, retained form). |
| **Adapter** | A database-specific implementation of persistence operations. |
| **ASI** | Adapter Service Interface. The abstract contract any conforming adapter must implement. |
| **Governance Rule** | A protocol invariant that any conforming implementation must enforce. |
| **Namespace Firewall** | The inviolable rule that the protocol layer (`astp.protocol.*`) never imports from node-type layers (`astp.nodes.*`). |
| **Protocol Surface** | The set of primitives, invariants, and interfaces where no differential is permitted across conforming implementations. |
| **Implementation Space** | Architectural choices where conforming implementations MAY differ (payload schemas, storage adapters, signing algorithms, etc.). |

### 2.5 Protocol vs. Implementation Boundary

ASTP is a **protocol**, not an implementation. This distinction is load-bearing.

#### 2.5.1 The Differential Principle

A conforming ASTP implementation may make architectural choices — about agent reasoning models, storage backends, key management infrastructure, payload schemas, and operational policies — that differ from other conforming implementations. These are **implementation differentials**: legitimate variation that the protocol explicitly accommodates.

The protocol surface is the set of primitives, invariants, and interfaces where no differential is permitted. Deviation from the protocol surface produces a non-conforming implementation that cannot interoperate with or be verified by other conforming implementations.

#### 2.5.2 Protocol Surface (Non-Negotiable)

| Element | Constraint |
|---------|-----------|
| `CognitiveNode` schema (core fields) | Fixed. Field names, types, and semantics are immutable within a major version. |
| `NodePayload` interface | `validate()` and `to_content_hash_input()` are the only protocol-layer calls. The protocol NEVER inspects payload internals. |
| Leaf hash construction | SHA3-256 over the canonical field encoding of §5.1.1 with the position-binding preimage of §5.2. Field order, encoding and algorithm are fixed per `hash_version`. |
| Spine Merkle algorithm | SHA3-256 binary Merkle tree with per-version domain prefixes (§5.3) and deterministic leaf ordering by `sequence_index`, selected by `spine_algorithm_version`. |
| `spine_root` semantics | The Merkle root of the Episode's non-ephemeral Segments' leaf hashes in `sequence_index` order (§5.6). |
| `ContentDelta` / `StructuralDelta` structure | Core fields (`pre_root`, `post_root`, `delta_type`) are fixed. |
| Governance rules G-1 through G-40 | All conforming implementations enforce all protocol-mandatory governance rules. |
| Dual Index semantics | `sequence_index` is immutable and in the leaf hash. `tree_leaf_index` is mutable and NOT in the leaf hash. |
| Namespace Firewall | Protocol layer never imports from node-type layers. |

#### 2.5.3 Implementation Space (Differential-Permitted)

| Element | Permitted Variation |
|---------|-------------------|
| `NodePayload` schemas | Each node type defines its own payload schema. The protocol does not constrain payload content beyond the interface contract. |
| Storage adapter | Any conforming ASI implementation. |
| Key management infrastructure | HSM, KMS, software keystore, distributed threshold — implementation choice. |
| Signing algorithms | The protocol specifies the data to be signed **and** the scheme: Ed25519 over the 32 raw bytes of the commitment being signed (§4.6, §16.4). `ed25519` is the one registered scheme; the registry is extensible by amendment. |
| Transparency log target | Abstract `TransparencyLogAdapter` interface. Implementations choose the log. |
| Counter-signature policy | `min_counter_signatures` is a workspace-level configuration, not a protocol invariant. |
| Logical clock implementation | The protocol requires monotonic logical timestamps; the clock mechanism is implementation-defined. |
| Agent identity representation | The protocol requires an `agent_id` string; the identity system behind it is implementation-defined. |
| Cognitive architecture | BDI, ReAct, chain-of-thought, SOAR, or any other model. The protocol records outcomes, not reasoning mechanics. |

#### 2.5.4 Cross-Architecture Interoperability Guarantee

Two conforming implementations from different AI architectures MUST be able to:

1. **Verify each other's proofs.** An `InclusionProof` generated by Implementation A is verifiable by Implementation B using only protocol surface primitives.
2. **Traverse cross-node chains.** A proof chain linking nodes across implementations is valid if each link satisfies the leaf hash and spine root constraints.
3. **Agree on node identity.** `node_id` is a stable, architecture-independent identifier.

Interoperability does NOT require that implementations can read each other's payload content — only that they can verify the integrity and provenance of the node structure.

## 3. Architecture

### 3.1 The Three-Layer Model

```
PROTOCOL LAYER — Node-Generic (astp.protocol.*)
  CognitiveNode, CognitiveEdge, NodePayload ABC
  Position-binding leaf hash, Merkle tree, delta records, audit chain
  Governance rules, verification, version vectors
  → No Episode symbols. No episode_id. No session_bounds.

INSTANTIATION LAYER — Node Type Registry
  NodeTypeDefinition, open enum registration
  "episode" ← Phase 1    "signal" ← Phase 2    "agent" ← Phase 2

NODE TYPE LAYER — Type-Specific Extensions (astp.nodes.*)
  EpisodePayload implements NodePayload
  Episode lifecycle state machine
  → Dependency: Node Type Layer → Protocol Layer only. Never reverse.
```

### 3.2 The Namespace Firewall

The protocol layer MUST NOT import from any node-type layer. This boundary is enforced by automated testing (AST scan of all protocol-layer imports). Violations are CI failures, not warnings.

### 3.3 The Dual-Index Invariant

| Index | Type | Mutability | Meaning | In Hash Preimage |
|-------|------|-----------|---------|-----------------|
| `sequence_index` | `int` | **Immutable** | Nth cognitive event in this context | Yes |
| `tree_leaf_index` | `int` | Mutable | Current physical position in Merkle tree | **No** |

This separation enables tree rebalancing without breaking integrity. Changing `sequence_index` is equivalent to rewriting history — it is a protocol violation. Changing `tree_leaf_index` is a structural optimization with no integrity impact.

### 3.4 The Persistence Layer Model

The protocol defines three **persistence layers** — distinct from the code-architecture layering of §3.1. Each persistence layer is a separate cryptographic surface, owned by a distinct authority, and isolated from the others' hash integrity:

| Layer | Contents | Owner | Hash Participation |
|-------|----------|-------|-------------------|
| **Layer 1 — Merkle Spine** | EpisodeNode, IntentionNode, BeliefNode, SignalNode, and other cognitive primitives | Protocol kernel | Hash-chained, witness-signable, authoritative cognitive record |
| **Layer 2 — Episode Content** | Segments, BranchPoints, HITLEventNodes; the Episode spine tree (§5.6) | Protocol kernel | Anchored to Layer 1 via parent references |
| **Layer 3 — Workflow & Execution DAG** | WorkflowDeclaration, ExecutionNode, SkillInvocation | Cognitive Implementation Authority (per workspace, per node type — see §21 §3) | **Isolated**: Layer 3 nodes do NOT participate in Spine hash computation. Cross-layer references are by ID only. |

**Layer 3 is specified in §21 of this document.** The full Layer 3 surface — node schemas, hash preimage rules, immutability invariants, state machine, sole-writer principle (Cognitive Implementation Authority), and audit event types (`WORKFLOW_DECLARED`, `EXECUTION_RECORDED`, `SKILL_INVOKED`, `WORKFLOW_CLOSED`) — is normatively specified there. This section names Layer 3's existence and position in the persistence model; §21 is the authoritative reference for its semantics.

The two three-layer models — code-architecture (§3.1) and persistence (§3.4) — are **orthogonal**. The code-architecture layering governs what can import what (Protocol → Instantiation → Node Type, never reverse). The persistence layering governs what participates in which cryptographic structure. A given node type (e.g., `WorkflowDeclaration`) sits in the Node Type code-architecture layer AND in Persistence Layer 3 simultaneously; the two memberships describe different properties.

#### 3.4.1 Segment parentage is upward (to the episode), never lateral (to a sibling)

A Segment is Layer 2 content anchored to its Layer 1 `EpisodeNode`: a segment's `parent_node_id` is the **episode's** `node_id`. Segments therefore fan out from their episode — one parent reference each — and their relative order is carried entirely by `sequence_index`, which is immutable, part of the leaf-hash preimage (§5.2), and the key the Merkle spine orders by (§5.4).

There is **no segment→segment parent edge**, and none is needed. A `parent_node_id` pointing at the *preceding* segment would (a) bind a sibling, not the node's origin, into the immutable leaf hash — making "ordering" a hash-committed claim that diverges from `sequence_index` after any out-of-order insert, repair, or rebalance; and (b) hard-code a single successor, which a branch or fork cannot honor (a segment may have more than one successor across branches). Ordering already lives, authoritatively and twice, in `sequence_index` (on the node, in the leaf hash) — a parent chain can only ever be a third, un-hashed copy that is redundant-when-right and wrong-when-divergent.

A conforming implementation materializes this as one ordered containment edge per segment — e.g. `(Episode)-[:CONTAINS {sequence_index}]->(Segment)` — i.e. an ordered fan-out, not a linked list. If an explicit next/prev adjacency is wanted (e.g. for a visualization), **derive it at read time** by ordering on `sequence_index`; do not persist it as authoritative state.

> **Do not confuse this with proof-chain parentage (§16.5.3).** The chain-verification rule `B.parent_node_id == A.node_id` links *distinct cognitive nodes* into a causal proof chain (e.g. episode→episode) and is a cross-node construct. It says nothing about how segments order *within* an episode. Within-episode order is `sequence_index`; cross-node causal order is parent/cross-reference. These are two different uses of `parent_node_id` — keep them separate.

## 4. Data Model

### 4.1 CognitiveNode

The universal protocol primitive.

```
CognitiveNode {
  node_id:          UUID         (unique, immutable)
  node_type:        string       (open enum, validated via registry)
  schema_version:   string       ("2.0.0")
  sequence_index:   int          (IMMUTABLE — cognitive timeline position)
  tree_leaf_index:  int          (mutable — physical Merkle position)
  content_hash:     string       (SHA3-256 of payload)
  authored_by:      string       (agent identity)
  created_at:       datetime     (UTC)
  sealed_at:        datetime?    (null = unsealed)
  parent_node_id:   UUID?        (graph position anchor, IMMUTABLE)
  payload:          dict         (serialized NodePayload)
  leaf_hash:        string?      (computed once at creation, cached)
}
```

### 4.2 CognitiveEdge

A typed, directed edge between cognitive nodes.

```
CognitiveEdge {
  edge_id:          UUID
  edge_type:        string
  source_node_id:   UUID
  target_node_id:   UUID
  source_type:      string
  target_type:      string
  weight:           float
  created_at:       datetime
}
```

### 4.3 NodePayload Interface

Protocol code interacts with payloads through three methods only:

- `validate() -> None` — check type-specific invariants
- `to_content_hash_input() -> bytes` — deterministic byte representation
- `to_dict() -> dict` — serialization for storage

The protocol MUST NOT inspect payload fields directly.

### 4.4 Episode (Phase 1 Node Type)

`EpisodePayload` implements `NodePayload` with fields: title, context_note, episode_type, episode_mode, workspace_id, participants, segment_count, signal_reads.

#### 4.4.1 Episode Lifecycle States

An Episode is in exactly one of the following states. The set is closed: an
implementation MUST NOT persist an `episode_status` outside it.

| State | Meaning |
|-------|---------|
| `CREATED` | Node written; no content committed yet. |
| `ACTIVE` | Accepting segments and signals. The ordinary working state. |
| `PENDING_HITL` | A blocking human-in-the-loop gate is unresolved (§4.6). Advisory gates do not enter this state. |
| `CLOSING` | Closure initiated; final contributions still permitted. |
| `CLOSING_PENDING_SEAL` | All contributions in; grace period active before the record is fixed. |
| `CLOSED` | Closure recorded. Further content is admissible only as a codicil (`CODICIL_APPEND`, §12.4.1). |
| `CRYSTALLIZATION_PENDING` | The crystallization lock is held. A transient state, not a resting one. |
| `CRYSTALLIZED` | A crystallization completed and the episode was left in this state. |
| `SEALING` | Seal in progress. |
| `SEALED` | Sealed; the record is cryptographically fixed. |
| `ARCHIVED` | Retired from active use. Terminal. |

**Crystallization is a fact, not a state.** Whether an episode is crystallized
is determined by the existence of a `CrystallizationDelta`, not by
`episode_status`. An implementation MUST NOT infer crystallization from the
status field. `CRYSTALLIZED` therefore records only that a crystallization
concluded while the episode was in no other pending state; an implementation
MAY instead restore the status the episode held before acquiring the lock,
which is the correct behaviour when crystallizing mid-closure — an episode
being sealed must return to `CLOSING`, not to `CRYSTALLIZED`.

`CRYSTALLIZATION_PENDING` is the one state that blocks all content writes
without being a closure state; see §4.6 and G-18 for the HITL guard that refuses
to enter it.


### 4.5 Segment Metadata: signal_versions_read

Every segment carries an optional `signal_versions_read` field: a list of signal IDs that were visible in the Episode when the segment was written. This enables post-hoc stale-read detection — if a REASONING segment was written while referencing a signal that had already been superseded, the version mismatch is auditable after the fact.

`signal_versions_read` is **side-channel metadata**. It is NOT included in `content_hash` computation. The content hash covers only the segment's actual content; the signal version snapshot is recorded for audit purposes but does not affect integrity verification.

A conforming adapter SHOULD populate `signal_versions_read` at segment write time by querying current signal state for the Episode. Adapters MAY leave it empty if signal tracking is not supported.

### 4.6 HITLEventNode (Phase 4 — Human-in-the-Loop)

A first-class node type representing a human oversight decision within an episode. HITL events have a two-phase temporal structure — the gate is raised (INVOKED), a pending interval occurs, and the human resolves (RESOLVED/TIMED_OUT/ESCALATED).

```
HITLEventNode {
  hitl_event_id:          UUID         (unique, immutable)
  episode_id:             UUID
  hitl_request_id:        string       (FK to operational HITL store)
  schema_version:         string

  // Gate classification
  gate_type:              HITLGateType (APPROVAL_REQUIRED | REVIEW_ADVISORY | ESCALATION |
                                        COMPLIANCE_CHECKPOINT | MODIFICATION_REQUEST)
  status:                 HITLNodeStatus (INVOKED | RESOLVED | TIMED_OUT | ESCALATED)
  requesting_agent:       string

  // Phase 1 — Invocation (immutable after creation)
  invoked_at:             datetime (ms precision)
  timeout_at:             datetime?
  spine_snapshot_index:   int?         (spine state when gate was raised)

  // Phase 2 — Resolution (written on resolution)
  resolved_at:            datetime?
  decision:               HITLDecision (APPROVED | REJECTED | MODIFIED | DEFERRED | ESCALATED)
  resolved_by:            string?      (human principal identifier)
  rationale:              string?
  pending_duration_ms:    int?         (computed: resolved_at - invoked_at)

  // Integrity
  context_hash:           string       (SHA3-256 of invocation context)
  resolution_hash:        string?      (SHA3-256 of resolution payload)
  node_hash:              string?      (see Hash computation below)

  // Cryptographic attestation
  invocation_signature:   string?      (Ed25519 sig over context_hash, hex-encoded)
  invocation_key_fingerprint: string?  (SHA3-256 of agent public key)
  resolution_signature:   string?      (Ed25519 sig over resolution_hash, hex-encoded)
  resolution_key_fingerprint: string?  (SHA3-256 of human public key)
  key_derivation_version: int?         (§16.2.1: the derivation the signing keys used; 1 when absent)
}
```

**Hash computation (5.0.0).** The three constructions are those of the §5.7.1 member row, built from the field encoding of §5.1.1, each under its own prefix in the §5.1.3 registry:

- `context_hash = SHA3-256("HITL_CONTEXT:v2:" ‖ STRING(hitl_request_id) ‖ UUID(episode_id) ‖ STRING(gate_type) ‖ STRING(requesting_agent) ‖ TIMESTAMP(invoked_at) ‖ STRING(context_json))`
- `resolution_hash = SHA3-256("HITL_RESOLUTION:v2:" ‖ UUID(hitl_event_id) ‖ STRING(decision) ‖ STRING(resolved_by) ‖ TIMESTAMP(resolved_at) ‖ STRING|NULL(rationale))`
- `node_hash = SHA3-256("HITL_NODE:v2:" ‖ HASH(context_hash) ‖ HASH(resolution_hash))`

`node_hash` so computed is the structural-manifest member hash of a concluded event (§5.7.1). A version 2 seal computes it from the event's **stored fields** at seal time; it does not read a stored hash value, and an event stored without the fields the construction needs (its `context_json`, for one) cannot be sealed under version 2 (§15).

**4.x constructions (retained).** Events written under 4.x carry `context_hash = SHA3-256("HITL_CTX:" || request_id || episode_id || gate_type || agent || invoked_at || context_json)`, `resolution_hash = SHA3-256("HITL_RES:" || event_id || decision || resolved_by || resolved_at || rationale)` and `node_hash = SHA3-256("NODE:" || context_hash || resolution_hash)`, `||` being the 4.x text concatenation. They are retained as the definitions of those stored values and are never reused (§5.1.3); `NODE:` was shared with the 4.x Merkle interior node and the version 1 Episode root, a reuse 5.0.0 removed. No 4.x seal commits to any of them (§5.6, retained form).

**Two-layer signing model:**

1. **Agent invocation signature:** `Sign(agent_private_key, bytes.fromhex(context_hash))` — proves the agent created the gate.
2. **Human resolution signature:** `Sign(human_private_key, bytes.fromhex(resolution_hash))` — proves the human made the decision.

Both use the HKDF key hierarchy (§16.2) with `entity_type` parameter distinguishing agent from user key derivation paths.

**HITL_GATE edge:**

A directed edge from Episode to HITLEventNode with properties:
- `gate_type`: Classification of the HITL gate
- `blocking`: Boolean — whether the gate blocks episode progression
- `dependency`: `"BLOCKS"` (approval required) or `"FOLLOWS"` (advisory review)

**Spine participation:**

A resolved HITL event's `node_hash` is the record of the human decision. It is **not** a spine leaf: the spine is the Episode's non-ephemeral Segments and nothing else (§5.6), and resolving a gate does not change the spine root. Under `spine_algorithm_version` 2 a concluded event — `RESOLVED`, `TIMED_OUT` or `ESCALATED` — is a structural-manifest member, so its `node_hash` is committed into the Episode root and removing it changes that root (§5.7.1); an event still `INVOKED` is not a member. Under `spine_algorithm_version` 0 and 1 no sealed root commits to HITL events; §5.6 (retained form) states what that means for a verifier of a 4.x seal.

**Crystallization guard:**

An episode in `PENDING_HITL` status (blocking HITL gate open) cannot be crystallized. `acquire_crystallization_lock()` queries for unresolved HITLEventNode nodes before acquiring the lock. This is a hard protocol invariant — an episode with an outstanding human decision is an open episode.

**Advisory gates and CONDITIONALLY_VALID:**

Segments written while a `REVIEW_ADVISORY` gate is pending are tagged with `pending_hitl_ref` (the HITLEventNode ID). These segments are `CONDITIONALLY_VALID` — included in the spine but with a governance caveat. The advisory gate does not block episode progression.

**HITLEventNode is the only node type that permits post-creation mutation** — but only during the INVOKED → RESOLVED transition. All other transitions are immutable. This exception is enforced by G-17.

**Escalation concludes the gate.** `ESCALATED` is a terminal status: the resolution recorded is the escalation decision, and any further deliberation happens at a distinct gate raised with the higher authority, which references this one. `ESCALATED` and `RESOLVED` MUST remain distinguishable — whether a human decided here or passed the decision up is a fact about how the gate concluded — and a resolution writer MUST NOT record an escalation as `RESOLVED`.

**Timeout is a recorded event.** `TIMED_OUT` is a valid terminal status treated as implicit rejection. Orphaned pending decisions are not permitted — all HITL invocations must specify a timeout policy.

### 4.7 AttachmentNode

External content injected into an Episode's context — a file, an image, a
transcript, a fetched page — recorded so that the injection is verifiable after
the fact.

The protocol's concern is narrow: an Episode's reasoning was influenced by
content the Episode does not itself contain, and the record must show *what*
that content was, in a form that detects later change. Everything else about
the artifact is an implementation matter.

```
AttachmentNode {
  attachment_id:  UUID
  episode_id:     UUID
  content_hash:   string       (SHA3-256 of the attached content)
  media_type:     string?      (IANA media type, e.g. "image/png")
  content_ref:    string?      (implementation-defined locator)
  attached_by:    string       (agent_id or user_id)
  attached_at:    datetime
  schema_version: string
}
```

**Kind is a property, not a node type.** A document, an image and an audio file
are one node type distinguished by `media_type`. Defining separate node types
per artifact kind would contradict §1 — the protocol is agnostic to node type —
and would require a protocol revision for every new format an implementation
wants to attach.

**`content_hash` is over the attached content as received**, not over any
extraction of it. Text pulled out of a PDF is a derived representation; hashing
it would prove the extraction unchanged while leaving the PDF unverified.
Implementations that store an extraction MUST keep it separate from the hashed
content.

**`content_ref` is implementation-defined**, exactly as on a Segment.
The protocol does not constrain locator schemes and MUST NOT be read as
endorsing any particular storage or vendor.

An implementation MAY carry additional fields on its own attachment records —
original filename, byte size, source system, retrieval URL. Those are
implementation surface. They MUST NOT be relied upon by a verifier, and their
absence MUST NOT affect conformance.

Attaching produces an `ATTACHMENT_COMMIT` ledger entry (§12.4.1).

**What the seal covers.** An AttachmentNode is not a spine leaf and is not a
member of any Episode root component (§5.6, §5.7): it is in neither the signal
manifest, the structural manifest nor the exclusion set. Its `content_hash`
therefore detects **substitution** — a change to the attached bytes after the
fact — and that is what "verifiable after the fact" means in this section. No
sealed root detects the **addition or removal** of an AttachmentNode after the
seal; the `ATTACHMENT_COMMIT` entry is write coordination (§12), not a
tamper-evident chain, and does not close that gap. Binding attachments into the
Episode root would change its preimage and is a MAJOR change
([`VERSIONING.md`](./VERSIONING.md)); this version does not make it.

## 5. Hash Chain

### 5.1 Hash Algorithm

Every digest in this protocol is **SHA3-256** (FIPS 202): 32 bytes. In a preimage a digest is its 32 raw bytes (HASH, §5.1.1); in text — a stored `content_hash`, a seal record, a proof file — it is 64 lowercase hexadecimal characters, and a reader that meets uppercase normalizes before comparing. There is no other hash function, no truncation and no keyed variant. Every 5.0.0 construction — those with a prefix in §5.1.3 — is built from the field encoding of §5.1.1: **a construction differs from another only by its domain prefix and its fields.** The 4.x constructions retained in this document keep their own byte forms as the definitions of their versions. Two families of hash are outside this statement by judgment, not oversight: Layer 3's byte form is governed by §21 Part III §8, which does not lock a byte form and therefore claims no digest for §5.1 to govern; and the `MembershipRecord` and `ConformanceDeclaration` hashes of §20, which were not among the constructions 5.0.0 examined and are unchanged. The two non-digest primitives are named where they are used and nowhere else: HKDF-SHA3-256 for key derivation (§16.2) and Ed25519 over 32 raw digest bytes for every signature (§4.6, §16.4). Changing any of this is a MAJOR change ([`VERSIONING.md`](./VERSIONING.md)).

#### 5.1.1 Canonical field encoding

A construction built from named fields is `SHA3-256(prefix ‖ enc(f₁) ‖ … ‖ enc(fₙ))`: a domain prefix (the ASCII bytes shown, e.g. `LEAF_HASH:v2:`), then the fields in the order the construction lists them. Each field is a one-byte type tag followed by its payload:

| Tag | Type | Payload |
|---|---|---|
| `0x00` | NULL | none — an absent optional field |
| `0x01` | BYTES | `u32be(length)` ‖ bytes |
| `0x02` | STRING | `u32be(length)` ‖ UTF-8 of the text after Unicode NFC normalization |
| `0x03` | UINT | 8 bytes big-endian, 0 ≤ n < 2⁶⁴ |
| `0x04` | UUID | 16 bytes |
| `0x05` | TIMESTAMP | 8 bytes big-endian: whole milliseconds since 1970-01-01T00:00:00Z |
| `0x06` | HASH | 32 bytes — a SHA3-256 value, raw, never its hex text |
| `0x07` | LIST | `u32be(count)` ‖ the items in order, each encoded as a field of the one type the construction states for the list |
| `0x08` | BOOL | one byte: `0x00` false, `0x01` true |
| `0x09` | FLOAT | 8 bytes: IEEE 754 binary64, big-endian. The admissible set is exhaustive: NaN and ±∞ are refused before encoding (so no NaN payload ever enters a preimage), subnormals are encoded as-is, and −0 → +0 is the *only* normalization performed; the encoding is otherwise bit-faithful |

A TIMESTAMP MUST be computed from a timezone-aware instant, converted to UTC, in integer arithmetic; a value with no timezone MUST be refused. Sub-millisecond precision is truncated, and a record stores the timestamp at the precision it hashed. An absent optional field is NULL, which is distinct from an empty STRING and from the nil UUID. A field count is fixed by its construction, every field is self-delimiting, and no domain prefix in this document is a prefix of another, so distinct inputs cannot encode to the same bytes.

An order-independent **set of hashes** is `SHA3-256(prefix ‖ u32be(n) ‖ h₁ ‖ … ‖ hₙ)` over the distinct members, 32 raw bytes each, sorted ascending bytewise. The empty set is `n = 0`; there is no sentinel.

#### 5.1.2 Canonical JSON

Where a 5.0.0 construction's preimage contains a JSON document — an audit record's deltas (§8) — the bytes hashed are the document's canonical form: **RFC 8785** (JSON Canonicalization Scheme), with every string, object keys and values alike, first normalized to Unicode NFC. Concretely: object members sorted by key, keys compared as sequences of UTF-16 code units (RFC 8785 §3.2.3), no whitespace; strings in UTF-8 with only `"`, `\` and control characters below U+0020 escaped (the two-character escapes for backspace, form feed, newline, carriage return and tab, otherwise lowercase `\u00xx`); integers as digits; other numbers as ECMAScript `Number::toString` (RFC 8785 §3.2.2.3) — shortest round-tripping digits, negative zero as `0`, NaN and infinities refused; the literals `true`, `false`, `null`. Two keys that become equal after NFC make the document invalid; it MUST be refused, not merged.

**The canonical form is what is hashed and what is stored.** A record that hashes canonical JSON stores canonical JSON; a reader that hashes what it reads gets the writer's digest with no re-serialization step. A canonical document is a fixed point — canonicalizing it again yields the same bytes — and that is the check a verifier applies to a stored document before hashing it.

#### 5.1.3 Domain prefix registry

Each construction has exactly one prefix, used by no other construction, none a prefix of another. 5.0.0: `LEAF_HASH:v2:` · `TREE_LEAF:v2:` · `TREE_NODE:v2:` · `SIGNAL_MANIFEST:v2:` · `EXCLUSION:v2:` · `STRUCTURAL_MANIFEST:v1:` · `EPISODE_ROOT:v2:` · `BRANCH_POINT:v2:` · `BRANCH_TERMINUS:v2:` · `FORK_POINT:v2:` · `DEPARTURE_FORK_POINT:v2:` · `FORK_RETURN:v2:` · `MERGE_POINT:v2:` · `HITL_CONTEXT:v2:` · `HITL_RESOLUTION:v2:` · `HITL_NODE:v2:` · `AUDIT_RECORD:v2:` · `ASIDE:v2:` · `ASIDE_TERMINUS:v2:` · `SOLILOQUY:v2:` · `DELIBERATION_CHAIN:v2:` · `SOLILOQUY_CONCLUSION:v2:` · `LINK_SIGNAL:v2:` · `EPISODE_LINK:v2:` · `WITNESS_COMMITMENT:v2:` · `ANCHOR_COMMITMENT:v2:`. The 4.x prefixes (`LEAF:`, `NODE:`, `SIGNAL_MANIFEST:v1:`, `EXCLUSION:v1:`, `AUDIT:`, `ASIDE:`, `SOLILOQUY_PLACEHOLDER:`, `SOLILOQUY_FULL:`, `DELIBERATION_CHAIN:`, `SOLILOQUY_CONCLUSION:`, …) remain the prefixes of the 4.x constructions and are never reused. `FINGERPRINT:` is retired with no successor (§19.5).

### 5.2 Position-Binding Leaf Hash

The leaf hash binds identity, type, schema, position, content and graph position into a single commitment. It is computed once, at node creation, and never recomputed. `tree_leaf_index` is excluded (dual-index invariant, §3.3).

**`hash_version` 2 (current):**

```
leaf_hash = SHA3-256( "LEAF_HASH:v2:"
                      ‖ UUID(node_id) ‖ STRING(node_type) ‖ STRING(schema_version)
                      ‖ UINT(sequence_index) ‖ HASH(content_hash) ‖ UUID|NULL(parent_node_id) )
```

An absent parent is NULL, which cannot be confused with the nil UUID. `sealed_at` is not in the preimage: a leaf hash is computed at creation, when a node is unsealed; the seal record binds the seal.

**Segments created before 5.0.0.** A leaf hash is a function of a node's immutable fields, so an Episode containing Segments that predate 5.0.0 is sealed under 5.0.0 by computing their `hash_version` 2 leaf hashes **from their stored fields** at seal time. It MUST NOT be computed from a stored version 1 leaf hash: re-hashing a hash reproduces nothing.

**`node_id` MUST be generated with at least 122 bits of randomness** (UUIDv4 or equivalent) and MUST NOT be derived from the node's content or any other guessable input. This requirement is new in 5.0.0 and takes effect on ratification. `content_hash` is an unsalted hash of content; it is the unguessable `node_id` in this preimage that makes a published leaf hash useless for testing a guess at a Segment's content. From ratification on, the requirement reaches back through a seal that includes older Segments: if their `node_id`s do not meet it, the Episode's leaf hashes are not safe to publish.

#### 5.2.1 `hash_version` 1 (retained)

The construction every 4.x node carries. Retained as the definition of `hash_version` 1; nodes are never re-hashed.

```
leaf_hash = SHA3-256(
  node_id                              (16 bytes, UUID)
  len(node_type).to_bytes(4, "big")    (4 bytes, length prefix)
  node_type                            (variable, UTF-8)
  len(schema_version).to_bytes(4, "big")  (4 bytes, length prefix)
  schema_version                       (variable, UTF-8)
  sequence_index.to_bytes(8, "big")    (8 bytes, big-endian)
  content_hash                         (32 bytes, hex-decoded)
  sealed_at_ms.to_bytes(8, "big")      (8 bytes, Unix ms or 0)
  parent_node_id                       (16 bytes, UUID or 16 zero bytes)
)
```

Variable fields are length-prefixed; `sealed_at_ms` is 0 for an unsealed node and an absent parent is 16 zero bytes — which is why version 1 cannot distinguish "no parent" from "parent is the nil UUID", and why version 2 re-encodes the leaf rather than deleting a field. Because `sealed_at` is in the preimage and a node is unsealed at creation, every version 1 leaf hash of a later-sealed node fails to recompute from the sealed node's fields; a verifier of a 4.x seal computes it with `sealed_at_ms = 0`.

### 5.3 Domain Separation

Leaves and interior nodes of a tree are hashed under different prefixes, and every construction in this document has its own (§5.1.3). Under `spine_algorithm_version` 2 the tree prefixes are `TREE_LEAF:v2:` and `TREE_NODE:v2:`, and every hash value enters as **32 raw bytes**.

**`spine_algorithm_version` 0 and 1 (retained).** Leaf level `SHA3-256("LEAF:" ‖ x)`, interior `SHA3-256("NODE:" ‖ left ‖ right)`, where at every level a hash value is carried as its **64-character lowercase hexadecimal string** and what is concatenated is the ASCII encoding of that string — not the raw bytes. A leaf is SHA3-256 over 5 + 64 bytes and an interior node over 5 + 64 + 64 bytes. A verifier MUST derive the encoding from the version identifier — hex text under 0 and 1, raw bytes under 2 — never assume it.

### 5.4 Merkle Tree

A binary Merkle tree over a list of leaf inputs, in the order given. The algorithm is the same under every `spine_algorithm_version`; the versions differ in leaf input, encoding and prefixes (§5.3, §5.6):

1. Hash each input at the leaf level (§5.3). This is level 0.
2. To form the next level, take the current level's nodes in pairs from the left and hash each pair as an interior node. If the level has an odd number of nodes, the last node is **carried up unchanged** — it is not duplicated and not re-hashed.
3. Repeat until one node remains. That node is the root.

A tree with a single leaf has that leaf's level-0 hash as its root. **The root of an empty list is undefined**: an implementation MUST refuse to compute one, and an Episode with no spine leaf cannot be sealed.

```
spine_algorithm_version 2:   level 0   SHA3-256( "TREE_LEAF:v2:" ‖ input )         input: 32 raw bytes
                             interior  SHA3-256( "TREE_NODE:v2:" ‖ left ‖ right )   left, right: 32 raw bytes
```

The tree supports full construction from a leaf list, incremental append (O(log n)) and inclusion proofs (§9.2). It is node-type-agnostic: it operates on hash values only.

**One tree.** Under `spine_algorithm_version` 2 the Episode spine (§5.6), the tree of the five-test gate (§9) and the tree of chain-proof inclusion proofs (§16.5) are **the same tree over the same inputs** — the §5.2 leaf hashes — so an inclusion proof proves position in the sealed spine. Under versions 0 and 1 they were not: the spine took Segment *content hashes* while the proof tree took leaf hashes, and a 4.x `spine_root` is never a root over §5.2 leaf hashes.

### 5.5 Type Isolation Property

A CognitiveNode with `node_type="episode"` and one with `node_type="signal"` at the same `sequence_index` produce **different leaf hashes** because `node_type` is in the preimage.

### 5.6 Episode Spine Leaf Set

The spine of an Episode is the Merkle tree (§5.4) whose leaf inputs are the **`hash_version` 2 leaf hashes (§5.2) of the Episode's non-ephemeral Segments**, ordered by `sequence_index` (`ordering_version` 2). There is no other leaf.

- Segments whose `retention_tier` is `EPHEMERAL` (the epistemic record — PASS decisions, evaluation metadata) are **not** leaves; their content hashes enter the exclusion set (§5.7) so that what was left out is itself committed.
- **Signals are not spine leaves.** A signal is cross-episode linkage, not spine content; it commits through the signal manifest (§5.7).
- **Structural nodes are not spine leaves.** Branch, fork, departure-fork and merge points, and concluded human-in-the-loop events, commit through the structural manifest (§5.7.1). They have no `sequence_index`; as leaves they would need an ordering key they do not reliably have, which is the defect behind the 4.x tie-order seals. As a set, removing one changes the root and no ordering question arises.
- `sequence_index` is the **only** ordering key. It is unique per Episode by construction (§3.3; G-3), so the leaf order is total and needs no tiebreak.
- **No Episode-identifier leaf.** Each leaf binds its parent — the Episode — and the Episode root binds `episode_id` explicitly (§5.7). Under `spine_algorithm_version` 1 the leaf was the only thing that stopped a spine being transplanted; under 2 it is redundant and is dropped.

A verifier MUST be able to rebuild the spine root from the stored Segment nodes alone. Any construction that requires state not present on the nodes — insertion order, a store's default sort, a cache — is non-conformant (§9.3).

**What the spine root binds.** Under version 2 the spine root commits to each non-ephemeral Segment's identity, type, schema version, position, content and parent, and to their order — the leaf hash is the spine's input. `content_hash` remains an unsalted SHA3-256 of content; the leaf's unguessable `node_id` (§5.2) is what makes a published leaf hash safe.

**`spine_algorithm_version` 0 and 1 (retained).** The leaf inputs are the Segments' bare `content_hash` values (hex text, §5.3), in the order given by `ordering_version` (§5.8). Under version 1 the leaf list is preceded by one input that is not a node — `SHA3-256(episode_id)`, where `episode_id` is the Episode's identifier in its canonical string form, UTF-8 encoded, carried as a hex string like any other input, always first — which binds the root to the Episode; version 0 has no such leaf. **These roots commit to content and order only**: not to a Segment's `node_id`, `node_type`, `schema_version` or parent, so a Segment's identity is neither recoverable from nor protected by a 4.x spine root, and a published 4.x leaf list lets anyone test a guess at a Segment's content. Resolved HITL events, BranchPoints and the other structural nodes are not committed into any 4.x root: removing one changes no 4.x sealed root. These are properties of those constructions and are stated so that verifiers of 4.x seals do not assume otherwise.

### 5.7 Episode Root

The integrity commitment of a sealed Episode. **Version 2 (`spine_algorithm_version` 2):**

```
episode_root_hash = SHA3-256( "EPISODE_ROOT:v2:" ‖ UUID(episode_id)
                              ‖ HASH(spine_root) ‖ HASH(signal_manifest_hash)
                              ‖ HASH(structural_manifest_hash) ‖ HASH(exclusion_hash) )

signal_manifest_hash     = set( "SIGNAL_MANIFEST:v2:",     content_hash of each SPINE-placed Signal )
exclusion_hash           = set( "EXCLUSION:v2:",           content_hash of each EPHEMERAL Segment )
structural_manifest_hash = set( "STRUCTURAL_MANIFEST:v1:", member hashes — §5.7.1 )
```

`set(…)` is the order-independent set of §5.1.1. The manifests and the exclusion set are **sets**: membership binds, order does not; duplicated hashes collapse. `episode_id` is a UUID, as §4.1 requires; the root does not admit a string identifier, because identity bound by string equality is only as strong as the strings' encoding. An Episode whose identifier is not a UUID cannot be sealed under this construction and must say so (G-40).

`sealed_chain_root` on a `CrystallizationDelta` records the `spine_root`; `episode_root_hash` on the Episode records the composed root. Both MUST be persisted at seal, with the §5.8 identifiers.

#### 5.7.1 Structural manifest

**Membership rule.** A structural node is a member if and only if removing it would let a verifier be deceived about the Episode's branch, fork, merge or termination structure. The same rule decides fields: a field that makes a structural claim is in a member's preimage; commentary is not. `spine_merkle_snapshot` binds a divergence to the history it left from, and `merge_type` says how two histories combined — both are in. A `branch_label`, a `merge_summary` or a `synthesis_summary` is commentary: binding it would make an honest edit break a seal while proving nothing. Who initiated a branch, fork or merge, and who returned a fork, is provenance: binding actor identity is the audit chain's job (§8), and the manifest binding it for some nodes and not others, as 4.x did, has no principled defence. All of these are out. A `ForkOrphanMarker` (§19.3.7) is a diagnostic satellite and is not a member; a `CoherenceFingerprint` (§19.5) likewise.

**Named exception to the actor rule.** Actor identity *is* bound where the actor constitutes the construction's defining claim rather than the provenance of an operation on a structure that exists without them: the aside binds both of its parties (G-25 makes the human's presence its defining claim) and the soliloquy binds `initiated_by_agent` (§19.4). A later reader tightening this rule must not strip those: doing so hashes a weaker claim than the node makes.

Members, each under its own prefix (so the set needs no per-member type tag):

| Node | Member hash | Fields, in order |
|---|---|---|
| BranchPoint | `BRANCH_POINT:v2:` | UUID `branch_point_id`, UUID `episode_id`, UUID `branch_id`, UUID `source_segment_id`, HASH `spine_merkle_snapshot`, STRING `branch_type`, STRING `declaration_type`, TIMESTAMP `created_at`, HASH\|NULL `parent_hash` |
| BranchTerminus | `BRANCH_TERMINUS:v2:` | UUID `terminus_id`, UUID `branch_id`, STRING `terminus_type`, HASH `branch_point_hash`, HASH\|NULL `final_merkle_root`, TIMESTAMP `created_at` |
| ForkPoint | `FORK_POINT:v2:` | UUID `fork_point_id`, UUID `fork_id`, UUID `episode_id`, UUID `origin_episode_id`, UUID `origin_segment_id`, STRING `fork_objective`, UINT `sibling_index`, TIMESTAMP `created_at`, HASH\|NULL `parent_hash` |
| DepartureForkPoint | `DEPARTURE_FORK_POINT:v2:` | UUID `fork_point_id`, UUID `fork_id`, UUID `fork_episode_id`, UUID `origin_episode_id`, UUID `origin_segment_id`, STRING `fork_objective`, STRING `fork_creation_trigger`, HASH `spine_tip_hash_at_departure`, TIMESTAMP `created_at`, HASH\|NULL `parent_hash` |
| ForkReturn | `FORK_RETURN:v2:` | UUID `fork_return_id`, UUID `fork_id`, UUID `fork_episode_id`, UUID `origin_episode_id`, STRING `return_type`, HASH `fork_final_spine_tip_hash`, TIMESTAMP `created_at`, HASH\|NULL `parent_hash` |
| MergePoint | `MERGE_POINT:v2:` | UUID `merge_point_id`, UUID `merge_id`, UUID `source_episode_id`, UUID `target_episode_id`, HASH `source_merkle_root`, HASH `target_merkle_root_pre`, HASH `target_merkle_root_post`, UUID\|NULL `common_ancestor_id`, STRING `merge_type`, TIMESTAMP `created_at`, HASH\|NULL `parent_hash` |
| HITL event in a terminal state — `RESOLVED`, `TIMED_OUT` or `ESCALATED` | `HITL_NODE:v2:` | HASH `context_hash`, HASH `resolution_hash` — where `context_hash` = `HITL_CONTEXT:v2:` over STRING `hitl_request_id`, UUID `episode_id`, STRING `gate_type`, STRING `requesting_agent`, TIMESTAMP `invoked_at`, STRING `context_json`; and `resolution_hash` = `HITL_RESOLUTION:v2:` over UUID `hitl_event_id`, STRING `decision`, STRING `resolved_by`, TIMESTAMP `resolved_at`, STRING\|NULL `rationale` |

Relative to the 4.x node hashes the lists add `spine_merkle_snapshot` and `merge_type` and drop `initiated_by`, `initiator`, `returned_by` and `synthesis_summary`; the remaining fields keep their 4.x order. `parent_hash` is NULL at the head of a chain (4.x used the text `GENESIS`). A HITL event still `INVOKED` is not a member. `ESCALATED` is terminal: escalation concludes *this* gate — its resolution is the escalation decision — and any further deliberation happens at a distinct gate raised with the higher authority; `ESCALATED` and `RESOLVED` MUST remain distinguishable (§4.6). Removing any member changes `structural_manifest_hash` and therefore the Episode root. This is the anchoring path for human decisions: a concluded HITL event is not a spine leaf, and it is committed.

**A structural node created after a seal.** A sealed Episode root is immutable, so a node created after a seal is never a member of that seal's manifest. It is committed by the Episode's **next** crystallization — deltas chain — and it MUST carry a reference to the earlier seal it post-dates (its `episode_root_hash` and `sealed_at`). It is a member of the later root that *references* the earlier one, never of the earlier one, and the two MUST NOT be conflated. A structural node that is never committed into any root is not permitted: it would assert structure while bound to nothing. This governs the one retroactive write of §19.3.7.

#### 5.7.2 Episode root, version 1 (retained)

Under `spine_algorithm_version` 0 and 1 the Episode root is three-component:

```
episode_root_hash = SHA3-256("NODE:" || spine_root || signal_manifest_hash || exclusion_hash)
```

| Component | Over | Construction |
|---|---|---|
| `spine_root` | non-ephemeral Segments (§5.6, retained form) | Merkle root, `ordering_version` order |
| `signal_manifest_hash` | the Episode's SPINE-placed Signals | `SHA3-256("SIGNAL_MANIFEST:v1:" || sorted(content_hash) joined by "\|")`; empty set → `SHA3-256("SIGNAL_MANIFEST:v1:EMPTY")` |
| `exclusion_hash` | Segments excluded from the spine | `SHA3-256("EXCLUSION:v1:" || sorted(content_hash) joined by "\|")`; empty set → `SHA3-256("EXCLUSION:v1:EMPTY")` |

In all three a hash value is its 64-character lowercase hex string, ASCII-encoded, as in §5.3 (retained form). "sorted" is lexicographic order of those strings after de-duplication; the separator is the single byte `|`; the empty-set form hashes the prefix followed by the five bytes `EMPTY`. There is no structural manifest: no structural node is committed into a version 1 root.

### 5.8 Algorithm and Ordering Versions

Hash functions are never modified in place ([`VERSIONING.md`](./VERSIONING.md)); they are versioned, and a record says which version produced it. Three identifiers carry that:

| Field | On | Values | Meaning |
|---|---|---|---|
| `hash_version` | `CognitiveNode` | `1` · `2` (current) | which leaf-hash construction produced the node's leaf hash (§5.2). A node that lacks it is `1` |
| `spine_algorithm_version` | `CrystallizationDelta` | `0` · `1` · `2` (current) | which **seal construction** produced `sealed_chain_root` and `episode_root_hash` |
| `ordering_version` | `CrystallizationDelta` | `1` · `2` (current) | which leaf set and ordering produced `sealed_chain_root` |

**`spine_algorithm_version` 2 selects the entire seal construction** — leaf hash (`hash_version` 2), tree (§5.4), encoding (§5.3), sets and Episode root (§5.7) — not the tree alone. There is deliberately no separate identifier for the Episode root: a second identifier would make an invalid combination representable, and one identifier makes it unrepresentable. Read the name as *seal construction version*. Under version 2, `ordering_version` is necessarily 2.

| `spine_algorithm_version` | Leaf input | Encoding | Episode-identifier leaf | Episode root |
|---|---|---|---|---|
| `0` | Segment `content_hash`, ordered by `ordering_version` | hex text, `LEAF:` / `NODE:` | none | version 1 (§5.7.2) |
| `1` | Segment `content_hash`, ordered by `ordering_version` | hex text, `LEAF:` / `NODE:` | `SHA3-256(episode_id)` first | version 1 (§5.7.2) |
| `2` | `hash_version` 2 leaf hash, `sequence_index` order | raw bytes, `TREE_LEAF:v2:` / `TREE_NODE:v2:` | none | version 2 (§5.7) |

**`ordering_version`.**

| Value | Ordered inputs |
|---|---|
| `1` | the `content_hash` of each non-ephemeral Segment in `sequence_index` order, **followed by** the `content_hash` of each SPINE-placed Signal in order of arrival time |
| `2` | each non-ephemeral Segment in `sequence_index` order. Signals commit through the manifest (§5.7) |

`ordering_version` 1 does not determine a leaf order. Arrival time is not a total order — Signals can share a timestamp — and the order in which tied Signals were folded in at seal time is not recorded on any node. A seal made under `ordering_version` 1 whose Signals include such a tie can be reproduced only by trying the orderings of each tied group until one yields the stored root, or from a checked `resolved_signal_order` annotation (§5.8.1). That is the defect `ordering_version` 2 removes, and it is why §9.3 does not hold unconditionally for `ordering_version` 1 seals.

These identifiers are diagnostic metadata **outside every hash preimage**: a verifier reads them to select the reproduction function; altering them cannot make a tampered root verify, only cause a genuine one to fail. A record that lacks them was written before 4.3.0 and MUST be read as `spine_algorithm_version = 1`, `ordering_version = 1` unless the implementation's history says otherwise — the reference implementation's own seals before 2026-04-01 are version `0`. A verifier MUST refuse identifiers it does not know.

#### 5.8.1 `resolved_signal_order` (annotation)

A seal made under `ordering_version` 1 may depend on an order of same-timestamp Signals that no stored node records (above). An implementation that has established that order — typically by search, during a verification run — MAY record it on the `CrystallizationDelta` as `resolved_signal_order`: the `content_hash` values of the Episode's SPINE-placed Signals, in the order that reproduces `sealed_chain_root`.

This is an **annotation**, not a version identifier. An identifier names a construction; the annotation supplies an input that the named construction left undetermined. The rules that make it safe:

- **Outside every preimage.** It is not hashed, not signed and not part of any root. It cannot change what a seal proves.
- **Written by a verification run, never by a re-seal.** It records an observation about a seal that already exists.
- **Checked, never trusted.** A verifier MUST NOT use a `resolved_signal_order` unless (a) the listed hashes are exactly the Episode's stored SPINE-placed Signal hashes, in some order, and (b) recomputing the spine under the seal's §5.8 identifiers with that order reproduces `sealed_chain_root`. An annotation that fails either test MUST be ignored; the verifier proceeds as if none were present. A false annotation therefore cannot make a root verify — it can only fail to help.
- **`ordering_version` 1 only.** Under `ordering_version` 2 Signals are not spine leaves, so the annotation has no meaning: a verifier MUST ignore one found on such a seal.
- **No inference from absence.** The annotation saves a search; it adds no strength. A seal whose order is found by search is reproduced to exactly the same root as one whose order is recorded. A seal that reproduces under *no* order is a different matter — that is a root that cannot be rebuilt (§9.3), and no annotation can or should repair it.
- **Not for publication alongside roots alone.** The listed values are unsalted content hashes (§5.6). An exported proof that withholds the leaf list MUST withhold this annotation too.

Conforming implementations MUST write these fields on every new seal and MAY
backfill them on historical records from a verification run; a backfill is an
annotation, never a re-seal (a re-seal would itself be a post-closure mutation).

## 6. Governance Rules

These invariants MUST be enforced by any conforming implementation.

### G-1: Write Guard

No modifications to sealed nodes, **and no new children appended to them.** A
node with non-null `sealed_at` is frozen. For an Episode the record is fixed from
`CLOSING_PENDING_SEAL` onward (§4.4.1): an implementation MUST refuse a Segment
or Signal commit against an Episode in `CLOSING_PENDING_SEAL`, `CLOSED`,
`CRYSTALLIZATION_PENDING`, `SEALING`, `SEALED` or `ARCHIVED`. The codicil
(`CODICIL_APPEND`, §12.4.1) is the sole sanctioned post-closure append and uses
its own path. A refused commit is a governance event; if the implementation
ledgers refusals it does so outside the §12.4 register.

A seal MAY be established at any time at or after close (G-40): the write guard
takes effect at closure, not at the seal.

### G-2: Reparenting Prohibition

`parent_node_id` is immutable after creation. Reparenting is a governance violation, not a valid operation. A node's parentage is a fact about its origin.

**Correction path:** Create a new node with correct parentage. Issue a deprecation record on the original. The original's hash and position remain permanently in the audit trail.

### G-3: Sequence Monotonicity

New `sequence_index` values must be strictly greater than the current maximum. Non-monotonic sequence indices indicate either a bug or an insertion attack.

### G-4: Logical Clock Monotonicity

Logical clock values must be strictly monotonically increasing across audit records. A decreasing clock indicates backdating — either tampering or out-of-order insertion.

### G-5: Node Type Registration

`node_type` must be registered in the `NodeTypeRegistry` before a node can be created. Unregistered types are rejected.

### G-6: Namespace Firewall

The protocol layer (`astp.protocol.*`) MUST NOT import from any node-type layer (`astp.nodes.*`). This is enforced by automated testing.

### G-7 through G-9: Signal Governance (inherited from v1)

- **G-7:** Causal signals require a TRIGGERED edge to at least one segment
- **G-8:** Exchange entries require a prior initiation_hash on the consultation node
- **G-9:** Consultation resolution requires at least one exchange entry

### G-10: Structural Delta Content Invariant

A structural delta (rebalancing) that sets `sequence_indices_unchanged: false` is an integrity violation. Rebalancing must never alter logical ordering.

### G-11: Witness Threshold (Phase 3)

If a workspace declares `min_counter_signatures > 0` for a `node_type`, a node of that type MUST have at least that many **valid** (G-12) `WitnessRecord` entries before transitioning to SEALED state, counted as follows: the count is the size of a **maximum bipartite matching between distinct `witness_id` values and distinct `public_key_fingerprint` values over the valid records** — not a deduplication of names, not a deduplication of keys, and not a greedy pass, each of which under-counts and (for a greedy pass) depends on record order. One key cannot count twice under two names; one name cannot count twice under two keys. (A under k₁, A under k₂ and B under k₁ admit two witnesses — A/k₂ and B/k₁; a greedy pass that takes A/k₁ first finds one.) The protocol does not mandate a threshold value — this is workspace-configured (§16.4.5).

### G-12: Witness Validity (Phase 3)

A `WitnessRecord` is **valid** if and only if all of: its `commitment_hash` recomputes from its fields (§16.4.2); its `public_key_fingerprint` is the SHA3-256 of its `public_key`; its `signature` verifies under `public_key` over the 32 raw bytes of the commitment, under the registered scheme it names; and its `witness_id` is not the node's author (`authored_by`) — a party cannot witness its own claim, and a self-witness is not an attestation, not merely an uncounted one. A record failing any condition is recorded but never valid, and MUST NOT count toward any threshold. A verifier reports the first condition that failed. Whether the named key belongs to the named witness is the workspace key registry's question, outside this rule.

### G-13: Chain Root Integrity (Phase 3)

A `ProofChain` `chain_root` must equal `SHA3-256` of the concatenated `spine_root` values of all links in order. A chain with an incorrect `chain_root` is invalid regardless of individual link validity.

### G-14: Transparency Log Anchoring Timing (Phase 3)

Transparency log anchoring MUST occur at crystallization. Anchoring at other times is permitted but does not satisfy G-14.

### G-15: Key Version Monotonicity (Phase 3)

`NodeKeyRecord.key_version` MUST be monotonically non-decreasing for a given `node_id`. Key version rollback is a governance violation.

### G-16: Node Type in Key Derivation (Phase 3)

The HKDF `info` string for node key derivation MUST include `node_type`. Keys derived without `node_type` in the context are non-conforming. This prevents cross-type key confusion.

### G-17: HITL Invocation Before Resolution (Phase 4)

`resolution_hash` MUST NOT be set on an HITLEventNode in `INVOKED` status. Resolution data may only be written during the `INVOKED → RESOLVED/TIMED_OUT/ESCALATED` transition. An HITLEventNode is the only node type that permits post-creation mutation, and this mutation is constrained to the single-phase transition.

### G-18: HITL Crystallization Block (Phase 4)

An episode with any HITLEventNode in `INVOKED` status (for blocking gate types: `APPROVAL_REQUIRED`, `COMPLIANCE_CHECKPOINT`) MUST NOT transition to `CRYSTALLIZATION_PENDING`. The crystallization lock acquisition MUST query for pending HITL events and refuse if any exist. Advisory gates (`REVIEW_ADVISORY`) do not block crystallization.

### G-40: Sealed Requires a Record; Episode Identifiers Are UUIDs (5.0.0)

**Outcome-state invariant.** A node whose `sealed_at` is non-null MUST have a crystallization record bound to it: the `CrystallizationDelta` from which its roots reproduce under its recorded §5.8 identifiers. A `sealed_at` with no bound record is not a seal — it is a claim of fixity with nothing fixed — and a verifier MUST report it as `NO_CRYSTAL`, never as sealed. The rule is stated on the stored outcome, not on a code path: the case that produced it was application code swallowing a failed crystallization after the seal flag had been written, and a rule a verifier enforces against stored state catches that whatever path wrote it.

**Late seal.** A seal MAY be established at any time at or after close. `closed_at` records when the Episode was closed; `sealed_at` records when fixity was computed and is never back-dated; `sealed_at ≥ closed_at` is the only ordering constraint. A non-zero gap is valid and carries no adverse inference: the record was fixed later, and says so. An Episode closed with no Segments and no Signals is closed and unsealed, with nothing to fix.

**Episode identifiers.** An Episode identifier that is not a UUID MUST be refused where Episodes are created (§4.1). An Episode created under an earlier version with a non-UUID identifier is a well-formed `spine_algorithm_version` 1 Episode — version 1 hashes the identifier as text — and is sealed under version 1; it cannot be sealed under version 2 (§5.7). An implementation that holds such an Episode MUST seal it under version 1 before it closes the write boundary, because closing it first would strand the Episode unsealable.

## 7. Delta Records

Every state transition is recorded as a delta.

### 7.1 Content Delta

Records content mutations (segment appends, updates):
```
ContentDelta {
  delta_id, node_id, segment_id,
  sequence_index,                    (for verification)
  previous_content_hash, new_content_hash,
  pre_root, post_root,              (the CAS condition and result)
  wall_clock, logical_clock, author
}
```

### 7.2 Structural Delta

Records structural mutations (rebalancing):
```
StructuralDelta {
  delta_id, node_id, delta_type,
  sequence_indices_unchanged: bool,  (INVARIANT — must be true)
  pre_rebalance_root, post_rebalance_root,
  wall_clock, logical_clock, author
}
```

## 8. Tamper-Evident Audit Chain

The audit trail is a first-class data structure, independent of every seal: an integrity structure over what was *done* to a node, verified on its own. Each record links to the prior record's hash, so the trail is tamper-evident independently of the delta chain.

### 8.1 Audit record, version 2

One schema and one preimage, for every audit record in the protocol (the taxonomy records of §19.1.1 included):

```
record_hash = SHA3-256( "AUDIT_RECORD:v2:"
    ‖ UUID(audit_id)
    ‖ STRING(chain_key)                  the chain: an Episode's UUID as text, or a declared synthetic key
    ‖ UINT(delta_sequence)               1 for the first record of a chain, +1 per record, never reset
    ‖ STRING(delta_type)
    ‖ STRING(agent_id)
    ‖ STRING(session_id)
    ‖ STRING(human_actor) | NULL
    ‖ TIMESTAMP(wall_clock_time)         UTC, whole milliseconds — stored at that precision
    ‖ UINT(episode_time)                 logical clock
    ‖ BYTES(forward_delta)               canonical JSON (§5.1.2), UTF-8 — stored in that form
    ‖ BYTES(reverse_delta)               canonical JSON (§5.1.2), UTF-8 — stored in that form
    ‖ LIST(STRING)(affected_nodes)       identifiers as canonical text, in the order written
    ‖ STRING(trigger_context)
    ‖ STRING(explicit_reason) | NULL
    ‖ STRING(caught_by)
    ‖ BOOL(detection_window_open)
    ‖ HASH(prior_audit_hash) | NULL      NULL for the first record of a chain; there is no text sentinel
)
```

`chain_key` and `affected_nodes` are `STRING` and `LIST(STRING)` deliberately, not by oversight: the audit chain is outside every seal, and its integrity rests on the `record_hash` recurrence below, not on the identity-canonicality that §5.7's string-identity argument requires inside a seal. A synthetic key such as `declaration:<system>:<group>` is a conformant `chain_key`, and `affected_nodes` may list Episode identifiers beside node identifiers because that is what an operation touches. A `chain_key` is hashed as its `STRING` bytes like every other string: a UUID-shaped key gets no UUID treatment in the preimage — an Episode's chain is keyed by the UUID's canonical text, hashed as text.

Every field is bound. An absent optional field encodes as NULL, which is distinct from an empty string — `human_actor` unset and `human_actor` `""` are different records. The deltas enter as BYTES, not STRING: they are documents already in canonical form, hashed byte-exact, and a writer MUST refuse a delta text that is not its own canonical form. There is no `schema_version` field: the prefix carries the schema.

### 8.2 Chain verification

A chain is identified by `chain_key` and verified from its first record: `delta_sequence` runs 1, 2, 3, … without gap; the first record's `prior_audit_hash` is NULL; every later record's is the previous record's `record_hash`; every `record_hash` recomputes from the stored fields. A verifier reports the first record that fails and why. An empty chain verifies. Deletion, insertion, reordering and alteration of any field are each detected at the first affected record; the sequence rule makes a deletion visible even to a reader holding only sequence numbers, and the hash rule makes it visible to a reader holding only hashes.

A writer that cannot read the chain head MUST NOT emit a record with a guessed `prior_audit_hash` or `delta_sequence`; it fails the operation (§15). The 4.x reference helpers fell through to `1` and `"GENESIS"` on a query error, which manufactures a second genesis mid-chain; that fall-through is retired with them.

**Invariant.** Rollback creates a new forward record. The log is never edited in place — a reverse delta is written as a new audit record that references the original.

### 8.3 Audit records, 4.x (retained)

4.x carried two audit record forms — `AuditRecord { record_id, node_id, delta_id, delta_type, actor, actor_role, wall_clock, logical_clock, pre_state_hash, post_state_hash, delta_hash, prev_audit_hash, reason }` hashed as sorted JSON, and the §19.1.1 taxonomy record hashed as `SHA3-256("AUDIT:" ‖ colon-joined fields)` — both with the text `"GENESIS"` as the first link. Both are superseded by §8.1. Chains written under them remain verifiable by the 4.x constructions that wrote them, and are not rewritten; new chains are written under §8.1.

## 9. Verification

### 9.1 The Five-Test Gate

Any conforming implementation MUST detect all five classes of tampering:

| # | Attack | Detection Mechanism |
|---|--------|-------------------|
| 1 | Content tampering | `content_hash` changes → `leaf_hash` mismatch → root mismatch |
| 2 | Sequence index modification | `sequence_index` in leaf hash preimage → `leaf_hash` changes |
| 3 | Segment insertion/deletion | Leaf count changes → root mismatch; position gaps detected |
| 4 | Audit chain tampering | `prev_audit_hash` chain breaks at tampered record |
| 5 | Backdated wall_clock | Logical clock monotonicity violation |

A verifier catching only test 1 is a *content* integrity verifier. Tests 2-5 are required for *temporal* integrity. All five must pass.

### 9.2 Inclusion Proof

Under `spine_algorithm_version` 2 the spine and the proof tree are one tree (§5.4), so a position-binding inclusion proof proves position *in the sealed spine*.

```
InclusionProof {
  leaf_index    UINT     position of the leaf in the spine's leaf list
  leaf_count    UINT     number of leaves in that list
  leaf_hash     HASH     the hash_version 2 leaf hash being proven
  siblings      HASH[]   the sibling at each level where one exists, leaf level first
  spine_root    HASH     the root being proven against
}
```

**The prover does not state the path's shape.** From `leaf_index` and `leaf_count` a verifier derives, level by level, whether the node has a sibling (it has none exactly when it is the unpaired last node of its level, which is carried up unchanged) and on which side that sibling sits (a node at an even position is the left child). The verifier then: rejects the proof if `leaf_index` is out of range or the number of siblings is not the number the shape requires; hashes the leaf under `TREE_LEAF:v2:`; and at each level with a sibling computes `TREE_NODE:v2:` over left ‖ right in the derived order. The proof is valid if and only if the result equals `spine_root`.

**What a proof commits to.** The leaf, and its position: a sibling list verifies at no position other than the one the tree gave it, and no sibling can be altered. It does **not** commit to the tree's size — a `leaf_count` that yields the same path shape verifies too — so the number of leaves in a sealed spine is a claim of the seal record, not of any proof. This is deliberate: the seal record already makes that claim, reproducibly, and two mechanisms binding one fact can disagree; binding the count into the leaf hash would also make every leaf hash depend on the tree's eventual size, so no leaf hash could be final when its Segment was written. Each mechanism makes exactly one claim. A proof carries no content and no identifiers; it is safe to publish wherever the leaf hash it proves is.

`leaf_index` is not `sequence_index`: ephemeral Segments have a `sequence_index` but are not leaves. The leaf hash binds `sequence_index`; the path binds `leaf_index`; a verifier holding the Segment checks both.

**Proofs over `spine_algorithm_version` 0 and 1 trees (retained).** A proof over a 4.x tree is the 4.x form — `{ sequence_index, leaf_hash, merkle_path: Hash[], path_directions: str[], spine_root }` with hex-ASCII values, `LEAF:` and `NODE:`, and the Episode-identifier leaf — frozen, and never re-issued in the version 2 form. The two are different formats because they make different claims: a version 2 proof proves position in the sealed spine, while a 4.x proof proves position in a proof tree that was a separate structure from the spine the seal recorded, and re-issuing one in the version 2 form would claim a guarantee the 4.x seal never made. A verifier of a 4.x proof MUST use its stated `path_directions` rather than derive them: the derivation rule is earned by the version 2 tree's discipline and was never stated for the 4.x tree. The version identifier selects which claim a proof makes, not merely how it is encoded.

### 9.3 Reproducibility Obligation

A verifier holding only the stored nodes of a sealed Episode — its identifier,
its Segments, Signals and the seal record with its §5.8 version identifiers — MUST be able to
recompute `spine_root` and `episode_root_hash` and compare them to the sealed
values, with no out-of-band state. The Five-Test Gate is only as strong as this
obligation: a root that cannot be rebuilt cannot be tested.

This holds for every seal made under `spine_algorithm_version` 2, and for every seal made under
`ordering_version` 2. For a seal made under `ordering_version` 1 it holds only up to the order of same-timestamp Signals, which
no stored node records (§5.8): a verifier may have to search those orderings — or use a
`resolved_signal_order` annotation, after checking it (§5.8.1) — and a seal whose tied groups
are too large to search, and which carries no admissible annotation, cannot be reproduced at all.

An endpoint or tool that returns a *stored* root is an anchor lookup, not a
verification, and MUST NOT be described as one.

Conformance is tested by the `RP-*` family in
[`CONFORMANCE-REPRODUCIBILITY.md`](./CONFORMANCE-REPRODUCIBILITY.md).

## 10. Agent-Directed Retrieval

> **Node-Type Scope Note:** The retrieval operations defined below are the Episode-parameterized retrieval contract — the Phase 1 instantiation for `node_type="episode"`. Future node types (signals, agents, artifacts) will define their own retrieval contracts appropriate to their structure and access patterns. The protocol-level invariants — snapshot isolation (10.4), tail write advisory (10.5), HITL re-validation (10.6), and the side-effect contract (Section 11) — apply to ALL node-type retrieval contracts, not just Episode retrieval.

A conforming adapter implementing Episode retrieval MUST provide three operations:

**get_segment_by_id** — single segment by ID, node-scoped. Node scoping MUST be enforced at the query level — a query against node A must never return content belonging to node B.

**get_segment_range** — contiguous range by sequence_index (inclusive). Supports filtering by segment_type and author. Returns ordered by sequence_index ASC.

**get_episode_spine** — most recent N segments from an Episode's spine. Supports before_index scoping, segment_type filter, retention_tier filter. Returns ordered by sequence_index ASC.

`content_text` MUST be returned verbatim — no truncation, summarization, or modification. The retrieval layer does not decide what content is relevant.

### 10.4 Snapshot Isolation

All retrieval operations within a single agent turn MUST read against a consistent spine snapshot, not live database state. This prevents parallel branches from observing divergent Episode content due to concurrent writes by other agents.

**Snapshot capture:** At the start of each agent turn, the system queries the current `max(sequence_index)` for the active Episode and pins all retrieval to that boundary. Segments written after the snapshot are invisible to that turn's retrieval calls.

**Snapshot lifecycle:**
1. Turn begins → capture `max_sequence_index` from the authoritative store
2. All retrieval tool calls within the turn pass `max_sequence_index` to the query layer
3. Query layer filters: only segments at or below the snapshot index are returned
4. Turn ends → snapshot is cleared; next turn captures a fresh snapshot

**Parallel branch guarantee:** If multiple agents or specialists execute in parallel (e.g., fan-out patterns), and all share the same snapshot boundary, they are guaranteed to reason from identical Episode context. Divergence between branches is task-driven, not memory-driven.

A conforming adapter MUST support `max_sequence_index` as an optional parameter on all three retrieval operations (`get_segment_by_id`, `get_segment_range`, `get_episode_spine`). When provided, results MUST be filtered to segments at or below that index.

**Snapshot capture function:** A conforming adapter MUST implement `get_spine_snapshot_index(episode_id) -> Optional[int]` which returns the current maximum `sequence_index` for an Episode, or None if no segments exist.

### 10.5 Tail Write Advisory

When an agent is actively writing segments to the Episode spine, other agents capturing snapshots during that write window may observe a partially-committed state. The tail write advisory is a coordination signal that protects snapshot capture.

**Protocol:**
1. Before writing segments to the authoritative store, the writing agent sets a tail write advisory for the Episode
2. Any agent capturing a spine snapshot checks the advisory; if active, the snapshot index is reduced by one (excluding the in-progress tail)
3. After the write completes (success or failure), the advisory is cleared

**Scope:** The advisory is a soft coordination signal, not a hard lock. It does not prevent writes or reads — it adjusts snapshot boundaries to avoid phantom reads of uncommitted segments.

**Implementation note:** The advisory is in-process state (not persisted to the ephemeral coordinator) when all agents run in the same process. Distributed deployments require the advisory to be stored in the ephemeral coordinator with a short TTL as a safety bound.

### 10.6 HITL Re-Validation Gate

Write operations that require human-in-the-loop (HITL) approval introduce a temporal gap between when the action is requested and when it is executed. During this gap, the Episode spine may advance, making the approval context stale.

**Protocol:**
1. When a write capability requests HITL approval, the current `spine_snapshot_index` is stored in the approval request context
2. When the approved action is executed, the system queries the current `max(sequence_index)` for the Episode
3. If the spine has advanced beyond the stored snapshot index, the execution is rejected with a `stale_approval` error
4. The requesting agent must re-evaluate the action against current Episode state and re-request if still appropriate

**Rationale:** A stale approval is worse than a rejected one. An action approved based on Episode state at index 42 may be semantically incorrect at index 47 — five new segments may have introduced context that contradicts the action's premise. The re-validation gate surfaces this conflict rather than silently executing.

**Failure mode:** If the re-validation check itself fails (e.g., database unavailable), the system SHOULD log a warning and proceed with execution. The re-validation gate is a safety mechanism, not a hard blocker — availability takes precedence over stale-detection in degraded conditions.

## 11. Retrieval Side-Effect Contract

Retrieval operations MUST NOT modify the Episode spine. Retrieval is a read-only operation — no segment creation, no hash updates, no state transitions.

If an implementation adds access logging (e.g., `last_retrieved_at`, `retrieval_count` on segments), these fields MUST be stored as **side-channel data** explicitly excluded from `content_hash` and `leaf_hash` computation. A retrieval that updates an access counter must not invalidate the Merkle tree.

**The invariant:** A retrieval tool call, followed by a full Merkle verification, MUST produce the same result as the verification without the retrieval. Retrieval is observationally transparent to the integrity layer.

### 11.1 Retrieval Audit Records

Every retrieval tool call SHOULD produce a `RetrievalAuditRecord` — a side-channel record capturing what an agent read, when, and through which snapshot boundary.

```
RetrievalAuditRecord {
  record_id:       UUID
  node_id:         string       (the CognitiveNode being read from)
  actor:           string       (agent_id performing the retrieval)
  tool_name:       string       (which retrieval tool was called)
  parameters:      dict         (from_index, to_index, limit, filters, etc.)
  segment_count:   int          (number of segments returned)
  segment_ids:     list[string] (UUIDs of returned segments)
  snapshot_index:  int?         (spine snapshot boundary at retrieval time)
  wall_clock:      datetime
}
```

Retrieval audit records are stored on separate nodes (not on segment nodes), linked to the source CognitiveNode via dedicated edges. They are NOT included in any hash computation. A conforming adapter SHOULD persist retrieval audit records but MUST NOT fail a retrieval if audit persistence fails — retrieval availability takes precedence over audit completeness.

Retrieval audit records enable post-hoc analysis: which agents read what content, at what point in the node's spine, and whether their snapshot was current or stale. This is the read-path complement to the WIL's write-path observability.

## 12. Write Intent Log (WIL)

### 12.1 Three Storage Invariants

1. **The ephemeral coordinator is not a persistent store.** Loss of coordinator state is recoverable from the authoritative store.
2. **Write ordering is a formal invariant.** Durable content store → authoritative structural store → ephemeral coordinator → semantic search index.
3. **Provisional state never enters persistent storage.**

**Roles are named by role.** Wherever a storage role is recorded — a WIL entry's `stores_involved`, a conformance declaration — its value is `durable_content`, `authoritative_structural`, `ephemeral_coordinator` or `semantic_index`. A provider is a deployment's choice and is never named in normative text. Ledger entries written under 4.x carry the reference deployment's provider names; they are stored data and are not rewritten. A reader maps them to roles by the fixed correspondence the reference implementation publishes (`store_role_of`) and refuses any other value.

### 12.2 Three-Phase Write Protocol

**Phase 1 — INTENT_DECLARED:** Create WIL entry with `completed_at=null`.
**Phase 2 — WRITE_EXECUTION:** Execute writes in mandatory order, recording each store completion.
**Phase 3 — COMPLETION:** Mark complete, graduate from ephemeral coordinator to durable store.

### 12.3 Ephemeral Coordinator TTL Policy

Every coordinator key MUST carry an explicit TTL. Keys without a TTL policy entry are a governance violation. Alternative coordinator implementations MUST define equivalent TTL policies.

### 12.4 Ledgered Operations

§12.2 defines *how* a write intent is recorded. This section defines the
operation vocabulary and the two forms an entry can take. §12.4.2 addresses the
separate question of which operations an implementation is obliged to ledger.

Without a registered vocabulary the WIL is unfalsifiable. An implementer cannot
know what to ledger; a consumer cannot know what the absence of an entry means
— whether the operation is not ledgered by design, or was ledgered and lost.
"The ledger is silent here" has to mean something specific for the ledger to be
evidence.

Operations divide into two tiers by whether there is anything to coordinate.

**Tier 1 — Coordinated write.** The operation writes to more than one store.
Partial failure is possible and recoverable, so the full three-phase protocol
of §12.2 applies: intent declared before the first store write, each store
completion recorded as it lands, completion marked only once every declared
store has confirmed. An entry with `completed_at=null` past the provisional
window is a recovery candidate.

**Tier 2 — Ledger record.** The operation writes to exactly one authoritative
store. There is no cross-store ordering to protect and nothing to replay, so
the three-phase protocol would record ceremony rather than information. A
single completed entry is written when the store write commits:
`initiated_at == completed_at`, `status = COMPLETE`, `stores_involved` naming
the one store.

The distinction is not stylistic. A Tier 2 entry is a provenance breadcrumb; a
Tier 1 entry is a recovery instrument. Treating a Tier 2 entry as a recovery
candidate would replay an operation that never failed.

**The tier turns on whether an interruption leaves recoverable work, not on
store count.** Multiple stores are the common reason it does, and the usual
case, but not the test. An operation that writes several dependent records to
one store — a consultation and its ordered exchange chain, where a partial
write leaves a chain that stops mid-sequence — is Tier 1, because
`completed_at=null` says something true and useful about it. An operation that
commits indivisibly to one store is Tier 2 however important it is, because
there is no partial state for an incomplete entry to describe.

**G-37.** An implementation that ledgers a Tier 1 operation MUST declare the
write intent before the first store write, and MUST NOT mark completion before
every store named in `stores_involved` has recorded completion.

**G-38.** An implementation that ledgers a Tier 2 operation MUST write a
completed entry naming exactly one store, and MUST NOT select that entry as a
recovery candidate in a replay scan.

G-37 and G-38 govern the *form* of an entry, and apply whenever an entry is
written. Neither compels an entry to exist — see §12.4.2.

#### 12.4.1 Operation Register

`SEGMENT_COMMIT` and `SIGNAL_COMMIT` are distinct operations: a segment is
spine content, a signal is cross-episode linkage. They are not interchangeable,
and an implementation MUST NOT ledger one under the other's name.

| Operation | Tier |
|-----------|------|
| `EPISODE_CREATE` | 1 |
| `SEGMENT_COMMIT` | 1 |
| `SIGNAL_COMMIT` | 1 |
| `EPISODE_SEAL` | 1 |
| `MANIFEST_FINALIZE` | 1 |
| `CRYSTALLIZATION` | 1 |
| `EPISODE_ARCHIVE` | 1 |
| `EPISODE_CLOSE` | 1 |
| `CODICIL_APPEND` | 1 |
| `ATTACHMENT_COMMIT` | 1 |
| `CONSULTATION_COMMIT` | 1 |
| `BRANCH_CREATE` | 2 |
| `BRANCH_ABANDON` | 2 |
| `FORK_CREATE` | 2 |
| `FORK_RESOLVE` | 2 |
| `DEPARTURE_FORK_CREATE` | 2 |
| `MERGE_EXECUTE` | 2 |
| `ASIDE_OPEN` | 2 |
| `ASIDE_CLOSE` | 2 |
| `SOLILOQUY_INIT` | 2 |
| `SOLILOQUY_CONCLUDE` | 2 |

The register is closed with respect to its names. An implementation MUST NOT
write an operation value absent from this table unless that value carries an
implementation-specific namespace prefix, so protocol operations and extension
operations remain distinguishable at read time without out-of-band knowledge.

`CONSULTATION_COMMIT` covers the whole consultation write — the consultation
node, its ordered exchange entries and the consulted agent's participation
record. They commit together, so they are one operation rather than three.

Consultation is protocol surface, governed by G-8 and G-9 since v1. A previous
release removed this operation on the stated ground that "the protocol does not
define" consultation, which contradicted the governance section in the same
document; §12.4.1 and G-8/G-9 now agree.

A *collaborative* consultation has no separate operation. Collaboration is a
`ConsultationType`, so a collaborative session commits as a consultation and
the type distinguishes it — a second operation name would encode in the
register what the node already records.

Interaction patterns the protocol genuinely does not define — an
implementation's own routing, escalation or session semantics — are namespaced
under the prefix rule above rather than registered here.

#### 12.4.2 Ledgering Obligations

A conforming implementation MUST write a ledger entry for every operation in
the §12.4.1 register that it performs, in the form that operation's tier
requires (G-37, G-38).

**G-39.** An implementation that performs a registered operation MUST record a
ledger entry for it. Performing a registered operation without an entry is a
conformance violation, not a degraded mode.

This is what makes the ledger evidence. Until an implementation is obliged to
record what it does, a missing entry has two readings — "it did not happen" and
"nobody wrote it down" — and a record that cannot distinguish those is not a
record of anything. §12.4.1 closed the vocabulary so entries mean the same
thing everywhere; this closes the coverage so their absence does too.

##### Operations an implementation does not perform

The obligation is on operations performed, not on the register as a whole. An
implementation that never crystallizes owes no `CRYSTALLIZATION` entries. This
is deliberate: the register describes what the protocol can express, not a
feature checklist every implementation must implement.

##### Best-effort writes

An implementation MAY treat its ledger writes as best-effort with respect to
availability — a coordinator outage need not fail the operation it was meant to
record. What it MUST NOT do is silently proceed as though the entry existed. An
operation performed while the ledger was unavailable leaves the same gap as one
never ledgered, and the implementation MUST surface that rather than absorb it.

The distinction is between an implementation that cannot record and knows it,
and one that does not record and cannot tell.

##### What a verifier may conclude

With G-39 in force, a missing entry from a conforming implementation means the
operation did not occur. That inference is the point of the obligation and was
explicitly unavailable before it.

It remains unavailable for records written by an implementation that was not
conforming at the time of writing, including every record written before this
version. An implementation MUST NOT retroactively assert coverage over a period
it did not have it. Where the distinction matters, a verifier needs the
implementation's conformance claim for the period in question, not merely the
absence of an entry.

##### Incomplete entries

A Tier 1 entry with `completed_at=null` past the provisional window records an
interrupted write, not a missing one. It is evidence the operation was
attempted and that its outcome is unknown — which is strictly more than either
a completed entry or no entry conveys, and is why Tier 1 exists.

## 13. Spine Tip Cache

Segment append and snapshot capture both need to know the current `max(sequence_index)` for an Episode. Without caching, every such operation requires a database traversal.

A conforming implementation SHOULD maintain a cached spine tip per Episode in the ephemeral coordinator. The cache lifecycle:

1. **Invalidate** before any segment write begins (ensures no stale reads during the write window)
2. **Update** after segment write commits (sets cache to the new max sequence_index)
3. **Read** during snapshot capture — cache hit avoids database traversal
4. **TTL** as safety bound — cached entries expire if not refreshed (handles crashed writes that never reach the update step)

**The spine tip cache is a performance optimization, not a source of truth.** The authoritative max_sequence_index is always in the structural store. If the cache is empty, unavailable, or suspected of being stale, the system falls back to querying the structural store directly.

A conforming adapter MUST implement `get_spine_snapshot_index()` which returns the authoritative max_sequence_index from the structural store. The cache layer sits above this function and is implementation-defined.

## 14. Rebalance Events

Tree rebalancing modifies `tree_leaf_index` values without changing content. Without an audit trail, a legitimate rebalance is indistinguishable from tampering. The `RebalanceEventNode` is the forensic record that proves a rebalance was legitimate.

### 14.1 Root-Preservation Invariant

A correct rebalance MUST NOT change the spine root hash. The root is computed from leaf hashes, and leaf hashes are computed from `sequence_index` (immutable) and `content_hash` (unchanged by rebalancing). Therefore, `pre_rebalance_root` MUST equal `post_rebalance_root`.

A `RebalanceEventNode` where these values differ indicates the rebalance modified content — this is a governance violation and MUST be rejected at creation time.

### 14.2 Rebalance Event Record

```
RebalanceEventNode {
  event_id:              UUID
  node_id:               UUID         (the CognitiveNode being rebalanced)
  rebalance_generation:  int          (increments on each rebalance)
  triggered_by:          string       ("SIZE_THRESHOLD" | "MANUAL" | "SEAL_OPTIMIZATION")
  pre_rebalance_root:    string       (spine root before — MUST equal post)
  post_rebalance_root:   string       (spine root after — MUST equal pre)
  leaf_index_delta:      dict?        (optional: {segment_id: {old: N, new: M}})
  affected_leaf_count:   int
  executed_at:           datetime
  executor_id:           string
}
```

A conforming adapter MUST persist rebalance events and link them to the rebalanced node. The `rebalance_generation` counter enables detection of stale `tree_leaf_index` values — any `tree_leaf_index` from a prior generation may be incorrect.

## 15. Adapter Requirements

A conforming adapter MUST:

1. Implement the `ASTPAdapter` interface
2. Enforce all governance rules
3. Preserve hash chain integrity — never modify leaf_hash, spine_root, or content_hash after creation
4. Enforce the dual-index invariant: `tree_leaf_index` never in any hash preimage
5. Respect write ordering invariants across stores
6. Support idempotent writes for WIL recovery
7. Fail loudly on errors — never silently swallow writes. A writer or reader that cannot complete raises a typed error to the host, chained to the store's; it does not return a default, log and continue, or gate itself on a feature flag — whether to call the adapter is the host's decision, and an operation the host asked for either happened or raised. A ledger entry is never written as `COMPLETE` for a write that did not happen (G-39), and an audit writer that cannot read its chain head fails rather than guesses (§8.2).
8. Implement `get_spine_snapshot_index()` for authoritative spine tip queries
9. Persist rebalance events with root-preservation invariant enforcement
10. Implement `TransparencyLogAdapter` interface if transparency log anchoring is supported
11. Persist `WitnessRecord` entries and enforce workspace-level witness policies

## 16. Trust Infrastructure (Phase 3)

### 16.1 Overview

Phase 3 adds cryptographic trust infrastructure to the `CognitiveNode` primitive. All Phase 3 machinery operates at the protocol surface — designed against `CognitiveNode`, not against any specific node type.

| Capability | Protocol-Mandatory | Implementation-Defined |
|-----------|-------------------|----------------------|
| Node Key Hierarchy | HKDF derivation path and context string format | Key material source, KMS integration |
| Transparency Log Anchoring | Anchor data structure, anchor timing (at crystallization) | Log target, submission mechanism |
| Node Witness Signatures | Witness record schema, what is signed | Signing algorithm, key management, threshold policy |
| Cross-Node Chain Proof | Proof chain data structure, verification algorithm | Chain traversal strategy, caching |

### 16.2 Node Key Hierarchy

#### 16.2.1 Derivation Path

All node keys are derived using HKDF-SHA3-256. A derivation is named by its `info` string, and the string carries a **derivation version**; changing a string changes every key it derives, so a string is never edited — a new version is added and the old one retained. **Derivation version 2 (current):**

```
Root Key Material
    └── Workspace Key: HKDF(RKM, salt=workspace_id, info="astp.workspace.v2")
            └── Node Key: HKDF(WK, salt=node_id, info="astp.node.v2:{node_type}")
                    └── Seal Key: HKDF(NK, salt=spine_root_at_seal, info="astp.seal.v2")
```

**Derivation version 1 (retained).** Keys derived before 5.2.0 used `info="ariadne.workspace.v1"`, `"ariadne.node.v1:{node_type}"` and `"ariadne.seal.v1"`, with the same salts and the same HKDF-SHA3-256. Version 1 is retained as the definition of those keys: a record that carries a signature also carries the `derivation_version` of the key that made it (§16.2.4; `key_derivation_version` on a `HITLEventNode`, §4.6), a record that lacks it is version 1, and a verifier that re-derives a key to check a fingerprint selects the derivation the record names. An implementation MAY continue to derive under version 1 for a workspace whose keys it does not wish to rotate; a new workspace derives under 2.

The `node_type` participates in the HKDF `info` string at the Node Key level. Keys derived for `node_type="episode"` are cryptographically distinct from keys derived for `node_type="signal"` or `node_type="artifact"`. New node types automatically receive distinct key spaces without protocol changes.

#### 16.2.2 Two Cryptographic Identities

| Identity | Key | Derived From | Semantics |
|----------|-----|-------------|-----------|
| **Node Identity Key** | `NK` | `node_id` + `node_type` + `workspace_id` | "This is the node." Available from creation. |
| **Seal Commitment Key** | `SK` | `NK` + `spine_root_at_seal` | "This is the node at seal." Available only after sealing. |

The Seal Commitment Key binds the key to the sealed state. A signature under `SK` is a commitment to a specific `spine_root`, not just a node identity.

#### 16.2.3 Key Scope

Node keys support **signing only** at the protocol layer. Encryption (confidentiality of segment content) is implementation-defined and outside the protocol surface. This keeps the protocol surface minimal and avoids key escrow and rotation complexity at the protocol layer.

#### 16.2.4 Schema: NodeKeyRecord

```
NodeKeyRecord {
  node_id:                 string
  node_type:               string    (participates in HKDF context)
  workspace_id:            string
  key_version:             int       (monotonically increasing — G-15)
  public_key_fingerprint:  string    (SHA3-256 of public key bytes)
  derivation_version:      int       (§16.2.1: 1 · 2 (current); a stored record without it is 1)
  derivation_path:         string    (human-readable: "workspace/{wid}/node/{nid}")
  created_at:              datetime
}
```

### 16.3 Transparency Log Anchoring

#### 16.3.1 Anchor Timing

Transparency log anchoring MUST occur at **crystallization boundaries** (G-14). Crystallization is already a protocol-level state transition producing an immutable snapshot — the natural anchor point. Anchoring provides external temporal proof that the crystallization existed at wall-clock time T and was not backdated.

#### 16.3.2 Anchor Data

What is submitted to a transparency log at crystallization (G-14): that this node, in this workspace, had this root at this sequence and clock, at this time. No payload internals.

```
anchor_commitment = SHA3-256( "ANCHOR_COMMITMENT:v2:" ‖ UUID(node_id) ‖ STRING(node_type) ‖ STRING(workspace_id)
                              ‖ HASH(root) ‖ UINT(root_version)
                              ‖ UINT(crystallization_sequence) ‖ UINT(logical_clock) ‖ TIMESTAMP(anchored_at) )
```

`root` is the node's outermost sealed commitment and `root_version` the version of the construction that produced it, exactly as for the witness commitment (§16.4.2), so that a log receipt and a witness record attest the same object for the same crystallization. The 4.x `AnchorCommitment` — a sorted-JSON document carrying a `protocol_version` string that defaulted to a literal and a timestamp truncated to the second — is superseded by `ANCHOR_COMMITMENT:v2:` above and retained only as the definition of receipts already issued under 4.x; neither retired field was a claim about the node.

#### 16.3.3 TransparencyLogAdapter Interface

The protocol defines an abstract interface. Implementations provide a concrete adapter:

- `submit(commitment) -> AnchorReceipt` — submit an anchor commitment, receive a receipt with log proof
- `verify(receipt) -> bool` — verify a receipt is valid for its claimed log
- `retrieve(node_id, crystallization_root) -> AnchorReceipt?` — retrieve a previously submitted receipt

```
AnchorReceipt {
  log_id:             string    (identifies the transparency log)
  log_entry_id:       string    (log-specific entry identifier)
  commitment_hash:    string    (SHA3-256 of AnchorCommitment)
  log_timestamp:      datetime  (timestamp assigned by the log)
  inclusion_proof:    bytes?    (log's own inclusion proof)
  submitted_at:       datetime
}
```

#### 16.3.4 Hybrid Temporal Reasoning

The transparency log receipt's `log_timestamp` provides an **external monotonicity anchor** that the logical clock alone cannot provide. Conforming implementations SHOULD record the `log_timestamp` alongside the logical clock value, enabling: logical clock for intra-system ordering, log timestamp for cross-system and cross-architecture temporal proof.

### 16.4 Node Witness Signatures

#### 16.4.1 Purpose

A witness signature is a statement by a party that it observed a specific sealed root for a specific `CognitiveNode` at a specific time, in a specific role. It is additive evidence — it does not alter the node's state or hash chain.

#### 16.4.2 Witness Commitment

A witness record is a claim by one party about what it saw: **this witness** saw **this root** for **this node** at **this time**, in **this role**. The commitment binds all five.

```
witness_commitment = SHA3-256( "WITNESS_COMMITMENT:v2:" ‖ STRING(witness_id) ‖ UUID(node_id) ‖ STRING(node_type)
                               ‖ HASH(root) ‖ UINT(root_version)
                               ‖ UINT(sequence_index) ‖ UINT(logical_clock) ‖ TIMESTAMP(witnessed_at)
                               ‖ STRING(role) ‖ STRING(role_detail) | NULL )
```

`root` is defined by construction, not by enumeration: **the node's outermost sealed commitment** — whatever construction commits everything under the node's seal. For an Episode that is the Episode root (§5.7), which commits the spine and both manifests; for a node type with no manifests it is the spine root; a future node type with manifests inherits the right binding without being added to a list. `root_version` is the version of the construction that produced it, so a verifier knows what kind of object the witnessed digest is before it compares. `sequence_index` and `logical_clock` are the node's position claims at the moment of witnessing. `role_detail` is bound so that a `CUSTOM` role says what it was.

The 4.x commitment (`node_id|node_type|spine_root|sequence_index|logical_clock|role`, pipe-joined UTF-8) bound neither the witness nor the time: every witness of a root shared one commitment, and a record copied under a second `witness_id` counted again. It is superseded by `WITNESS_COMMITMENT:v2:` above and retained only as the definition of witness records already written under 4.x.

**Signature.** Ed25519 over the 32 raw bytes of the commitment — `Sign(sk, bytes.fromhex(commitment_hash))`, the same form §4.6 fixes for HITL signatures — carried with the 32-byte public key and `public_key_fingerprint = SHA3-256(public_key)`. `ed25519` is the one registered `signature_scheme`; a record naming an unregistered scheme is not valid. This is a registry with one entry, not a hardcoding: the commitment is scheme-independent — the signature is *over* it — so a later scheme enters by amendment as a new registered name that a verifier dispatches on, and the commitment is unchanged. The protocol verifies that a record was signed by the key it names; whether that key belongs to the named `witness_id` is the workspace key registry's question, outside the preimage. Validity is G-12; the threshold count is G-11.

#### 16.4.3 Schema: WitnessRecord

```
WitnessRecord {
  witness_id:              string    (agent_id of the witness)
  node_id:                 UUID
  node_type:               string
  root:                    Hash      (the outermost sealed commitment witnessed)
  root_version:            int
  sequence_index:          int
  logical_clock:           int
  witnessed_at:            datetime  (stored at the millisecond precision it is hashed at)
  role:                    WitnessRole
  role_detail:             string?   (for CUSTOM)
  commitment_hash:         Hash      (§16.4.2)
  signature_scheme:        string    ("ed25519")
  signature:               bytes     (64 bytes, over the raw commitment)
  public_key:              bytes     (32 bytes)
  public_key_fingerprint:  Hash      (SHA3-256 of public_key)
}
```

#### 16.4.4 Witness Roles

- `REVIEWER` — reviewed node content and attests to accuracy
- `AUDITOR` — audited node for compliance or correctness
- `SEAL_WITNESS` — witnessed the sealing event
- `CHAIN_ANCHOR` — attests to cross-node chain integrity
- `CUSTOM` — implementation-defined role (the differential hook for architectures with witness semantics the protocol hasn't anticipated)

#### 16.4.5 Witness Policy

The `min_counter_signatures` threshold is workspace-level configuration, not a protocol governance rule. The protocol defines the witness record schema and verification semantics; the threshold policy is an implementation differential (G-11).

### 16.5 Cross-Node Chain Proof

#### 16.5.1 Purpose

A cross-node chain proof answers: "Prove that Node B's state at sequence index N was causally downstream of Node A's state at sequence index M." This is the protocol-level mechanism for verifying causal relationships across node boundaries, node types, and AI architectures.

#### 16.5.2 ProofChain Data Structure

```
ProofLink {
  node_id:           string
  node_type:         string
  spine_root:        string
  sequence_index:    int
  inclusion_proof:   InclusionProof    (from Section 9.2)
  parent_node_id:    string?           (graph anchor)
  anchor_receipt:    AnchorReceipt?    (transparency log receipt, if available)
  witness_records:   WitnessRecord[]   (witness signatures at this link)
}

ProofChain {
  chain_id:          string
  links:             ProofLink[]       (ordered: root cause → effect)
  chain_root:        string            (SHA3-256 of concatenated link spine_roots)
  created_at:        datetime
  protocol_version:  string
}
```

#### 16.5.3 Chain Verification Algorithm

A `ProofChain` is valid if and only if:

1. **Each link is internally valid:** `link.inclusion_proof` verifies against `link.spine_root` using the inclusion proof algorithm from Section 9.2.
2. **The chain is causally ordered:** For consecutive links (A, B), either `B.parent_node_id == A.node_id` (direct parentage) or a valid cross-reference exists. This causal-ordering rule links **distinct cognitive nodes** (e.g. episode→episode); it does **not** describe how segments order within an episode — a segment's `parent_node_id` is its episode, and segments order by `sequence_index`, not by a parent chain (§3.4.1).
3. **Logical clock monotonicity:** Ordering is consistent with causal direction. Where chains cross architecture boundaries with independent clocks, transparency log timestamps resolve ordering.
4. **Chain root integrity:** `chain_root == SHA3-256(links[0].spine_root ‖ links[1].spine_root ‖ ... ‖ links[n].spine_root)` (G-13).

#### 16.5.4 Cross-Architecture Chain Proof

When a `ProofChain` spans nodes from different conforming implementations, the chain is valid if all links satisfy the verification algorithm above, each link's `inclusion_proof` is verifiable using only protocol-surface primitives, and `anchor_receipt` entries provide temporal ordering where logical clocks are incommensurable.

This is the concrete expression of the cross-architecture interoperability guarantee in Section 2.5.4.

## 17. Conformance Testing

The `astp.protocol.verification` module provides the `DeltaVerifier` — the five-test gate that any conforming implementation must pass.

### 17.1 Phase 1-2 Conformance (Five-Test Gate)

| Layer | Verifies |
|-------|----------|
| **Structural** | Hash chain integrity, leaf hash correctness, Merkle root consistency |
| **Temporal** | Sequence monotonicity, logical clock monotonicity, position-binding |
| **Audit** | Tamper-evident chain integrity, delta record consistency |

The five specific test cases are defined in Section 9.1. A conforming implementation MUST detect all five tampering classes.

### 17.2 Phase 3 Conformance Test Vectors

Phase 3 adds the following prescriptive test vectors. Implementors claiming Phase 3 conformance MUST pass all of them:

**Key Derivation Tests:**

| # | Test | Expected |
|---|------|----------|
| K1 | Derive Node Key with `node_type="episode"` and again with `node_type="signal"` using same `node_id` | Keys MUST differ (G-16) |
| K2 | Derive Seal Key with two different `spine_root` values for same node | Keys MUST differ |
| K3 | Attempt to create `NodeKeyRecord` with `key_version` less than existing | MUST reject (G-15) |

**Witness Verification Tests:**

| # | Test | Expected |
|---|------|----------|
| W1 | Create `WitnessRecord` with correct `commitment_hash` | Verification passes |
| W2 | Create `WitnessRecord` with tampered `commitment_hash` | Verification MUST fail (G-12) |
| W3 | Set `min_counter_signatures=2`, attempt seal with 1 valid witness | MUST reject (G-11) |
| W4 | Set `min_counter_signatures=2`, attempt seal with 2 witnesses but same `witness_id` | MUST reject (G-11 requires distinct names) |
| W5 | Set `min_counter_signatures=2`, two valid records with distinct `witness_id` signed by the same key | MUST reject (G-11 requires distinct keys) |
| W6 | A valid record copied under a second `witness_id`, with its commitment recomputed for the new name | Invalid — signature does not verify (G-12); the copy is cryptographically invalid, not merely uncounted |
| W7 | A record with an empty or unverifiable `signature` | Invalid (G-12); MUST NOT count |
| W8 | A record whose `witness_id` is the node's `authored_by` | Invalid (G-12) |
| W9 | Records A/k₁, A/k₂, B/k₁ (two names, two keys) with threshold 2 | MUST accept — the maximum matching is 2 (G-11) |

**Transparency Log Tests:**

| # | Test | Expected |
|---|------|----------|
| T1 | Submit `AnchorCommitment` at crystallization | Receipt returned with valid `commitment_hash` |
| T2 | Verify receipt against `AnchorCommitment` | Passes |
| T3 | Tamper with `AnchorCommitment` after receipt | Verification MUST fail (`commitment_hash` mismatch) |

**Chain Proof Tests:**

| # | Test | Expected |
|---|------|----------|
| C1 | Build 3-link `ProofChain` with valid links and parentage | `chain_root` verification passes |
| C2 | Tamper with one link's `spine_root` without updating `chain_root` | Verification MUST fail (G-13) |
| C3 | Reorder links in chain (break causal order) | Verification MUST fail (causality check) |
| C4 | Cross-architecture chain: two implementations, valid links | Verification passes using only protocol-surface primitives |

### 17.3 Cross-Architecture Interoperability Test

The definitive conformance test for two implementations claiming interoperability:

1. Implementation A creates a `CognitiveNode`, appends segments, seals, and generates an `InclusionProof`
2. Implementation B receives only the proof and the `spine_root` (no payload, no internal state)
3. Implementation B verifies the proof using protocol-surface primitives
4. Result: proof MUST verify. If it does not, at least one implementation is non-conforming.

This test should be run bidirectionally (A→B and B→A).

## 18. Version History

The change history of this specification is maintained in [`CHANGELOG.md`](./CHANGELOG.md), one entry per released version, under the policy in [`VERSIONING.md`](./VERSIONING.md). It is not restated here, so the two cannot drift. The text of prior MAJOR versions is retained under [`docs/history/`](./docs/history/).

## 19. Branch/Fork/Merge Taxonomy

This section specifies the node types, governance rules, delta types, and
state transitions that model non-linear cognitive work: when an agent (or
human) diverges from a single coherent thread and later reconciles (or
terminates) the divergence. The taxonomy is orthogonal to §4–§16 — it
adds new node types on top of the `CognitiveNode` primitive.

**Governing principle.** Every state transition in this taxonomy
simultaneously produces (a) a structural node, (b) a cognitive delta, and
(c) an append-only audit record. If any of the three writes is absent or
fails, the transition is incomplete. A partial transition is worse than
no transition — it produces ghost state the system cannot reason about.

### 19.1 Foundation Layer

#### 19.1.1 AuditRecord

The taxonomy's tamper-evident append-only log is the audit chain of §8: one record schema, one preimage (`AUDIT_RECORD:v2:`), one chain per `chain_key` (an Episode's UUID as text, or a declared synthetic key such as `declaration:<system>:<group>`), verified per §8.2. The fields the taxonomy relies on — `delta_type` (§19.1.2), `trigger_context`, `forward_delta` / `reverse_delta` written simultaneously as canonical JSON, `affected_nodes`, `caught_by` (AGENT / HUMAN / SYSTEM / UNCAUGHT) and `detection_window_open` — are all bound. Records written under the 4.x taxonomy form (`sha3_256(b"AUDIT:" + …)`, `"GENESIS"`) remain verifiable by it (§8.3).

**Invariant.** Rollback creates a new forward record. The log is never edited in place — a reverse delta is written as a new audit record that references the original.

#### 19.1.2 CognitiveDelta Registry — Taxonomy Types

| Delta Type | Phase | Writer |
|-----------|-------|--------|
| `BRANCH_CREATED` | 1 | `create_branch()` |
| `BRANCH_ABANDONED` | 1 | `abandon_branch()` |
| `FORK_CREATED` | 2 | `create_fork()` |
| `FORK_RESOLVED` | 2 | `resolve_fork()` |
| `MERGE_EXECUTED` | 2 | `execute_merge()` |
| `ASIDE_OPENED` | 3 | `create_aside()` |
| `ASIDE_CLOSED` | 3 | `close_aside()` |
| `SOLILOQUY_INITIATED` | 3 | `create_soliloquy()` |
| `SOLILOQUY_CONCLUDED` | 3 | `conclude_soliloquy()` |

All types register at protocol load time. Functions reference the
registry — the registry never references functions.

#### 19.1.3 AccessPolicy

Per-resource read/write policy. Default resource types: `BRANCH`, `FORK`,
`ASIDE`, `SOLILOQUY`. Defaults:

| Resource | `other_agents_read` | `audit_on_access` |
|----------|--------------------|--------------------|
| `BRANCH` / `FORK` / `ASIDE` | `OPEN` | false |
| `SOLILOQUY` | `ESCALATION_ONLY` | true |

**Enforcement rule:** fail-closed. If a policy cannot be evaluated,
access is denied and a denial is written to the audit chain.

#### 19.1.4 IntentRecord

Prevents concurrent duplicate creation. Idempotency
key: `SHA3-256("INTENT:" + source_episode_id + source_segment_id + intent_hash)`.
An `acquire_intent_sync` lookup with a COMPLETE status returns the prior
result; a PENDING status short-circuits; a new intent is written
atomically.

### 19.2 Phase 1 — Branch Lifecycle

#### 19.2.1 BranchPointNode

Created by `create_branch()` at the exact divergence point on the spine.
Immutable after creation; lifecycle state is derived from the presence
or absence of a matching `BranchTerminusNode`.

Key fields: `branch_id` (stable UUID), `parent_episode_id`,
`source_segment_id`, `branch_type`, `branch_depth` (soft max 4),
`declaration_type` (`EXPLICIT` / `INFERRED` / `RETROACTIVE`),
`spine_merkle_snapshot` (immutable coherence anchor), `content_hash`
(domain prefix `BRANCH_POINT:`).

Retroactive declarations additionally carry
`pre_declaration_merkle_root`, `declared_retroactively_at`, `declared_by`.

#### 19.2.2 BranchTerminusNode

Created by `abandon_branch()` (type `ABANDONED`) or `execute_merge()`
(type `MERGED`). Terminal — the branch cannot be reopened.

Integrity link: `branch_point_hash` MUST equal the originating
`BranchPointNode.content_hash`. The terminus hash uses domain prefix
`BRANCH_TERMINUS:`.

#### 19.2.3 Dual Hash Chain

Branches create non-linear Episode graphs that must remain verifiable:

- **Spine chain.** The spine is self-contained and verifiable without
  branch contents. The `BranchPointNode` anchors to the spine by reference
  — `source_segment_id` and `spine_merkle_snapshot` — and carries its own
  `content_hash`; it is **not** a spine leaf. Under `spine_algorithm_version` 2
  it is a structural-manifest member, committed into the Episode root under
  `BRANCH_POINT:v2:` (§5.7.1); under versions 0 and 1 no sealed root commits
  to it (§5.6, retained form).
- **Branch chain.** Starts at `BranchPointNode` and ends at
  `BranchTerminusNode`. Verifiable independently of the spine.
- **Merge verification (Phase 2).** Requires three Merkle roots — see §19.3.3.

**Depth constraint.** `branch_depth` maximum of 4 (soft). Exceeding it
raises `ASTPGovernanceError`; callers may catch and record an
override in the audit trail.

#### 19.2.4 Derived Lifecycle State

Lifecycle state is always recomputed from the log — never stored as a
mutable field:

```
IF BranchPointNode(branch_id) missing             → ERROR
IF BranchTerminusNode(branch_id, MERGED) exists   → MERGED
IF BranchTerminusNode(branch_id, ABANDONED) exists → ABANDONED
ELSE                                              → ACTIVE
```

### 19.3 Phase 2 — Resolution Primitives

#### 19.3.1 ForkPointNode

Forks differ from branches: a fork produces a new Episode with a
distinct objective. A single `create_fork()` call writes N ForkPointNodes
sharing the same `fork_id`; each ForkPoint anchors a new Episode.
Domain prefix: `FORK_POINT:`.

Governance:
- **G-19.** `fork_objective` non-empty. A fork without an objective is
  indistinguishable from a branch.
- **G-20.** At least 2 alternatives per fork. Single-path divergence is
  a branch.

`resolve_fork()` marks one sibling `PROMOTED` and all others `DISCARDED`,
writing `FORK_RESOLVED`. `resolution_rationale` is required (G-21).

#### 19.3.2 MergePointNode

Created by `execute_merge()` on the target spine. Carries three Merkle
roots: `source_merkle_root` (branch state at merge),
`target_merkle_root_pre` (spine before merge), `target_merkle_root_post`
(spine after merge — must match recompute). Domain prefix: `MERGE_POINT:`
binds all three roots into the content hash.

**G-22.** `merge_summary` non-empty. The synthesis is the audit trail.

**G-23 (Conflict Surface Invariant).** `execute_merge()` never resolves
conflicts silently. When conflicts exist without matching
`ConflictResolution` entries, or when `merge_strategy == AUTO` and any
conflicts exist, the function returns a `ConflictManifest` and writes
NO merge records. The manifest carries `source_merkle_root`,
`target_merkle_root_pre`, the common ancestor, and all conflict
segments; callers must re-invoke with resolutions.

**G-24.** The three integrity assertions of §19.3.3
must pass before `MergePointNode` is written. On failure the merge is
aborted and a SYSTEM-caught failure audit record is written.

#### 19.3.3 Merge Integrity Verification

```
source_valid      := merge.source_merkle_root      == branch.merkle_root at merge time
target_pre_valid  := merge.target_merkle_root_pre  == spine.merkle_root before merge
target_post_valid := merge.target_merkle_root_post == recomputed spine root
integrity_holds   := all three
```

`verify_merge_integrity(merge_id)` returns a `MergeIntegrityResult`.
Any `false` in `integrity_holds` is a critical health metric
(`merge_integrity_failures`, target: 0).

#### 19.3.4 BranchReturnEdge

On merge, a `BRANCH_RETURN` edge connects `BranchTerminusNode(MERGED)`
to the `MergePointNode` on the target spine. Carries
`synthesis_summary` and `nodes_integrated`.

#### 19.3.5 DepartureForkPointNode (Phase D — Departure Fork Lifecycle)

A **departure fork** is distinct from the speculative fork of §19.3.1. It is a
single **directional departure**: one topic diverges into a new Episode while the
originating Episode *continues* uninterrupted. There are no siblings and no
resolve/promote/discard — a departure fork, if not abandoned, *is* an Episode
("fork is a verb, not a noun"). Created by `create_departure_fork()`.
Domain prefix: `DEPARTURE_FORK_POINT:`.

`create_departure_fork()` writes atomically: the new fork Episode (status ACTIVE,
carrying the immutable fork provenance of §19.3.6), a single
`DepartureForkPointNode` on the *originating* spine (`FORK_ORIGIN` edge), and a
`DEPARTURE_FORK_CREATED` audit record.

**G-30 (Backdating integrity invariant).**
`DepartureForkPointNode.spine_tip_hash_at_departure` == the fork Episode's
`fork_origin_spine_tip_hash`. Both are the originating spine tip at the departure
moment; a mismatch is a fatal integrity violation at creation. The branch point
records where divergence *began*, cross-verifiable across the two independent spines.

Governance:
- **G-31.** `fork_objective` non-empty (as G-19).
- **G-32.** `fork_creation_trigger ∈ {TOPIC_SHIFT, PARALLEL_THREAD, EXPLICIT_FORK,
  AGENT_ESCALATION}`. `EXPLORATORY_THREAD` routes to the speculative `create_fork()`,
  not here.
- **G-33.** `fork_trigger_segment_id` required when `fork_creation_trigger ==
  AGENT_ESCALATION`.

**Lifecycle FSM.** States `ACTIVE → COMPLETED | ABANDONED`, a distinct vocabulary
from the speculative fork's `PROMOTED | DISCARDED` (an abandoned departure is not a
discarded alternative). `ACTIVE` covers both in-progress and *parked*;
**resumption** — re-entering the origin while the fork stays ACTIVE — is a
non-event: no node, no declaration.

- `complete_departure_fork()` — `ACTIVE → COMPLETED`. A first-person declaration by
  the fork Episode's own agent. Writes `DEPARTURE_FORK_COMPLETED`.
- `abandon_departure_fork()` — `ACTIVE → ABANDONED` (terminal). By the originating
  agent, or system cleanup of a never-entered stub. A COMPLETED fork returns; it is
  not abandoned. Writes `DEPARTURE_FORK_ABANDONED`.

**Formal return.** `declare_fork_return()` (authority: the originating agent) writes
a `ForkReturnNode` to the *originating* spine (`FORK_RETURN` edge) plus a
`RETURNED_FROM` edge to the fork Episode, and a `DEPARTURE_FORK_RETURNED` audit.
Domain prefix: `FORK_RETURN:`. A fork return is **declarative** — the origin asserts
incorporation across two independent spines — never the branch's *structural*
merge; integration content is written as subsequent origin-spine segments.
`return_type ∈ {INCORPORATED, ACKNOWLEDGED, SUPERSEDED}`.
- **G-34.** The fork must be `COMPLETED` before a return may be declared.
- **G-35.** At most one return declaration per `fork_id`.

Resumption requires no node; only a formal return writes to the spine.

#### 19.3.6 Departure-fork Episode provenance

An Episode created via `create_departure_fork()` carries immutable provenance
fields, set once at creation and never mutated: `fork_origin_episode_id`,
`fork_anchor_index`, `fork_id`, `fork_created_at`, `fork_creation_trigger`,
`fork_trigger_confidence`, `fork_trigger_segment_id`, `fork_origin_spine_tip_hash`,
`fork_origin_active_branch_ids`, `fork_status`, `fork_return_type`. This is
provenance — "how did this Episode come to exist" — not identity, analogous to
`continuation_of`. Null on non-fork Episodes.

#### 19.3.7 Departure-fork Orphan Recovery

The two-write departure-fork producer (§19.3.5) and the declarative return (§19.3.5)
each hold a cross-verifiable integrity invariant at write time. **Orphan recovery is
the runtime enforcement of those invariants after a partial failure** — the producers
enforce them at write time; orphan recovery catches the cases where enforcement failed
(a crash between the two writes, a rolled-back status). This section defines the
**normative recovery surface**: the `ForkOrphanMarker` node, the recovery field
mutations, and the one permitted retroactive spine write. **The detection cadence — how
often an implementation scans for orphans, and whether it scans at all — is NOT
normative** (it is operational hygiene); only the shape of a *conformant recovery* is.

**Orphan classes.** Four structurally-impossible-under-normal-writes states:

| Class | Definition | Severity |
|-------|------------|----------|
| **A** — Dangling point | A `DepartureForkPointNode` exists on the origin spine with no Episode carrying its `fork_id`. | High |
| **B** — Unanchored episode | An Episode has `fork_origin_episode_id` set (and thus, per §19.3.6, `fork_anchor_index`) but no `DepartureForkPointNode` with a matching `fork_id` exists on the origin spine. | High |
| **C** — Return/status mismatch | A `ForkReturnNode` exists for a `fork_id` whose fork Episode is not `COMPLETED`. | Medium |
| **D** — Stale ACTIVE fork | An `ACTIVE` fork with no spine activity past an implementation-defined staleness threshold. | Low |

A **non-null `fork_anchor_index` with no corresponding `DepartureForkPointNode`** is the defining corruption signature of Class B (the producer patches `fork_anchor_index` only *after* the point write — §19.3.5).

**`ForkOrphanMarker`** — a **non-chained diagnostic satellite** recording a detection
event. Written to the origin spine (linked by an `ORPHAN_MARKER` edge from the origin
Episode), it is **self-hashed** for tamper-evidence with domain prefix
`FORK_ORPHAN_MARKER:` but is **NOT a member of the origin spine's Merkle chain** — it
carries no `parent_hash`, and writing it MUST NOT alter the origin Episode's spine
root/tip. Fields: `fork_orphan_marker_id`, `fork_id`, `origin_episode_id`,
`orphan_class` (`CLASS_A`…`CLASS_D`), `sequence_index`, `detection_run_id`,
`recovery_action`, `requires_operator_review`, `detected_at`. It is **read-only after
write**, **deduplicated one-per-orphaned-fork** (keyed on `fork_id` — a re-detection
sweep MUST NOT write a duplicate), and **excluded from departure-registry queries**
(which match `DepartureForkPointNode` / `ForkReturnNode` only).

**Recovery actions** (the producer exposes the writes; an orchestrator decides which to run):

- **Class A** — flag the dangling `DepartureForkPointNode` `orphaned = true` (append-only — the point is **never deleted**; spine nodes are append-only) and write a `ForkOrphanMarker` (`requires_operator_review = true` — a dangling point may reference an Episode in a storage layer the detection query cannot reach).
- **Class B** — validate that the fork Episode's `fork_origin_spine_tip_hash` is consistent with the origin spine at `fork_anchor_index`. **If consistent**, perform the **one permitted retroactive spine write** (below). **If inconsistent**, escalate to an operator — do NOT auto-write. **If the origin Episode is unreachable**, mark the fork Episode `fork_orphaned = true`, `fork_orphan_class = UNANCHORED`.
- **Class C** — if the fork Episode is `ACTIVE`, the `ForkReturnNode` is authoritative: set `fork_status = COMPLETED`, `status_corrected_by_orphan_recovery = true`, `status_corrected_at`. If the fork Episode is `ABANDONED`, this is a data-integrity violation requiring operator review — do NOT auto-correct.
- **Class D** — notification only. An implementation MAY, after a longer abandonment threshold, invoke `abandon_departure_fork()` via the system/housekeeping actor (§19.3.5). It MUST NOT auto-abandon on staleness alone.

**The retroactive `DepartureForkPointNode` write (Class B).** The point was *supposed*
to be on the spine — its absence is a write failure, not a design choice — so its
recovery is the one place a fork point is written after the fact. It is an **append**,
governed by the same discipline as a RETROACTIVE branch declaration (§19.2):

1. It **records the backdated anchor**: the point's `spine_tip_hash_at_departure` MUST be the fork Episode's stored `fork_origin_spine_tip_hash`, so the cross-verifiable invariant `DepartureForkPointNode.spine_tip_hash_at_departure == fork Episode.fork_origin_spine_tip_hash` holds by construction.
2. It **MUST NOT recompute or mutate any existing spine node or chain hash** — it only creates the missing point.
3. The point's `content_hash` is computed exactly as an on-time write, so a recovered point is **byte-identical** to one written on time; the recovery flags `retroactive = true` and `orphan_recovery_timestamp` are diagnostic metadata **outside** the hash preimage.
4. The consistency check of the preceding paragraph is the **gate**: on mismatch, escalate — never write.

**Invariants.** (a) Spine nodes are append-only — orphan recovery never deletes.
(b) The `ForkOrphanMarker` never enters any root — a diagnostic write
never alters an Episode's cryptographic fingerprint. (c) The retroactive point write
preserves the §19.3.5 cross-verifiable anchor by construction.

**A recovered point written after a seal (§5.7.1).** The one permitted retroactive write is a structural node, and if the origin Episode has already been sealed the recovered point is never a member of that seal's manifest. It is committed by the Episode's **next** crystallization and MUST reference the earlier seal it post-dates (its `episode_root_hash` and `sealed_at`). Before that crystallization it is a node the current seal does not commit and says nothing about; after it, it is a member of the successor's structural manifest. It is never an unbound phantom between two seals. Invariant (b) is unchanged: the `ForkOrphanMarker` is not a member; the recovered point is.

### 19.4 Phase 3 — Social/Internal Primitives

#### 19.4.1 AsideSegmentNode

Human-initiated side channel with a target agent. The aside's content hash and its terminus hash are its own commitments — the claim each node makes, bound so it cannot be altered afterwards — and are not seal inputs.

```
aside_hash = SHA3-256( "ASIDE:v2:" ‖ UUID(aside_id) ‖ UUID(parent_episode_id) ‖ UUID(parent_segment_id)
                       ‖ HASH(parent_segment_content_hash) ‖ STRING(initiated_by_human) ‖ STRING(target_agent_id)
                       ‖ TIMESTAMP(opened_at) )

aside_terminus_hash = SHA3-256( "ASIDE_TERMINUS:v2:" ‖ UUID(aside_terminus_id) ‖ UUID(aside_id) ‖ UUID(parent_episode_id)
                       ‖ HASH(aside_hash) ‖ LIST(HASH)(produced_content_hashes) ‖ STRING(close_reason)
                       ‖ BOOL(reference_scan_passed) ‖ LIST(UUID)(external_references_found)
                       ‖ STRING(termination_status) ‖ TIMESTAMP(closed_at) )
```

An aside is a channel between one human and one agent, opened from one Segment. **The two parties are bound** — the named exception of §5.7.1: the human and the agent *are* the channel, and G-25 makes the human's presence the node's defining claim. The Segment it opened from is bound by identity and by content hash. `aside_label` is commentary and is not bound. The terminus binds what the channel produced — the content hashes of the Segments written inside it, in the order written — the close reason, the reference-scan outcome and the Segments outside the aside found holding references into it; notification targets and duration are not bound. (4.x: `ASIDE:` bound a `parent_hash` that was never populated, and the terminus hash was an unprefixed SHA3 over the identifier, the sorted reference list and the close reason. Both are superseded by the `ASIDE:v2:` and `ASIDE_TERMINUS:v2:` constructions above and are retained only as the definitions of nodes already written under 4.x.)

**G-25 (Aside Human-Initiation Invariant).** Asides are ALWAYS
human-initiated. `initiated_by_human` is required; an attempt to create
an aside without a human actor raises `ASTPGovernanceError`.
Agent-initiated internal branches are soliloquies (§19.4.2).

**G-26 (Aside Return Obligation).** An aside that remains OPEN at
episode seal is an audit violation. `check_aside_return_obligation()`
enforces this at seal time.

**Asymmetric merge on close.** `close_aside()` runs a reference scan:
external segments that hold references to aside-internal segments are
recorded in the `AsideTerminusNode` and `ASIDE_CLOSED` audit record as
`external_references_found`, and bound into the terminus hash. The close proceeds — the scan is a
disclosure mechanism, not a block — but the leak is part of the
permanent, committed record.

#### 19.4.2 SoliloquySegmentNode

Agent-initiated private deliberation.

```
soliloquy_hash = SHA3-256( "SOLILOQUY:v2:" ‖ UUID(soliloquy_id) ‖ UUID(parent_episode_id) ‖ UUID(parent_segment_id)
                           ‖ HASH(parent_segment_content_hash) ‖ STRING(initiated_by_agent) ‖ TIMESTAMP(opened_at) )

deliberation_chain_hash = SHA3-256( "DELIBERATION_CHAIN:v2:" ‖ UUID(soliloquy_id) ‖ LIST(HASH)(deliberation_content_hashes) )

conclusion_hash = SHA3-256( "SOLILOQUY_CONCLUSION:v2:" ‖ UUID(conclusion_id) ‖ UUID(soliloquy_id) ‖ UUID(parent_episode_id)
                            ‖ HASH(deliberation_chain_hash) ‖ STRING(conclusion_summary) ‖ UUID(merged_into_segment_id)
                            ‖ STRING(termination_status) ‖ TIMESTAMP(concluded_at) )
```

The soliloquy node binds what is true at open: who opened it (`initiated_by_agent`, bound under the §5.7.1 named exception — whose deliberation it is, is what it is), from which Segment, with what content there, when. `soliloquy_purpose` is commentary and is not bound; the visibility policy governs access and is not a hash input.

**G-27 (Soliloquy Human Accessibility Invariant).** Humans
ALWAYS have read access. `SoliloquyVisibilityPolicy.human_accessible`
defaulting or being set to `false` raises `ASTPGovernanceError`.
Deliberation content can be private to other agents, never private to
humans.

**G-28 (Soliloquy Return Obligation).** Soliloquies left ACTIVE at
episode seal are audit violations. Coherence monitoring continues
inside the soliloquy — the agent cannot use soliloquy to escape the
framework.

**Conclusion merges, chain stays.** `conclude_soliloquy()` writes a
`SoliloquyConclusionNode` carrying `conclusion_content_hash` (public)
and `deliberation_chain_hash`. Only the conclusion is absorbed into the spine; the
deliberation chain remains sealed inside the `SoliloquySegmentNode`.

#### 19.4.3 Deliberation Chain Binding

**The deliberation chain is bound by content, not by name.** `deliberation_chain_hash` is over the deliberation Segments' content hashes in order — order is meaning in a deliberation — so a human auditor with access (G-27) verifies the chain against the conclusion without the content being in the hash. An empty chain is a valid chain. The conclusion binds the chain hash, the public summary, the spine Segment it merged into and how it terminated; duration is derived and is not bound.

The 4.x soliloquy's two constructions collapsed to the single one above. 4.x offered two content-hash policies, `HASH_PLACEHOLDER` (identity and time) and `FULL_CONTENT` (identity, time and the deliberation chain as written at open); the chain does not exist when a soliloquy opens, so the two differed in nothing a verifier could use, and the 4.x chain hash was over the Segments' *identifiers* joined by `|`, which binds nothing about what was thought. `SoliloquyContentHashPolicy` is retired; the 4.x forms (`SOLILOQUY_PLACEHOLDER:`, `SOLILOQUY_FULL:`, `DELIBERATION_CHAIN:`, `SOLILOQUY_CONCLUSION:`) are superseded by §19.4.2 and retained only as the definitions of nodes already written under 4.x.

### 19.5 Phase 4 — Prescriptive Enforcement

Detection moves from descriptive (retroactive analysis) to prescriptive
(active, at segment write time).

#### 19.5.1 CoherenceFingerprint

Embedded per segment at write time:

| Field | Purpose |
|-------|---------|
| `topic_vector` | Caller-supplied embedding |
| `intent_class` | CONTINUE / EXPAND / SHIFT / RESOLVE / INTRODUCE |
| `objective_hash` | `sha3_256("OBJECTIVE:" + canonicalized objective)` |
| `drift_from_spine` | 0.0–1.0 cosine distance |
| `consecutive_drift_count` | Persisted across turns |
| `detection_state` | NOMINAL / WATCHING / CANDIDATE / MATERIALIZED |

A `CoherenceFingerprint` has **no content hash**. It is a diagnostic satellite in the sense of §5.7.1: it records a detector's reading and never enters a seal or a chain. The 4.x `FINGERPRINT:` prefix is retired with no successor; a fingerprint that needs to be attested is attested by the audit record of the transition it triggered.

**G-29 (Write-Time Fingerprint Invariant).** Fingerprints must be
computed at segment write time. `enforce_write_time_fingerprint(None)`
raises — retroactive fingerprinting defeats the detection window.

#### 19.5.2 Detection State Machine

`advance_detection_state(prior_state, prior_count, drift, obj_changed, intent, thresholds)`
is a pure function. Default thresholds match the spec:

| Target state | Drift ≥ | Consecutive turns ≥ |
|--------------|--------|---------------------|
| WATCHING | 0.3 | 1 |
| CANDIDATE | 0.3 | 3 |
| MATERIALIZED | 0.5 | 5 |

Two overrides force immediate CANDIDATE regardless of drift:
- `objective_hash` changed between consecutive observations
- `intent_class == INTRODUCE`

Drift below `watching_drift` resets the count to 0 and returns state to
NOMINAL. Thresholds are tunable per-episode-type via
`DetectionThresholds`.

#### 19.5.3 Write Intercept Protocol

`intercept_segment_write()` is the application hook. Sequence:

1. Compute `objective_hash` from the current episode objective.
2. Call `detect_branch_candidate()` — reads last fingerprint, advances
   state, computes `materialized_recommendation` if the state
   transitions to MATERIALIZED for the first time.
3. Persist the new fingerprint via the registry.
4. Return `DetectionResult`. If the result carries a
   `materialized_recommendation`, the caller SHOULD invoke
   `create_branch(declaration_type=RETROACTIVE, source_segment_id=rec.source_segment_id)`.
   The recommendation anchors at the last NOMINAL segment — the point
   before drift began.

`detect_branch_candidate()` is pure-read; only
`intercept_segment_write()` persists.

#### 19.5.4 ConfirmationCache

Prevents the confirmation loop when a detected candidate is confirmed
as a legitimate branch. TTL is measured in episode turns:

```
confirmation_valid_until = confirmed_at_turn + valid_for_turns
```

Lookup is case- and whitespace-insensitive on the action description.
Expiry is checked at read time; expired entries are discarded.

### 19.6 Edge and Relationship Summary

| Edge | From → To | Phase |
|------|-----------|-------|
| `BRANCH_ORIGIN` | Episode → BranchPoint | 1 |
| `BRANCH_TERMINUS` | BranchPoint → BranchTerminus | 1 |
| `AUDIT_TRAIL` | Episode → AuditRecord | 1 |
| `FORK_ORIGIN` | Episode → ForkPoint | 2 |
| `MERGE_INTO` | Source Episode → MergePoint | 2 |
| `MERGE_TARGET` | MergePoint → Target Episode | 2 |
| `BRANCH_RETURN` | BranchTerminus(MERGED) → MergePoint | 2 |
| `ASIDE_OPEN` | Episode → Aside | 3 |
| `ASIDE_CLOSED` | Aside → AsideTerminus | 3 |
| `SOLILOQUY_OPEN` | Episode → Soliloquy | 3 |
| `SOLILOQUY_CONCLUDED` | Soliloquy → SoliloquyConclusion | 3 |
| `FINGERPRINTS` | Episode → CoherenceFingerprint | 4 |
| `FORK_ORIGIN` (departure) | Origin Episode → DepartureForkPoint | D |
| `FORK_RETURN` | Origin Episode → ForkReturn | D |
| `RETURNED_FROM` | ForkReturn → Fork Episode | D |

### 19.7 Implementation Status

All four BFM phases **plus the Phase D departure-fork lifecycle** are implemented
and covered by unit tests against the reference adapter (mocked driver). See
`tests/unit/protocol/test_phase2_*.py`, `test_phase3_*.py`, `test_phase4_*.py`, and
the departure-fork suites in `test_phase2_operations.py` (`TestCreateDepartureFork`,
`TestDepartureForkFSM`).

The following are **known limitations / forward-compatible extensions** —
deliberately scoped out of this version, non-breaking to add later, and safe to
build on:

1. **`target_merkle_root_post`** in `execute_merge()` is computed
   deterministically from pre-merge roots and resolutions rather than
   from full spine recomputation. Full recomputation requires a
   branch-aware segment model (segments tagged with `branch_id`), which
   is a forward-compatible extension.
2. **`find_common_ancestor()`** walks one level — from the branch's
   originating BranchPoint to the target spine. Multi-level nested
   merges require iterative traversal (forward-compatible).
3. **Return-obligation checks** (`check_aside_return_obligation`,
   `check_soliloquy_return_obligation`) are available as callable
   guards but are not yet invoked from the episode-seal path; the
   integration is owned by the seal implementation.
4. **Access-policy runtime enforcement** (audit on ESCALATION_ONLY reads)
   is spec'd at the coordination layer and left to the application.

## 20. Cross-Episode Linking & Grouping

This section defines cross-episode linking and grouping — how Episodes connect and relate across time (continuation, supersession, branching, informing, references, spawning). It integrates the normative content first published as **Amendment v2.0** (SPEC v3.0.0); that amendment file is now historical-reference only. The internal §1–§12 numbering below is the amendment's original scheme, scoped within §20.

### Part I — Cross-Episode Linking

#### §1 Protocol Constants

Named constants replace magic numbers throughout the inference pipeline. These values are protocol-level defaults; calibration is implementation-side (see §12 — behavioral tier).

```
DISCOVERY_THRESHOLD    = 0.75   // minimum composite score to surface a candidate to human review
AUTO_ACCEPT_THRESHOLD  = 0.90   // composite score above which a link may be auto-accepted without human review
```

**Calibration narrative:** Begin conservative. The rejection signal produced by `CANDIDATE_REJECTED` audit events (§5) is the primary input for threshold tuning. A high rejection rate at scores near `DISCOVERY_THRESHOLD` indicates the threshold should be raised; a low proposal rate with known missed links indicates it should be lowered. Threshold adjustment is an implementation decision (§12 behavioral tier); the protocol records the threshold value at the time of each inference event (§12 audit-the-decision pattern).

---

#### §2 `EpisodeLink` Node — Amended Schema

```
EpisodeLink {
  // Identity — immutable
  link_id:               UUID
  source_episode:        EpisodeID
  target_episode:        EpisodeID
  created_at:            Timestamp
  created_by:            AgentID

  // Semantic characterization
  link_type:             LinkType              // see §3
  link_strength:         Float [0.0, 1.0]      // semantic similarity score; 0.0 = no semantic relationship, 1.0 = near-identical
  is_inferred:           Boolean               // true = system-generated candidate; false = human-asserted

  // Inference provenance — immutable once set
  inference_signals:     Signal[]              // see §4
  inference_threshold:   Float                 // value of DISCOVERY_THRESHOLD at inference time
  retroactive:           Boolean               // true = link created after source episode crystallization

  // Health state — mutable
  health_state:          LinkHealthState        // VALID | STALE | FROZEN | BROKEN | QUARANTINED
  health_checked_at:     Timestamp
  source_version:        SemVer                // version of source episode at link creation
  target_version:        SemVer                // version of target episode at link creation

  // Quarantine
  quarantine_reason:     Optional<String>
  quarantined_at:        Optional<Timestamp>
  quarantine_resolved_at:    Optional<Timestamp>    // set when quarantine exits
  quarantine_resolution:     Optional<QuarantineResolution>  // CONFIRMED | DISSOLVED | ESCALATED

  // Binding to the two ends' sealed states at link creation (5.0.0)
  source_episode_root:   Optional<Hash>        // Episode root of the source when it was sealed at link creation; null otherwise
  target_episode_root:   Optional<Hash>        // likewise for the target

  // Integrity
  content_hash:          Hash                  // EPISODE_LINK:v2: — see below
}
```

**Content hash.** A link is a claim about a relationship between two Episodes in *specific states*, and its hash binds exactly that claim:

```
signal_hash = SHA3-256( "LINK_SIGNAL:v2:" ‖ STRING(signal_type) ‖ FLOAT(signal_weight) ‖ FLOAT(signal_value) ‖ TIMESTAMP(computed_at) )

content_hash = SHA3-256( "EPISODE_LINK:v2:" ‖ UUID(link_id) ‖ UUID(source_episode) ‖ UUID(target_episode)
                         ‖ HASH(source_episode_root) | NULL ‖ HASH(target_episode_root) | NULL
                         ‖ TIMESTAMP(created_at) ‖ STRING(link_type) ‖ FLOAT(link_strength) ‖ BOOL(is_inferred)
                         ‖ LIST(HASH)(inference_signal_hashes) ‖ FLOAT(inference_threshold) | NULL ‖ BOOL(retroactive)
                         ‖ STRING(source_version) | NULL ‖ STRING(target_version) | NULL )
```

**What a link binds on each end.** The end's Episode identifier, always; and the end's Episode root at link creation when that end was sealed then, NULL when it was not. A link from or to a sealed Episode is therefore a claim about a specific sealed state, not merely a name: if the source is later re-sealed under a successor, the link says which state it was made against. A sealed end with a NULL root is nonconformant — the writer had the root and declined to bind it — and a verifier holding the seal records checks this; `retroactive` (the source was crystallized before the link) therefore implies a non-NULL `source_episode_root`. The version strings remain as the human-readable form of the same claim.

**What a link binds about itself.** Its type, its strength as an exact real number, whether it was inferred, and if so every signal that contributed — each hashed on its own with its type, weight, value and time, listed in the order recorded — and the threshold in force: §12.2's audit-the-decision, made a commitment.

**What a link does not bind.** `created_by` — provenance, by the §5.7.1 rule, the audit chain's. `health_state`, `health_checked_at`, `quarantine_reason`, `quarantined_at`, `quarantine_resolved_at` and `quarantine_resolution` — lifecycle, whose integrity is the audit chain's (§8). The hash is fixed at creation and never re-stamped. (4.x bound the four health and quarantine fields, so a 4.x link's `content_hash` changed whenever its health did and committed to no stable claim; the 4.x `LINK_INTEGRITY` proof, recomputing from current fields, could detect only a row whose hash had not been re-stamped. The 4.x form is superseded by `EPISODE_LINK:v2:` above and retained only as the definition of links already written under 4.x.)

---

#### §3 Link Type Taxonomy

| Type | Semantics | Mutual Exclusivity |
|------|-----------|-------------------|
| `CONTINUES_FROM` | Direct continuation of prior episode | ⊕ `SUPERSEDES`, ⊕ `BRANCHES_FROM` |
| `SUPERSEDES` | This episode replaces target | ⊕ `CONTINUES_FROM` |
| `BRANCHES_FROM` | Divergent thread from target | ⊕ `CONTINUES_FROM` |
| `INFORMED_BY` | Prior knowledge dependency, not continuation | — |
| `REFERENCES` | Audit-only citation; non-loading on resumption | — |
| `SPAWNED_FROM` | Task/sub-episode origin | — |
| `MERGED_INTO` | Convergence record | — |
| `PEER_REVIEWED_BY` | Cross-agent review relationship | — |

**Resumption isolation rule:** On episode resumption, the loader MUST follow `CONTINUES_FROM` and `SUPERSEDES` links (spine traversal) and MAY follow `INFORMED_BY` and `SPAWNED_FROM` links up to one hop. `REFERENCES` links are non-loading — they are available for audit but do not trigger episode content retrieval.

---

#### §4 Inference Signal Specification

Signal combination is implementation-side (§12 behavioral tier). The protocol requires that all signals contributing to a candidate's composite score be recorded in `inference_signals` at the time of candidate proposal.

```
Signal {
  signal_type:    SignalType    // SEMANTIC_SIMILARITY | PARTICIPANT_OVERLAP | TEMPORAL_PROXIMITY | EXPLICIT_REFERENCE | SHARED_ARTIFACT
  signal_weight:  Float         // weight applied to this signal in composite score computation
  signal_value:   Float         // raw signal value before weighting
  computed_at:    Timestamp
}
```

**Audit-the-decision pattern (§12):** The protocol does not mandate how signals are combined. It mandates that the combination — which signals, which weights, which threshold — is recorded. This record is the basis for calibration and retrospective audit.

---

#### §5 Audit Event Types — Cross-Episode Linking

```
AuditEventType (linking):
  LINK_PROPOSED          // inference candidate surfaced; score >= DISCOVERY_THRESHOLD
  LINK_ACCEPTED          // human-confirmed or auto-accepted (score >= AUTO_ACCEPT_THRESHOLD)
  LINK_REJECTED          // human-rejected candidate
  CANDIDATE_REJECTED     // inference candidate below threshold, not surfaced
  LINK_HEALTH_CHANGED    // health state transition recorded
  LINK_QUARANTINED       // link moved to QUARANTINED state
  LINK_QUARANTINE_RESOLVED   // quarantine exited (CONFIRMED | DISSOLVED | ESCALATED)
  QUARANTINE_ESCALATED   // quarantine escalated to human review after TTL — §11.3.3
```

**`CANDIDATE_REJECTED` note:** This event fires when an inference candidate is computed but falls below `DISCOVERY_THRESHOLD` and is therefore not surfaced for human review. Recording it enables retrospective analysis of the threshold calibration — if known-good links were suppressed, the threshold was too high.

---

#### §6 Link Health State Machine

```
LinkHealthState:
  VALID        // target episode exists and version delta is within tolerance
  STALE        // target episode has advanced by minor/patch version since link creation
  FROZEN       // target episode is crystallized; link is permanently anchored to crystallized version
  BROKEN       // target episode unreachable or deleted
  QUARANTINED  // link flagged for integrity review; excluded from active traversal
```

**State transitions:**

```
VALID       → STALE        (target minor/patch version advance)
VALID       → FROZEN       (target episode crystallizes)
VALID       → BROKEN       (target episode deleted or unreachable)
VALID       → QUARANTINED  (orphan detection or integrity flag)
STALE       → BROKEN       (target episode deleted)
STALE       → QUARANTINED  (orphan detection)
QUARANTINED → VALID        (quarantine resolved: CONFIRMED)
QUARANTINED → BROKEN       (quarantine resolved: DISSOLVED — link invalid)
QUARANTINED → ESCALATED    (quarantine TTL exceeded; human review required — §11.3.3)
BROKEN      → QUARANTINED  (re-evaluation triggered)
```

**Major version advance:** A link where the target episode has advanced by a major version since link creation MUST be routed to human review. The link remains `VALID` or `STALE` during review; it does not automatically transition to `BROKEN`.

---

### Part II — Episode Grouping Interface

#### §7 `MembershipRecord` Node — Amended Schema

```
MembershipRecord {
  // Identity — immutable
  record_id:             UUID
  episode_id:            EpisodeID
  group_id:              GroupID
  group_system:          String           // "claude_project" | "notion_database" | "astp_native" | ...
  asserted_at:           Timestamp
  asserted_by:           AgentID

  // Membership characterization — included in content_hash
  membership_role:       MembershipRole   // PRIMARY | SUPPORTING | REFERENCE | ARCHIVED

  // Succession
  supersedes_record_id:  Optional<UUID>   // prior MembershipRecord this record replaces
  succession_reason:     Optional<String> // why this record supersedes the prior

  // Integrity — immutable once set
  content_hash:          Hash             // SHA3-256 of: record_id + episode_id + group_id + group_system + asserted_at + asserted_by + membership_role + supersedes_record_id + succession_reason
}
```

**Immutability rule:** `MembershipRecord` nodes are append-only. Membership changes are recorded by creating a new `MembershipRecord` with `supersedes_record_id` pointing to the prior record. The prior record is never modified or deleted. The active record for a `(episode_id, group_id)` pair is the record with no `superseded_by_record_id` in the succession chain.

---

#### §8 `ConformanceDeclaration` Node — Amended Schema

```
ConformanceDeclaration {
  // Identity — immutable
  declaration_id:        UUID
  group_id:              GroupID
  group_system:          String
  declared_at:           Timestamp
  declared_by:           AgentID

  // Versioning
  declaration_version:   SemVer           // major.minor.patch

  // Capabilities — included in content_hash
  capabilities:          Capability[]

  // Succession — excluded from content_hash
  superseded_by:         Optional<UUID>   // declaration_id of successor

  // Integrity
  declaration_hash:      Hash             // SHA3-256 of: declaration_id + group_id + group_system + declared_at + declared_by + declaration_version + capabilities
}
```

**Version semantics:**

| Change type | Version bump | Effect |
|-------------|-------------|--------|
| Field rename, type change, removal | Major | Breaking — existing `MembershipRecord` hashes may be invalid; re-verification required |
| New optional field | Minor | Compatible — existing records remain valid |
| Documentation, threshold change | Patch | Compatible — no schema effect |

**Succession rule:** When a `ConformanceDeclaration` is superseded, the prior declaration is updated with `superseded_by` pointing to the new declaration. The `superseded_by` field is excluded from `declaration_hash` — it is a lifecycle annotation, not a content field.

---

#### §9 Phase Label Scoping

Phase labels in this amendment are scoped to their document. There is no global phase namespace.

- **Cross-Episode Linking phases** are labeled: Linking Phase 1, Linking Phase 2, etc.
- **Grouping Interface phases** are labeled: Grouping Phase 1, Grouping Phase 2, etc.

Implementations referencing phases in documentation or tooling MUST use scoped labels. Bare phase numbers (e.g., "Phase 3") without document scope are non-conforming in any context where ambiguity is possible.

---

### Part III — Implementation Coordination, Verification & Lifecycle Governance

#### §11 Implementation Architecture

> This section is normative. §11.1–§11.3 specify storage architecture, verification requirements, and lifecycle governance that implementations must honor to claim conformance with Amendment v2.0. §11.4 is the canonical audit event registry. §11.5 specifies consistency requirements.

---

#### §11.1 Storage Architecture

##### 11.1.1 Consistency Model

The protocol names four storage **roles**. They are roles, not products: the provider that fills each role is the implementer's choice (§2.5.3), and one system MAY fill more than one role provided it meets the obligations of each. The role names are those of §12.1.

| Role | Holds | Consistency obligation |
|------|-------|------------------------|
| **Authoritative structural store** | Structural ground truth — links, membership records, declarations, and their relationships | Written synchronously. The single source of truth for structural state. |
| **Append-only audit store** | The audit history | Written synchronously. Authoritative for the event log. Never modified, never deleted. |
| **Semantic search index** | Vectors used to discover link candidates | Eventually consistent with the structural store. Derived; never authoritative. |
| **Ephemeral coordinator** | Working state — caches and queues | Eventually consistent. Always reconstructable from the structural and audit stores. |

**The authoritative structural store is the single source of truth for structural state.** No read operation on structural data (link health, membership records, declaration versions) may serve a response that contradicts it. Divergence of the semantic search index or the ephemeral coordinator from the structural store is a consistency error, not an alternative view.

##### 11.1.2 Structural Records

New record types and relationships introduced in Amendment v2.0. The notation is illustrative — it names what must be recorded and how records relate, not how an adapter represents them:

```
// Record types
EpisodeLink {
  link_id,
  link_strength,              // Float [0.0, 1.0]
  is_inferred,                // Boolean
  health_state,               // LinkHealthState enum
  quarantine_reason,          // Optional<String>
  quarantined_at,             // Optional<Timestamp>
  quarantine_resolved_at,     // Optional<Timestamp>
  quarantine_resolution       // Optional<QuarantineResolution>
}

MembershipRecord {
  record_id,
  membership_role,            // included in content_hash
  content_hash,
  supersedes_record_id        // Optional — succession
}

ConformanceDeclaration {
  declaration_id,
  declaration_version,        // SemVer
  declaration_hash,
  superseded_by               // Optional — succession; excluded from hash
}

// Relationships
Episode            —LINKED_TO {via: link_id}→   Episode
MembershipRecord   —SUPERSEDES→                 MembershipRecord (prior)
ConformanceDeclaration —SUPERSEDED_BY→          ConformanceDeclaration (successor)
Episode            —MEMBER_OF {record_id}→      EpisodeGroup
```

**Active-record index:** Implementations MUST maintain a materialized index for the active `MembershipRecord` per `(episode_id, group_id)` pair — defined as the record with no `superseded_by_record_id`. This is a storage-layer obligation, not a protocol mandate on query strategy.

##### 11.1.3 Semantic Search Index

Discovery uses two vector spaces, which MUST be kept separate:

| Vector space | One entry per | Required payload |
|--------------|---------------|------------------|
| **Episode content** | Episode | `episode_id`, `spine_version`, `indexed_at`, `discovery_threshold_at_index`, `auto_accept_threshold_at_index` |
| **Participant context** | (Episode, participant) | `episode_id`, `participant_id`, `context_type` |

The index stores per-Episode vectors. Link candidates are the *result* of a similarity query over them; candidates are not stored objects.

**Threshold payload fields:** `discovery_threshold_at_index` and `auto_accept_threshold_at_index` record the protocol threshold values in effect at the time this vector was indexed. This enables retrospective comparison — if thresholds were recalibrated between index time and query time, the stored values allow an auditor to determine whether a link would have been proposed under the prior regime. This is an audit-the-decision application (§12).

**Embedding model, dimensionality and distance metric are implementation choices**, and the two vector spaces need not share them — participant identity signals occupy a smaller semantic space than full episode content, and a lower-dimensional model is appropriate there. Implementations MUST NOT mix embeddings from different model families within the same vector space.

##### 11.1.4 Ephemeral Coordinator (Working State)

The coordinator holds three kinds of working state:

| State | Scope | Notes |
|-------|-------|-------|
| **Quarantine queue** | One per Episode, ordered by quarantine deadline | The default quarantine TTL is implementation-configurable. |
| **Threshold calibration state** | Workspace | Current `DISCOVERY_THRESHOLD` and `AUTO_ACCEPT_THRESHOLD`, with a history of calibration snapshots. |
| **Link health cache** | One per link | Cached `health_state` and the time it was checked. |

Key names, data structures and encodings are implementation choices.

**Quarantine queue scope:** The quarantine queue MUST be scoped per Episode. A single global queue across all Episodes would create scaling problems and scope confusion — a quarantine event in one Episode would be processed in the context of another. Implementations using a single global queue are non-conforming.

**The coordinator is always reconstructable.** All coordinator state can be rebuilt from the structural store and the audit store. Coordinator failure does not constitute data loss; it constitutes a consistency window until reconstruction completes.

---

#### §11.2 Verification Architecture

##### 11.2.1 Proof Types

Four proof types are defined for this amendment. A fifth (non-existence proof) is flagged as a known gap.

| Proof Type | What It Proves | Verified Against |
|------------|---------------|-----------------|
| `LINK_INTEGRITY` | `content_hash` matches canonical field set | Structural store |
| `MEMBERSHIP_CHAIN` | Succession chain is unbroken and hashes are valid | Structural store |
| `DECLARATION_COMPATIBILITY` | Version transition is compatible (minor/patch) or breaking (major) | Structural store |
| `AUDIT_COMPLETENESS` | All required audit events are present for a lifecycle | Audit store |

**Known gap — non-existence proof:** Proof that no `EpisodeLink` exists between Episode A and Episode B is not specified in this amendment. This is a meaningful proof type — "we never connected these two episodes" is an auditable claim — but specifying it requires additional Merkle commitments not introduced here. Implementations requiring negative-space proofs should treat this as a future amendment item.

##### 11.2.2 `LINK_INTEGRITY` Proof

```
Proof {
  proof_type:     LINK_INTEGRITY
  link_id:        UUID
  claimed_hash:   Hash           // hash stored in EpisodeLink.content_hash
  computed_hash:  Hash           // hash recomputed from canonical fields at proof time
  field_snapshot: {              // the bound fields (§2) at proof time
    link_id, source_episode, target_episode, source_episode_root, target_episode_root,
    created_at, link_type, link_strength, is_inferred, inference_signals,
    inference_threshold, retroactive, source_version, target_version
  }
  verified_at:    Timestamp
  verified_by:    AgentID
  result:         VALID | INVALID
}
```

##### 11.2.3 `MEMBERSHIP_CHAIN` Proof

```
Proof {
  proof_type:       MEMBERSHIP_CHAIN
  episode_id:       EpisodeID
  group_id:         GroupID
  chain_length:     Integer        // number of MembershipRecord nodes in succession chain
  chain_hashes:     Hash[]         // content_hash of each record, oldest first
  active_record_id: UUID           // record_id of the active (terminal) record
  verified_at:      Timestamp
  verified_by:      AgentID
  result:           VALID | INVALID | BROKEN_CHAIN
}
```

##### 11.2.4 `DECLARATION_COMPATIBILITY` Proof

```
Proof {
  proof_type:          DECLARATION_COMPATIBILITY
  prior_version:       SemVer
  new_version:         SemVer
  change_classification: COMPATIBLE | BREAKING
  affected_records:    UUID[]      // MembershipRecord IDs requiring re-verification if BREAKING
  verified_at:         Timestamp
  verified_by:         AgentID
  result:              VALID | INVALID
}
```

##### 11.2.5 `AUDIT_COMPLETENESS` Proof

```
Proof {
  proof_type:       AUDIT_COMPLETENESS
  subject_id:       UUID           // link_id or record_id
  subject_type:     EPISODE_LINK | MEMBERSHIP_RECORD
  required_events:  AuditEventType[]
  present_events:   AuditEventType[]
  missing_events:   AuditEventType[]
  verified_at:      Timestamp
  verified_by:      AgentID
  result:           COMPLETE | INCOMPLETE
}
```

##### 11.2.6 Human Ratification Verification

Human ratification of a link or membership record is verified against the crystallization chain entry in the Episode of Record.

**Session record definition:** The session record is the crystallization chain entry in the Episode of Record — the sealed spine position produced by the ratifying agent's ratification commit, verifiable against the Episode's Merkle root. For approvals by the ratifying human principal within the Episode of Record, the session record is the sealed spine position at the crystallization event, counter-signed by the ratifying human principal's approval key.

##### 11.2.7 Encryption at Rest

`MembershipRecord` content is encrypted at rest with a per-Episode key.

**Key derivation dependency:** Per-Episode encryption key derivation is not fully specified in this amendment. Implementations should treat key derivation as a future amendment item; this clause is aspirational pending that specification. The encryption-at-rest requirement stands; the key derivation mechanism is deferred.

---

#### §11.3 Lifecycle Governance

##### 11.3.1 Quarantine Lifecycle

```
Quarantine entry:
  1. Orphan detection OR integrity flag triggers LINK_QUARANTINED audit event
  2. EpisodeLink.health_state → QUARANTINED
  3. Link added to ariadne:quarantine:queue:{episode_id} with deadline = now() + ariadne:quarantine:ttl
  4. Link excluded from active traversal during quarantine

Quarantine resolution (before TTL):
  CONFIRMED:  Link validated; health_state → VALID; quarantine_resolved_at + quarantine_resolution set; LINK_QUARANTINE_RESOLVED audit event
  DISSOLVED:  Link invalid; health_state → BROKEN; quarantine_resolved_at + quarantine_resolution set; LINK_QUARANTINE_RESOLVED audit event

Quarantine escalation (TTL exceeded — §11.3.3):
  ESCALATED:  health_state remains QUARANTINED; QUARANTINE_ESCALATED audit event; human review required
```

##### 11.3.2 MembershipRecord Succession Lifecycle

```
Succession entry:
  1. New MembershipRecord created with supersedes_record_id = prior record_id
  2. Prior record updated: superseded_by_record_id = new record_id (lifecycle annotation only; excluded from content_hash)
  3. Active-record index updated to point to new record
  4. Audit event recorded

Succession is irreversible. Prior records are never deleted.
```

##### 11.3.3 Quarantine Escalation

```
AuditEvent: QUARANTINE_ESCALATED {
  link_id:           UUID
  episode_id:        EpisodeID
  quarantined_at:    Timestamp
  ttl_deadline:      Timestamp
  escalated_at:      Timestamp
  escalation_reason: String      // "TTL_EXCEEDED" | "INTEGRITY_UNRESOLVABLE" | "HUMAN_REQUIRED"
}
```

Escalated links remain in `QUARANTINED` state. They are not auto-resolved. Human review is required to transition to `CONFIRMED` or `DISSOLVED`.

---

#### §11.4 Audit Event Registry

Complete registry of all audit events introduced in Amendment v2.0:

| Event Type | Trigger | Required Fields | Storage |
|------------|---------|-----------------|---------|
| `LINK_PROPOSED` | Candidate score >= DISCOVERY_THRESHOLD | link_id, score, signals, threshold | Audit store |
| `LINK_ACCEPTED` | Human confirmation or auto-accept | link_id, accepted_by, method | Audit store |
| `LINK_REJECTED` | Human rejection of proposed candidate | link_id, rejected_by, reason | Audit store |
| `CANDIDATE_REJECTED` | Candidate below DISCOVERY_THRESHOLD | episode_pair, score, threshold | Audit store |
| `LINK_HEALTH_CHANGED` | Health state transition | link_id, prior_state, new_state | Audit store |
| `LINK_QUARANTINED` | Link moved to QUARANTINED | link_id, reason, ttl_deadline | Audit store |
| `LINK_QUARANTINE_RESOLVED` | Quarantine exited | link_id, resolution, resolved_by | Audit store |
| `QUARANTINE_ESCALATED` | Quarantine TTL exceeded | link_id, escalation_reason | Audit store |
| `MEMBERSHIP_RECORD_CREATED` | New MembershipRecord asserted | record_id, episode_id, group_id | Audit store |
| `MEMBERSHIP_RECORD_SUPERSEDED` | Succession recorded | prior_record_id, new_record_id | Audit store |
| `DECLARATION_VERSION_BUMPED` | ConformanceDeclaration versioned | declaration_id, prior_version, new_version, classification | Audit store |
| `DECLARATION_SUPERSEDED` | Declaration succeeded | prior_declaration_id, new_declaration_id | Audit store |

All audit events are stored in the append-only audit store. Audit events are never modified or deleted.

---

#### §11.5 Consistency Requirements

##### 11.5.1 Write Path

```
1. Write to the authoritative structural store (synchronous — must succeed before continuing)
2. Append to the audit store (synchronous — must succeed before continuing)
3. Propagate to the semantic search index (asynchronous — within consistency window)
4. Update the ephemeral coordinator's caches and queues (asynchronous — within consistency window)
```

Steps 1 and 2 are atomic from the protocol's perspective. A write that succeeds in the structural store but fails in the audit store is a partial write and MUST be retried or rolled back.

##### 11.5.2 Consistency Window SLA

Implementations MUST define a maximum consistency window for propagation to the semantic search index and the ephemeral coordinator.

**Required SLA:**
- Typical propagation: < 60 seconds
- Maximum propagation: 5 minutes

Implementations exceeding the maximum propagation window without a documented exception are non-conforming at the state tier (§12). Implementations MUST expose a consistency status endpoint or mechanism that allows callers to determine whether the semantic search index and the ephemeral coordinator are within the consistency window.

##### 11.5.3 Sequence Numbers and Timestamps

Two ordering mechanisms are used in this amendment. They are complementary, not redundant:

- **Sequence numbers** are scoped per-Episode and are the basis for completeness proofs within an Episode. A sequence gap within an Episode's audit log indicates a missing event.
- **Timestamps assigned by a workspace-wide monotonic timestamp authority** are the basis for ordering across Episodes. Cross-Episode temporal ordering uses timestamps, not sequence numbers, because sequence scopes do not extend across Episode boundaries.

Implementations MUST NOT use sequence numbers for cross-Episode ordering. Implementations MUST NOT use timestamps as the sole basis for within-Episode completeness proofs.

---

### §12 Protocol Scope and Conformance Boundaries

#### 12.1 The Three-Tier Taxonomy

This protocol is a contract about externalities. Internal implementation choices are sovereign.

| Tier | What it covers | Conformance |
|------|---------------|-------------|
| **Wire tier** | Schemas, edge types, hash preimages | **Required** |
| **State tier** | Lifecycle enums, audit event types, consistency SLAs | **Required** |
| **Behavioral tier** | Scoring algorithms, embedding choices, threshold tuning, internal indexing | **Not required** |

**Wire tier** conformance makes two implementations interoperable — they can exchange `EpisodeLink`, `MembershipRecord`, and `ConformanceDeclaration` structures and verify each other's hashes.

**State tier** conformance makes audit logs comparable across implementations — a third party can verify lifecycle events and consistency guarantees without knowing implementation internals.

**Behavioral tier** is sovereign. The protocol does not mandate how signals are combined, which embedding model is used, or how thresholds are tuned. These are implementation decisions.

#### 12.2 The Audit-the-Decision Pattern

Where implementation choice is permitted at the behavioral tier, the protocol mandates the audit record — what was computed, with which threshold, by which signal — not the value.

This pattern resolves all behavioral-tier questions in this amendment:

| Question | Resolution |
|----------|-----------|
| How are signals combined? | Implementation-side. Record: which signals, which weights, which composite score. |
| Which embedding model? | Implementation-side. Record: model identifier at index time. |
| What threshold values? | Implementation-side. Record: threshold values at inference time. |
| When to recalibrate? | Implementation-side. Record: prior and new threshold values, calibration event. |

**The audit record is the protocol artifact.** The decision is the implementation artifact.

#### 12.3 Future Amendment Guidance

Gaps deferred from this amendment that future amendments should address:

1. **Non-existence proofs** — Proof that no `EpisodeLink` exists between two Episodes (§11.2.1)
2. **Per-Episode encryption key derivation** — Key derivation mechanism for `MembershipRecord` encryption at rest (§11.2.7)
3. **Behavioral tier calibration protocol** — Optional (non-required) standard for threshold calibration reporting, enabling cross-implementation comparison without mandating algorithm

---

### Appendix A — Breaking Change Reference

Changes that constitute major version bumps to `ConformanceDeclaration`:

- Renaming any field in `EpisodeLink`, `MembershipRecord`, or `ConformanceDeclaration` that appears in a `content_hash` preimage
- Changing the type of any such field
- Removing any such field
- Changing the hash algorithm or canonical serialization format

Changes that constitute minor version bumps:

- Adding a new optional field to any schema node
- Adding a new `LinkType` value
- Adding a new `AuditEventType`
- Adding a new `LinkHealthState` value

Changes that constitute patch version bumps:

- Documentation corrections
- Threshold default value changes (behavioral tier)
- Editorial clarifications with no schema effect

---

### Appendix B — Conformance Checklist

An implementation claiming conformance with Amendment v2.0 MUST:

**Wire tier:**
- [ ] Implement `EpisodeLink` with all fields in §2, including `link_strength`, `is_inferred`, quarantine fields
- [ ] Implement `MembershipRecord` with `membership_role` in content_hash and succession fields
- [ ] Implement `ConformanceDeclaration` with `declaration_version` and succession fields
- [ ] Compute `content_hash` and `declaration_hash` using specified canonical field sets

**State tier:**
- [ ] Implement all `LinkHealthState` values including `QUARANTINED`
- [ ] Implement all `AuditEventType` values in §11.4
- [ ] Implement quarantine lifecycle including TTL and escalation (§11.3.1, §11.3.3)
- [ ] Scope the quarantine queue per Episode (§11.1.4); a single global queue is non-conforming
- [ ] Define and publish consistency window SLA within bounds specified in §11.5.2
- [ ] Use sequence numbers for within-Episode completeness proofs; timestamps assigned by a workspace-wide monotonic timestamp authority for cross-Episode ordering

**Behavioral tier (sovereign — no conformance requirement):**
- Signal combination algorithm
- Embedding model selection
- Threshold calibration strategy
- Internal indexing implementation


## 21. Layer 3 — Workflow & Execution DAG

This section defines **Layer 3** — the Workflow & Execution DAG, the provenance record of *how* an Episode's cognition was carried out (workflow declarations, execution steps, skill invocations). Layer 3 is cryptographically isolated from the Spine: it references Layers 1/2 by ID only and never participates in Spine hashing. It integrates the normative content first published as **Amendment v3.0** (SPEC v3.1.0); that amendment file is now historical-reference only. The CIA Declaration conformance rule (originally numbered G-19, which collided with the §19 Branch/Fork/Merge taxonomy) is **renumbered G-36** here. The internal §1–§13 numbering below is the amendment's original scheme, scoped within §21.

### Part I — Layer 3 Architecture

#### §1 Three-Layer Cognitive Model

The ASTP protocol now defines **three layers** of cryptographic persistence, each owned by a distinct authority and each isolated from the others' hash integrity:

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1 — Merkle Spine (kernel-owned, hash-chained)         │
│  EpisodeNode, IntentionNode, BeliefNode, SignalNode, …       │
│  → Authoritative cognitive record. Owned by the protocol     │
│    kernel implementation. Hash-chained. Witness-signable.    │
└────────────────────────┬─────────────────────────────────────┘
                         │ referenced by ID only
┌────────────────────────▼─────────────────────────────────────┐
│  LAYER 2 — Episode Content (Episode spine tree)              │
│  Segments, BranchPoints, HITLEventNodes                      │
│  → Episode body. Adaptive tree under the Spine.              │
└────────────────────────┬─────────────────────────────────────┘
                         │ referenced by ID only
┌────────────────────────▼─────────────────────────────────────┐
│  LAYER 3 — Workflow & Execution DAG (CIA-owned)              │
│  WorkflowDeclaration, ExecutionNode, SkillInvocation         │
│  → What was done. Written by the workspace's Cognitive       │
│    Implementation Authority. Hash-isolated from Spine.       │
└──────────────────────────────────────────────────────────────┘
```

**Layer 3's purpose** is to answer the questions that Layers 1 and 2 cannot:

- *What did the agent (or its delegates) actually do to act on this intention?*
- *Which discrete steps composed that execution?*
- *Which skills were invoked, by whom, with what parameters, with what result?*
- *Where did execution fail, and what state preceded that failure?*

These questions are forensic; their answers must survive arbitrary failure modes (process kill, partial writes, retries) without contaminating the cognitive record above them.

#### §2 Layer Isolation and the Spine Firewall

The defining invariant of Layer 3 is **isolation from Spine hash computation**:

> **Invariant L3-I1 (Spine Isolation).** No field of any Layer 3 node, and no field of any Layer 3 edge, shall be included in the preimage of any Layer 1 or Layer 2 hash. Layer 3 nodes reference Layer 1/2 nodes by `node_id` (UUID) only. Layer 1/2 nodes shall not contain references to Layer 3 `node_id` values in their hash preimage.

This invariant has three consequences that conforming implementations MUST guarantee:

1. **No write to Layer 3, under any circumstance, can invalidate any Spine hash.** The kernel may freeze, the Spine may seal, the Spine fingerprint may be witness-signed — none of these states are altered by Layer 3 activity.
2. **A workspace whose Layer 3 is entirely absent or entirely corrupt remains a valid ASTP workspace** at Layers 1 and 2. Layer 3 is a strict augmentation, never a dependency.
3. **Layer 3 verification is performed against its own audit chain** (§11), not by walking the Spine. Verification at Layer 3 confirms execution-record integrity; verification at Layer 1 confirms cognitive integrity. The two verifications are independent.

The protocol layer makes no claim about whether Layer 3 storage and Layer 1/2 storage share infrastructure. They MAY share a database, a blob store, an index. Adapter choices are unconstrained. What is constrained is the **hash preimage** — never crosses the layer boundary.

#### §3 The Sole-Writer Principle — Cognitive Implementation Authority (CIA)

A second invariant governs **who** may write Layer 3:

> **Invariant L3-I2 (Sole Writer).** For each Layer 3 node type within a workspace, exactly one entity — the **Cognitive Implementation Authority** (CIA) for that node type in that workspace — is authorized to issue creation writes. Writes from any other source MUST be rejected at the wire tier.

A CIA is a protocol-level role, not a specific implementation technology. The CIA for `WorkflowDeclaration` in a workspace may be:

- An MCP server (as in the reference deployment — its adapter guide, `IMPLEMENTATION-LAYER3.md` §6.4, ships with that adapter),
- An in-process module of a single-process implementation,
- A network-attached daemon with cryptographic identity,
- Any other entity that the workspace's `ConformanceDeclaration` names.

What matters is that **the CIA is unique** for a given (workspace, node type) pair, and that the implementation demonstrates enforcement. Enforcement may take any of the following forms (this list is illustrative, not exhaustive):

- Database-level access control (only the CIA's principal has INSERT on the relevant tables/collections).
- Application-layer guards (all write paths route through the CIA, no parallel ingestion).
- Cryptographic identity (writes are signed by the CIA's key; non-CIA writes fail signature verification).
- Audit-detection (writes by non-CIA principals are admitted but flagged in the audit chain as `WIRE_VIOLATION`, which conforming verifiers reject).

A workspace MAY designate **the same CIA for all three Layer 3 node types**, and the reference implementation does so. A workspace MAY also designate **distinct CIAs per node type** — for example, one authority writes WorkflowDeclarations under organizational policy review, while another writes ExecutionNodes from a high-throughput operational substrate. The protocol permits either; the audit chain records which CIA wrote each record (§11).

> **Conformance G-36 (CIA Declaration).** Every conforming workspace's `ConformanceDeclaration` MUST name the CIA for each Layer 3 node type, identify the enforcement mechanism, and commit to the chosen mechanism in the wire tier. Changes to CIA assignment are protocol events that MUST be recorded in the audit chain (event type: `CIA_DESIGNATION_CHANGED`, deferred to a future amendment if/when CIA changes prove non-rare).

The sole-writer principle is what makes verifiable cognition extend across the execution layer. Without it, an attacker (or an unaware sibling process) could inject forged execution records whose audit chain would still verify cryptographically. The CIA designation is the protocol's commitment that *only one principal* could have written a given record, and the audit chain's job is to prove the chain of those writes is unbroken.

---

### Part II — Data Model

#### §4 WorkflowDeclaration

A `WorkflowDeclaration` is the intent-record for a discrete autonomous agentic workflow. It is created at workflow initiation — before any execution step writes — and it persists independently of whether execution completes. A WorkflowDeclaration with zero child ExecutionNodes is a valid forensic state ("workflow declared but never started"), and the protocol assigns it no different treatment from a fully-executed workflow.

```
WorkflowDeclaration {
  // Identity
  node_id            UUID            [primary key, immutable]
  node_type          "WorkflowDeclaration"  [literal, immutable]
  schema_version     String          [semver, immutable]

  // Spine References (Layer 1, by ID only)
  episode_id         UUID            [→ EpisodeNode, REQUIRED, immutable]
  intention_id       UUID            [→ IntentionNode, NULLABLE, immutable]

  // Mandate Provenance — see §13 for Mandate's deferred protocol surface
  mandate_id         UUID            [→ Mandate, NULLABLE, immutable]

  // Declaration Content
  workflow_name      String          [human-readable identifier, immutable]
  workflow_version   String          [semver, default "1.0.0", immutable]
  declared_by        String          [agent or CIA identifier, immutable]
  declared_at        ISO8601         [immutable]

  // Execution Parameters
  input_context      JSON            [parameters at declaration, immutable]
  expected_outputs   JSON            [success criteria, NULLABLE, immutable]
  timeout_ms         Integer         [NULLABLE — absent = no timeout, immutable]

  // Mutable Terminal State (the only mutation surface in Layer 3)
  status             WorkflowStatus  [DECLARED | IN_PROGRESS | COMPLETED | FAILED | INTERRUPTED]
  status_updated_at  ISO8601         [updated on every status transition]
  error_detail       JSON            [NULLABLE, populated on FAILED/INTERRUPTED close]

  // Integrity
  content_hash       String          [hash of all IMMUTABLE fields; see §8]
}
```

**Immutability**: every field above is immutable after creation **except** `status`, `status_updated_at`, and `error_detail`. The mutable trio constitutes the controlled mutation surface; no other mutation is permitted. The state machine governing valid `status` transitions is given in §10.

**Hash preimage note (§8 governs the byte form):** `status`, `status_updated_at`, `error_detail`, and `content_hash` itself are **excluded** from the preimage. `mandate_id` and `intention_id`, though nullable, are **included** — they are immutable provenance fields, and their nullability is itself part of the immutable record. A WorkflowDeclaration declared with `mandate_id = null` produces a different hash than one declared with a non-null `mandate_id`, even if no other field differs.

#### §5 ExecutionNode

An `ExecutionNode` is the atomic record of one discrete execution step within a workflow. **ExecutionNodes are terminal-on-write**: the `status` field is final at the moment of creation, and no update path exists. A failed step that is retried produces a *new* ExecutionNode with the same `step_name`, a new `node_id`, and a new `sequence_index`; the original failed node is preserved unchanged. This guarantees that the failure trace is a permanent forensic record, not erasable by retry.

```
ExecutionNode {
  // Identity
  node_id            UUID            [primary key, immutable]
  node_type          "ExecutionNode" [literal, immutable]
  schema_version     String          [semver, immutable]

  // Workflow & Episode References (Layer 3 and Layer 1, by ID only)
  workflow_id        UUID            [→ WorkflowDeclaration, REQUIRED, immutable]
  episode_id         UUID            [→ EpisodeNode, REQUIRED, immutable; denormalized for query speed]

  // Sequence
  sequence_index     Integer         [0-based position in workflow, immutable]
  step_name          String          [human-readable step identifier, immutable]

  // Execution Record
  agent_id           String          [executing agent identifier, immutable]
  executed_at        ISO8601         [immutable]
  duration_ms        Integer         [NULLABLE if interrupted, immutable]

  // Input / Output State
  input_state        JSON            [REQUIRED — may be {}, immutable]
  output_state       JSON            [NULLABLE if failed or interrupted, immutable]

  // Terminal Status (written once, never updated)
  status             ExecutionStatus [COMPLETED | FAILED | INTERRUPTED]
  error_detail       JSON            [NULLABLE — populated when status ≠ COMPLETED]
  error_type         ErrorType       [NULLABLE — required when status ≠ COMPLETED]

  // Integrity
  content_hash       String          [hash of all fields except content_hash; see §8]
}
```

**Immutability**: every field is immutable. There is no write-after-create path of any kind.

**Hash preimage note:** all fields except `content_hash` itself contribute to the preimage. Unlike WorkflowDeclaration, `status` is **included** in the ExecutionNode hash — because it is terminal-on-write, never mutated, and forensically meaningful (the hash binds the agent's record of *what status was written*, not just *what data*).

**The retry pattern is a protocol commitment, not an adapter choice.** If an implementation provides a "retry" surface that mutates the prior ExecutionNode, it is non-conforming. Retry creates a new node.

#### §6 SkillInvocation

A `SkillInvocation` records a single skill invocation performed within an ExecutionNode. It is the protocol surface for capturing what skills (in any sense the workspace's CIA defines that term — markdown-driven, capability-registry-resolved, tool-call-style, model-context-protocol-tool, or otherwise) were invoked in service of a step. SkillInvocation is **optional**: an ExecutionNode may complete without any SkillInvocation children (a step that consists entirely of native agent reasoning, for instance).

```
SkillInvocation {
  // Identity
  node_id            UUID            [primary key, immutable]
  node_type          "SkillInvocation" [literal, immutable]
  schema_version     String          [semver, immutable]

  // Parent References (Layer 3 and Layer 1, by ID only)
  execution_node_id  UUID            [→ ExecutionNode, REQUIRED, immutable]
  workflow_id        UUID            [→ WorkflowDeclaration, REQUIRED, immutable; denormalized]
  episode_id         UUID            [→ EpisodeNode, REQUIRED, immutable; denormalized]

  // Skill Identity — open behavioral-tier surface (§12)
  skill_id           String          [implementation-defined string, immutable]
  skill_source       String          [implementation-defined enum value, immutable]
  skill_version      String          [NULLABLE, implementation-defined, immutable]

  // Invocation Record
  invoked_by         String          [agent or CIA identifier, immutable]
  invoked_at         ISO8601         [immutable]
  duration_ms        Integer         [NULLABLE, immutable]

  // Parameters & Result
  input_parameters   JSON            [REQUIRED — may be {}, immutable]
  output_result      JSON            [NULLABLE if failed, immutable]

  // Terminal Status
  status             SkillStatus     [COMPLETED | FAILED | INTERRUPTED]
  error_detail       JSON            [NULLABLE, immutable]

  // Reserved — Skill Registry bridge (deferred; see §13)
  registry_id        UUID            [NULLABLE, EXCLUDED from content_hash]

  // Integrity
  content_hash       String          [hash of all fields except content_hash and registry_id; see §8]
}
```

**Immutability**: all fields immutable except `registry_id` (a deferred field; see §13). `registry_id` may be populated later by a backfill operation **without** invalidating `content_hash`, because it is excluded from the preimage by design.

**Hash preimage note:** `registry_id` is the **only** Layer 3 field excluded from a content hash for reasons other than mutation. Its exclusion is a forward-compatibility provision (see §13).

**On `skill_id` and `skill_source`:** these fields are deliberately open. The protocol does not constrain what counts as a "skill," what counts as a "source," or how implementations choose between sources. The protocol's commitment is that *whatever the implementation chose, it is recorded immutably and contributes to the content hash.* This is the **audit-the-decision pattern** (§12) applied to skill taxonomy.

#### §7 Cross-Layer References

All Layer 3 → Layer 1/2 references are by `node_id` (UUID). No Layer 3 field is embedded by value in any Layer 1/2 hash. The seven edges introduced by this amendment are:

| Edge | From | To | Cardinality | Required? | Purpose |
|------|------|-----|-------------|-----------|---------|
| `DECLARED_WITHIN` | `WorkflowDeclaration` | `EpisodeNode` | many-to-one | REQUIRED | Workflow's episode anchor |
| `SERVES_INTENTION` | `WorkflowDeclaration` | `IntentionNode` | many-to-one | OPTIONAL | BDI-spawned workflow's intention link |
| `SPAWNED_BY_MANDATE` | `WorkflowDeclaration` | `Mandate` | many-to-one | OPTIONAL | Faculty-delegation provenance |
| `EXECUTES_WITHIN` | `ExecutionNode` | `WorkflowDeclaration` | many-to-one | REQUIRED | Step's workflow parent |
| `PRECEDES` | `ExecutionNode` | `ExecutionNode` | flexible | OPTIONAL | Sequence ordering (absent on first step) |
| `INVOKED_WITHIN` | `SkillInvocation` | `ExecutionNode` | many-to-one | REQUIRED | Skill's step parent |
| `SKILL_PRECEDES` | `SkillInvocation` | `SkillInvocation` | one-to-one | OPTIONAL | Skill chaining within a step |

The edge **names** above are normative at the protocol level. Edge **storage format** is adapter-defined: implementations using a graph database MAY store them as native edges; implementations using a relational database MAY store them as foreign keys; implementations using a document store MAY store them as embedded reference arrays. Whatever the storage, conforming implementations MUST expose query paths equivalent to the seven edges (see Appendix A for reference patterns).

**Edge property normativity.** Edge property *names* are normative where given (e.g., `PRECEDES` carries `sequence_gap: Integer` and `edge_type: SEQUENTIAL | CONDITIONAL | PARALLEL`). Edge property *types* are normative. Additional implementation-specific edge properties are permitted but MUST NOT alter the semantics of the seven core edges.

---

### Part III — Integrity and Lifecycle

#### §8 Hash Preimages — Deterministic Serialization Requirement

The protocol does not lock Layer 3 implementations to a specific byte-form for hash preimages. It does, however, impose three normative requirements:

> **Conformance W-L3-1 (Determinism).** Each Layer 3 node type's `content_hash` MUST be computed from a deterministic byte serialization of its immutable-and-hashable field set. The same field values MUST always produce the same hash, on any conforming implementation.

> **Conformance W-L3-2 (Field Inclusion).** The byte serialization MUST include every field marked immutable-and-hashable in §4, §5, and §6 exactly once. It MUST exclude every field marked excluded-from-hash. No additional fields may contribute to the hash.

> **Conformance W-L3-3 (Documentation).** The implementation MUST document its chosen byte serialization in its `ConformanceDeclaration`, in sufficient detail that an independent verifier can reproduce any node's hash from its field values.

Two valid byte-serialization forms are illustrated here:

**Form A — Length-prefixed concatenation (Spine-style, SHA3-256), modeled on SPEC.md §5.2:**

```
preimage = (
  node_id                              (16 bytes, UUID)
  len(node_type).to_bytes(4, "big")    (4 bytes, length prefix)
  node_type                            (variable, UTF-8)
  len(schema_version).to_bytes(4, "big")
  schema_version                       (variable, UTF-8)
  …                                    (remaining immutable fields, in declared order)
)
content_hash = SHA3-256(preimage).hex()
```

**Form B — Ordered JSON, used by the reference implementation (with SHA3-256):**

```
payload = {field: value for each immutable field, in the declared preimage order}
canonical = json.dumps(payload, sort_keys=False, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
content_hash = SHA3-256(canonical).hex()
```

(The reference implementation uses **SHA3-256** and **declared field order** — not SHA-256 or key-sorting — consistent with the protocol's SHA3-256 commitment in §5. Per this section the byte-form remains implementation-open; a different conforming implementation MAY choose SHA-256 or key-sorted JSON, provided it is internally consistent.)

Both forms satisfy W-L3-1, W-L3-2, and W-L3-3. An implementation choosing Form A and an implementation choosing Form B will produce **different hashes for the same field values** — this is intentional and acceptable. Cross-implementation hash equivalence is not a protocol requirement at Layer 3; cross-implementation *verifiability* is, and is achieved via the documented serialization, not via a single canonical hash function.

**Excluded fields** (per §4–§6, summarized):

| Node | Excluded from `content_hash` |
|------|------------------------------|
| `WorkflowDeclaration` | `status`, `status_updated_at`, `error_detail`, `content_hash` itself |
| `ExecutionNode` | `content_hash` itself |
| `SkillInvocation` | `registry_id`, `content_hash` itself |

#### §9 Immutability Invariants

> **Invariant L3-I3 (Terminal-on-Write).** `ExecutionNode` and `SkillInvocation` are fully immutable after creation. No field of either type may be altered. Implementations MUST reject any update operation.

> **Invariant L3-I4 (WorkflowDeclaration Mutation Surface).** The only mutable fields on `WorkflowDeclaration` are `status`, `status_updated_at`, and `error_detail`. Any mutation to any other field is a wire-tier violation. Mutations to the permitted three are constrained by the state machine of §10.

> **Invariant L3-I5 (Retry-by-New-Node).** A retried execution step MUST produce a new `ExecutionNode` with a new `node_id` and a new `sequence_index`. The prior `ExecutionNode` is preserved unchanged. Implementations MUST NOT provide a "retry" surface that mutates a prior node.

#### §10 Workflow Status State Machine

`WorkflowDeclaration.status` follows this transition graph:

```
                                    ┌─────────────┐
            ┌─────────────────────► │ INTERRUPTED │  (process killed before
            │                       └─────────────┘   any ExecutionNode written)
            │
   ┌──────────────┐  first ExecutionNode write   ┌─────────────┐
   │   DECLARED   │ ───────────────────────────► │ IN_PROGRESS │
   └──────────────┘                              └──────┬──────┘
                                                        │
                                                        ▼
                                       ┌──────────────────────────────┐
                                       │  close_workflow(COMPLETED)   │ ──► COMPLETED
                                       │  close_workflow(FAILED)      │ ──► FAILED
                                       │  close_workflow(INTERRUPTED) │ ──► INTERRUPTED
                                       └──────────────────────────────┘
```

**Auto-transition rule:** the first creation of an `ExecutionNode` with a given `workflow_id` MUST transition that workflow's `status` from `DECLARED` to `IN_PROGRESS` atomically with the ExecutionNode write. The transition is a wire-tier guarantee: a workspace whose `WorkflowDeclaration.status` is `DECLARED` while ExecutionNodes for it exist is non-conforming.

**Terminal states:** `COMPLETED`, `FAILED`, and `INTERRUPTED` are terminal. No transition out of these states is permitted. A workflow in any terminal state is closed permanently.

**Two distinct `INTERRUPTED` states are observable**, both valid:
- WorkflowDeclaration with `status = INTERRUPTED` and zero ExecutionNodes — declared, never started.
- WorkflowDeclaration with `status = INTERRUPTED` and one or more ExecutionNodes (the last of which may itself have status `INTERRUPTED`) — started, terminated mid-execution.

Neither is a schema violation. Conforming verifiers MUST distinguish them in forensic output.

#### §11 Audit Event Registry

Layer 3 writes are anchored to the protocol's audit chain by four new `CognitiveDeltaType` values:

| Event Type | Trigger | Required Fields | Storage |
|------------|---------|-----------------|---------|
| `WORKFLOW_DECLARED` | `WorkflowDeclaration` creation | `workflow_id`, `episode_id`, `intention_id` (nullable), `mandate_id` (nullable), `declared_by`, `declared_at`, `content_hash`, `cia_identifier` | Audit store, append-only |
| `EXECUTION_RECORDED` | `ExecutionNode` creation | `execution_node_id`, `workflow_id`, `episode_id`, `sequence_index`, `agent_id`, `status`, `executed_at`, `content_hash`, `cia_identifier` | Audit store, append-only |
| `SKILL_INVOKED` | `SkillInvocation` creation | `skill_invocation_id`, `execution_node_id`, `workflow_id`, `episode_id`, `skill_id`, `skill_source`, `invoked_by`, `invoked_at`, `status`, `content_hash`, `cia_identifier` | Audit store, append-only |
| `WORKFLOW_CLOSED` | `close_workflow` operation (§10) | `workflow_id`, `final_status`, `status_updated_at`, `error_detail` (nullable), `cia_identifier` | Audit store, append-only |

**Audit chain integrity.** Each Layer 3 audit event is hash-chained per the existing protocol convention: each record carries `prev_audit_hash` pointing at the preceding record in its chain, and records form an append-only sequence per workspace (or per chain-key as the implementation declares). The chain key for Layer 3 events MAY be the `episode_id` (reference implementation choice) or any other declared key, provided the implementation documents the choice in its `ConformanceDeclaration` and is consistent within a workspace.

**`cia_identifier` is mandatory in every Layer 3 audit event.** The principal that performed the write — the workspace's designated CIA for that node type — MUST be recorded. This is what makes the sole-writer principle (§3) verifiable: a verifier walking the audit chain can confirm that every L3 write was performed by the declared CIA, and that no other principal contributed.

**Conformance W-L3-4 (Audit Emission).** Every Layer 3 node creation and every `WorkflowDeclaration.status` mutation MUST emit the corresponding audit event into the chain **before** the operation is considered durable. Implementations MAY order these writes audit store → structural store → index, in which case the audit-event write precedes the node creation in the structural store.

---

### Part IV — Conformance and Governance

#### §12 Three-Tier Conformance

This amendment slots into the conformance taxonomy established by Amendment v2.0 §12:

| Tier | What Layer 3 covers at this tier | Required? |
|------|----------------------------------|-----------|
| **Wire** | Node schemas (§4–§6), edge names (§7), hash preimage rules (§8), immutability invariants (§9), state machine (§10), audit event types and required fields (§11), CIA sole-writer enforcement (§3) | **REQUIRED** |
| **State** | Status transition semantics, retry-by-new-node, distinction between the two `INTERRUPTED` states | **REQUIRED** |
| **Behavioral** | Hash byte-form choice (Form A / Form B / other), `skill_id` and `skill_source` vocabularies, CIA enforcement mechanism, audit-chain chain-key choice, edge storage representation, denormalization choices | **NOT REQUIRED** — but the audit-the-decision pattern applies: the choice MUST be documented in the `ConformanceDeclaration`. |

**Audit-the-decision pattern applied to Layer 3:**

| Question | Where the protocol commits | Where the implementation chooses |
|----------|---------------------------|----------------------------------|
| What hash algorithm? | Result MUST be deterministic | Implementation picks (SHA3-256 / SHA-256 / other) |
| What byte form? | Field inclusion is fixed | Implementation picks (concatenation / canonical JSON / other) |
| What `skill_source` values are valid? | Field is recorded immutably | Implementation defines its enum |
| Who is the CIA? | Sole-writer principle | Workspace names the entity in its `ConformanceDeclaration` |
| How is CIA enforcement implemented? | Enforcement at wire tier required | Implementation picks (DB ACL / app guard / signing / audit-detection) |
| What is the audit chain key? | Append-only, hash-chained, per-chain-key | Implementation picks the key dimension |

#### §13 Deferred Items

Three protocol surfaces touched by this amendment are explicitly deferred to future amendments:

1. **Mandate — full protocol surface.** This amendment introduces `mandate_id` as an optional, immutable, hash-included field on `WorkflowDeclaration`, and the `SPAWNED_BY_MANDATE` edge to a `Mandate` node. The `Mandate` node type itself — its fields, its hash preimage, its lifecycle, its position in the layer hierarchy (Mandate is most naturally a Layer 1 or Layer 2 cognitive primitive, not Layer 3) — is **not specified by this amendment**. Conforming implementations MAY treat `Mandate` as an opaque reference for the purposes of Layer 3 conformance. A future amendment will define the full Mandate surface.

2. **Skill Registry.** The `SkillInvocation.registry_id` field is reserved for a future protocol surface that catalogues skills as first-class addressable entities. Until that surface is defined, conforming implementations MUST leave `registry_id` null. The field's exclusion from `content_hash` is a deliberate forward-compatibility provision: when the Skill Registry amendment ships, a backfill operation MAY populate `registry_id` on existing `SkillInvocation` records without invalidating their content hashes.

3. **SkillInvocation as Spine-resident node.** Some implementations may eventually want SkillInvocation to participate in Spine hashing — turning skill invocation into a cryptographically-anchored cognitive primitive for ecosystems where agent cognition is substantially composed of skill chains rather than native reasoning. This amendment **declines** that promotion: SkillInvocation remains a Layer 3 node. A future major amendment may revisit this decision once production usage of Layer 3 has informed the design.

---

### Appendix A — Reference Adapter Notes (Non-Normative)

This specification does not describe any particular storage provider. One complete adapter path for Layer 3 — edge storage, suggested indexes, forensic query patterns, and how a deployment designates and enforces its Cognitive Implementation Authority — is described in the reference deployment's adapter guide (`IMPLEMENTATION-LAYER3.md` §6), which ships with that adapter rather than with this specification. That material is non-normative: conforming implementations need not adopt any of it.

---

### Appendix B — Conformance Checklist

A conforming Layer 3 implementation MUST:

- [ ] Implement `WorkflowDeclaration`, `ExecutionNode`, and `SkillInvocation` with the fields specified in §4–§6, respecting all immutability constraints.
- [ ] Support all seven edge types named in §7 (storage form is unconstrained).
- [ ] Compute `content_hash` from a documented deterministic serialization per §8, including only the fields marked immutable-and-hashable and excluding all fields marked excluded-from-hash.
- [ ] Enforce the immutability invariants of §9 — reject all mutation attempts on ExecutionNode and SkillInvocation; permit only `status`, `status_updated_at`, `error_detail` mutations on WorkflowDeclaration.
- [ ] Enforce the WorkflowDeclaration state machine of §10, including the atomic auto-transition `DECLARED → IN_PROGRESS` on first ExecutionNode write.
- [ ] Emit `WORKFLOW_DECLARED`, `EXECUTION_RECORDED`, `SKILL_INVOKED`, `WORKFLOW_CLOSED` audit events per §11, with `cia_identifier` populated, into a documented append-only hash-chained audit log.
- [ ] Designate, in its `ConformanceDeclaration`, exactly one Cognitive Implementation Authority per Layer 3 node type, identify the enforcement mechanism, and demonstrate enforcement at the wire tier (§3, §12).
- [ ] Document its chosen hash byte serialization in sufficient detail that an independent verifier can reproduce any Layer 3 node's hash from its field values (§8, W-L3-3).
- [ ] Document its `skill_source` vocabulary, its audit chain-key dimension, and its CIA enforcement mechanism in its `ConformanceDeclaration` (§12, audit-the-decision pattern).
- [ ] Leave `SkillInvocation.registry_id` null pending the future Skill Registry amendment (§13 item 2).

A conforming Layer 3 implementation MUST NOT:

- [ ] Include any Layer 3 field in the preimage of any Layer 1 or Layer 2 hash (§2, L3-I1).
- [ ] Mutate any field of an `ExecutionNode` or `SkillInvocation` after creation (§9, L3-I3).
- [ ] Mutate any field of a `WorkflowDeclaration` other than the three permitted (§9, L3-I4).
- [ ] Provide a "retry" surface that updates a prior `ExecutionNode` (§9, L3-I5).
- [ ] Admit Layer 3 writes from any principal other than the designated CIA for the relevant node type (§3, L3-I2).
- [ ] Populate `SkillInvocation.registry_id` until the future Skill Registry amendment defines its semantics (§13 item 2).

## 22. References

Public standards this document relies on:

| Reference | Title | Used in |
|-----------|-------|---------|
| FIPS 202 | *SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions*, NIST, August 2015 | SHA3-256, all hashing (§5.1) |
| RFC 2119 | *Key words for use in RFCs to Indicate Requirement Levels*, BCP 14, March 1997 | Requirement keywords (Conventions) |
| RFC 8174 | *Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words*, BCP 14, May 2017 | Requirement keywords (Conventions) |
| RFC 5869 | *HMAC-based Extract-and-Expand Key Derivation Function (HKDF)*, May 2010 | Node key hierarchy (§16.2) |
| RFC 8032 | *Edwards-Curve Digital Signature Algorithm (EdDSA)*, January 2017 | Ed25519 signatures on HITL events (§4.6) |
| RFC 9562 | *Universally Unique IDentifiers (UUIDs)*, May 2024 (obsoletes RFC 4122) | `node_id` and other UUID-typed identifiers (§4.1, §5.2) |
| SemVer 2.0.0 | *Semantic Versioning 2.0.0*, https://semver.org/ | Protocol and declaration version numbers ([`VERSIONING.md`](./VERSIONING.md), §20) |

---

*ASTP (AI State Tree Protocol) is developed by Scorched Earth Labs.*
