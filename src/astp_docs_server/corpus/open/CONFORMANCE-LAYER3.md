# ASTP — Layer 3 (Workflow & Execution DAG) Conformance Test Vectors

**Version:** 1.1.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md §21 (Layer 3 — Workflow & Execution DAG), 5.1.0 (SPEC §21; unchanged by 5.0.0 — see the note in §1)

---

## 1. Overview

> **SPEC 5.0.0 / 5.1.0 note.** Layer 3 is unchanged by 5.0.0: its byte form is governed by SPEC §21 Part III §8 and is deliberately outside the §5.1 single-encoding statement (§5.1 says so). What did change around it: the audit records Layer 3 events write are the version 2 audit record of SPEC §8; and, under the 5.1.0 adapter failure contract, a Layer 3 writer that cannot complete raises rather than returning a default.

This document specifies the conformance test vectors for **Layer 3 — the Workflow & Execution DAG** of ASTP (the AI State Tree Protocol). A conforming implementation MUST pass all vectors marked **REQUIRED**. Vectors marked **RECOMMENDED** test behaviors that conforming implementations SHOULD support.

Layer 3 is the forensic provenance layer: `WorkflowDeclaration`, `ExecutionNode`, and `SkillInvocation` record *how* an Episode's cognition was carried out. Its defining property is **cryptographic isolation from the Merkle Spine** — Layer 3 nodes reference Layers 1/2 by `node_id` only and MUST NOT participate in Spine hashing (Invariant L3-I1). This isolation is a first-class conformance concern; see the `L3-` vectors of §6.

These vectors are **cross-implementation-consistency** vectors: they assert canonical *field inclusion and ordering* and behavioral invariants, not hardcoded golden-hash values. Per SPEC §21 §8, the hash **byte-form is left open at the protocol layer** — each implementation chooses a serialization (SHA3-256 length-prefixed concatenation, SHA-256 canonical JSON, or other) and MUST be internally consistent. Two conforming implementations that adopt the *same* documented serialization MUST produce identical bytes for identical inputs; two implementations that adopt *different* serializations legitimately produce different hashes. What every conforming implementation MUST agree on is **which fields contribute, in what order** (W-L3-2).

Vectors are organized to match the reference deployment's adapter guide, `IMPLEMENTATION-LAYER3.md` (which lives with that adapter):

| Scope | Description | Vector Prefix |
|-------|-------------|---------------|
| WorkflowDeclaration | Schema, hash preimage, mutation surface, state machine | `WF-` |
| ExecutionNode | Schema, hash preimage, terminal-on-write, error consistency | `EX-` |
| SkillInvocation | Schema, hash preimage, `registry_id` deferral | `SK-` |
| Sole-writer (CIA) | G-36 sole-writer principle + audit attribution | `CIA-` |
| Layer invariants | Spine isolation, immutability, retry-by-new-node | `L3-` |

All hex values lowercase. All string fields UTF-8.

---

## 2. WorkflowDeclaration Vectors (§21 §4)

### 2.1 Hash Canonicalization

**WF-001** — `WorkflowDeclaration` content hash — field order
- **Class:** REQUIRED
- **Spec Reference:** §21 §4, §21 §8 (W-L3-1, W-L3-2)
- **Description:** `compute_workflow_declaration_content_hash()` MUST canonicalize, in this exact order: `node_id`, `node_type`, `schema_version`, `episode_id`, `intention_id`, `mandate_id`, `workflow_name`, `workflow_version`, `declared_by`, `declared_at`, `input_context`, `expected_outputs`, `timeout_ms`. It MUST exclude `status`, `status_updated_at`, `error_detail`, and `content_hash` itself.
- **Verification Protocol:** Cross-implementation consistency check. Two implementations sharing a documented serialization MUST produce identical bytes for the same input tuple; every conforming implementation MUST agree on the field set and order.
- **Failure Condition:** Any excluded field contributes to the hash; any listed field is missing or reordered; wrong integer/UUID/datetime encoding.

