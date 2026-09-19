# ASTP — Layer 3 (Workflow & Execution DAG) Implementation Guide

**Version:** 1.1.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md §21 (Layer 3 — Workflow & Execution DAG), 5.1.0 (SPEC §21; unchanged by 5.0.0 — see the note in §1)

---

## 1. Purpose and Relationship to SPEC.md

> **SPEC 5.0.0 / 5.1.0 note.** Layer 3 is unchanged by 5.0.0: its byte form is governed by SPEC §21 Part III §8 and is deliberately outside the §5.1 single-encoding statement (§5.1 says so). What did change around it: the audit records Layer 3 events write are the version 2 audit record of SPEC §8; and, under the 5.1.0 adapter failure contract, a Layer 3 writer that cannot complete raises rather than returning a default.

SPEC §21 defines the protocol surface of **Layer 3 — the Workflow & Execution DAG**: the forensic provenance record of *how* an Episode's cognition was carried out — which autonomous workflows were declared, which discrete execution steps ran, which skills were invoked, and where execution failed. It is the third cryptographic layer, cryptographically **isolated** from the Merkle Spine (Layers 1/2): it references them by `node_id` only and never participates in Spine hashing. This document describes **how Scorched Earth Labs implemented that surface** — the `astp.core.workflow_execution` protocol-type module and the reference storage adapter in Ignis OS (Scorched Earth Labs' agent runtime, the first consumer of this protocol). It is not normative: another adapter (relational, document, graph) may differ in storage layout while remaining spec-conforming.

What is normative from this file:

- The **content-hash preimage field orders** for `WorkflowDeclaration`, `ExecutionNode`, and `SkillInvocation` (§4 below). The *field set and its ordering* are part of the protocol (SPEC §21 §8, conformance W-L3-2); the byte serialization *form* is implementation-space (SPEC §21 §8 permits Form A / Form B / other).
- The **excluded-from-hash** field sets: `WorkflowDeclaration` excludes `status`, `status_updated_at`, `error_detail`; `SkillInvocation` excludes `registry_id`; every node excludes `content_hash` itself.
- The **seven edge names** of SPEC §21 §7 (`DECLARED_WITHIN`, `SERVES_INTENTION`, `SPAWNED_BY_MANDATE`, `EXECUTES_WITHIN`, `PRECEDES`, `INVOKED_WITHIN`, `SKILL_PRECEDES`). Edge *names* are normative; edge *storage form* is not.
- The **four audit event types** (`WORKFLOW_DECLARED`, `EXECUTION_RECORDED`, `SKILL_INVOKED`, `WORKFLOW_CLOSED`) and their `cia_identifier`-mandatory rule.
- The **CIA sole-writer principle** (G-36): exactly one Cognitive Implementation Authority per (workspace, node type).

What is implementation-space:

- The concrete byte serialization. The reference canonicalizer (`astp/core/hash_canonical.py`) uses `sort_keys=False` field-ordered JSON (`separators=(",", ":")`, `ensure_ascii=False`, UTC-ISO8601 datetimes, UUID→str, Enum→`.value`) hashed with **SHA3-256**. This is a variant of SPEC §21 §8 Form B (canonical JSON) but with SHA3-256 rather than SHA-256 and caller-ordered rather than key-sorted fields. Another implementation may choose Form A (length-prefixed concatenation) and produce different bytes — legally, per SPEC §21 §8: cross-implementation hash *equivalence* is a non-goal at Layer 3; cross-implementation *verifiability* (documented, reproducible serialization) is the requirement.
- Neo4j labels, edge storage, indexes, and constraint names (§6 below; SPEC §21 Appendix A points here).
- The identity of the CIA and its enforcement mechanism (the Ignis reference names the `ignis_mcp_server` MCP server; SPEC §21 §3 permits any unique entity).
- Which chain key anchors the Layer 3 audit chain (the Ignis reference uses `episode_id`).

---

## 2. Module Layout

