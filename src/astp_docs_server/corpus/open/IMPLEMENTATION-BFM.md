# ASTP — Branch/Fork/Merge Implementation Guide

**Version:** 1.2.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-07-04
**Applies To:** SPEC.md §19 (Branch / Fork / Merge / Departure Fork / Aside / Soliloquy / CoherenceFingerprint + Orphan Recovery), v3.3.0
**Scope:** All four phases of the Branch/Fork/Merge taxonomy (SPEC §19), plus the **Phase D departure-fork lifecycle** (SPEC §19.3.5–19.3.7, added §5 — incl. orphan recovery §5.8)
**Target audience:** Implementers extending a conforming ASTP instance with the BFM taxonomy.

---

## 1. Purpose and Relationship to SPEC.md

SPEC §19 defines the protocol surface of the Branch/Fork/Merge/Aside/Soliloquy/CoherenceFingerprint taxonomy — the normative invariants any conforming implementation must satisfy. This document describes **how Scorched Earth Labs implemented that taxonomy** against the Neo4j adapter. It is not normative: another adapter (Postgres, DynamoDB, a vector store + relational hybrid) may differ in storage layout while remaining spec-conforming.

What is normative from this file:
- The domain-separation hash prefixes (`BRANCH_POINT:`, `MERGE_POINT:`, `DEPARTURE_FORK_POINT:`, `FORK_RETURN:`, `ASIDE:`, `SOLILOQUY_PLACEHOLDER:`, `SOLILOQUY_FULL:`, `DELIBERATION_CHAIN:`, `SOLILOQUY_CONCLUSION:`, `FINGERPRINT:`, `OBJECTIVE:`, `AUDIT:`, `INTENT:`, `CONFIRMATION:`, `CONFLICT_MANIFEST:`, `MERGE_SPINE_POST:`, `ASIDE_FINAL:`). These are part of the protocol.
- The three-writes rule: every taxonomy state transition writes a structural node, a cognitive delta, and an audit record, or it writes nothing.
- The conflict-manifest short-circuit in `execute_merge()`.

What is implementation-space:
- Neo4j labels, properties, and constraint names.
- The mocked-driver test harness.
- How `drift_from_spine` and `topic_vector` are computed (caller-supplied here; another adapter might embed a model directly).

---

## 2. Module Layout

```
astp/
├── core/
│   ├── branching.py             # All BFM schema types + hash functions + governance
│   ├── branch_operations.py     # create/abandon/fork/resolve/merge/aside/soliloquy + departure-fork ops
│   └── coherence.py             # Phase 4 registry + detect + intercept
└── adapters/
    └── neo4j/
        └── writer.py            # All BFM writers + schema constraints/indexes
tests/unit/protocol/
├── test_phase2_schema.py        # Fork/merge/conflict schema
├── test_phase2_operations.py    # Fork/merge operations with mocked driver
├── test_phase3_schema.py        # Aside/soliloquy schema + governance
├── test_phase3_operations.py    # Aside/soliloquy operations with mocked driver
├── test_phase4_schema.py        # Fingerprint, state machine, confirmation cache
└── test_phase4_intercept.py     # Write intercept integration
```

---

## 3. Phase 1 — Branch Lifecycle

### 3.1 Public API

```python
from astp.core.branch_operations import create_branch, abandon_branch

result = create_branch(
    driver,
    source_episode_id: str,
    source_segment_id: str,
    branch_intent: str,
    declaration_type: BranchDeclarationType = EXPLICIT,
    branch_type: BranchType = EXPLORATORY,
    trigger: TriggerType = HUMAN_EXPLICIT,
    initiator: str = "system",
    caught_by: str = "HUMAN",
    detection_window_open: bool = False,
    branch_depth: int = 0,
) -> Optional[BranchResult]

result = abandon_branch(
    driver,
    branch_id: str,
    initiator: str,
    abandonment_reason: str,
    preserve_artifacts: bool = True,
) -> Optional[AbandonResult]
```

### 3.2 Governance Summary