**WF-002** — Nullable provenance fields are hash-included
- **Class:** REQUIRED
- **Spec Reference:** §21 §4 (hash preimage note)
- **Description:** `intention_id` and `mandate_id` MUST contribute to the preimage even when null. A `WorkflowDeclaration` with `mandate_id = null` MUST produce a different `content_hash` than one with a non-null `mandate_id`, all other fields equal. Nullability is part of the immutable record.
- **Failure Condition:** A null `mandate_id` (or `intention_id`) hashes identically to the field's absence, or to a distinct non-null value.

**WF-003** — Mutation surface is hash-stable
- **Class:** REQUIRED
- **Spec Reference:** §21 §4, §21 §9 (L3-I4)
- **Description:** Mutating any of `status`, `status_updated_at`, `error_detail` and recomputing MUST yield the **same** `content_hash`. The mutation surface is excluded from the preimage precisely so that lawful terminal-state transitions never alter the declaration's content identity.
- **Verification Protocol:** Stamp a declaration; mutate the trio; re-stamp; assert equal hashes.
- **Failure Condition:** A permitted mutation changes the content hash.

### 2.2 State Machine

**WF-004** — Status transition legality
- **Class:** REQUIRED
- **Spec Reference:** §21 §10
- **Description:** `enforce_workflow_status_transition()` MUST permit exactly: `DECLARED → {IN_PROGRESS, INTERRUPTED}` and `IN_PROGRESS → {COMPLETED, FAILED, INTERRUPTED}`. `COMPLETED`, `FAILED`, and `INTERRUPTED` are terminal — no outbound transition is permitted. Illegal transitions MUST raise, not silently no-op.
- **Verification Protocol:** For each (from, to) pair, assert permitted pairs succeed and all others raise `Layer3GovernanceError`.
- **Failure Condition:** A transition out of a terminal state is admitted, or a non-listed transition succeeds.

**WF-005** — Auto-transition on first execution write
- **Class:** REQUIRED
- **Spec Reference:** §21 §10
- **Description:** The first `ExecutionNode` write for a given `workflow_id` MUST atomically transition that workflow's `status` from `DECLARED` to `IN_PROGRESS`. A workspace whose `WorkflowDeclaration.status == DECLARED` while ExecutionNodes for it exist is non-conforming.
- **Failure Condition:** A workflow remains `DECLARED` after an ExecutionNode is recorded against it.

**WF-006** — Two distinct `INTERRUPTED` states are distinguishable
- **Class:** RECOMMENDED
- **Spec Reference:** §21 §10
- **Description:** A conforming verifier SHOULD distinguish `status == INTERRUPTED` with **zero** ExecutionNodes ("declared, never started") from `status == INTERRUPTED` with **one or more** ExecutionNodes ("started, terminated mid-execution"). Neither is a schema violation; both are valid forensic states.

---

## 3. ExecutionNode Vectors (§21 §5)

### 3.1 Hash Canonicalization

**EX-001** — `ExecutionNode` content hash — field order
- **Class:** REQUIRED
- **Spec Reference:** §21 §5, §21 §8 (W-L3-1, W-L3-2)
- **Description:** `compute_execution_node_content_hash()` MUST canonicalize, in this exact order: `node_id`, `node_type`, `schema_version`, `workflow_id`, `episode_id`, `sequence_index`, `step_name`, `agent_id`, `executed_at`, `duration_ms`, `input_state`, `output_state`, `status`, `error_detail`, `error_type`. It MUST exclude **only** `content_hash` itself.
- **Verification Protocol:** Cross-implementation consistency check; field set + order agreement.
- **Failure Condition:** Any field except `content_hash` is excluded; wrong order.

**EX-002** — `status` is hash-included
- **Class:** REQUIRED
- **Spec Reference:** §21 §5 (hash preimage note)
- **Description:** Unlike `WorkflowDeclaration`, `ExecutionNode.status` MUST contribute to the content hash. Because the node is terminal-on-write, its status is a permanent forensic fact — two ExecutionNodes identical but for `status` MUST hash differently.
- **Failure Condition:** `status` is excluded from the ExecutionNode preimage, or two nodes differing only in `status` hash identically.