```
astp/
├── core/
│   ├── workflow_execution.py   # Layer 3 schema types + enums + hash functions + governance + delta payloads
│   ├── hash_canonical.py       # shared canonicalizer — hash_preimage(model, ordered_fields)
│   └── branching.py            # CognitiveDeltaType enum — carries the 4 Layer 3 audit event values (§11)
tests/unit/protocol/
└── test_workflow_execution.py  # all Layer 3 schema, hash, governance, and delta-payload vectors
```

**Note on adapter locality.** In `astp`, Layer 3 is a **protocol-type surface only** — `workflow_execution.py` defines the schemas, the three hash functions, the two governance guards, and the four audit-delta payloads. The reference **storage adapter** (the Neo4j writer + the four `ignis_*` MCP write tools that constitute the CIA) lives in the Ignis OS implementation, not in the protocol package. This is deliberate: the protocol layer commits to *what* is written and *how it is hashed*; *where and by whom* it is stored is the CIA's concern (SPEC §21 §3, §12). The Neo4j reference layout is reproduced from SPEC §21 Appendix A in §6 below.

---

## 3. Layer 3 Node Types and the Public Surface

### 3.1 The three node types

```python
from astp.core.workflow_execution import (
    WorkflowDeclaration, ExecutionNode, SkillInvocation,
    WorkflowStatus, ExecutionStatus, SkillStatus, ErrorType, PrecedesEdgeType,
    LAYER_3_SCHEMA_VERSION,   # "3.0.0"
)
```

| Node | Mutation surface | Retry behavior | SPEC |
|------|------------------|----------------|------|
| `WorkflowDeclaration` | `status`, `status_updated_at`, `error_detail` ONLY (L3-I4) | n/a | §21 §4 |
| `ExecutionNode` | **none** — terminal-on-write (L3-I3) | new node, new `node_id`, new `sequence_index` (L3-I5) | §21 §5 |
| `SkillInvocation` | **none** except deferred `registry_id` backfill (L3-I3, §13.2) | n/a | §21 §6 |

A `WorkflowDeclaration` with zero child `ExecutionNode`s is a valid forensic state ("declared, never started"); the protocol assigns it no special treatment.

### 3.2 Governance guards

```python
from astp.core.workflow_execution import (
    Layer3GovernanceError,
    enforce_workflow_status_transition,   # (current: WorkflowStatus, target: WorkflowStatus) -> None
    enforce_execution_error_consistency,  # (node: ExecutionNode) -> None
)
```

`enforce_workflow_status_transition` implements the §10 state machine directly:

| From | Permitted targets |
|------|-------------------|
| `DECLARED` | `IN_PROGRESS`, `INTERRUPTED` |
| `IN_PROGRESS` | `COMPLETED`, `FAILED`, `INTERRUPTED` |
| `COMPLETED` / `FAILED` / `INTERRUPTED` | ∅ (terminal — closed permanently) |

`enforce_execution_error_consistency` enforces the §5 status/error coupling: a `COMPLETED` node MUST have null `error_type` **and** null `error_detail`; a `FAILED`/`INTERRUPTED` node MUST have `error_type` set (`error_detail` is recommended, not enforced — some failure modes legitimately carry no detail payload).

### 3.3 Hash stamping

```python
from astp.core.workflow_execution import (
    compute_workflow_declaration_content_hash, stamp_workflow_declaration_hash,
    compute_execution_node_content_hash,      stamp_execution_node_hash,
    compute_skill_invocation_content_hash,    stamp_skill_invocation_hash,
)

wf = stamp_workflow_declaration_hash(WorkflowDeclaration(...))   # sets .content_hash
```

The `stamp_*` helpers compute and set `content_hash` in place and return the instance for chaining. **Key invariant:** re-stamping a `WorkflowDeclaration` after a permitted mutation (status/status_updated_at/error_detail) yields the **same** hash — the mutation surface is excluded from the preimage. Re-stamping a `SkillInvocation` after a `registry_id` backfill yields the **same** hash — `registry_id` is excluded by design (§13.2 forward-compat).