| Rule | Enforcement |
|------|-------------|
| branch_intent non-empty | `create_branch` step 1 |
| branch_depth soft max 4 | `enforce_branch_depth_limit` — override logs to audit |
| Source episode ACTIVE | `create_branch` step 1 |
| Intent idempotency | `acquire_intent_sync` on `SHA3-256("INTENT:" + ep + seg + intent)` |
| abandonment_reason non-empty | `enforce_abandonment_reason_required` |
| ABANDONED terminal | Lifecycle derived from log; no reopen |

### 3.3 Writes per `create_branch()`

1. `BranchPointNode` (`AriadneBranchPoint`) + `BRANCH_ORIGIN` edge from parent Episode
2. `AuditRecord` (`AriadneAuditRecord`, `delta_type=BRANCH_CREATED`) + `AUDIT_TRAIL` edge
3. `IntentRecord` marked COMPLETE
4. WIL entry (`AriadneWILEntry`, operation `BRANCH_CREATE`)

Forward delta fields: `parent_node_id`, `branch_id`, `branch_type`, `trigger_context`, `declaration_type`.
Reverse delta fields: `delete_branch_id`, `restore_parent_cursor`.

### 3.4 Retroactive Declaration

When `declaration_type == RETROACTIVE`:
- `source_segment_id` is the last segment BEFORE drift began (supplied by caller).
- `spine_merkle_snapshot` is historical (from that segment).
- Additional fields: `pre_declaration_merkle_root`, `declared_retroactively_at`, `declared_by`.
- The audit record shows the branch existed — declared late, not absent.

---

## 4. Phase 2 — Resolution Primitives

### 4.1 Public API

```python
from astp.core.branch_operations import (
    create_fork, resolve_fork,
    find_common_ancestor, execute_merge, verify_merge_integrity,
)

fork_result = create_fork(
    driver, origin_episode_id, origin_segment_id,
    fork_objective, fork_intent,
    alternatives=[{"episode_id": "...", "participants": [...]}, ...],
    initiator="system",
    carried_artifacts=None,
) -> Optional[ForkResult]

resolve_result = resolve_fork(
    driver, fork_id, selected_fork_point_id, resolution_rationale,
    initiator="system",
) -> Optional[ResolveForkResult]

ancestor = find_common_ancestor(driver, branch_id, target_episode_id) -> Optional[CommonAncestorResult]

merge_result_or_manifest = execute_merge(
    driver,
    source_branch_id, target_episode_id,
    merge_summary,
    initiator="system",
    merge_strategy="AUTO" | "MANUAL_REVIEW" | "AGENT_RESOLVED" | "CONCLUSION_ONLY",
    conflict_segments=[{"segment_id", "ancestor_content_hash", "source_content_hash", "target_content_hash"}, ...],
    conflict_resolutions=[{"segment_id", "resolution_type", "resolved_content_hash", "resolver", "rationale"}, ...],
    resolution_artifacts=[...],
)   # returns MergeResult OR ConflictManifest

integrity = verify_merge_integrity(driver, merge_id) -> Optional[MergeIntegrityResult]
```

### 4.2 The Conflict Surface Invariant (G-23)

This is the spine of Phase 2. In both conditions below, `execute_merge()` writes no merge records and returns a `ConflictManifest` carrying the three things the caller needs to resolve the conflict:

1. Any `conflict_segment` without a matching entry in `conflict_resolutions` (matched by `segment_id`).
2. `merge_strategy == AUTO` and any `conflict_segments` present (AUTO never commits resolutions — even if resolutions were attached).

A conflict manifest is not a failure; it is the mechanism by which conflicts are surfaced. The caller re-invokes `execute_merge` with `merge_strategy=MANUAL_REVIEW` or `AGENT_RESOLVED` and complete resolutions.

### 4.3 Three-Root Integrity

`MergePointNode` stores three Merkle roots, all bound into its `content_hash` via domain prefix `MERGE_POINT:`:

- `source_merkle_root` — captured from source episode spine BEFORE any writes (step 2 of the merge sequence). Falls back to `BranchPointNode.spine_merkle_snapshot` if the source episode has no `spine_hash`.
- `target_merkle_root_pre` — captured from target episode spine BEFORE any writes.
- `target_merkle_root_post` — derived deterministically:
  ```
  sha3_256("MERGE_SPINE_POST:" + target_pre + ":" + source + ":" + common_ancestor + ":" + merge_type + ":" + sorted_conflict_segs + ":" + sorted_resolved_hashes)
  ```
  Implementation-space note: a branch-aware segment model (segments tagged with `branch_id`) permits true post-merge spine recomputation; the current derivation is forward-compatible with that upgrade.

`verify_merge_integrity()` re-reads the `MergePointNode`, recovers the `conflict_resolutions` from the MERGE_EXECUTED audit record's `forward_delta`, and recomputes `target_merkle_root_post`. Any mismatch surfaces as `integrity_holds = false` — a critical health signal.

### 4.4 Writes per `execute_merge()` (success path)

1. `MergePointNode` (`AriadneMergePoint`) + `MERGE_INTO` (source→MergePoint) + `MERGE_TARGET` (MergePoint→target) edges
2. `BranchTerminusNode` (`AriadneBranchTerminus`, type `MERGED`) + link edge from BranchPoint, carrying `branch_point_hash` integrity link
3. `BranchReturnEdge` (`BRANCH_RETURN` edge) linking terminus to MergePoint
4. `AuditRecord` (`delta_type=MERGE_EXECUTED`) with all three Merkle roots in `forward_delta`
5. WIL entry (operation `MERGE_EXECUTE`)

Abort path (integrity assertion failure): writes only a SYSTEM-caught failure audit record with `outcome=ABORTED`.

### 4.5 Fork Semantics

- Each `create_fork()` call writes N ForkPointNodes sharing one `fork_id` (a UUID). Siblings have distinct `sibling_index` values and independent `episode_id`s — a fork produces N new Episodes.
- `fork_status` on each ForkPoint starts as `ACTIVE`; `resolve_fork()` mutates it to `PROMOTED` (the selected alternative) or `DISCARDED` (all others).
- Discarded ForkPoints' Episodes remain in the graph as sealed history — not deleted. The `fork_status` field tracks resolution.

---

## 5. Phase D — Departure Fork Lifecycle

Phase D adds the **departure fork**, distinct from the speculative fork of §4.5. A speculative fork (`create_fork()`) opens N sibling alternatives that resolve to `PROMOTED`/`DISCARDED`; a departure fork (`create_departure_fork()`) is a single **directional departure** — one topic leaves into a new Episode while the originating Episode *continues*, with no siblings and no resolve/promote/discard. If not abandoned, a departure fork *is* an Episode ("fork is a verb, not a noun"). SPEC §19.3.5–19.3.6 is the normative surface; this section describes the Neo4j implementation.

### 5.1 Public API

```python
from astp.core.branch_operations import (
    create_departure_fork,
    complete_departure_fork, abandon_departure_fork,
    declare_fork_return,
)

result = create_departure_fork(
    driver,
    origin_episode_id, origin_segment_id,
    fork_objective,
    fork_creation_trigger,             # ForkCreationTrigger — EXPLORATORY_THREAD routes to create_fork(), not here (G-32)
    initiator="system",
    fork_agent_id=None,
    fork_title=None,
    participants=None,
    fork_trigger_segment_id=None,      # REQUIRED when fork_creation_trigger == AGENT_ESCALATION (G-33)
    fork_trigger_confidence=None,
    fork_origin_active_branch_ids=None,
    episode_mode="directed",
    caught_by="HUMAN",
    fork_episode_id=None,
) -> Optional[DepartureForkResult]

ok = complete_departure_fork(driver, fork_episode_id, actor="system", note="")  -> bool   # ACTIVE → COMPLETED
ok = abandon_departure_fork(driver, fork_episode_id, actor="system", reason="") -> bool   # ACTIVE → ABANDONED (terminal)

ret = declare_fork_return(
    driver, fork_id, origin_episode_id,
    return_type,                       # ForkReturnType: INCORPORATED | ACKNOWLEDGED | SUPERSEDED
    returned_by,                       # the originating agent (authority)
    synthesis_summary="",
    fork_episode_id=None,
) -> Optional[ForkReturnResult]
```