### 3.2 Error Consistency

**EX-003** — Error field / status coupling
- **Class:** REQUIRED
- **Spec Reference:** §21 §5
- **Description:** `enforce_execution_error_consistency()` MUST reject a `COMPLETED` node with non-null `error_type` or non-null `error_detail`, and MUST reject a `FAILED`/`INTERRUPTED` node with null `error_type`. (`error_detail` on a failed node is RECOMMENDED, not enforced.) `error_type ∈ {AGENT_ERROR, TIMEOUT, DEPENDENCY_FAILURE, SKILL_ERROR, UNKNOWN}`.
- **Failure Condition:** A `COMPLETED` node carries error fields, or a failed/interrupted node omits `error_type`.

---

## 4. SkillInvocation Vectors (§21 §6)

### 4.1 Hash Canonicalization

**SK-001** — `SkillInvocation` content hash — field order
- **Class:** REQUIRED
- **Spec Reference:** §21 §6, §21 §8 (W-L3-1, W-L3-2)
- **Description:** `compute_skill_invocation_content_hash()` MUST canonicalize, in this exact order: `node_id`, `node_type`, `schema_version`, `execution_node_id`, `workflow_id`, `episode_id`, `skill_id`, `skill_source`, `skill_version`, `invoked_by`, `invoked_at`, `duration_ms`, `input_parameters`, `output_result`, `status`, `error_detail`. It MUST exclude `registry_id` and `content_hash` itself.
- **Verification Protocol:** Cross-implementation consistency check; field set + order agreement.
- **Failure Condition:** `registry_id` contributes to the hash; any listed field is missing or reordered.

**SK-002** — `registry_id` backfill is hash-stable
- **Class:** REQUIRED
- **Spec Reference:** §21 §6, §21 §13.2
- **Description:** Populating `registry_id` on an existing `SkillInvocation` (a future Skill Registry backfill) MUST NOT change its `content_hash`. `registry_id` is the only Layer 3 field excluded from a content hash for a reason other than mutation — a deliberate forward-compatibility provision.
- **Verification Protocol:** Stamp with `registry_id = null`; populate `registry_id`; re-stamp; assert equal hashes.
- **Failure Condition:** Setting `registry_id` alters the content hash.

**SK-003** — `registry_id` left null pending Skill Registry
- **Class:** REQUIRED
- **Spec Reference:** §21 §13.2
- **Description:** A conforming implementation MUST leave `SkillInvocation.registry_id` null until the future Skill Registry amendment defines its semantics.
- **Failure Condition:** An implementation populates `registry_id` under its own ad-hoc semantics.

### 4.2 Open Behavioral Surface

**SK-004** — Skill taxonomy is recorded, not validated
- **Class:** REQUIRED
- **Spec Reference:** §21 §6, §21 §12 (audit-the-decision)
- **Description:** `skill_id` and `skill_source` are open, implementation-defined strings. The protocol does not constrain their vocabulary; it commits only that whatever value the implementation chose is recorded immutably and contributes to `content_hash`. An implementation MUST document its `skill_source` vocabulary in its `ConformanceDeclaration`.
- **Failure Condition:** An implementation drops `skill_id`/`skill_source` from the hash, or claims a fixed protocol-level skill vocabulary.

---

## 5. Sole-Writer / CIA Vectors (§21 §3, G-36)

**CIA-001** — Sole-writer enforcement (G-36)
- **Class:** REQUIRED
- **Spec Reference:** §21 §3 (L3-I2), G-36, §21 §12
- **Description:** For each Layer 3 node type in a workspace, exactly one entity — the Cognitive Implementation Authority — MUST be authorized to issue creation writes. Writes from any other principal MUST be rejected at the wire tier (or, under the audit-detection enforcement style, admitted but flagged `WIRE_VIOLATION`, which conforming verifiers reject). The `ConformanceDeclaration` MUST name the CIA per node type and identify the enforcement mechanism.
- **Verification Protocol:** Attempt a Layer 3 creation write from a non-CIA principal; assert rejection (or `WIRE_VIOLATION` flag). Confirm the `ConformanceDeclaration` names a unique CIA per node type.
- **Failure Condition:** A non-CIA principal's Layer 3 write is admitted and unflagged; or the `ConformanceDeclaration` omits/duplicates the CIA for a node type.

