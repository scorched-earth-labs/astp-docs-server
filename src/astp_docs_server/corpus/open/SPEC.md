# ASTP — AI State Tree Protocol Specification

**Version:** 3.4.0
**Status:** Stable. The full normative protocol is defined in this document's body. (v3.4.0 adds **§12.4 Ledgered Operations** — the closed register of WIL operation values and the Tier 1 coordinated-write / Tier 2 ledger-record distinction, with governance rules G-37 and G-38 governing the *form* of an entry whenever one is written. **Which operations an implementation MUST ledger is explicitly deferred to 4.0.0** (§12.4.2): every such obligation is conformance-breaking and therefore MAJOR, requiring a ratifying Episode of Record. Additive — no existing conformant implementation is affected.) v3.3.0 added the departure-fork **orphan-recovery** surface at §19.3.7 — the `ForkOrphanMarker` node, per-class recovery field mutations, and the one permitted retroactive spine write — additively; no existing canonical form changes, so every v3.2.x-conformant implementation remains conformant. Detection cadence is non-normative.) The Phase D departure-fork lifecycle (v3.2.0) is at §19.3.5–19.3.7; cross-episode linking + grouping (v3.0.0) at §20; the Layer 3 Workflow & Execution DAG (v3.1.0) at §21. The v3.2.1 integration pass folded the former standalone amendments into the SPEC body — editorial only, no normative change. The historical amendment documents ([`AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`](./AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md) → §20, [`AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`](./AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md) → §21) are retained for provenance only. Amendment filenames retain their authoring numerals; under the canonical SPEC versioning policy ([`VERSIONING.md`](./VERSIONING.md)) they correspond to SPEC v3.0.0 and v3.1.0 respectively.
**Authors:** Scorched Earth Labs
**Date:** 2026-06-07
**Supersedes:** SPEC-v1.md (0.1.0-draft)

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
| **HITLEventNode** | A first-class node representing a human-in-the-loop decision gate. Two-phase lifecycle: INVOKED (gate raised) → RESOLVED/TIMED_OUT (decision recorded). Participates in the Merkle spine as a causal anchor. |
| **HITL Gate** | An edge from an Episode to an HITLEventNode. Typed as BLOCKS (approval required) or FOLLOWS (advisory review). |
| **Causal Anchor** | A Merkle spine leaf whose hash ancestry carries the authorization chain for subsequent segments. HITL nodes are causal anchors — post-approval segments cryptographically depend on the human decision. |
| **Adapter** | A database-specific implementation of persistence operations. |
| **ASI** | Adapter Service Interface. The abstract contract any conforming adapter must implement. |
| **Governance Rule** | A protocol invariant that any conforming implementation must enforce. |
| **Namespace Firewall** | The inviolable rule that the protocol layer (`ariadne.protocol.*`) never imports from node-type layers (`ariadne.nodes.*`). |
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
| Leaf hash construction | SHA3-256 with the position-binding preimage defined in Section 5.2. Concatenation order, length prefixing, and algorithm are fixed. |
| Spine Merkle algorithm | SHA3-256 binary Merkle tree with domain separation (LEAF:/NODE:) and deterministic leaf ordering by `sequence_index`. |
| `spine_root` semantics | The Merkle root of all domain-separated leaf hashes in `sequence_index` order. |
| `ContentDelta` / `StructuralDelta` structure | Core fields (`pre_root`, `post_root`, `delta_type`) are fixed. |
| Governance rules G-1 through G-16 | All conforming implementations enforce all protocol-mandatory governance rules. |
| Dual Index semantics | `sequence_index` is immutable and in the leaf hash. `tree_leaf_index` is mutable and NOT in the leaf hash. |
| Namespace Firewall | Protocol layer never imports from node-type layers. |

#### 2.5.3 Implementation Space (Differential-Permitted)

| Element | Permitted Variation |
|---------|-------------------|
| `NodePayload` schemas | Each node type defines its own payload schema. The protocol does not constrain payload content beyond the interface contract. |
| Storage adapter | Any conforming ASI implementation. |
| Key management infrastructure | HSM, KMS, software keystore, distributed threshold — implementation choice. |
| Signing algorithms | The protocol specifies the *data to be signed*; the signing algorithm is implementation-defined (subject to minimum security requirements). |
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
PROTOCOL LAYER — Node-Generic (ariadne.protocol.*)
  CognitiveNode, CognitiveEdge, NodePayload ABC
  Position-binding leaf hash, Merkle tree, delta records, audit chain
  Governance rules, verification, version vectors
  → No Episode symbols. No episode_id. No session_bounds.

INSTANTIATION LAYER — Node Type Registry
  NodeTypeDefinition, open enum registration
  "episode" ← Phase 1    "signal" ← Phase 2    "agent" ← Phase 2

NODE TYPE LAYER — Type-Specific Extensions (ariadne.nodes.*)
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
| **Layer 2 — Episode Content** | Segments, BranchPoints, HITLEventNodes; Adaptive Merkle Tree under the Spine | Protocol kernel | Anchored to Layer 1 via parent references |
| **Layer 3 — Workflow & Execution DAG** | WorkflowDeclaration, ExecutionNode, SkillInvocation | Cognitive Implementation Authority (per workspace, per node type — see Amendment v3.0 §3) | **Isolated**: Layer 3 nodes do NOT participate in Spine hash computation. Cross-layer references are by ID only. |

**Layer 3 was introduced by Amendment v3.0 — Workflow & Execution DAG Codification.** The full Layer 3 surface — node schemas, hash preimage rules, immutability invariants, state machine, sole-writer principle (Cognitive Implementation Authority), and audit event types (`WORKFLOW_DECLARED`, `EXECUTION_RECORDED`, `SKILL_INVOKED`, `WORKFLOW_CLOSED`) — is normatively specified in `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`. This section names Layer 3's existence and position in the persistence model; the amendment is the authoritative reference for its semantics.

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