---

## 4. Content-Hash Preimages — Exact Field Orders

Ground truth is `astp/core/workflow_execution.py`; each order below is the literal tuple passed to `hash_preimage(node, ordered_fields)`. The serialization form is implementation-space (SPEC §21 §8); the **field set and its order** are the protocol commitment (W-L3-2). Field order is caller-controlled (`sort_keys=False`) — the tuple order *is* the preimage order.

### 4.1 `WorkflowDeclaration` — `compute_workflow_declaration_content_hash()`

```
node_id, node_type, schema_version,
episode_id, intention_id, mandate_id,
workflow_name, workflow_version, declared_by, declared_at,
input_context, expected_outputs, timeout_ms
```

**Excluded:** `status`, `status_updated_at`, `error_detail` (the mutation surface, §9 L3-I4) and `content_hash` itself.

**Nullable-but-included:** `intention_id` and `mandate_id` contribute even when null — they are immutable provenance, and their nullability is itself part of the immutable record (SPEC §21 §4 hash preimage note). A declaration with `mandate_id = null` hashes differently from one with a non-null `mandate_id`, all else equal.

### 4.2 `ExecutionNode` — `compute_execution_node_content_hash()`

```
node_id, node_type, schema_version,
workflow_id, episode_id,
sequence_index, step_name,
agent_id, executed_at, duration_ms,
input_state, output_state,
status, error_detail, error_type
```

**Excluded:** only `content_hash` itself. **`status` is INCLUDED** — unlike `WorkflowDeclaration`, `ExecutionNode` is terminal-on-write, so its status is a permanent, forensically-meaningful part of the immutable record (SPEC §21 §5 hash preimage note).

### 4.3 `SkillInvocation` — `compute_skill_invocation_content_hash()`

```
node_id, node_type, schema_version,
execution_node_id, workflow_id, episode_id,
skill_id, skill_source, skill_version,
invoked_by, invoked_at, duration_ms,
input_parameters, output_result,
status, error_detail
```

**Excluded:** `registry_id` (the **only** Layer 3 field excluded for a reason *other than mutation* — a §13.2 forward-compatibility provision so a future Skill Registry backfill can populate it without invalidating the hash) and `content_hash` itself.

---

## 5. Per-Operation Writes and the Audit Chain

Every Layer 3 write is anchored to the protocol audit chain by one of four `CognitiveDeltaType` values (defined in `astp/core/branching.py`; SPEC §21 §11). **`cia_identifier` is mandatory on every one** — it is the field that makes the sole-writer principle (§3) verifiable: a verifier walking the chain confirms every L3 write came from the declared CIA and no other principal contributed.

| Operation | Delta type | Delta payload class | Required forward fields |
|-----------|-----------|---------------------|-------------------------|
| `WorkflowDeclaration` creation | `WORKFLOW_DECLARED` | `WorkflowDeclaredDelta` | `workflow_id`, `episode_id`, `intention_id?`, `mandate_id?`, `declared_by`, `declared_at`, `content_hash`, `cia_identifier` |
| `ExecutionNode` creation | `EXECUTION_RECORDED` | `ExecutionRecordedDelta` | `execution_node_id`, `workflow_id`, `episode_id`, `sequence_index`, `agent_id`, `status`, `executed_at`, `content_hash`, `cia_identifier` |
| `SkillInvocation` creation | `SKILL_INVOKED` | `SkillInvokedDelta` | `skill_invocation_id`, `execution_node_id`, `workflow_id`, `episode_id`, `skill_id`, `skill_source`, `invoked_by`, `invoked_at`, `status`, `content_hash`, `cia_identifier` |
| Terminal `status` transition | `WORKFLOW_CLOSED` | `WorkflowClosedDelta` | `workflow_id`, `final_status`, `status_updated_at`, `error_detail?`, `cia_identifier` |

