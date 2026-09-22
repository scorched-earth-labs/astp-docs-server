# ASTP — BFM Conformance Test Vectors

**Version:** 1.3.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md §19 (Branch / Fork / Merge / **Departure Fork** / Aside / Soliloquy / CoherenceFingerprint + Orphan Recovery), 5.1.0 (SPEC §19 as of 5.1.0; see the note in §1)

---

## 1. Overview

> **SPEC 5.0.0 / 5.1.0 note.** Two things changed above this document and are stated here so it is not read as current on them. (1) **Seals commit structural nodes.** Under `spine_algorithm_version` 2 a BranchPoint, BranchTerminus, ForkPoint, DepartureForkPoint, ForkReturn, MergePoint and every concluded HITL event is a *structural-manifest member* (SPEC §5.7.1), hashed from its **stored fields** under its own `:v2:` prefix by the canonical field encoding of §5.1.1 — provenance and commentary fields (`initiated_by`, `initiator`, `returned_by`, labels, summaries) are out of those preimages, `spine_merkle_snapshot` and `merge_type` are in, and `GENESIS` is NULL. Those member hashes are pinned in [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json) and computed by `astp/core/seal_v2.py`; the reference deployment's adapter supplies the reader. The 4.x `content_hash` values this document describes are still what the reference writers stamp on the nodes; they are not what a version 2 seal commits. (2) **Asides and soliloquies.** SPEC §19.4 now defines their content hashes as `ASIDE:v2:`, `ASIDE_TERMINUS:v2:`, `SOLILOQUY:v2:`, `DELIBERATION_CHAIN:v2:` (over the deliberation Segments' content hashes, in order) and `SOLILOQUY_CONCLUSION:v2:`, with the 4.x forms — including the two-policy `SoliloquyContentHashPolicy` — retained only as the definitions of nodes already written. The reference writers (`create_aside`, `close_aside`, `create_soliloquy`, `conclude_soliloquy`) stamp the 5.0.0 forms from `astp` 0.5.0; nodes written before that carry the 4.x forms this document describes. The `FINGERPRINT:` prefix is retired: a coherence fingerprint has no content hash (§19.5.1).

This document specifies the conformance test vectors for the Branch/Fork/Merge (BFM) feature family of ASTP (the AI State Tree Protocol). A conforming implementation MUST pass all vectors marked **REQUIRED**. Vectors marked **RECOMMENDED** test behaviors that conforming implementations SHOULD support.