Episode lifecycle states: ACTIVE, REBALANCING, SEALING, SEALED, SEALING_FAILED, REBALANCE_FAILED, ARCHIVED, EXPIRED.

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
  node_hash:              string?      (H(NODE: context_hash || resolution_hash))

  // Cryptographic attestation
  invocation_signature:   string?      (Ed25519 sig over context_hash, hex-encoded)
  invocation_key_fingerprint: string?  (SHA3-256 of agent public key)
  resolution_signature:   string?      (Ed25519 sig over resolution_hash, hex-encoded)
  resolution_key_fingerprint: string?  (SHA3-256 of human public key)
}
```

**Hash computation:**

- `context_hash = SHA3-256("HITL_CTX:" || request_id || episode_id || gate_type || agent || invoked_at || context_json)`
- `resolution_hash = SHA3-256("HITL_RES:" || event_id || decision || resolved_by || resolved_at || rationale)`
- `node_hash = SHA3-256("NODE:" || context_hash || resolution_hash)`

Domain separation prefixes (`HITL_CTX:`, `HITL_RES:`) prevent cross-type hash confusion.

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

Resolved HITL `node_hash` values participate in the Merkle spine as causal anchor leaves with `importance=2` (high). The spine hash changes when a HITL event resolves — the human decision becomes part of the episode's integrity fingerprint.

**Crystallization guard:**

An episode in `PENDING_HITL` status (blocking HITL gate open) cannot be crystallized. `acquire_crystallization_lock()` queries for unresolved HITLEventNode nodes before acquiring the lock. This is a hard protocol invariant — an episode with an outstanding human decision is an open episode.

**Advisory gates and CONDITIONALLY_VALID:**

Segments written while a `REVIEW_ADVISORY` gate is pending are tagged with `pending_hitl_ref` (the HITLEventNode ID). These segments are `CONDITIONALLY_VALID` — included in the spine but with a governance caveat. The advisory gate does not block episode progression.

**HITLEventNode is the only node type that permits post-creation mutation** — but only during the INVOKED → RESOLVED transition. All other transitions are immutable. This exception is enforced by G-17.

**Timeout is a recorded event.** `TIMED_OUT` is a valid terminal status treated as implicit rejection. Orphaned pending decisions are not permitted — all HITL invocations must specify a timeout policy.

## 5. Hash Chain

### 5.1 Hash Algorithm

All hashing uses **SHA3-256** (Keccak). No exceptions. This is a protocol-level commitment: changing the hash algorithm requires a major version bump.

### 5.2 Position-Binding Leaf Hash

The leaf hash preimage binds identity, type, position, content, temporal state, and graph position into a single commitment:

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

**Design rationale:**
- **Length prefixing** on variable fields prevents collision attacks (e.g., `("ep","2.0")` vs `("e","p2.0")`)
- **Unix milliseconds** for `sealed_at` avoids timezone/format non-determinism of ISO strings
- **`node_type` in preimage** makes type confusion cryptographically detectable
- **`tree_leaf_index` excluded** — the dual-index invariant requires it

The leaf hash is computed once at node creation and never recomputed.

### 5.3 Domain Separation

To prevent second-preimage attacks across tree levels:
- Leaf level: `SHA3-256(b"LEAF:" + leaf_hash)`
- Internal nodes: `SHA3-256(b"NODE:" + left + right)`

### 5.4 Merkle Tree

A binary Merkle tree over domain-separated leaf hashes. Supports:
- Full construction from leaf set
- Incremental append (O(log n))
- Inclusion proof generation (P2 — position-binding)
- Inclusion proof verification

The tree is node-type-agnostic — it operates on hash strings only.

### 5.5 Type Isolation Property

A CognitiveNode with `node_type="episode"` and one with `node_type="signal"` at the same `sequence_index` produce **different leaf hashes** because `node_type` is in the preimage.

## 6. Governance Rules

These invariants MUST be enforced by any conforming implementation.

### G-1: Write Guard

No modifications to sealed nodes. A node with non-null `sealed_at` is frozen.

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

The protocol layer (`ariadne.protocol.*`) MUST NOT import from any node-type layer (`ariadne.nodes.*`). This is enforced by automated testing.

### G-7 through G-9: Signal Governance (inherited from v1)

- **G-7:** Causal signals require a TRIGGERED edge to at least one segment
- **G-8:** Exchange entries require a prior initiation_hash on the consultation node
- **G-9:** Consultation resolution requires at least one exchange entry

### G-10: Structural Delta Content Invariant

A structural delta (rebalancing) that sets `sequence_indices_unchanged: false` is an integrity violation. Rebalancing must never alter logical ordering.

### G-11: Witness Threshold (Phase 3)

If a workspace declares `min_counter_signatures > 0` for a `node_type`, a node of that type MUST have at least that many valid `WitnessRecord` entries with distinct `witness_id` values before transitioning to SEALED state. The protocol does not mandate a default value — this is workspace-configured.

### G-12: Witness Commitment Integrity (Phase 3)

A `WitnessRecord` is invalid if `commitment_hash` does not match the computed `WitnessCommitment` over the record's fields. Invalid witness records MUST NOT count toward any threshold.

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

The audit trail is a first-class data structure. Each `AuditRecord` includes `prev_audit_hash` — a chain link that makes the trail tamper-evident independently of the delta chain.

```
AuditRecord {
  record_id, node_id, delta_id, delta_type,
  actor, actor_role,
  wall_clock, logical_clock,
  pre_state_hash, post_state_hash,
  delta_hash,
  prev_audit_hash,                   ("GENESIS" for first record)
  reason
}
```

Tampering with any record breaks the chain at that point, detectable by any verifier replaying from genesis.

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

### 9.2 Inclusion Proof (P2)

A position-binding Merkle inclusion proof proves a node exists at a specific position:

```
InclusionProof {
  sequence_index,           (the position claim)
  leaf_hash,                (content commitment — not content)
  merkle_path: Hash[],      (sibling hashes to root)
  path_directions: str[],   (left/right for each sibling)
  spine_root                (root being proven against)
}
```

Verifier recomputes domain-separated leaf hash, walks the Merkle path, confirms it reaches `spine_root`. Segment content is never revealed.

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

**Implementation note:** The advisory is in-process state (not persisted to the ephemeral coordinator) when all agents run in the same process. Distributed deployments require the advisory to be stored in the ephemeral coordinator (e.g., Redis) with a short TTL as a safety bound.

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
| `CONSULTATION_COMMIT` | 2 |
| `COLLABORATION_COMMIT` | 2 |
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

`CONSULTATION_COMMIT` and `COLLABORATION_COMMIT` describe multi-agent
interaction patterns the protocol does not itself define. They are registered
so that implementations which do ledger them collide with nothing.

#### 12.4.2 Ledgering Obligations

**Which operations an implementation MUST ledger is not specified in the 3.x
line. It is deferred to 4.0.0.**

This is deliberate, and the reasoning is worth stating rather than leaving to
inference. Every candidate obligation here is conformance-breaking: an
implementation that does not currently ledger an operation stops conforming the
moment the specification requires it. Under the versioning policy that is a
MAJOR change, and a MAJOR change to this protocol requires a ratifying Episode
of Record. Introducing such requirements through a MINOR release — or
pre-committing to them with SHOULD, which invites implementers to treat the
weaker form as settled — would either break conformance without ratification or
enshrine the current coverage gaps as the intended shape.

The vocabulary and the entry forms are stable and usable now. The obligations
are a single decision, to be taken once, at full strength, with the coverage
work completed first.

Until then: an implementation that ledgers an operation MUST do so in the form
its tier requires (G-37, G-38), and an implementation's ledger is exactly as
strong as the coverage it chooses. A verifier MUST NOT infer from a missing
entry that an operation did not occur.

## 13. Spine Tip Cache

Segment append and snapshot capture both need to know the current `max(sequence_index)` for an Episode. Without caching, every such operation requires a database traversal.

A conforming implementation SHOULD maintain a cached spine tip per Episode in the ephemeral coordinator (e.g., Redis). The cache lifecycle:

1. **Invalidate** before any segment write begins (ensures no stale reads during the write window)
2. **Update** after segment write commits (sets cache to the new max sequence_index)
3. **Read** during snapshot capture — cache hit avoids database traversal
4. **TTL** as safety bound — cached entries expire if not refreshed (handles crashed writes that never reach the update step)

**The spine tip cache is a performance optimization, not a source of truth.** The authoritative max_sequence_index is always in the structural store (e.g., Neo4j). If the cache is empty, unavailable, or suspected of being stale, the system falls back to querying the structural store directly.

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

1. Implement the `AriadneAdapter` interface
2. Enforce all governance rules
3. Preserve hash chain integrity — never modify leaf_hash, spine_root, or content_hash after creation
4. Enforce the dual-index invariant: `tree_leaf_index` never in any hash preimage
5. Respect write ordering invariants across stores
6. Support idempotent writes for WIL recovery
7. Fail loudly on errors — never silently swallow writes
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

All node keys are derived using HKDF-SHA3-256:

```
Root Key Material
    └── Workspace Key: HKDF(RKM, salt=workspace_id, info="ariadne.workspace.v1")
            └── Node Key: HKDF(WK, salt=node_id, info="ariadne.node.v1:{node_type}")
                    └── Seal Key: HKDF(NK, salt=spine_root_at_seal, info="ariadne.seal.v1")