Each delta payload carries a **reverse delta** for audit-chain rollback consistency: node-creation deltas reverse to node deletion (the immutable nodes carry no field-restoration state); `WorkflowClosedDelta` carries `reverse_prior_status` / `reverse_prior_status_updated_at` / `reverse_prior_error_detail`. NOTE: terminal-state transitions are effectively one-way at the protocol level (§10 forbids leaving a terminal state); the reverse delta exists for chain consistency, not as a permitted operation.

**The auto-transition write.** The first `EXECUTION_RECORDED` for a given `workflow_id` MUST atomically transition that workflow `DECLARED → IN_PROGRESS` alongside the ExecutionNode write (SPEC §21 §10). A workspace whose `WorkflowDeclaration.status == DECLARED` while ExecutionNodes for it exist is non-conforming.

**Audit emission ordering (W-L3-4).** Every node creation and every `status` mutation MUST emit its audit event into the chain **before** the operation is durable. Implementations MAY use the protocol's Blob → Adapter → Index write ordering, in which case the audit blob write precedes the adapter node write. Each Layer 3 audit record hash-chains via `prev_audit_hash`; the chain key is a declared implementation choice (the Ignis reference uses `episode_id`).

---

## 6. Neo4j Reference Storage Layout (Non-Normative)

SPEC.md is provider-neutral; this section is where the reference deployment's provider-specific layout is recorded. The reference storage adapter lives in the Ignis OS implementation; these notes describe one complete adapter path, and nothing here is a conformance requirement.

### 6.1 Edge vocabulary — the seven edges (§7)

```cypher
(:WorkflowDeclaration)-[:DECLARED_WITHIN {declared_at}]->(:EpisodeNode)          // REQUIRED
(:WorkflowDeclaration)-[:SERVES_INTENTION {declared_at}]->(:IntentionNode)       // OPTIONAL
(:WorkflowDeclaration)-[:SPAWNED_BY_MANDATE {declared_at}]->(:Mandate)           // OPTIONAL
(:ExecutionNode)-[:EXECUTES_WITHIN {sequence_index}]->(:WorkflowDeclaration)     // REQUIRED
(:ExecutionNode)-[:PRECEDES {sequence_gap, edge_type}]->(:ExecutionNode)         // OPTIONAL (absent on first step)
(:SkillInvocation)-[:INVOKED_WITHIN {invoked_at}]->(:ExecutionNode)              // REQUIRED
(:SkillInvocation)-[:SKILL_PRECEDES {sequence_index}]->(:SkillInvocation)        // OPTIONAL
```

Edge **names** are normative; storage form is not (a relational adapter may realize these as foreign keys, a document adapter as embedded reference arrays). The `PRECEDES` edge carries the normative property `edge_type ∈ {SEQUENTIAL, CONDITIONAL, PARALLEL}` (the `PrecedesEdgeType` enum) — recorded even when the default `SEQUENTIAL` applies, because the alternatives carry forensic weight.

### 6.2 Indexes and constraints

```cypher
CREATE INDEX workflow_episode_idx       FOR (w:WorkflowDeclaration) ON (w.episode_id);
CREATE INDEX workflow_mandate_idx       FOR (w:WorkflowDeclaration) ON (w.mandate_id);
CREATE INDEX workflow_status_idx        FOR (w:WorkflowDeclaration) ON (w.status);
CREATE INDEX execution_workflow_idx     FOR (e:ExecutionNode) ON (e.workflow_id);
CREATE INDEX execution_status_idx       FOR (e:ExecutionNode) ON (e.status);
CREATE INDEX execution_agent_status_idx FOR (e:ExecutionNode) ON (e.agent_id, e.status);
CREATE INDEX skill_execution_idx        FOR (s:SkillInvocation) ON (s.execution_node_id);
CREATE INDEX skill_id_idx               FOR (s:SkillInvocation) ON (s.skill_id);
CREATE CONSTRAINT workflow_node_id_unique  FOR (w:WorkflowDeclaration) REQUIRE w.node_id IS UNIQUE;
CREATE CONSTRAINT execution_node_id_unique FOR (e:ExecutionNode)       REQUIRE e.node_id IS UNIQUE;
CREATE CONSTRAINT skill_node_id_unique     FOR (s:SkillInvocation)     REQUIRE s.node_id IS UNIQUE;
```