**CIA-002** — `cia_identifier` mandatory in every audit event
- **Class:** REQUIRED
- **Spec Reference:** §21 §11
- **Description:** Every `WORKFLOW_DECLARED`, `EXECUTION_RECORDED`, `SKILL_INVOKED`, and `WORKFLOW_CLOSED` audit event MUST carry a non-null `cia_identifier` naming the principal that performed the write. This is what makes sole-writer verifiable: a verifier walking the chain confirms every L3 write came from the declared CIA.
- **Failure Condition:** Any Layer 3 audit event lacks `cia_identifier`.

**CIA-003** — Audit event emission before durability (W-L3-4)
- **Class:** REQUIRED
- **Spec Reference:** §21 §11 (W-L3-4)
- **Description:** Each Layer 3 node creation and each `WorkflowDeclaration.status` mutation MUST emit its corresponding audit event into the append-only, hash-chained log **before** the operation is considered durable. Each record hash-chains via `prev_audit_hash`; the chain-key dimension is a documented implementation choice (the reference implementation in Ignis OS — Scorched Earth Labs' agent runtime, the first consumer of this protocol — uses `episode_id`).
- **Failure Condition:** A durable Layer 3 write with no preceding audit event, or an audit chain whose recomputed `prev_audit_hash` linkage is broken.

**CIA-004** — Audit event required-field completeness
- **Class:** REQUIRED
- **Spec Reference:** §21 §11
- **Description:** Each of the four audit event types MUST carry its §11 required fields: `WORKFLOW_DECLARED` (`workflow_id`, `episode_id`, `intention_id?`, `mandate_id?`, `declared_by`, `declared_at`, `content_hash`, `cia_identifier`); `EXECUTION_RECORDED` (`execution_node_id`, `workflow_id`, `episode_id`, `sequence_index`, `agent_id`, `status`, `executed_at`, `content_hash`, `cia_identifier`); `SKILL_INVOKED` (`skill_invocation_id`, `execution_node_id`, `workflow_id`, `episode_id`, `skill_id`, `skill_source`, `invoked_by`, `invoked_at`, `status`, `content_hash`, `cia_identifier`); `WORKFLOW_CLOSED` (`workflow_id`, `final_status`, `status_updated_at`, `error_detail?`, `cia_identifier`).
- **Failure Condition:** Any required field is absent from its event.

---

## 6. Layer-Invariant Vectors (§21 §2, §9)

**L3-001** — Spine isolation (L3-I1) — first-class conformance
- **Class:** REQUIRED
- **Spec Reference:** §21 §2 (L3-I1)
- **Description:** No field of any Layer 3 node or edge may appear in the preimage of any Layer 1 or Layer 2 hash, and no Layer 1/2 node may embed a Layer 3 `node_id` by value in its hash preimage. **Layer 3 is cryptographically isolated from the Spine — Layer 3 data MUST NEVER enter Spine hash computation.** All Layer 3 → Layer 1/2 references are by `node_id` (UUID) only.
- **Verification Protocol:** Freeze a Spine fingerprint; perform arbitrary Layer 3 writes; recompute the Spine fingerprint and assert it is byte-identical. Independently, inspect every Layer 1/2 hash preimage and confirm no Layer 3 `node_id` appears.
- **Failure Condition:** Any Layer 3 write alters any Spine hash; any Spine/Layer-2 preimage contains a Layer 3 field or `node_id`. This is a cryptographic-chain-corrupting defect.

**L3-002** — Layer 3 absence/corruption does not invalidate Layers 1/2
- **Class:** REQUIRED
- **Spec Reference:** §21 §2 (consequence 2)
- **Description:** A workspace whose Layer 3 is entirely absent or entirely corrupt MUST remain a valid ASTP workspace at Layers 1 and 2. Layer 3 is a strict augmentation, never a dependency.
- **Verification Protocol:** Delete/corrupt all Layer 3 records; assert Layer 1 and Layer 2 verification still pass.
- **Failure Condition:** Layer 1/2 verification depends on Layer 3 state.

**L3-003** — Independent Layer 3 verification chain
- **Class:** REQUIRED
- **Spec Reference:** §21 §2 (consequence 3), §21 §11
- **Description:** Layer 3 integrity MUST be verifiable against its own audit chain (§11), independently of walking the Spine. Layer 3 verification confirms execution-record integrity; Layer 1 verification confirms cognitive integrity; the two are independent.
- **Failure Condition:** Layer 3 verification requires Spine traversal, or vice versa.

**L3-004** — Terminal-on-write immutability (L3-I3)
- **Class:** REQUIRED
- **Spec Reference:** §21 §9 (L3-I3)
- **Description:** `ExecutionNode` and `SkillInvocation` are fully immutable after creation. Every mutation attempt on any field of either type MUST be rejected. Neither type has a write-after-create path.
- **Failure Condition:** Any field of a created `ExecutionNode` or `SkillInvocation` is successfully mutated.

**L3-005** — WorkflowDeclaration mutation surface (L3-I4)
- **Class:** REQUIRED
- **Spec Reference:** §21 §9 (L3-I4)
- **Description:** The only mutable fields on `WorkflowDeclaration` are `status`, `status_updated_at`, and `error_detail`. Any attempt to mutate any other field MUST be rejected as a wire-tier violation; the permitted three are further constrained by the §10 state machine.
- **Failure Condition:** Any field outside the permitted trio is mutated.

**L3-006** — Retry-by-new-node (L3-I5)
- **Class:** REQUIRED
- **Spec Reference:** §21 §9 (L3-I5)
- **Description:** A retried execution step MUST produce a **new** `ExecutionNode` with a new `node_id` and a new `sequence_index`; the prior (failed) node MUST be preserved unchanged. Implementations MUST NOT provide a "retry" surface that mutates a prior node.
- **Verification Protocol:** Record a `FAILED` step; retry; assert two distinct nodes exist, the original unchanged, sharing `step_name` but differing in `node_id` and `sequence_index`.
- **Failure Condition:** A retry mutates the prior ExecutionNode, or reuses its `node_id`/`sequence_index`.

**L3-007** — Seven edge names present and correctly directed
- **Class:** REQUIRED
- **Spec Reference:** §21 §7
- **Description:** The implementation MUST expose query paths equivalent to the seven edges: `DECLARED_WITHIN` (Workflow→Episode, REQUIRED), `SERVES_INTENTION` (Workflow→Intention, OPTIONAL), `SPAWNED_BY_MANDATE` (Workflow→Mandate, OPTIONAL), `EXECUTES_WITHIN` (Execution→Workflow, REQUIRED), `PRECEDES` (Execution→Execution, OPTIONAL; absent on first step), `INVOKED_WITHIN` (Skill→Execution, REQUIRED), `SKILL_PRECEDES` (Skill→Skill, OPTIONAL). Edge *names* are normative; storage form is not.
- **Failure Condition:** A required edge is unqueryable, misdirected, or renamed.

**L3-008** — `PRECEDES` edge-type property
- **Class:** RECOMMENDED
- **Spec Reference:** §21 §7
- **Description:** Where the `PRECEDES` edge is stored, it SHOULD carry the normative property `edge_type ∈ {SEQUENTIAL, CONDITIONAL, PARALLEL}` (the `PrecedesEdgeType` enum), recorded even when the default `SEQUENTIAL` applies, and `sequence_gap: Integer`. Additional implementation-specific edge properties are permitted but MUST NOT alter the semantics of the seven core edges.

---

## 7. Governance Rule Enforcement Matrix

Layer 3 governance centers on the single numbered SPEC rule **G-36 (CIA Declaration)** — renumbered from its authoring numeral G-19 during the v3.2.1 integration (the original G-19 collided with the §19 Branch/Fork/Merge taxonomy). The remaining Layer 3 requirements are stated as **invariants** (L3-I1 … L3-I5) and **wire-tier conformance rules** (W-L3-1 … W-L3-4) rather than G-numbers.

| Rule / Invariant | Scope | Vector(s) |
|------------------|-------|-----------|
| **G-36** | CIA sole-writer declaration + enforcement | CIA-001 |
| L3-I1 | Spine isolation — no Layer 3 data in Spine hash | L3-001, L3-002, L3-003 |
| L3-I2 | Sole writer (one CIA per node type) | CIA-001 |
| L3-I3 | Terminal-on-write immutability | L3-004 |
| L3-I4 | WorkflowDeclaration mutation surface | L3-005, WF-003 |
| L3-I5 | Retry-by-new-node | L3-006 |
| W-L3-1 | Hash determinism | WF-001, EX-001, SK-001 |
| W-L3-2 | Hash field inclusion/exclusion | WF-001/002, EX-001/002, SK-001/002 |
| W-L3-3 | Documented serialization | (declared in `ConformanceDeclaration`; see §8) |
| W-L3-4 | Audit emission before durability | CIA-002, CIA-003, CIA-004 |
| §10 state machine | Status transitions + auto-transition | WF-004, WF-005, WF-006 |
| §5 error consistency | ExecutionNode error/status coupling | EX-003 |
| §7 edges | Seven cross-layer edges | L3-007, L3-008 |
| §13.2 deferral | `registry_id` null + hash-excluded | SK-002, SK-003 |

---

## 8. Conformance Levels

### Level 1: Protocol Conformance (Wire + State tiers)

Implementation passes all **REQUIRED** vectors in sections 2–6 and the governance matrix of section 7. This covers the SPEC §21 §12 **Wire tier** (node schemas §4–§6, edge names §7, hash preimage rules §8, immutability §9, state machine §10, audit events §11, CIA sole-writer §3) and **State tier** (status-transition semantics, retry-by-new-node, the two-`INTERRUPTED` distinction). No claim is made about storage layout, hash byte-form, or performance.

### Level 2: Full Conformance (+ Behavioral tier documentation)

Level 1 plus all **RECOMMENDED** vectors, plus the SPEC §21 §12 **Behavioral tier** audit-the-decision documentation obligations: the implementation MUST document, in its `ConformanceDeclaration`, its chosen **hash byte serialization** (W-L3-3, in enough detail that an independent verifier can reproduce any node's hash from its field values), its **`skill_source` vocabulary**, its **CIA enforcement mechanism**, its **audit chain-key dimension**, and its **edge storage representation**. These choices are unconstrained by the protocol but MUST be recorded.

The Behavioral tier is **NOT REQUIRED** for protocol conformance; the audit-the-decision pattern requires only that each choice be documented, not that any particular choice be made. The Ignis OS reference chooses: SHA3-256 over field-ordered canonical JSON, the four `ignis_*` MCP tools as the sole CIA write path (`cia_identifier = ignis_mcp_server@<workspace_id>`), `episode_id` as the audit chain key, and native graph relationships for the seven edges.

---

## 9. Cross-Reference

- **SPEC.md §21** — normative protocol surface (v3.2.1); §2 Spine isolation, §3 CIA / G-36, §4–§6 schemas, §7 edges, §8 hash preimages, §9 immutability, §10 state machine, §11 audit registry, §12 three-tier conformance, Appendix B conformance checklist.
- **IMPLEMENTATION-LAYER3.md** — the reference deployment's adapter guide (non-normative; shipped with that adapter, not with the protocol): exact hash-preimage field orders, one storage layout, the reference CIA.
- **CONFORMANCE-BFM.md** — Branch/Fork/Merge conformance vectors (§19).
- Ground-truth code: `astp/core/workflow_execution.py` (schemas + `compute_*_content_hash` functions), `astp/core/hash_canonical.py` (reference canonicalizer), `astp/core/branching.py` (`CognitiveDeltaType` Layer 3 audit values).

---

*ASTP Layer 3 Conformance Test Vectors are maintained by Scorched Earth Labs.*
*Vector set version: 1.0.0 | Applies to SPEC.md: v3.2.1 §21*