```

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
  derivation_path:         string    (human-readable: "workspace/{wid}/node/{nid}")
  created_at:              datetime
}
```

### 16.3 Transparency Log Anchoring

#### 16.3.1 Anchor Timing

Transparency log anchoring MUST occur at **crystallization boundaries** (G-14). Crystallization is already a protocol-level state transition producing an immutable snapshot — the natural anchor point. Anchoring provides external temporal proof that the crystallization existed at wall-clock time T and was not backdated.

#### 16.3.2 Anchor Data

```
AnchorCommitment {
  node_id:                   string
  node_type:                 string
  workspace_id:              string
  crystallization_root:      string    (spine_root at crystallization)
  crystallization_sequence:  int       (sequence_index of last segment)
  logical_clock:             int
  wall_clock:                datetime
  protocol_version:          string
}
```

The `AnchorCommitment` contains only protocol-surface data. No payload internals are anchored.

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

A witness signature is a statement by an agent that it observed a specific `spine_root` for a specific `CognitiveNode` at a specific time. It is additive evidence — it does not alter the node's state or hash chain.

#### 16.4.2 Witness Commitment

```
WitnessCommitment = SHA3-256(
    node_id ‖ node_type ‖ spine_root ‖ sequence_index ‖ logical_clock ‖ role
)
```

Fields are UTF-8 encoded with `|` as separator, then hashed. The signature is over the commitment hash, not the raw fields.

#### 16.4.3 Schema: WitnessRecord