### 6.3 Reference forensic queries

**"What led to this failure?"** — join workflow → steps → skills, ordered by sequence:

```cypher
MATCH (w:WorkflowDeclaration {node_id: $workflow_id})
OPTIONAL MATCH (w)<-[:EXECUTES_WITHIN]-(e:ExecutionNode)
OPTIONAL MATCH (e)<-[:INVOKED_WITHIN]-(s:SkillInvocation)
RETURN w.workflow_name, w.status, e.step_name, e.status, e.error_type,
       e.error_detail, s.skill_id, s.status, s.error_detail
ORDER BY e.sequence_index, s.invoked_at
```

**"Full provenance: intention → mandate → workflow → execution"** — walks the cross-layer references:

```cypher
MATCH (i:IntentionNode {node_id: $intention_id})
OPTIONAL MATCH (i)<-[:SERVES_INTENTION]-(w:WorkflowDeclaration)
OPTIONAL MATCH (w)-[:SPAWNED_BY_MANDATE]->(m:Mandate)
OPTIONAL MATCH (w)<-[:EXECUTES_WITHIN]-(e:ExecutionNode)
RETURN i, m, w, collect(e) AS executions
```

### 6.4 Reference CIA (§3, G-36)

The Ignis reference designates a single MCP server — `ignis_mcp_server` — as the CIA for **all three** Layer 3 node types in its workspace. Enforcement is layered:

- **Application-layer guard:** no other process holds Neo4j credentials with INSERT on the Layer 3 labels.
- **MCP-tool surface:** the four write tools `ignis_declare_workflow`, `ignis_record_execution_step`, `ignis_record_skill_invocation`, `ignis_close_workflow` are the *only* authorized write paths.
- **Database constraint:** the `node_id` uniqueness constraints above prevent accidental duplicate writes from any source.

The `cia_identifier` emitted in every audit event for this implementation is `ignis_mcp_server@<workspace_id>`.

---

## 7. Governance Summary

| Rule / Invariant | SPEC | Enforcement |
|------------------|------|-------------|
| **G-36 (CIA Declaration)** — one CIA per (workspace, node type), enforcement declared, non-CIA writes rejected at wire tier | §21 §3, §12 | Application guard + MCP-tool sole write path + node_id uniqueness; `cia_identifier` on every audit event |
| **L3-I1 (Spine Isolation)** — no Layer 3 field in any Spine hash preimage; references by ID only | §21 §2 | Layer 3 hash functions live in a separate module; Spine hash functions are untouched; cross-layer refs are UUIDs |
| **L3-I2 (Sole Writer)** — exactly one CIA authorized to create each node type | §21 §3 | As G-36 |
| **L3-I3 (Terminal-on-Write)** — `ExecutionNode`/`SkillInvocation` fully immutable | §21 §9 | No update path; reject all mutation attempts |
| **L3-I4 (WorkflowDeclaration Mutation Surface)** — only `status`, `status_updated_at`, `error_detail` mutable | §21 §9 | Hash excludes the trio; other mutations are wire-tier violations |
| **L3-I5 (Retry-by-New-Node)** — a retried step is a new `ExecutionNode` (new `node_id`, new `sequence_index`) | §21 §9 | No retry-mutates-prior surface exists |
| State machine — `DECLARED → IN_PROGRESS → {COMPLETED, FAILED, INTERRUPTED}`; terminal states final | §21 §10 | `enforce_workflow_status_transition` |
| Auto-transition — first `ExecutionNode` write flips `DECLARED → IN_PROGRESS` atomically | §21 §10 | Adapter write ordering |
| Error consistency — `COMPLETED` ⇒ null error fields; `FAILED`/`INTERRUPTED` ⇒ `error_type` set | §21 §5 | `enforce_execution_error_consistency` |
| Deterministic hash (W-L3-1) + field inclusion (W-L3-2) + documented serialization (W-L3-3) | §21 §8 | `hash_canonical.hash_preimage` + the ordered-field tuples of §4; serialization documented in §1 |
| Audit emission before durability (W-L3-4), `cia_identifier` mandatory | §21 §11 | Delta payloads carry `cia_identifier`; Blob-first write ordering |
| `registry_id` left null pending Skill Registry (§13.2) | §21 §13 | Field defaults null; excluded from hash |