BFM is organized into the following phases (the reference deployment's adapter guide, `IMPLEMENTATION-BFM.md`, which lives with that adapter, follows the same order):

| Phase | Scope | Vector Prefix |
|-------|-------|---------------|
| 1 | Branch lifecycle (linear deviation) | `BR-` |
| 2 | Fork / merge / common ancestor | `FM-` |
| D | Departure-fork lifecycle (single directional departure; origin continues) + orphan recovery | `DF-` / `FO-` |
| 3 | Aside / Soliloquy (social & internal primitives) | `AS-` / `SL-` |
| 4 | Coherence fingerprint write-time branch detection | `CF-` |

Vector format matches `CONFORMANCE.md` (Phase 3 Trust Infrastructure §16): ID, spec reference, class, description, inputs, expected output, failure condition. All hex values lowercase. All string fields UTF-8.

> **v1.1.0 reconciliation note.** This vector set was realigned to SPEC v3.2.1: §19 subsection references and governance rule numbers were corrected to the consolidated §19 / G-19–G-29 numbering (the v1.0.0-draft predated it), and the Phase D `DF-` set was added. Branch-phase governance (depth limit, access policy, abandonment reason) is enforced at the implementation layer — it has no numbered SPEC §19 governance rule — so those vectors cite the `IMPLEMENTATION-BFM.md` enforcement function rather than a G-number.
>
> **v1.2.0 note.** Added the orphan-recovery `FO-` set (§4.5, SPEC §19.3.7). These are state-integrity vectors (they test the shape of a conformant *recovery*), not new governance rules — and FO-008 makes explicit that running detection is **not** a conformance requirement.

---

## 2. Phase 1 — Branch Lifecycle Vectors (§19.2)

### 2.1 Hash Canonicalization

**BR-001** — `BranchPointNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.2.1, §19.2.3 (Dual Hash Chain)
- **Description:** `compute_branch_point_hash()` MUST produce identical bytes across implementations given identical inputs. The canonical byte layout covers: `parent_episode_id`, `branch_id`, `declaration_type`, `parent_sequence_index`, `branch_root_content_hash`, `authored_by`, `created_at`.
- **Verification Protocol:** Cross-implementation consistency check (pattern matches KH-001). Two conforming implementations MUST produce identical `branch_point_hash` bytes for the same input tuple.
- **Failure Condition:** Divergent bytes indicate a canonicalization error (wrong field order, wrong integer encoding, missing field).

**BR-002** — `BranchTerminusNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.2.2, §19.2.3
- **Description:** `compute_branch_terminus_hash()` canonicalizes `branch_id`, `terminus_type`, `final_sequence_index`, `terminus_content_hash`, `abandonment_reason` (optional), `authored_by`, `closed_at`.

**BR-003** — `AuditRecord` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.2.4 (Derived Lifecycle State)
- **Description:** `compute_audit_record_hash()` forms a content-addressed chain where `prior_audit_hash` binds each record to its predecessor. Implementations MUST NOT allow silent tampering; recomputing the hash over stored fields MUST match the stored `audit_hash`.
- **Failure Condition:** Any stored `AuditRecord` whose recomputed hash diverges from its stored value.

**BR-004** — `IntentRecord` idempotency key
- **Class:** REQUIRED
- **Spec Reference:** §19.2.4
- **Description:** `compute_intent_idempotency_key()` MUST collapse retried writes with the same `(agent_id, intent_type, resource_id, request_sequence)` tuple to the same key. A second `create_branch` call with the same idempotency key MUST return the original `BranchResult` without creating a new `BranchPointNode`.

### 2.2 Governance Enforcement

> Branch-phase governance below is enforced at the implementation layer (the reference adapter's guide, `IMPLEMENTATION-BFM.md` §3.2, shipped with that adapter); the current SPEC §19 defines no numbered branch-phase governance rule. Numbered SPEC governance begins at G-19 (fork).

**BR-005** — Branch depth limit
- **Class:** REQUIRED
- **Spec Reference:** §19.2, IMPLEMENTATION-BFM §3.2 (`enforce_branch_depth_limit`)
- **Description:** `enforce_branch_depth_limit()` MUST reject (or log-on-override) any `create_branch` whose resulting lineage depth exceeds the soft maximum (default 4). Depth is counted from the root episode, inclusive.
- **Failure Condition:** A lineage past the soft max is created with no audit record of the override.

**BR-006** — Access policy gate
- **Class:** RECOMMENDED
- **Spec Reference:** §19.2, IMPLEMENTATION-BFM §3.2
- **Description:** Where an implementation records an `AccessPolicy`, branch creation whose policy denies the requester's `AccessLevel` for the requested `AccessResourceType` MUST be rejected before any write.

**BR-007** — Abandonment reason required
- **Class:** REQUIRED
- **Spec Reference:** §19.2.2, IMPLEMENTATION-BFM §3.2 (`enforce_abandonment_reason_required`)
- **Description:** `enforce_abandonment_reason_required()` MUST reject `abandon_branch()` calls whose `reason` is `None` or the empty string. A branch with `terminus_type=ABANDONED` MUST have a non-empty reason recorded.

---

## 3. Phase 2 — Fork / Merge Vectors (§19.3)

### 3.1 Hash Canonicalization

**FM-001** — `ForkPointNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.3.1
- **Description:** `compute_fork_point_hash()` canonicalizes `parent_episode_id`, `fork_id`, `objective_hash`, `sibling_branch_ids` (sorted), `parent_sequence_index`, `authored_by`, `created_at`.

**FM-002** — `MergePointNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.3.2
- **Description:** `compute_merge_point_hash()` canonicalizes all three integrity roots (`source_merkle_root`, `target_merkle_root_pre`, `target_merkle_root_post`) plus `merge_id`, `source_episode_id`, `target_episode_id`, `common_ancestor_id`, `timestamp`, `parent_hash`. Domain prefix `MERGE_POINT:`.

**FM-003** — `ConflictManifest` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.3.2 (G-23 Conflict Surface Invariant)
- **Description:** `compute_conflict_manifest_hash()` canonicalizes an ordered list of `ConflictSegment`+`ConflictResolution` pairs. Order-independence is a non-goal; reordering changes the hash. Domain prefix `CONFLICT_MANIFEST:`.

### 3.2 Governance Enforcement

**FM-004** — Fork objective required (G-19)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.1, G-19
- **Description:** `create_fork()` with a missing or empty `fork_objective` MUST be rejected. A fork without an objective is indistinguishable from a branch.

**FM-005** — Fork alternatives ≥ 2 (G-20)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.1, G-20
- **Description:** A fork creating fewer than 2 sibling alternatives MUST be rejected. Single-path divergence is a branch, not a fork.

**FM-006** — Merge summary required (G-22)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.2, G-22
- **Description:** `execute_merge()` calls without a non-empty `merge_summary` MUST be rejected. Every merge records why the convergence happened.

**FM-007** — Three-root conflict-surface integrity (G-23)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.2, G-23, IMPLEMENTATION-BFM §4.3
- **Description:** On conflicts without matching resolutions — or `merge_strategy == AUTO` with any conflicts — `execute_merge()` MUST write NO merge records and return a `ConflictManifest` carrying `source_merkle_root`, `target_merkle_root_pre`, the common ancestor, and all conflict segments. Every manifest-referenced segment MUST be reachable from at least one of the three recorded roots.
- **Failure Condition:** A merge silently commits a conflicted resolution, or a manifest entry references a segment not present under any of the three roots.

**FM-008** — `find_common_ancestor()` determinism
- **Class:** REQUIRED
- **Spec Reference:** §19.3.2
- **Description:** `find_common_ancestor(branch_id, target_episode_id)` MUST return the same `CommonAncestorResult` across repeated invocations on stable graph state, preferring the most-recent shared ancestor (LCA semantics) when multiple common ancestors exist.

**FM-009** — Merge integrity verification (G-24)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.3, G-24
- **Description:** `verify_merge_integrity()` MUST re-verify all three Merkle roots against stored `MergePointNode` fields (`source_valid ∧ target_pre_valid ∧ target_post_valid`). Any field-level mutation MUST produce `integrity_holds = false`.

---

## 4. Phase D — Departure-Fork Vectors (§19.3.5–19.3.6)

A departure fork is a single directional departure (`create_departure_fork()`) into a new Episode while the origin *continues* — distinct from the speculative fork of §3. (The reference adapter's guide, `IMPLEMENTATION-BFM.md` §5, describes one storage layout.)

### 4.1 Hash Canonicalization

**DF-001** — `DepartureForkPointNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5
- **Description:** `compute_departure_fork_point_hash()` canonicalizes, in order, `fork_point_id`, `fork_id`, `fork_episode_id`, `origin_episode_id`, `origin_segment_id`, `fork_objective`, `fork_creation_trigger`, `spine_tip_hash_at_departure`, `initiator`, `timestamp`, `parent_hash`. Domain prefix `DEPARTURE_FORK_POINT:` (SHA3-256).
- **Verification Protocol:** Cross-implementation consistency check. Two conforming implementations MUST produce identical bytes for the same input tuple.
- **Failure Condition:** The `DEPARTURE_FORK_POINT:` prefix collides with `FORK_POINT:` (a departure fork point and a speculative fork point with otherwise-identical fields MUST hash differently), or any field-order divergence.

**DF-002** — `ForkReturnNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5
- **Description:** `compute_fork_return_hash()` canonicalizes, in order, `fork_return_id`, `fork_id`, `fork_episode_id`, `origin_episode_id`, `return_type`, `synthesis_summary`, `fork_final_spine_tip_hash`, `returned_by`, `timestamp`, `parent_hash`. Domain prefix `FORK_RETURN:` (SHA3-256).

### 4.2 The Backdating Integrity Invariant

**DF-003** — Backdating integrity (G-30)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-30
- **Description:** `create_departure_fork()` MUST make `DepartureForkPointNode.spine_tip_hash_at_departure` equal to the fork Episode's `fork_origin_spine_tip_hash` — both derived from a single read of the origin spine tip at the departure moment. Cross-verifiable across the two independent spines.
- **Failure Condition:** The fork point's `spine_tip_hash_at_departure` and the fork Episode's `fork_origin_spine_tip_hash` differ. This MUST be a fatal error at creation, never a runtime reconciliation.

### 4.3 Governance Enforcement

**DF-004** — Fork objective required (G-31)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-31
- **Description:** `create_departure_fork()` with an empty `fork_objective` MUST be rejected (mirrors G-19 for the speculative fork).

**DF-005** — Trigger whitelist (G-32)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-32
- **Description:** `fork_creation_trigger` MUST be one of `{TOPIC_SHIFT, PARALLEL_THREAD, EXPLICIT_FORK, AGENT_ESCALATION}`. `EXPLORATORY_THREAD` MUST be rejected here — it routes to the speculative `create_fork()`.

**DF-006** — Escalation requires trigger segment (G-33)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-33
- **Description:** When `fork_creation_trigger == AGENT_ESCALATION`, `fork_trigger_segment_id` MUST be present. Escalations must point at the segment that provoked them.

### 4.4 Lifecycle FSM

**DF-007** — State transitions
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5
- **Description:** The lifecycle FSM is `ACTIVE → COMPLETED | ABANDONED`. `complete_departure_fork()` (`ACTIVE → COMPLETED`) and `abandon_departure_fork()` (`ACTIVE → ABANDONED`, terminal) MUST reject transitions from any non-`ACTIVE` state. A `COMPLETED` fork MUST NOT be abandoned.
- **Verification Protocol:** Given a state and an operation, the resulting state MUST match the FSM; illegal transitions MUST raise, not silently no-op.
- **Failure Condition:** A `COMPLETED` or `ABANDONED` fork accepts a further transition; resumption (re-entering the origin while the fork stays `ACTIVE`) writes any node or declaration (it MUST be a non-event).

**DF-008** — Return requires COMPLETED (G-34)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-34
- **Description:** `declare_fork_return()` MUST reject any fork whose `fork_status` is not `COMPLETED`.

**DF-009** — At most one return per fork (G-35)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.5, G-35
- **Description:** A second `declare_fork_return()` for a `fork_id` that already has a `ForkReturnNode` MUST be rejected. `return_type ∈ {INCORPORATED, ACKNOWLEDGED, SUPERSEDED}`; the return is declarative (origin-spine assertion across two spines), never a structural merge.

### 4.5 Orphan Recovery (§19.3.7)

These vectors test the *shape of a conformant recovery*, not that an implementation runs detection — **detection cadence is explicitly non-normative** (FO-008).

**FO-001** — `ForkOrphanMarker` self-hash determinism
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** `compute_fork_orphan_marker_hash()` (domain `FORK_ORPHAN_MARKER:`) canonicalizes `fork_orphan_marker_id`, `fork_id`, `origin_episode_id`, `orphan_class`, `sequence_index`, `detection_run_id`, `recovery_action`, `requires_operator_review`, `detected_at`. Two conforming implementations MUST produce identical bytes for the same input tuple.

**FO-002** — Marker is a non-chained satellite (Spine isolation)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** A `ForkOrphanMarker` is self-hashed (`content_hash`) but MUST NOT participate in the origin spine's Merkle chain — it carries no `parent_hash`, and writing it MUST NOT change the origin Episode's spine root/tip.
- **Verification Protocol:** Capture the origin Episode's spine root; write a marker; the root MUST be unchanged.
- **Failure Condition:** Writing a marker alters the origin Episode's integrity fingerprint (a diagnostic write mutating the cryptographic record).

**FO-003** — Marker dedup (one per orphaned fork)
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** Markers are deduplicated on `fork_id` — a re-detection sweep that re-finds the same orphan MUST NOT create a duplicate marker.
- **Failure Condition:** Two detection passes over the same unresolved orphan yield two marker nodes.

**FO-004** — Marker excluded from departure registry
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** Departure-registry queries match `DepartureForkPointNode` / `ForkReturnNode` only. A `ForkOrphanMarker` MUST NOT appear in departure-registry results.

**FO-005** — Class-B retroactive write: append + backdated anchor + byte-identical
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** The Class-B retroactive `DepartureForkPointNode` write MUST (a) use the fork Episode's stored `fork_origin_spine_tip_hash` as the point's `spine_tip_hash_at_departure` so the cross-verifiable invariant holds, (b) produce a `content_hash` **byte-identical** to an on-time write (the `retroactive` / `orphan_recovery_timestamp` flags are outside the preimage), and (c) create ONLY the missing point — no existing spine node or chain hash is recomputed.
- **Failure Condition:** The recovered point's `content_hash` differs from an on-time write, OR any pre-existing spine hash changes.

**FO-006** — Class-B hash-mismatch gate
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** When the fork provenance is inconsistent with the origin spine at `fork_anchor_index`, recovery MUST escalate to an operator and MUST NOT write the retroactive point.

**FO-007** — Append-only recovery
- **Class:** REQUIRED
- **Spec Reference:** §19.3.7
- **Description:** Orphan recovery MUST NOT delete spine nodes. A dangling point (Class A) is flagged `orphaned=true` and marked, never removed.

**FO-008** — Detection cadence is non-normative
- **Class:** RECOMMENDED
- **Spec Reference:** §19.3.7
- **Description:** Conformance does NOT require an implementation to run orphan detection, nor at any particular cadence. Only the node schema, the field mutations, and the retroactive-write discipline (FO-001…007) are normative. An implementation that never orphans (or resolves orphans by other means) is conformant provided it never violates the invariants.

---

## 5. Phase 3 — Aside / Soliloquy Vectors (§19.4)

### 5.1 Aside Hash Canonicalization

**AS-001** — `AsideSegmentNode` commitment hash
- **Class:** REQUIRED
- **Spec Reference:** §19.4.1
- **Description:** `compute_aside_hash()` canonicalizes `aside_id`, `parent_segment_id`, `initiated_by_human`, `target_agent_id`, `content_hash`, `opened_at`.

### 5.2 Aside Governance

**AS-002** — Aside human-initiated (G-25)
- **Class:** REQUIRED
- **Spec Reference:** §19.4.1, G-25
- **Description:** An aside whose `initiated_by_human` is missing or does not identify a human user MUST be rejected. Asides are strictly human-initiated — agent-initiated diversions use soliloquy.

**AS-003** — Aside target agent required
- **Class:** REQUIRED
- **Spec Reference:** §19.4.1
- **Description:** An aside without a `target_agent_id` MUST be rejected. Every aside pairs one human with one agent; multi-agent asides are modeled as nested asides.

**AS-004** — Aside close reason required
- **Class:** REQUIRED
- **Spec Reference:** §19.4.1
- **Description:** `close_aside()` without a non-empty `reason` MUST be rejected. The close reason distinguishes `AsideTerminationStatus` values (`resolved`, `abandoned`, `superseded`, etc).

**AS-005** — Aside return obligation at episode seal (G-26)
- **Class:** REQUIRED
- **Spec Reference:** §19.4.1, G-26
- **Description:** `check_aside_return_obligation(aside_open=True, episode_sealing=True)` MUST raise. An episode MUST NOT seal while an aside is open; all asides must close or be explicitly abandoned first.

**AS-006** — Aside external reference scan
- **Class:** RECOMMENDED
- **Spec Reference:** IMPLEMENTATION-BFM §6.2
- **Description:** On aside close, implementations SHOULD scan for segments outside the aside subgraph that reference the aside's segments and flag them for review. Advisory (not governance) but valuable for downstream audit.

### 5.3 Soliloquy Hash Canonicalization

**SL-001** — `SoliloquySegmentNode` content hash
- **Class:** REQUIRED
- **Spec Reference:** §19.4.3 (Soliloquy Content Hash Policy)
- **Description:** `compute_soliloquy_content_hash()` is policy-dependent on `SoliloquyContentHashPolicy`:
  - `HASH_PLACEHOLDER` (default) — preimage `{id}:{ep}:{seg}:{agent}:{ts}`; content NOT recoverable from the hash, chain integrity preserved.
  - `FULL_CONTENT` — preimage `{id}:{ep}:{seg}:{agent}:{ts}:{chain}`; allows direct hash verification of the chain.
- **Verification Protocol:** Given a fixed policy, implementations MUST match byte-for-byte. Switching policy across implementations expectedly produces different hashes.

**SL-002** — Deliberation chain hash
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2
- **Description:** *4.x form — retained for nodes written before astp 0.5.0; the 5.0.0 construction is `DELIBERATION_CHAIN:v2:` over the deliberation Segments' content hashes in order (SPEC §19.4).* `compute_deliberation_chain_hash()` (domain `DELIBERATION_CHAIN:`) binds each soliloquy segment to its predecessor via a rolling hash chain. Tampering with any intermediate segment MUST be detectable by recomputing the chain and comparing to the stored conclusion's chain hash.

**SL-003** — `SoliloquyConclusionNode` hash
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2
- **Description:** *4.x form — retained for nodes written before astp 0.5.0; the 5.0.0 construction is `SOLILOQUY_CONCLUSION:v2:` (SPEC §19.4).* `compute_soliloquy_conclusion_hash()` (domain `SOLILOQUY_CONCLUSION:`) canonicalizes `soliloquy_id`, `conclusion_content_hash`, `deliberation_chain_hash`, `merged_into_segment_id`, `concluded_at`.

### 5.4 Soliloquy Governance

**SL-004** — Soliloquy purpose required
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2
- **Description:** `create_soliloquy()` without a non-empty `purpose` MUST be rejected. A soliloquy without a purpose is indistinguishable from a branch.

**SL-005** — Human-accessible visibility policy (G-27)
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2, G-27
- **Description:** Every soliloquy's `SoliloquyVisibilityPolicy` MUST allow at least one identified human user to view the conclusion. Agent-only soliloquies (no human visibility ever) are forbidden.

**SL-006** — Conclusion summary required
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2
- **Description:** `conclude_soliloquy()` without a non-empty `summary` MUST be rejected. The summary is the only content guaranteed visible to humans under all visibility policies.

**SL-007** — Soliloquy return obligation (G-28)
- **Class:** REQUIRED
- **Spec Reference:** §19.4.2, G-28
- **Description:** `check_soliloquy_return_obligation()` MUST raise when an episode attempts to seal with an open soliloquy. Mirror of AS-005 for agent-initiated deliberation.

---

## 6. Phase 4 — Coherence Fingerprint Vectors (§19.5)

### 6.1 Hash Canonicalization

**CF-001** — `CoherenceFingerprint` hash
- **Class:** REQUIRED
- **Spec Reference:** §19.5.1
- **Description:** `compute_fingerprint_hash()` canonicalizes `fingerprint_id`, `agent_id`, `session_id`, `computed_at`, `components` (a fixed-order dict of signal→score), `version`. Field order and component ordering are part of canonicalization.

**CF-002** — Objective hash
- **Class:** REQUIRED
- **Spec Reference:** §19.5.3
- **Description:** `compute_objective_hash()` (domain `OBJECTIVE:`) MUST be a stable function of the objective text. Two semantically-equivalent objectives with different wording MUST produce different hashes — the hash is syntactic, not semantic.

### 6.2 Detection State Machine

**CF-003** — State machine transitions
- **Class:** REQUIRED
- **Spec Reference:** §19.5.2, IMPLEMENTATION-BFM §7.2
- **Description:** `advance_detection_state()` MUST implement the canonical state machine (`NOMINAL → WATCHING → CANDIDATE → MATERIALIZED`), with drift-below-threshold resetting toward `NOMINAL`, and the overrides that force `CANDIDATE` (objective_hash change between consecutive observations; `intent_class == INTRODUCE`). Direct `NOMINAL → MATERIALIZED` MUST NOT occur.
- **Verification Protocol:** Given a sequence of `(drift, intent_class, objective_hash, thresholds)` inputs, the output state sequence MUST match the canonical execution.

**CF-004** — Materialized recommendation
- **Class:** REQUIRED
- **Spec Reference:** §19.5.3
- **Description:** The materialized recommendation MUST be deterministic given the same `DetectionResult`, and MUST anchor at the last NOMINAL segment (before drift began) so a retroactive branch covers the full drift window. Non-determinism (e.g., model-sampling-based suggestions) violates conformance.

### 6.3 Write-Time Enforcement

**CF-005** — Write-time fingerprint gate (G-29)
- **Class:** REQUIRED
- **Spec Reference:** §19.5.3, G-29
- **Description:** `enforce_write_time_fingerprint()` MUST reject segment writes whose `fingerprint` is `None` in episodes where fingerprint enforcement is enabled. Segments written without fingerprints cannot be retroactively analyzed for branch candidacy.

**CF-006** — Intercept sequence ordering
- **Class:** REQUIRED
- **Spec Reference:** §19.5.3, IMPLEMENTATION-BFM §7.3
- **Description:** `intercept_segment_write()` MUST execute in the order: (1) compute objective hash, (2) `detect_branch_candidate()` against the last fingerprint, (3) `advance_detection_state()`, (4) build + write-time-gate the fingerprint, (5) persist, (6) return a decision. A different ordering may produce inconsistent results.

### 6.4 Confirmation Cache Idempotency

**CF-007** — `ConfirmationCache` idempotency
- **Class:** REQUIRED
- **Spec Reference:** §19.5.4, IMPLEMENTATION-BFM §7.4
- **Description:** Given the same canonicalized `(action_description, confirming_party)` within its `valid_for_turns` window, `ConfirmationCache` MUST report the action confirmed across repeated lookups. Re-confirming a prior decision is a no-op, not a new decision.
- **Failure Condition:** Two lookups with identical keys inside the window produce different confirmation results.

**CF-008** — Cache expiry at read time
- **Class:** REQUIRED
- **Spec Reference:** §19.5.4
- **Description:** Expiry MUST be checked at read time; an entry past its turn window MUST be treated as absent (discarded, not merely filtered). A confirmation MUST NOT apply past its `valid_for_turns` horizon.

---

## 7. Governance Rule Enforcement Matrix

Summary of governance rules enforced across BFM, cross-referenced with SPEC §19's rule catalog (G-19–G-35). Branch-phase checks are implementation-enforced (no numbered SPEC rule) and omitted here.

| Rule | Scope | Vector(s) |
|------|-------|-----------|
| G-19 | Fork objective non-empty | FM-004 |
| G-20 | Fork alternatives ≥ 2 | FM-005 |
| G-22 | Merge summary non-empty | FM-006 |
| G-23 | Conflict surface invariant | FM-007 |
| G-24 | Merge integrity assertions | FM-009 |
| G-25 | Aside human-initiated | AS-002 |
| G-26 | Aside return obligation | AS-005 |
| G-27 | Soliloquy human accessibility | SL-005 |
| G-28 | Soliloquy return obligation | SL-007 |
| G-29 | Write-time fingerprint | CF-005 |
| G-30 | Departure-fork backdating integrity | DF-003 |
| G-31 | Departure-fork objective non-empty | DF-004 |
| G-32 | Departure-fork trigger whitelist | DF-005 |
| G-33 | Departure-fork escalation trigger segment | DF-006 |
| G-34 | Return requires COMPLETED | DF-008 |
| G-35 | One return per fork | DF-009 |

---

## 8. Conformance Levels

### Level 1: Protocol Conformance

Implementation passes all **REQUIRED** vectors in sections 2–6 and the governance matrix in section 7. No claim is made about storage layout or performance.

### Level 2: Full Conformance

Level 1 plus all **RECOMMENDED** vectors and the advisory checks in IMPLEMENTATION-BFM §6.2 (aside external reference scan) and §9 (test coverage matrix).

---

## 9. Cross-Reference

- **SPEC.md §19** — normative protocol surface (v3.3.0)
- **IMPLEMENTATION-BFM.md** — the reference deployment's adapter guide (non-normative; shipped with that adapter, not with the protocol)
- **CONFORMANCE.md** — Phase 3 Trust Infrastructure vectors (§16)

---

*ASTP BFM Conformance Test Vectors are maintained by Scorched Earth Labs.*
*Vector set version: 1.2.0 | Applies to SPEC.md: v3.3.0 §19*