```
WitnessRecord {
  witness_id:              string    (agent_id of the witness)
  node_id:                 string
  node_type:               string
  spine_root:              string    (the specific root being witnessed)
  sequence_index:          int
  logical_clock:           int
  wall_clock:              datetime
  role:                    WitnessRole
  commitment_hash:         string    (SHA3-256 of WitnessCommitment)
  signature:               bytes
  public_key_fingerprint:  string
  protocol_version:        string
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

The `ariadne.protocol.verification` module provides the `DeltaVerifier` — the five-test gate that any conforming implementation must pass.

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
| W4 | Set `min_counter_signatures=2`, attempt seal with 2 witnesses but same `witness_id` | MUST reject (G-11 requires distinct IDs) |

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

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0-draft | 2026-04-07 | Initial extraction. Episode-centric. See SPEC-v1.md. |
| 2.0.0-draft | 2026-04-09 | CognitiveNode foundation. Dual-index. Position-binding leaf hash. Five-test gate. Namespace firewall. |
| 2.1.0-draft | 2026-04-10 | Retrieval coordination protocol: snapshot isolation (10.4), tail write advisory (10.5), HITL re-validation gate (10.6), side-effect contract (11). |
| 2.2.0-draft | 2026-04-12 | Phase 2 observability: signal_versions_read (4.5), retrieval audit records (11.1), spine tip cache (13), rebalance events (14). |
| 2.3.0-draft | 2026-04-12 | Phase 3 trust infrastructure: Protocol vs. Implementation Boundary (2.5), node key hierarchy (16.2), transparency log anchoring (16.3), witness signatures (16.4), cross-node chain proof (16.5), G-11 through G-16. |
| 2.4.0-draft | 2026-04-16 | Phase 4 HITL: HITLEventNode first-class node type (4.6), two-phase lifecycle (INVOKED→RESOLVED), HITL_GATE edges (BLOCKS/FOLLOWS), Merkle spine participation as causal anchors, PENDING_HITL crystallization guard, two-layer Ed25519 signing (agent invocation + human resolution), CONDITIONALLY_VALID advisory gates, pending_hitl_ref segment tagging, G-17 (invocation before resolution), G-18 (crystallization block). Schema version 1.2.0. |
| 2.5.0-draft | 2026-04-21 | Branch/Fork/Merge Taxonomy §19 covering BFM Phases 1–4: BranchPoint/BranchTerminus (§19.2), ForkPoint/MergePoint/BranchReturn with three-Merkle-root verification (§19.3), AsideSegment/SoliloquySegment with HASH_PLACEHOLDER content policy and Decision 1 visibility (§19.4), CoherenceFingerprint write-intercept state machine and ConfirmationCache (§19.5). New governance rules G-19 through G-29. New delta types BRANCH_CREATED/ABANDONED, FORK_CREATED/RESOLVED, MERGE_EXECUTED, ASIDE_OPENED/CLOSED, SOLILOQUY_INITIATED/CONCLUDED. AuditRecord chain integrity (`prior_audit_hash`), IntentRecord idempotency, derived lifecycle state (§19.2.4). |
| 3.0.0 | 2026-06-07 | **MAJOR** — Cross-episode linking + grouping. Source: [`AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`](./AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md). Typed `EpisodeLink` with `LinkType`, `LinkHealthState`, `Signal`/`SignalType` machinery. `EpisodeGrouping` interface (`MembershipRecord` as protocol-owned artifact; `ConformanceDeclaration` for downstream conformance). Succession-chain governance for membership/conformance. Audit-the-decision pattern for behavioral-tier implementation choices (§12). Three-tier conformance taxonomy: wire / state / behavioral. **Breaking hash preimage changes on `EpisodeLink`, `MembershipRecord`, `ConformanceDeclaration`** — see amendment Appendix A for the full breaking-change reference. `LINK_*` audit events + `assert_episode_link` operation. Phase 2 discovery primitives (link proposals + calibration loop). Audit-chain + canonical-hash helpers lifted into shared core modules. |
| 3.1.0 | 2026-06-07 | **MINOR** — Layer 3 Workflow & Execution DAG. Source: [`AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`](./AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md). New node types: `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation`. Three-Merkle-layer model formalized: Layer 1 Spine, Layer 2 episode content, Layer 3 Workflow & Execution DAG. **Layer 3 is cryptographically isolated from Spine integrity** — references Layers 1/2 by ID only; never hash-linked into the Spine; no future Layer-3 change can force a MAJOR bump on Spine grounds. Cognitive Implementation Authority (CIA) — sole-writer guarantee as wire-tier conformance principle. New `CognitiveDeltaType` variants. `ExecutionNode` and `SkillInvocationNode` immutable after creation; only mutable Layer 3 field is `WorkflowDeclaration.status` (and `status_updated_at`). Hash byte-form left open at protocol layer per amendment §3. |
| 3.2.0 | 2026-07-04 | **MINOR** — Phase D departure-fork lifecycle, defined in-body (§19.3.5–19.3.6). `create_departure_fork()`: a single directional departure into a new (continuing) Episode, distinct from the speculative `create_fork()`. New nodes `DepartureForkPointNode` (domain `DEPARTURE_FORK_POINT:`) and `ForkReturnNode` (domain `FORK_RETURN:`). Backdating integrity invariant (G-30): `spine_tip_hash_at_departure` == the fork Episode's `fork_origin_spine_tip_hash`. Lifecycle FSM `ACTIVE → COMPLETED \| ABANDONED` (`complete_departure_fork` / `abandon_departure_fork` / `declare_fork_return`); resumption is a non-event. **Declarative** return (`INCORPORATED`/`ACKNOWLEDGED`/`SUPERSEDED`), never the branch's structural merge. Immutable Episode fork provenance (§19.3.6). New `CognitiveDeltaType` variants `DEPARTURE_FORK_CREATED`/`_COMPLETED`/`_ABANDONED`/`_RETURNED`; new edges `FORK_RETURN`, `RETURNED_FROM`. Governance G-30 through G-35. **Additive — no breaking changes.** |
| 3.2.1 | 2026-07-04 | **PATCH** — SPEC integration pass. Folded the two former standalone amendments into this document's body: cross-episode linking + grouping (was `AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`) → **§20**; Layer 3 Workflow & Execution DAG (was `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`) → **§21**; References moved to §22. The amendment's CIA conformance rule was renumbered from its authoring numeral G-19 (which collided with BFM's G-19) to **G-36**. Amendment files retained for provenance only (historical-reference banners). **Editorial only — no normative change.** |
| 3.3.0 | 2026-07-05 | **MINOR** — Departure-fork orphan recovery (§19.3.7). New non-chained diagnostic satellite node `ForkOrphanMarker` (domain `FORK_ORPHAN_MARKER:`, self-hashed, excluded from the spine Merkle chain and from departure-registry queries, deduplicated one-per-orphaned-fork). Four orphan classes (A dangling point / B unanchored episode / C return-status mismatch / D stale ACTIVE). Class-B recovery defines the **one permitted retroactive `DepartureForkPointNode` write** (append + backdated anchor + cross-verify gate, byte-identical to an on-time write; escalate-don't-write on hash mismatch). New diagnostic fields on the fork point (`orphaned`, `retroactive`, `orphan_recovery_timestamp`) and the fork episode (`fork_orphaned`, `fork_orphan_class=UNANCHORED`, `status_corrected_by_orphan_recovery`, `status_corrected_at`). **Detection cadence is non-normative** (operational hygiene). **Additive — no breaking changes.** |
| 3.4.0 | 2026-08-18 | **MINOR** — Write Intent Log operation register (§12.4). Registers all 21 WIL operation values and classifies each into one of two entry forms: **Tier 1 coordinated write** (multi-store; full three-phase §12.2 protocol; `completed_at=null` past the provisional window is a recovery candidate) and **Tier 2 ledger record** (single authoritative store; one completed entry at commit; never a recovery candidate). New governance rules **G-37** and **G-38** constrain the form of an entry whenever one is written, and compel no entry to exist. §12.4.1 closes the register against extension values lacking an implementation namespace prefix, and records that `SEGMENT_COMMIT` and `SIGNAL_COMMIT` are not interchangeable. §12.4.2 **defers ledgering obligations — which operations MUST be ledgered — to 4.0.0**, since each is conformance-breaking and therefore MAJOR under [`VERSIONING.md`](./VERSIONING.md), requiring a ratifying Episode of Record; and states that a verifier MUST NOT infer from a missing entry that an operation did not occur. **Additive — no breaking changes.** |
| 3.2.2 | 2026-07-04 | **PATCH** — prose errata. Corrected the §20 hash-preimage descriptions to match the reference implementation: `EpisodeLink.content_hash`, `MembershipRecord.content_hash`, `ConformanceDeclaration.declaration_hash` are **SHA3-256** (not SHA-256), per the §5 protocol commitment; `MembershipRecord` binds `supersedes_record_id` + `succession_reason` (the prose omitted them); `EpisodeLink` excludes only `quarantine_resolved_at` / `quarantine_resolution` (the prose wrongly listed `health_state` / `health_checked_at` as excluded — they ARE hashed). Corrected the §21 Form-B attribution (the Ignis reference implementation uses SHA3-256 + declared field order, not SHA-256 + key-sorting). **The canonical hash form is unchanged — prose-only; every v3.2.1 implementation remains conformant.** |

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

`AuditRecord` is the tamper-evident append-only log for the taxonomy.

| Field | Type | Purpose |
|-------|------|---------|
| `audit_id` | UUID | Record identity |
| `delta_sequence` | int (monotonic) | Global ordering; never resets |
| `agent_id`, `session_id`, `human_actor` | string | Who |
| `wall_clock_time`, `episode_time` | ISO8601, logical clock | When |
| `delta_type` | enum | What transition (see §19.1.2) |
| `forward_delta`, `reverse_delta` | payload | Forward + reverse written simultaneously |
| `prior_audit_hash` | SHA3-256 hex | Previous record's `record_hash` — chain link |
| `record_hash` | SHA3-256 hex | `sha3_256(b"AUDIT:" + …)` |
| `caught_by` | AGENT / HUMAN / SYSTEM / UNCAUGHT | Detection provenance |
| `detection_window_open` | bool | Was active detection running? |

**Chain integrity.** `prior_audit_hash` is the previous record's
`record_hash`, forming a hash chain scoped by `episode_id`. Any
insertion, deletion, or modification of a historical record breaks the
chain from that point forward.

**Invariant.** Rollback creates a new forward record. The log is never
edited in place — a reverse delta is written as a new audit record that
references the original.

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

Prevents concurrent duplicate creation (Harmonia Scenario A). Idempotency
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

- **Spine chain.** `BranchPointNode.content_hash` is included in the
  spine chain. Branch *contents* are NOT — the spine is self-contained
  and verifiable without them.
- **Branch chain.** Starts at `BranchPointNode` and ends at
  `BranchTerminusNode`. Verifiable independently of the spine.
- **Merge verification (Phase 2).** Requires three Merkle roots — see §19.3.3.

**Depth constraint.** `branch_depth` maximum of 4 (soft). Exceeding it
raises `AriadneGovernanceError`; callers may catch and record an
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

**G-24.** The three integrity assertions in §5 Step 8 of the build spec
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

A **non-null `fork_anchor_index` with no corresponding `DepartureForkPointNode`** is the defining corruption signature of Class B (the producer patches `fork_anchor_index` only *after* the point write — §19.3.5 STEP 6).

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
(b) The `ForkOrphanMarker` never enters the spine Merkle chain — a diagnostic write
never alters an Episode's cryptographic fingerprint. (c) The retroactive point write
preserves the §19.3.5 cross-verifiable anchor by construction.

### 19.4 Phase 3 — Social/Internal Primitives

#### 19.4.1 AsideSegmentNode

Human-initiated side channel with a target agent. Domain prefix `ASIDE:`.

**G-25 (Aside Human-Initiation Invariant).** Asides are ALWAYS
human-initiated. `initiated_by_human` is required; an attempt to create
an aside without a human actor raises `AriadneGovernanceError`.
Agent-initiated internal branches are soliloquies (§19.4.2).

**G-26 (Aside Return Obligation).** An aside that remains OPEN at
episode seal is an audit violation. `check_aside_return_obligation()`
enforces this at seal time.

**Asymmetric merge on close.** `close_aside()` runs a reference scan:
external segments that hold references to aside-internal segments are
recorded in the `AsideTerminusNode` and `ASIDE_CLOSED` audit record as
`external_references_found`. The close proceeds — the scan is a
disclosure mechanism, not a block — but the leak is part of the
permanent audit trail.

#### 19.4.2 SoliloquySegmentNode

Agent-initiated private deliberation. Domain prefix
`SOLILOQUY_PLACEHOLDER:` or `SOLILOQUY_FULL:` depending on the
`content_hash_policy` field (see §19.4.3).

**G-27 (Soliloquy Human Accessibility Invariant — Decision 1).** Humans
ALWAYS have read access. `SoliloquyVisibilityPolicy.human_accessible`
defaulting or being set to `false` raises `AriadneGovernanceError`.
Deliberation content can be private to other agents, never private to
humans.

**G-28 (Soliloquy Return Obligation).** Soliloquies left ACTIVE at
episode seal are audit violations. Coherence monitoring continues
inside the soliloquy — the agent cannot use soliloquy to escape the
framework.

**Conclusion merges, chain stays.** `conclude_soliloquy()` writes a
`SoliloquyConclusionNode` carrying `conclusion_content_hash` (public)
and `deliberation_chain_hash` (tamper-evident hash of the private
chain). Only the conclusion is absorbed into the spine; the
deliberation chain remains sealed inside the `SoliloquySegmentNode`.

#### 19.4.3 Soliloquy Content Hash Policy

| Policy | Preimage | Use Case |
|--------|---------|----------|
| `HASH_PLACEHOLDER` | `SOLILOQUY_PLACEHOLDER:{id}:{ep}:{seg}:{agent}:{ts}` | Preserves Merkle chain integrity without exposing content. Default. |
| `FULL_CONTENT` | `SOLILOQUY_FULL:{id}:{ep}:{seg}:{agent}:{ts}:{chain}` | Chain content bound into the hash. Use when privacy is not required. |

The placeholder variant is the key protocol innovation for private
deliberation — the spine verifies that a node exists at a given
position without the content being recoverable from the hash.

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
and covered by unit tests against the Neo4j adapter (mocked driver). See
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

  // Semantic characterization — GAP 1
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

  // Quarantine — GAP 4
  quarantine_reason:     Optional<String>
  quarantined_at:        Optional<Timestamp>
  quarantine_resolved_at:    Optional<Timestamp>    // set when quarantine exits
  quarantine_resolution:     Optional<QuarantineResolution>  // CONFIRMED | DISSOLVED | ESCALATED

  // Integrity
  content_hash:          Hash                  // SHA3-256 of canonical field set (excludes only quarantine_resolved_at, quarantine_resolution — the resolution fields are set after the hash, on quarantine exit)
}
```