### 5.2 Departure vs. Speculative Fork

| | Speculative fork (§4.5) | Departure fork (§5) |
|---|---|---|
| Op | `create_fork()` | `create_departure_fork()` |
| Shape | N siblings share one `fork_id` | One directional departure, single node |
| Origin | Suspended pending selection | **Continues uninterrupted** |
| Resolution | `resolve_fork()` → `PROMOTED`/`DISCARDED` | Lifecycle FSM → `COMPLETED`/`ABANDONED` |
| Bring-back | Structural (selection is the outcome) | **Declarative** `declare_fork_return()` across two spines |
| Node label | `AriadneForkPoint` | `AriadneDepartureForkPoint` (+ `AriadneForkReturn`) |
| Domain prefix | `FORK_POINT:` | `DEPARTURE_FORK_POINT:` (+ `FORK_RETURN:`) |
| Trigger routing | `EXPLORATORY_THREAD` | `TOPIC_SHIFT`, `PARALLEL_THREAD`, `EXPLICIT_FORK`, `AGENT_ESCALATION` |

### 5.3 Governance Summary (G-30–G-35)

| Rule | Enforcement |
|------|-------------|
| **G-30** Backdating integrity: `spine_tip_hash_at_departure` == fork Episode's `fork_origin_spine_tip_hash` | `create_departure_fork` derives both from a single origin-spine-tip read (see §5.4) |
| **G-31** `fork_objective` non-empty | `create_departure_fork` step 1 (as G-19) |
| **G-32** `fork_creation_trigger ∈ {TOPIC_SHIFT, PARALLEL_THREAD, EXPLICIT_FORK, AGENT_ESCALATION}` | `create_departure_fork` — `EXPLORATORY_THREAD` is rejected here (belongs to `create_fork()`) |
| **G-33** `fork_trigger_segment_id` required when trigger `== AGENT_ESCALATION` | `create_departure_fork` guard |
| **G-34** Fork must be `COMPLETED` before a return | `declare_fork_return` guard (reads `fork_status`) |
| **G-35** At most one return declaration per `fork_id` | `declare_fork_return` guard (no prior `ForkReturnNode` for the `fork_id`) |

### 5.4 The Backdating Integrity Invariant (G-30)

The branch point records where divergence *began* — not where it was declared. Because the origin continues, the fork point and the fork Episode must agree on the origin spine tip at the departure moment, verifiable across two independent spines. The implementation makes G-30 hold **by construction**: it reads the origin spine tip once and derives both `DepartureForkPointNode.spine_tip_hash_at_departure` and the fork Episode's `fork_origin_spine_tip_hash` from that single value. A mismatch is a fatal integrity violation at creation, never a runtime reconciliation.

### 5.5 Writes per operation

`create_departure_fork()` (atomic):
1. The fork **Episode** (status `ACTIVE`, immutable fork provenance of §19.3.6) — `write_departure_fork_episode_sync`
2. A single `DepartureForkPointNode` (`AriadneDepartureForkPoint`) on the *originating* spine + `FORK_ORIGIN` edge — `write_departure_fork_point_sync`
3. `AuditRecord` (`delta_type=DEPARTURE_FORK_CREATED`) + `AUDIT_TRAIL` edge

`complete_departure_fork()` / `abandon_departure_fork()`: `mark_departure_fork_status_sync` flips the fork Episode's `fork_status`; writes `DEPARTURE_FORK_COMPLETED` / `DEPARTURE_FORK_ABANDONED` audit. No structural node — status transition + audit.

`declare_fork_return()`: `ForkReturnNode` (`AriadneForkReturn`) on the *originating* spine (`FORK_RETURN` edge) + `RETURNED_FROM` edge to the fork Episode + `DEPARTURE_FORK_RETURNED` audit — `write_fork_return_node_sync`. Integration content is written as ordinary subsequent origin-spine segments, **not** by the return node.