---

## 8. Neo4j Schema Additions Summary

| Label | Unique constraint on | Notes |
|-------|----------------------|-------|
| `WorkflowDeclaration` | `node_id` | Mutable trio: `status`, `status_updated_at`, `error_detail` |
| `ExecutionNode` | `node_id` | Fully immutable |
| `SkillInvocation` | `node_id` | Immutable except deferred `registry_id` backfill |

Edge types: the seven of §6.1. Indexes: the eight of §6.2. All storage form is adapter-defined (SPEC §21 §7, §12 Behavioral tier).

---

## 9. Test Layout and Coverage

All Layer 3 protocol vectors run against the pure-Python schema types (no live adapter — the reference adapter is exercised in the Ignis OS repo).

| File | Focus |
|------|-------|
| `tests/unit/protocol/test_workflow_execution.py` | Enum surfaces (`WorkflowStatus`/`ExecutionStatus`/`SkillStatus`/`ErrorType`/`PrecedesEdgeType`), `LAYER_3_SCHEMA_VERSION`, the four `CognitiveDeltaType` additions, per-node instantiation, per-node hash (field inclusion/exclusion, mutation-surface hash-stability, `registry_id` backfill hash-stability), status-transition state machine, execution error consistency, delta-payload shapes |

Test classes: `TestWorkflowStatus`, `TestExecutionStatus`, `TestSkillStatus`, `TestErrorType`, `TestPrecedesEdgeType`, `TestSchemaVersion`, `TestCognitiveDeltaTypeAdditions`, `TestWorkflowDeclarationInstantiation`, `TestWorkflowDeclarationHash`, `TestExecutionNodeInstantiation`, `TestExecutionNodeHash`, `TestSkillInvocationInstantiation`, `TestSkillInvocationHash`, `TestWorkflowStatusTransitions`, `TestExecutionErrorConsistency`, `TestDeltaPayloads`.

Run the whole suite with `pytest`.

---

## 10. Forward Compatibility Notes

Deliberate scope limits, forward-compatible with future amendments (SPEC §21 §13):

1. **Mandate — full protocol surface (§13.1).** `mandate_id` and the `SPAWNED_BY_MANDATE` edge are introduced, but the `Mandate` node type itself (fields, hash preimage, lifecycle, layer position) is unspecified. Conforming implementations MAY treat `Mandate` as an opaque reference. A future amendment will define it.
2. **Skill Registry (§13.2).** `SkillInvocation.registry_id` is reserved and MUST be left null. Its exclusion from `content_hash` is the enabling provision: when the Skill Registry amendment ships, a backfill MAY populate `registry_id` on existing records without invalidating their hashes.
3. **SkillInvocation Spine promotion (§13.3).** SkillInvocation remains a Layer 3 node; this amendment declines to promote it into Spine hashing. A future major amendment may revisit once production usage informs the design.
4. **CIA designation change events.** SPEC §21 §3 reserves the `CIA_DESIGNATION_CHANGED` audit event type for a future amendment if/when CIA reassignment proves non-rare; the current surface treats the CIA as stable.

---

*Developed by Scorched Earth Labs. See SPEC.md §21 for the normative protocol surface.*