**Hash preimage note:** `quarantine_resolved_at` and `quarantine_resolution` are excluded from `content_hash`. Resolution fields record lifecycle events after link creation; including them would invalidate the hash on every quarantine close. The audit log (§5) is the authoritative record of quarantine resolution events.

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
  LINK_REJECTED          // human-rejected candidate — GAP 5
  CANDIDATE_REJECTED     // inference candidate below threshold, not surfaced — GAP 5
  LINK_HEALTH_CHANGED    // health state transition recorded
  LINK_QUARANTINED       // link moved to QUARANTINED state — GAP 4
  LINK_QUARANTINE_RESOLVED   // quarantine exited (CONFIRMED | DISSOLVED | ESCALATED) — GAP 4
  QUARANTINE_ESCALATED   // quarantine escalated to human review after TTL — Chronos §11.3.3
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
  QUARANTINED  // link flagged for integrity review; excluded from active traversal — GAP 4
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
  group_system:          String           // "claude_project" | "notion_database" | "ariadne_native" | ...
  asserted_at:           Timestamp
  asserted_by:           AgentID

  // Membership characterization — GAP 6; included in content_hash
  membership_role:       MembershipRole   // PRIMARY | SUPPORTING | REFERENCE | ARCHIVED

  // Succession — GAP 6
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

  // Versioning — GAP 7
  declaration_version:   SemVer           // major.minor.patch

  // Capabilities — included in content_hash
  capabilities:          Capability[]

  // Succession — GAP 7; excluded from content_hash
  superseded_by:         Optional<UUID>   // declaration_id of successor

  // Integrity
  declaration_hash:      Hash             // SHA3-256 of: declaration_id + group_id + group_system + declared_at + declared_by + declaration_version + capabilities
}
```

**Version semantics — GAP 7:**

| Change type | Version bump | Effect |
|-------------|-------------|--------|
| Field rename, type change, removal | Major | Breaking — existing `MembershipRecord` hashes may be invalid; re-verification required |
| New optional field | Minor | Compatible — existing records remain valid |
| Documentation, threshold change | Patch | Compatible — no schema effect |

**Succession rule:** When a `ConformanceDeclaration` is superseded, the prior declaration is updated with `superseded_by` pointing to the new declaration. The `superseded_by` field is excluded from `declaration_hash` — it is a lifecycle annotation, not a content field.

---

#### §9 Phase Label Scoping — GAP 8

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

The ASTP storage layer is a four-tier distributed system. The consistency hierarchy is:

```
PRIMARY TRUTH:   Neo4j       (structural ground truth — synchronous writes)
AUDIT TRUTH:     Blob        (append-only audit history — authoritative for event log)
DISCOVERY:       QDrant      (semantic search — eventually consistent with Neo4j)
WORKING STATE:   Redis       (ephemeral cache and queues — always reconstructable)
```

**Neo4j is the single source of truth for structural state.** No read operation on structural data (link health, membership records, declaration versions) may serve a response that contradicts Neo4j. QDrant and Redis divergence from Neo4j is a consistency error, not an alternative view.

##### 11.1.2 Neo4j Schema (Structural Memory)

New node types and relationships introduced in Amendment v2.0:

```cypher
// Node types
(:EpisodeLink {
  link_id,
  link_strength,              // Float [0.0, 1.0] — Gap 1
  is_inferred,                // Boolean — Gap 1
  health_state,               // LinkHealthState enum — Gap 4
  quarantine_reason,          // Optional<String>
  quarantined_at,             // Optional<Timestamp>
  quarantine_resolved_at,     // Optional<Timestamp> — Gap 4 closure
  quarantine_resolution       // Optional<QuarantineResolution> — Gap 4 closure
})