### 5.6 Lifecycle FSM

```
                complete_departure_fork()
     ┌────────┐ ───────────────────────▶ ┌───────────┐  declare_fork_return()
     │ ACTIVE │                          │ COMPLETED │ ─────────────────────▶ (origin-spine ForkReturnNode)
     └────────┘ ───────────────────────▶ └───────────┘   (G-34: only from COMPLETED; G-35: once)
          │      abandon_departure_fork()
          │                              ┌───────────┐
          └─────────────────────────────▶│ ABANDONED │ (terminal — never returns)
                                          └───────────┘

     ACTIVE covers in-progress AND parked. RESUMPTION (re-entering the origin
     while the fork stays ACTIVE) is a NON-EVENT: no node, no declaration.
     Actors: complete() = fork's own agent (first-person); abandon() = origin
     agent or system stub-cleanup; declare_fork_return() = originating agent.
```

### 5.7 Hash Domains

Both preimages are `sha3_256(prefix + ":" + colon-joined fields)`; ground truth is `astp/core/branching.py`.

| Node | Prefix | Preimage field order |
|------|--------|----------------------|
| `DepartureForkPointNode` | `DEPARTURE_FORK_POINT:` | `fork_point_id`, `fork_id`, `fork_episode_id`, `origin_episode_id`, `origin_segment_id`, `fork_objective`, `fork_creation_trigger`, `spine_tip_hash_at_departure`, `initiator`, `timestamp`, `parent_hash` |
| `ForkReturnNode` | `FORK_RETURN:` | `fork_return_id`, `fork_id`, `fork_episode_id`, `origin_episode_id`, `return_type`, `synthesis_summary`, `fork_final_spine_tip_hash`, `returned_by`, `timestamp`, `parent_hash` |

The `DEPARTURE_FORK_POINT:` prefix is deliberately distinct from `FORK_POINT:` — a departure fork point and a speculative fork point with otherwise-identical fields MUST NOT collide.

### 5.8 Orphan Recovery (§19.3.7)

The producer (§5.5) and return holds a cross-verifiable invariant at write time; **orphan recovery is its runtime enforcement** — it catches the partial-failure states the producer couldn't prevent (a crash between the two writes, a rolled-back status). Per the protocol/runtime split, this repo ships the **write primitives**; detection (which sweep, how often) and the detect→recover orchestration live in the consumer (ignis-os). **Detection cadence is not part of conformance** — only the shape of a conformant recovery is (SPEC §19.3.7).

**Write primitives** (`astp/adapters/neo4j/writer.py`):

```python
write_fork_orphan_marker_sync(driver, marker)                 # any class: diagnostic marker (dedup on fork_id)
mark_departure_fork_point_orphaned_sync(driver, fork_point_id)  # Class A: flag dangling point orphaned=true
write_retroactive_departure_fork_point_sync(driver, dfp, orphan_recovery_timestamp)  # Class B: append missing point
mark_fork_episode_unanchored_sync(driver, fork_episode_id)    # Class B (origin unreachable): fork_orphaned + UNANCHORED
correct_fork_status_by_orphan_recovery_sync(driver, fork_episode_id)  # Class C: ACTIVE -> COMPLETED (return is authoritative)
```

**`ForkOrphanMarker` — non-chained diagnostic satellite.** Written to the origin spine
(`ORPHAN_MARKER` edge from the origin Episode), self-hashed with domain
`FORK_ORPHAN_MARKER:` for tamper-evidence, but **NOT** a member of the origin spine's
Merkle chain — it carries **no `parent_hash`**, so writing it never changes the origin
Episode's root/tip. Neo4j: label `AriadneForkOrphanMarker`, uniqueness constraint on
`fork_id` (this is what enforces **one marker per orphaned fork** — a re-detection sweep
MERGEs onto the existing node). Read-only after write; `departure_registry` queries match
`DepartureForkPointNode`/`ForkReturnNode` only, so markers never surface there.

Hash preimage (SHA3-256, prefix `FORK_ORPHAN_MARKER:`):