(:MembershipRecord {
  record_id,
  membership_role,            // included in content_hash — Gap 6
  content_hash,
  supersedes_record_id        // Optional — Gap 6 succession
})

(:ConformanceDeclaration {
  declaration_id,
  declaration_version,        // SemVer — Gap 7
  declaration_hash,
  superseded_by               // Optional — Gap 7 succession; excluded from hash
})

// Relationships
(e1:Episode)-[:LINKED_TO {via: link_id}]->(e2:Episode)
(mr:MembershipRecord)-[:SUPERSEDES]->(mr_prev:MembershipRecord)
(cd:ConformanceDeclaration)-[:SUPERSEDED_BY]->(cd_new:ConformanceDeclaration)
(ep:Episode)-[:MEMBER_OF {record_id}]->(eg:EpisodeGroup)
```

**Active-record index:** Implementations MUST maintain a materialized index for the active `MembershipRecord` per `(episode_id, group_id)` pair — defined as the record with no `superseded_by_record_id`. This is a storage-layer obligation, not a protocol mandate on query strategy.

##### 11.1.3 QDrant Schema (Semantic Discovery)

**Collection: `episode_content_vectors`**

> **Naming note (§11 pushback #1):** This collection was previously named `episode_link_candidates`. That name was a misnomer — candidates are the result of a similarity query, not stored objects. The collection stores per-episode content vectors; candidates emerge at query time.

```json
{
  "collection": "episode_content_vectors",
  "vector_size": 1536,
  "distance": "Cosine",
  "payload_schema": {
    "episode_id": "keyword",
    "spine_version": "keyword",
    "indexed_at": "datetime",
    "discovery_threshold_at_index": "float",
    "auto_accept_threshold_at_index": "float"
  }
}
```

**Threshold payload fields:** `discovery_threshold_at_index` and `auto_accept_threshold_at_index` record the protocol threshold values in effect at the time this vector was indexed. This enables retrospective comparison — if thresholds were recalibrated between index time and query time, the stored values allow an auditor to determine whether a link would have been proposed under the prior regime. This is an audit-the-decision application (§12).

**Collection: `participant_context_vectors`**

```json
{
  "collection": "participant_context_vectors",
  "vector_size": 768,
  "distance": "Cosine",
  "payload_schema": {
    "episode_id": "keyword",
    "participant_id": "keyword",
    "context_type": "keyword"
  }
}
```

**Vector dimension note (§11 pushback #2):** `episode_content_vectors` uses 1536 dimensions (text-embedding-3-large or equivalent); `participant_context_vectors` uses 768 dimensions. The asymmetry is intentional — participant identity signals occupy a smaller semantic space than full episode content, and a reduced-dimension model is appropriate. Implementations MUST NOT mix embeddings from different model families within the same collection.

##### 11.1.4 Redis Schema (Working State)

```
// Quarantine queue — per-Episode
ariadne:quarantine:queue:{episode_id}    ZSET  // score = quarantine_deadline (Unix timestamp)
ariadne:quarantine:ttl                   STRING // default TTL in seconds (implementation-configurable)

// Threshold calibration state
ariadne:calibration:thresholds           HASH  // current DISCOVERY_THRESHOLD, AUTO_ACCEPT_THRESHOLD
ariadne:calibration:history:{date}       LIST  // daily calibration snapshots

// Link health cache
ariadne:link:health:{link_id}            HASH  // cached health_state + checked_at; always reconstructable from Neo4j
```

**Quarantine queue scope (§11 pushback #3):** The quarantine queue is keyed per-Episode (`ariadne:quarantine:queue:{episode_id}`). A single global queue across all Episodes would create scaling problems and scope confusion — a quarantine event in one Episode would be processed in the context of another. Implementations using a global key are non-conforming.

**Redis is always reconstructable.** All Redis state can be rebuilt from Neo4j and Blob. Redis failure does not constitute data loss; it constitutes a consistency window until reconstruction completes.

---

#### §11.2 Verification Architecture

##### 11.2.1 Proof Types

Four proof types are defined for this amendment. A fifth (non-existence proof) is flagged as a known gap.

| Proof Type | What It Proves | Primary Storage |
|------------|---------------|-----------------|
| `LINK_INTEGRITY` | `content_hash` matches canonical field set | Neo4j |
| `MEMBERSHIP_CHAIN` | Succession chain is unbroken and hashes are valid | Neo4j |
| `DECLARATION_COMPATIBILITY` | Version transition is compatible (minor/patch) or breaking (major) | Neo4j |
| `AUDIT_COMPLETENESS` | All required audit events are present for a lifecycle | Blob |

**Known gap — non-existence proof (§11 pushback #4):** Proof that no `EpisodeLink` exists between Episode A and Episode B is not specified in this amendment. This is a meaningful proof type — "we never connected these two episodes" is an auditable claim — but specifying it requires additional Merkle commitments not introduced here. Implementations requiring negative-space proofs should treat this as a future amendment item.

##### 11.2.2 `LINK_INTEGRITY` Proof

```
Proof {
  proof_type:     LINK_INTEGRITY
  link_id:        UUID
  claimed_hash:   Hash           // hash stored in EpisodeLink.content_hash
  computed_hash:  Hash           // hash recomputed from canonical fields at proof time
  field_snapshot: {              // canonical fields at proof time
    link_id, source_episode, target_episode, created_at, created_by,
    link_type, link_strength, is_inferred, inference_signals,
    inference_threshold, retroactive, health_state, health_checked_at,
    source_version, target_version, quarantine_reason, quarantined_at
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

**Session record definition:** The session record is the crystallization chain entry in the Episode of Record — the sealed spine position produced by the ratifying agent's ratification commit, verifiable against the Episode's Merkle root. For Devin's approvals within this amendment's Episode, the session record is the sealed spine position at the crystallization event, counter-signed by Devin's approval key.

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

**Reverse delta for `SECTION_SUPERSESSION` (§11 pushback #7):** Forward deltas are stored as diffs from the prior version. Reverse delta derivation for `SECTION_SUPERSESSION` requires the prior section text — this cannot be derived from the `supersedes_clause` identifier alone. The prior section text is stored at the superseded version's Blob path. The `supersedes_clause` identifies the path; the content is retrieved from Blob, not recomputed. Implementations MUST store prior section content in Blob before recording a supersession.

##### 11.3.2 MembershipRecord Succession Lifecycle

```
Succession entry:
  1. New MembershipRecord created with supersedes_record_id = prior record_id
  2. Prior record updated: superseded_by_record_id = new record_id (lifecycle annotation only; excluded from content_hash)
  3. Active-record index updated to point to new record
  4. Audit event recorded

Succession is irreversible. Prior records are never deleted.
```

##### 11.3.3 Quarantine Escalation — Chronos Addition

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
| `LINK_PROPOSED` | Candidate score >= DISCOVERY_THRESHOLD | link_id, score, signals, threshold | Blob |
| `LINK_ACCEPTED` | Human confirmation or auto-accept | link_id, accepted_by, method | Blob |
| `LINK_REJECTED` | Human rejection of proposed candidate | link_id, rejected_by, reason | Blob |
| `CANDIDATE_REJECTED` | Candidate below DISCOVERY_THRESHOLD | episode_pair, score, threshold | Blob |
| `LINK_HEALTH_CHANGED` | Health state transition | link_id, prior_state, new_state | Blob |
| `LINK_QUARANTINED` | Link moved to QUARANTINED | link_id, reason, ttl_deadline | Blob |
| `LINK_QUARANTINE_RESOLVED` | Quarantine exited | link_id, resolution, resolved_by | Blob |
| `QUARANTINE_ESCALATED` | Quarantine TTL exceeded | link_id, escalation_reason | Blob |
| `MEMBERSHIP_RECORD_CREATED` | New MembershipRecord asserted | record_id, episode_id, group_id | Blob |
| `MEMBERSHIP_RECORD_SUPERSEDED` | Succession recorded | prior_record_id, new_record_id | Blob |
| `DECLARATION_VERSION_BUMPED` | ConformanceDeclaration versioned | declaration_id, prior_version, new_version, classification | Blob |
| `DECLARATION_SUPERSEDED` | Declaration succeeded | prior_declaration_id, new_declaration_id | Blob |

All audit events are append-only and stored in Blob. Audit events are never modified or deleted.

---

#### §11.5 Consistency Requirements

##### 11.5.1 Write Path

```
1. Write to Neo4j (synchronous — must succeed before continuing)
2. Append to Blob audit log (synchronous — must succeed before continuing)
3. Propagate to QDrant (asynchronous — within consistency window)
4. Update Redis cache/queues (asynchronous — within consistency window)
```

Steps 1 and 2 are atomic from the protocol's perspective. A write that succeeds in Neo4j but fails in Blob is a partial write and MUST be retried or rolled back.

##### 11.5.2 Consistency Window SLA (§11 pushback #9)

Implementations MUST define a maximum consistency window for QDrant and Redis propagation.

**Required SLA:**
- Typical propagation: < 60 seconds
- Maximum propagation: 5 minutes

Implementations exceeding the maximum propagation window without a documented exception are non-conforming at the state tier (§12). Implementations MUST expose a consistency status endpoint or mechanism that allows callers to determine whether QDrant/Redis state is within the consistency window.

##### 11.5.3 Sequence Numbers and Timestamps (§11 pushback #8)

Two ordering mechanisms are used in this amendment. They are complementary, not redundant:

- **Sequence numbers** are scoped per-Episode and are the basis for completeness proofs within an Episode. A sequence gap within an Episode's audit log indicates a missing event.
- **Chronos-assigned timestamps** are the basis for ordering across Episodes. Cross-Episode temporal ordering uses timestamps, not sequence numbers, because sequence scopes do not extend across Episode boundaries.

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
- [ ] Key Redis quarantine queue per-Episode: `ariadne:quarantine:queue:{episode_id}`
- [ ] Define and publish consistency window SLA within bounds specified in §11.5.2
- [ ] Use sequence numbers for within-Episode completeness proofs; Chronos timestamps for cross-Episode ordering

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
│  LAYER 2 — Episode Content (Adaptive Merkle Tree)            │
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

- An MCP server (the Ignis reference implementation),
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

**Form B — Ordered JSON, used by the Ignis reference implementation (with SHA3-256):**

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
| `WORKFLOW_DECLARED` | `WorkflowDeclaration` creation | `workflow_id`, `episode_id`, `intention_id` (nullable), `mandate_id` (nullable), `declared_by`, `declared_at`, `content_hash`, `cia_identifier` | Blob, append-only |
| `EXECUTION_RECORDED` | `ExecutionNode` creation | `execution_node_id`, `workflow_id`, `episode_id`, `sequence_index`, `agent_id`, `status`, `executed_at`, `content_hash`, `cia_identifier` | Blob, append-only |
| `SKILL_INVOKED` | `SkillInvocation` creation | `skill_invocation_id`, `execution_node_id`, `workflow_id`, `episode_id`, `skill_id`, `skill_source`, `invoked_by`, `invoked_at`, `status`, `content_hash`, `cia_identifier` | Blob, append-only |
| `WORKFLOW_CLOSED` | `ignis_close_workflow`-equivalent operation | `workflow_id`, `final_status`, `status_updated_at`, `error_detail` (nullable), `cia_identifier` | Blob, append-only |

**Audit chain integrity.** Each Layer 3 audit event is hash-chained per the existing protocol convention: each record carries `prev_audit_hash` pointing at the preceding record in its chain, and records form an append-only sequence per workspace (or per chain-key as the implementation declares). The chain key for Layer 3 events MAY be the `episode_id` (Ignis reference choice) or any other declared key, provided the implementation documents the choice in its `ConformanceDeclaration` and is consistent within a workspace.

**`cia_identifier` is mandatory in every Layer 3 audit event.** The principal that performed the write — the workspace's designated CIA for that node type — MUST be recorded. This is what makes the sole-writer principle (§3) verifiable: a verifier walking the audit chain can confirm that every L3 write was performed by the declared CIA, and that no other principal contributed.

**Conformance W-L3-4 (Audit Emission).** Every Layer 3 node creation and every `WorkflowDeclaration.status` mutation MUST emit the corresponding audit event into the chain **before** the operation is considered durable. Implementations MAY use the existing protocol convention of Blob → Adapter → Index write ordering, in which case the audit-event blob write precedes the node creation in the adapter store.

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

1. **Mandate — full protocol surface.** This amendment introduces `mandate_id` as an optional, immutable, hash-included field on `WorkflowDeclaration`, and the `SPAWNED_BY_MANDATE` edge to a `Mandate` node. The `Mandate` node type itself — its fields, its hash preimage, its lifecycle, its position in the layer hierarchy (Mandate is most naturally a Layer 1 or Layer 2 cognitive primitive, not Layer 3) — is **not specified by this amendment**. Conforming implementations MAY treat `Mandate` as an opaque reference for the purposes of Layer 3 conformance. A future amendment (provisional designation: **v3.1.0 — Mandate Codification**) will define the full Mandate surface.

2. **Skill Registry.** The `SkillInvocation.registry_id` field is reserved for a future protocol surface that catalogues skills as first-class addressable entities. Until that surface is defined, conforming implementations MUST leave `registry_id` null. The field's exclusion from `content_hash` is a deliberate forward-compatibility provision: when the Skill Registry amendment ships, a backfill operation MAY populate `registry_id` on existing `SkillInvocation` records without invalidating their content hashes.

3. **SkillInvocation as Spine-resident node.** Some implementations may eventually want SkillInvocation to participate in Spine hashing — turning skill invocation into a cryptographically-anchored cognitive primitive for ecosystems where agent cognition is substantially composed of skill chains rather than native reasoning. This amendment **declines** that promotion: SkillInvocation remains a Layer 3 node. A future major amendment (provisional designation: **v4.0.0 — SkillInvocation Spine Promotion**) may revisit this decision once production usage of Layer 3 has informed the design.

---

### Appendix A — Reference Adapter Notes (Non-Normative)

The following notes derive from the reference implementation in the Ignis OS. They are non-normative: conforming implementations need not adopt them. They are included to illustrate one complete adapter path and to inform implementers considering similar designs.

#### A.1 Neo4j edge vocabulary

The reference implementation stores Layer 3 edges as native Neo4j relationships with the names given in §7:

```cypher
(:WorkflowDeclaration)-[:DECLARED_WITHIN {declared_at}]->(:EpisodeNode)
(:WorkflowDeclaration)-[:SERVES_INTENTION {declared_at}]->(:IntentionNode)
(:WorkflowDeclaration)-[:SPAWNED_BY_MANDATE {declared_at}]->(:Mandate)
(:ExecutionNode)-[:EXECUTES_WITHIN {sequence_index}]->(:WorkflowDeclaration)
(:ExecutionNode)-[:PRECEDES {sequence_gap, edge_type}]->(:ExecutionNode)
(:SkillInvocation)-[:INVOKED_WITHIN {invoked_at}]->(:ExecutionNode)
(:SkillInvocation)-[:SKILL_PRECEDES {sequence_index}]->(:SkillInvocation)
```

#### A.2 Suggested indexes

```cypher
CREATE INDEX workflow_episode_idx FOR (w:WorkflowDeclaration) ON (w.episode_id);
CREATE INDEX workflow_mandate_idx FOR (w:WorkflowDeclaration) ON (w.mandate_id);
CREATE INDEX workflow_status_idx FOR (w:WorkflowDeclaration) ON (w.status);
CREATE INDEX execution_workflow_idx FOR (e:ExecutionNode) ON (e.workflow_id);
CREATE INDEX execution_status_idx FOR (e:ExecutionNode) ON (e.status);
CREATE INDEX execution_agent_status_idx FOR (e:ExecutionNode) ON (e.agent_id, e.status);
CREATE INDEX skill_execution_idx FOR (s:SkillInvocation) ON (s.execution_node_id);
CREATE INDEX skill_id_idx FOR (s:SkillInvocation) ON (s.skill_id);
CREATE CONSTRAINT workflow_node_id_unique FOR (w:WorkflowDeclaration) REQUIRE w.node_id IS UNIQUE;
CREATE CONSTRAINT execution_node_id_unique FOR (e:ExecutionNode) REQUIRE e.node_id IS UNIQUE;
CREATE CONSTRAINT skill_node_id_unique FOR (s:SkillInvocation) REQUIRE s.node_id IS UNIQUE;
```

#### A.3 Reference forensic query patterns

**"What led to this failure?"**
```cypher
MATCH (w:WorkflowDeclaration {node_id: $workflow_id})
OPTIONAL MATCH (w)<-[:EXECUTES_WITHIN]-(e:ExecutionNode)
OPTIONAL MATCH (e)<-[:INVOKED_WITHIN]-(s:SkillInvocation)
RETURN w.workflow_name, w.status, e.step_name, e.status, e.error_type,
       e.error_detail, s.skill_id, s.status, s.error_detail
ORDER BY e.sequence_index, s.invoked_at
```

**"Full provenance chain: intention → mandate → workflow → execution"**
```cypher
MATCH (i:IntentionNode {node_id: $intention_id})
OPTIONAL MATCH (i)<-[:SERVES_INTENTION]-(w:WorkflowDeclaration)
OPTIONAL MATCH (w)-[:SPAWNED_BY_MANDATE]->(m:Mandate)
OPTIONAL MATCH (w)<-[:EXECUTES_WITHIN]-(e:ExecutionNode)
RETURN i, m, w, collect(e) AS executions
```

#### A.4 Reference CIA implementation

The Ignis reference implementation designates a single MCP server (the `ignis_mcp_server`) as the CIA for all three Layer 3 node types in the SEL workspace. Enforcement is achieved through:

- **Application-layer guard:** no other process holds Neo4j credentials with INSERT privileges on the Layer 3 labels.
- **MCP-tool surface:** the four write tools (`ignis_declare_workflow`, `ignis_record_execution_step`, `ignis_record_skill_invocation`, `ignis_close_workflow`) are the only authorized write paths.
- **Database constraint:** `node_id` uniqueness constraints (above) prevent accidental duplicate writes from any source.

The `cia_identifier` value emitted in audit events for this implementation is `ignis_mcp_server@<workspace_id>`.

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
- [ ] Leave `SkillInvocation.registry_id` null pending the future Skill Registry amendment (§13.2).

A conforming Layer 3 implementation MUST NOT:

- [ ] Include any Layer 3 field in the preimage of any Layer 1 or Layer 2 hash (§2, L3-I1).
- [ ] Mutate any field of an `ExecutionNode` or `SkillInvocation` after creation (§9, L3-I3).
- [ ] Mutate any field of a `WorkflowDeclaration` other than the three permitted (§9, L3-I4).
- [ ] Provide a "retry" surface that updates a prior `ExecutionNode` (§9, L3-I5).
- [ ] Admit Layer 3 writes from any principal other than the designated CIA for the relevant node type (§3, L3-I2).
- [ ] Populate `SkillInvocation.registry_id` until the future Skill Registry amendment defines its semantics (§13.2).

---

*Amendment v3.0.0 — Working Draft. Episode of Record: `615b41e2-33cf-49e4-8491-b8a3f2e4cd75` (Autonomous Agentic Workflows and Skills). Pending ratification in a sealing episode.*

## 22. References

Internal Scorched Earth Labs design documents that informed the protocol:

| Reference | Decision |
|-----------|----------|
| v2 Synthesis | Position-binding, dual-index, delta records, proof system P1-P13 |
| Node-Generic Architecture (Revised) | CognitiveNode as primitive, namespace firewall, reparenting prohibition |
| CLO-CONSOLIDATED-1.1 | Phase 1 architecture synthesis |
| OQ-D01 | Write ordering and provisional state invariants |
| OQ-D02 | Crystallization as state transition |

---

*ASTP (AI State Tree Protocol) is developed by Scorched Earth Labs.*