| Node | Preimage field order |
|------|----------------------|
| `ForkOrphanMarker` | `fork_orphan_marker_id`, `fork_id`, `origin_episode_id`, `orphan_class`, `sequence_index`, `detection_run_id`, `recovery_action`, `requires_operator_review`, `detected_at` |

**The Class-B retroactive write** (`write_retroactive_departure_fork_point_sync`) — the
one place a fork point is written after the fact. It is a **pure append** modeled on
RETROACTIVE branch declaration (§3.4): it MERGEs the missing `DepartureForkPointNode`
using the fork Episode's stored `fork_origin_spine_tip_hash` as the point's
`spine_tip_hash_at_departure` (so the cross-verifiable invariant holds by construction),
and touches **nothing else** — no existing spine node or chain hash is read-modified.
The point's `content_hash` is computed exactly as an on-time write, so a recovered point
is **byte-identical** to one written on time; `retroactive=true` and
`orphan_recovery_timestamp` are diagnostic fields **outside** the hash preimage. The
caller MUST verify hash consistency (fork provenance vs origin spine at
`fork_anchor_index`) BEFORE calling it — on mismatch, escalate to an operator, do not
write. Diagnostic fields land on the point (`orphaned`, `retroactive`,
`orphan_recovery_timestamp`) and the fork Episode (`fork_orphaned`, `fork_orphan_class`,
`status_corrected_by_orphan_recovery`, `status_corrected_at`); none are hashed.

---

## 6. Phase 3 — Social/Internal Primitives

### 6.1 Public API

```python
from astp.core.branch_operations import (
    create_aside, close_aside,
    create_soliloquy, conclude_soliloquy,
)

aside = create_aside(
    driver,
    parent_episode_id, parent_segment_id,
    aside_label, initiated_by_human, target_agent_id,
    return_obligation=True, content_refs=None,
) -> Optional[AsideResult]

close_result = close_aside(
    driver, aside_id, close_reason,
    notification_targets=None, additional_content_refs=None,
) -> Optional[AsideCloseResult]

soliloquy = create_soliloquy(
    driver,
    parent_episode_id, parent_segment_id,
    soliloquy_purpose, initiated_by_agent,
    visibility_policy=None,      # dict; defaults enforce G-27 (human accessibility)
    deliberation_chain=None,
) -> Optional[SoliloquyResult]

conclusion = conclude_soliloquy(
    driver, soliloquy_id,
    conclusion_summary, merged_into_segment_id,
    final_deliberation_chain=None,
) -> Optional[SoliloquyConclusionResult]
```

### 6.2 Aside Reference Scan (on close)

`scan_aside_external_references_sync()` runs:

```cypher
MATCH (ext:AriadneSegment)-[:REFERENCES]->(internal:AriadneSegment)
WHERE internal.segment_id IN $content_refs
  AND NOT ext.segment_id IN $content_refs
RETURN collect(DISTINCT ext.segment_id) AS offenders
```

External references do not block the close — they are recorded in both
the `AsideTerminusNode` and the ASIDE_CLOSED audit record. This is the
"asymmetric merge" in action: the close proceeds, other agents get
notified of the aside's existence, and leaks are part of the permanent
audit trail for review.

### 6.3 Soliloquy Merkle Handling

Two `SoliloquyContentHashPolicy` values:

| Policy | Preimage structure | When to use |
|--------|--------------------|-------------|
| `HASH_PLACEHOLDER` | `{id}:{ep}:{seg}:{agent}:{ts}` | Default. Placeholder preserves the Merkle chain integrity without exposing content. Chain content is NOT recoverable from the hash. |
| `FULL_CONTENT` | `{id}:{ep}:{seg}:{agent}:{ts}:{chain}` | When content privacy is not required; allows direct hash verification of the chain. |

The protocol default is `HASH_PLACEHOLDER` because it's the privacy-preserving choice. Deployments that need chain verification can opt in to `FULL_CONTENT` per-soliloquy via `visibility_policy.content_hash_policy`.

### 6.4 Conclusion Merge Model

`conclude_soliloquy()` writes `SoliloquyConclusionNode` with:

- `conclusion_content_hash` — hash of the public summary (domain `SOLILOQUY_CONCLUSION:`)
- `deliberation_chain_hash` — tamper-evident hash of the private chain (domain `DELIBERATION_CHAIN:`)
- `merged_into_segment_id` — the spine segment that receives the conclusion

The deliberation chain itself stays on the `SoliloquySegmentNode`. Only the conclusion is public. An auditor with read access to the Soliloquy node can verify the chain content against the stored hash — without the content ever leaving the node.

---

## 7. Phase 4 — Prescriptive Enforcement

### 7.1 Public API

```python
from astp.core.coherence import (
    CoherenceFingerprintRegistry,
    detect_branch_candidate,
    intercept_segment_write,
)

result = intercept_segment_write(
    driver,
    episode_id, segment_id, sequence_index,
    current_objective: str,
    topic_vector: Optional[List[float]] = None,
    drift_from_spine: float = 0.0,
    intent_class: IntentClass = CONTINUE,
    thresholds: DetectionThresholds = DEFAULT_DETECTION_THRESHOLDS,
) -> DetectionResult

# For read-only checks (no fingerprint write):
result = detect_branch_candidate(driver, episode_id, segment_id, sequence_index,
                                  drift_from_spine, intent_class, objective_hash, thresholds)
```

If `result.materialized_recommendation` is not None, the caller SHOULD invoke:

```python
create_branch(
    driver,
    source_episode_id=result.episode_id,
    source_segment_id=result.materialized_recommendation["source_segment_id"],
    branch_intent=result.materialized_recommendation["rationale"],
    declaration_type=BranchDeclarationType.RETROACTIVE,
    trigger=TriggerType.SYSTEM_AUTOMATIC,
    caught_by="SYSTEM",
    detection_window_open=True,
)
```

The recommendation anchors at the last NOMINAL segment — before drift began — so the retroactive branch covers the full drift window.

### 7.2 State Transitions (Default Thresholds)

```
                       drift < 0.3                drift < 0.3
                     ┌──────────────┐           ┌──────────────┐
                     ▼              │           ▼              │
     ┌──────────┐  drift≥0.3,  ┌──────────┐   drift≥0.3,  ┌──────────┐   drift≥0.5, ┌──────────────┐
     │ NOMINAL  │──────────────▶│ WATCHING │─────────────▶│ CANDIDATE│─────────────▶│ MATERIALIZED │
     │ count=0  │   count=1     │ count≥1  │    count≥3   │ count≥3  │   count≥5   │   count≥5    │
     └──────────┘               └──────────┘              └──────────┘             └──────────────┘
          ▲                                                                                │
          │                    drift < 0.3                                                 │
          └────────────────────────────────────────────────────────────────────────────────┘
                              (count resets to 0 on resolution)

     Overrides (forcing CANDIDATE regardless of drift/count):
       • objective_hash changed between consecutive observations
       • intent_class == INTRODUCE
```

### 7.3 Intercept Sequence

1. `objective_hash = sha3_256("OBJECTIVE:" + canonicalized_objective)`
2. `detect_branch_candidate()` reads the last fingerprint for the episode, applies `advance_detection_state()`, and (on first entry to MATERIALIZED) computes the recommendation anchored at `get_last_nominal_segment_sync()`.
3. Build `CoherenceFingerprint` with the new state and count.
4. `enforce_write_time_fingerprint()` — rejects None (G-29).
5. `write_coherence_fingerprint_sync()` persists to `AriadneCoherenceFingerprint` + `FINGERPRINTS` edge from episode.
6. Return `DetectionResult`.

### 7.4 Confirmation Cache

`ConfirmationCache` is an in-memory TTL-by-turn store. Callers use it to suppress re-prompting for confirmation of actions that were recently confirmed:

```python
cache = ConfirmationCache()
cache.record(action_description="declare branch for drift", confirmed_by="human-1",
             current_turn=current, valid_for_turns=10)
...
if not cache.is_confirmed(action_description, current_turn=now):
    ask_user_for_confirmation(...)
```

Keys are canonicalized (case-folded, stripped) before hashing. Expiry is checked at read time; expired entries are discarded, not just filtered.

---

## 8. Neo4j Schema Additions Summary

### 8.1 Node Labels

| Label | Unique constraint on | Phase |
|-------|----------------------|-------|
| `AriadneBranchPoint` | `branch_point_id` | 1 |
| `AriadneBranchTerminus` | `terminus_id` | 1 |
| `AriadneAuditRecord` | `audit_id` | 1 |
| `AriadneIntentRecord` | `intent_id`, `idempotency_key` | 1 |
| `AriadneForkPoint` | `fork_point_id` | 2 |
| `AriadneMergePoint` | `merge_point_id` | 2 |
| `AriadneDepartureForkPoint` | `fork_point_id` | D |
| `AriadneForkReturn` | `fork_return_id` | D |
| `AriadneForkOrphanMarker` | `fork_id` (dedup: one per orphaned fork) | D |
| `AriadneAside` | `aside_id` | 3 |
| `AriadneAsideTerminus` | `aside_terminus_id` | 3 |
| `AriadneSoliloquy` | `soliloquy_id` | 3 |
| `AriadneSoliloquyConclusion` | `conclusion_id` | 3 |
| `AriadneCoherenceFingerprint` | `fingerprint_id` | 4 |

### 8.2 Edge Types

See SPEC §19.6.

### 8.3 Indexes

Episode/status/owner-scoped indexes on every table for listing and state
derivation queries. Full list in `adapters/neo4j/writer.py`
`SCHEMA_INDEXES`.

---

## 9. Test Layout and Coverage

All tests pass under `ARIADNE_ENABLED=true` with a mocked Neo4j driver
(`tests/unit/protocol/test_phase*_{schema,operations,intercept}.py`).

| File | Focus |
|------|-------|
| `test_phase2_schema.py` | Fork/merge schema, hash domain separation, conflict manifest |
| `test_phase2_operations.py` | Fork N-way, resolve, merge clean/conflict/resolved paths, integrity; **Phase D** `TestCreateDepartureFork` + `TestDepartureForkFSM` + producer-hardening (idempotent re-drive, two-phase anchor, full-result replay) + `TestForkOrphanRecovery`: marker self-hash/satellite/dedup, Class-A/B/C recovery incl. retroactive append |
| `test_phase3_schema.py` | Aside/soliloquy schema, HASH_PLACEHOLDER independence from chain, governance |
| `test_phase3_operations.py` | Aside close + reference scan, soliloquy conclude, chain stays in soliloquy |
| `test_phase4_schema.py` | State machine transitions, thresholds, confirmation cache, write-time guard |
| `test_phase4_intercept.py` | Intercept progression NOMINAL→MATERIALIZED, drift reset, objective/INTRODUCE overrides |

The Phase D vectors are colocated in `test_phase2_operations.py` (the departure fork is part of the fork family). Run the whole suite with `pytest`.

---

## 10. Forward Compatibility Notes

The following are deliberate Phase-exit scope limits, forward-compatible
with future extension:

1. **Branch-aware segments.** Segments do not yet carry `branch_id`. When they do, `execute_merge()`'s `target_merkle_root_post` derivation can be replaced with a true spine recomputation, and `find_common_ancestor()` can do iterative traversal for nested branches.
2. **Return-obligation enforcement at seal time.** `check_aside_return_obligation()` and `check_soliloquy_return_obligation()` are callable guards but are not wired into the episode-seal path yet. Integration is the seal implementation's responsibility.
3. **Access-policy runtime enforcement.** Read-time enforcement of `ESCALATION_ONLY` with `audit_on_access=true` (for soliloquies) is coordinator-layer work. The policy is recorded; the guard is left to callers.
4. **Embedding model for `drift_from_spine`.** The protocol is embedding-agnostic — `topic_vector` and `drift_from_spine` are caller-supplied. Applications wire their embedding model into the write path and feed the output to `intercept_segment_write()`.

---

*Developed by Scorched Earth Labs. See SPEC.md §19 for the normative protocol surface.*
