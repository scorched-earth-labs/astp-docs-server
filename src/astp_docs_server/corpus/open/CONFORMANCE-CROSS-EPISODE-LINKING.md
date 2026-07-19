# Ariadne Protocol — Cross-Episode Linking & Grouping Conformance Test Vectors

**Version:** 1.0.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-07-04
**Applies To:** SPEC.md §20 (Cross-Episode Linking & Grouping), v3.2.1

---

## 1. Overview

This document specifies the conformance test vectors for the **Cross-Episode Linking & Grouping** feature family of the Ariadne Protocol (SPEC §20). A conforming implementation MUST pass all vectors marked **REQUIRED**. Vectors marked **RECOMMENDED** test behaviors that conforming implementations SHOULD support.

These are **cross-implementation-consistency** vectors, not hardcoded golden-hash values. A hash vector specifies the canonical byte layout (ordered field set + canonicalization rules) and asserts that **two conforming implementations MUST produce identical bytes for the same input tuple**. This is wire-tier conformance (§20 →12.1): the protocol fixes the preimage, not a specific digest. Where a vector references SPEC §20, it uses the amendment's internal §1–§12 numbering scoped within §20 (cited as `§20 →N`).

Cross-Episode Linking & Grouping is organized into the following scopes, matching `IMPLEMENTATION-CROSS-EPISODE-LINKING.md`:

| Scope | Coverage | Vector Prefix |
|-------|----------|---------------|
| Cross-episode link schema + integrity | `EpisodeLink` hash, mutual exclusivity, audit deltas | `CEL-` |
| Link health & quarantine lifecycle | Health-state FSM, quarantine resolution/escalation | `LH-` |
| Inference signals & discovery | `Signal` recording, propose/reject audit events | `SG-` |
| Episode membership | `MembershipRecord` hash + succession chain | `MR-` |
| Grouping conformance | `ConformanceDeclaration` hash + SemVer versioning | `CD-` |

All hex values lowercase. All string fields UTF-8. Datetimes UTC-normalized ISO 8601. Floats canonicalized via Python `repr()` semantics (round-trippable, platform-stable).

> **Governance model note.** Unlike the BFM family (SPEC §19, G-19–G-35), Cross-Episode Linking & Grouping has **zero numbered SPEC G-rules**. Its governance is enforced through (a) the `LinkGovernanceError` taxonomy (mutual exclusivity), (b) the Link Health / quarantine FSM (§20 →6, →11.3), (c) the immutable-with-succession chain-integrity checks for `MembershipRecord` / `ConformanceDeclaration`, and (d) the `GroupingGovernanceError` SemVer taxonomy. The governance matrix in §7 reflects THIS structure, not invented G-numbers.

---

## 2. Cross-Episode Link Vectors (§20 →2, →3, →5)

### 2.1 Hash Canonicalization

**CEL-001** — `EpisodeLink` content hash
- **Class:** REQUIRED
- **Spec Reference:** §20 →2 (hash preimage note)
- **Description:** `compute_episode_link_content_hash()` MUST produce identical bytes across implementations given identical inputs. The canonical layout is the ordered field set, serialized as a JSON object with `sort_keys=False` and `separators=(",",":")`, then SHA3-256. Field order (from `_HASH_PREIMAGE_FIELDS`): `link_id`, `source_episode`, `target_episode`, `created_at`, `created_by`, `link_type`, `link_strength`, `is_inferred`, `inference_signals`, `inference_threshold`, `retroactive`, `health_state`, `health_checked_at`, `source_version`, `target_version`, `quarantine_reason`, `quarantined_at`.
- **Verification Protocol:** Cross-implementation consistency check. Two conforming implementations MUST produce identical `content_hash` bytes for the same input tuple.
- **Failure Condition:** Divergent bytes indicate a canonicalization error (wrong field order, alphabetical key sort, non-`repr` float encoding, non-UTC datetime, or an unexpectedly included/excluded field).

**CEL-002** — Quarantine-resolution field exclusion
- **Class:** REQUIRED
- **Spec Reference:** §20 →2 (hash preimage note)
- **Description:** `quarantine_resolved_at` and `quarantine_resolution` MUST NOT appear in the `EpisodeLink` content-hash preimage. Setting either field on an existing link (on quarantine close) MUST NOT change `content_hash`.
- **Failure Condition:** A link's `content_hash` changes when only `quarantine_resolved_at` / `quarantine_resolution` are set — the resolution lifecycle is committed by the audit log, not the content hash.

**CEL-003** — Health-state field inclusion
- **Class:** REQUIRED
- **Spec Reference:** §20 →2, §20 →11.2.2 (`LINK_INTEGRITY` field snapshot)
- **Description:** Mutable health fields `health_state` and `health_checked_at` ARE part of the preimage (drift detection is cryptographically anchored to write-time state). The `LINK_INTEGRITY` proof's `field_snapshot` MUST cover exactly the CEL-001 field set. Re-stamping after a health transition MUST yield a new, deterministic hash.
- **Verification Protocol:** Recompute over stored canonical fields; MUST equal stored `content_hash`.

**CEL-004** — `LinkAcceptedDelta` audit binding
- **Class:** REQUIRED
- **Spec Reference:** §20 →5, §20 →11.4
- **Description:** Asserting a link (`assert_episode_link`) MUST emit a `LINK_ACCEPTED` `AuditRecord` on the **source-episode** chain, carrying forward delta (`link_id`, `source_episode`, `target_episode`, `link_type`, `link_strength`, `is_inferred`, `retroactive`) and reverse delta (`reverse_delete_link_id`). The record's `record_hash` MUST chain off `prior_audit_hash` and recompute deterministically.
- **Failure Condition:** A link node created with no corresponding `LINK_ACCEPTED` audit record, or an audit record whose recomputed hash diverges from stored.

### 2.2 Mutual-Exclusivity Governance (§20 →3)

**CEL-005** — Link-type mutual exclusivity
- **Class:** REQUIRED
- **Spec Reference:** §20 →3 (Link Type Taxonomy)
- **Description:** `enforce_link_mutual_exclusivity()` MUST raise `LinkGovernanceError` when a new link type collides with an existing type on the same `(source_episode, target_episode)` pair. The exclusion set is exactly `{CONTINUES_FROM, SUPERSEDES}` and `{CONTINUES_FROM, BRANCHES_FROM}`. `SUPERSEDES` and `BRANCHES_FROM` MUST coexist; all other types compose freely.
- **Failure Condition:** A `(source, target)` pair carries both `CONTINUES_FROM` and `SUPERSEDES` (or both `CONTINUES_FROM` and `BRANCHES_FROM`), or a valid compatible pair is spuriously rejected.

**CEL-006** — Endpoint existence precondition
- **Class:** REQUIRED
- **Spec Reference:** §20 →2, IMPLEMENTATION §4.4
- **Description:** A link assertion whose source or target Episode does not exist MUST be rejected before any node/edge write (no orphan links). The `LINKED_TO {via: link_id}` edge MUST carry the link_id for one-hop edge→node lookup.

**CEL-007** — Resumption isolation rule
- **Class:** RECOMMENDED
- **Spec Reference:** §20 →3 (Resumption isolation rule)
- **Description:** On episode resumption the loader MUST follow `CONTINUES_FROM` and `SUPERSEDES` links (spine traversal) and MAY follow `INFORMED_BY` / `SPAWNED_FROM` up to one hop. `REFERENCES` links are non-loading — available for audit but MUST NOT trigger content retrieval on resumption.

---

## 3. Link Health & Quarantine Vectors (§20 →6, →11.3)

**LH-001** — Health-state FSM
- **Class:** REQUIRED
- **Spec Reference:** §20 →6 (Link Health State Machine)
- **Description:** The health FSM MUST admit exactly the transitions in §20 →6: `VALID → {STALE, FROZEN, BROKEN, QUARANTINED}`, `STALE → {BROKEN, QUARANTINED}`, `QUARANTINED → {VALID (CONFIRMED), BROKEN (DISSOLVED), ESCALATED (TTL)}`, `BROKEN → QUARANTINED (re-evaluation)`. There is NO automatic `QUARANTINED → BROKEN`; exit requires an explicit `QuarantineResolution`.
- **Verification Protocol:** Given a state and a transition trigger, the resulting state MUST match the FSM; illegal transitions MUST be rejected, not silently applied.
- **Failure Condition:** A quarantined link auto-transitions to `BROKEN` without an explicit resolution, or a major-version target advance auto-transitions to `BROKEN` (it MUST route to human review, remaining `VALID`/`STALE`).

**LH-002** — Quarantine resolution semantics
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.3.1, `QuarantineResolution` enum
- **Description:** `CONFIRMED` → `health_state = VALID`; `DISSOLVED` → `health_state = BROKEN`; both set `quarantine_resolved_at` + `quarantine_resolution` and emit `LINK_QUARANTINE_RESOLVED`. `ESCALATED` keeps `health_state = QUARANTINED` and emits `QUARANTINE_ESCALATED`. Escalated links MUST NOT auto-resolve — human review is required to reach `CONFIRMED`/`DISSOLVED`.

**LH-003** — Per-Episode quarantine queue
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.1.4 (Redis schema, pushback #3)
- **Description:** The quarantine queue MUST be keyed per-Episode: `ariadne:quarantine:queue:{episode_id}` (a ZSET scored by deadline). A single global queue across all Episodes is non-conforming.
- **Failure Condition:** A global quarantine key is used, causing a quarantine event in one Episode to be processed in another's context.

**LH-004** — Quarantine escalation event
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.3.3 (Chronos addition)
- **Description:** On TTL breach a `QUARANTINE_ESCALATED` audit event MUST fire carrying `link_id`, `episode_id`, `quarantined_at`, `ttl_deadline`, `escalated_at`, `escalation_reason ∈ {TTL_EXCEEDED, INTEGRITY_UNRESOLVABLE, HUMAN_REQUIRED}`. The link remains `QUARANTINED`.

---

## 4. Inference Signal & Discovery Vectors (§20 →4, →5, →12.2)

**SG-001** — `Signal` recording completeness
- **Class:** REQUIRED
- **Spec Reference:** §20 →4 (Inference Signal Specification)
- **Description:** Every signal contributing to a candidate's composite score MUST be recorded in `inference_signals` with `signal_type ∈ {SEMANTIC_SIMILARITY, PARTICIPANT_OVERLAP, TEMPORAL_PROXIMITY, EXPLICIT_REFERENCE, SHARED_ARTIFACT}`, `signal_weight`, `signal_value`, `computed_at`. Signals are canonicalized into the CEL-001 preimage via `model_dump()` (recursively, in list order). Signal **combination** (weights, composite formula) is behavioral-tier (sovereign); signal **recording** is required.
- **Failure Condition:** A composite score computed from a signal not present in the recorded `inference_signals` list.

**SG-002** — `LINK_PROPOSED` audit-the-decision
- **Class:** REQUIRED
- **Spec Reference:** §20 →5, §20 →12.2, §1 (constants)
- **Description:** `propose_link_candidate()` (score in `[DISCOVERY_THRESHOLD, AUTO_ACCEPT_THRESHOLD)`) MUST emit an append-only `LINK_PROPOSED` audit event carrying `composite_score`, the full `inference_signals` breakdown, and `discovery_threshold_at_creation` + `auto_accept_threshold_at_creation` (the threshold values in effect at proposal time). No `EpisodeLink` node is created. The returned `audit_id` correlates later accept/reject decisions.
- **Failure Condition:** A proposal that omits the threshold-at-creation values, defeating post-hoc calibration.

**SG-003** — `CANDIDATE_REJECTED` sub-threshold recording
- **Class:** REQUIRED
- **Spec Reference:** §20 →5 (CANDIDATE_REJECTED note), §1
- **Description:** `record_candidate_rejection()` (score strictly `< DISCOVERY_THRESHOLD`) MUST emit an append-only `CANDIDATE_REJECTED` audit event with full signals + `discovery_threshold_at_creation`. Not surfaced for human review; exists purely so the calibration loop can analyze sub-threshold patterns.

**SG-004** — `LINK_REJECTED` proposal correlation
- **Class:** REQUIRED
- **Spec Reference:** §20 →5 (Gap 5), `RejectionReason` enum
- **Description:** `record_link_rejection()` MUST emit `LINK_REJECTED` carrying `proposed_audit_event_id` (the `LINK_PROPOSED` it rejects) and `rejection_reason ∈ {LOW_CONFIDENCE, WRONG_RELATIONSHIP_TYPE, NOT_RELATED, DUPLICATE_OF_EXISTING}`. Rejection is a new forward event (append-only) — it MUST NOT mutate or delete the prior proposal record.
- **Failure Condition:** A rejection that overwrites the proposal, or omits the `proposed_audit_event_id` linkage.

---

## 5. Episode Membership Vectors (§20 →7, →11.3.2)

### 5.1 Hash Canonicalization

**MR-001** — `MembershipRecord` content hash
- **Class:** REQUIRED
- **Spec Reference:** §20 →7 (Gap 6), §20 →10 (forward-pointer exclusion)
- **Description:** `compute_membership_record_content_hash()` canonicalizes, in order (from `_MEMBERSHIP_HASH_PREIMAGE_FIELDS`): `record_id`, `episode_id`, `group_id`, `group_system`, `asserted_at`, `asserted_by`, `membership_role`, `supersedes_record_id`, `succession_reason`. Same §3-canonicalizer (SHA3-256, `sort_keys=False`) as CEL-001. `membership_role` is INCLUDED (Gap 6): role is content, so a role change requires a new record via succession.
- **Verification Protocol:** Cross-implementation consistency check. Two conforming implementations MUST produce identical bytes for the same input tuple.
- **Failure Condition:** `membership_role` omitted from the preimage (would let a role edit go uncommitted), or `superseded_by_record_id` included (would invalidate a sealed record's hash on later succession).

**MR-002** — Forward-pointer exclusion
- **Class:** REQUIRED
- **Spec Reference:** §20 →10, §20 →11.3.2
- **Description:** `superseded_by_record_id` MUST NOT appear in the `MembershipRecord` preimage. Setting it (when a later record supersedes this one) MUST NOT change this record's `content_hash`.
- **Failure Condition:** A prior record's `content_hash` changes when its `superseded_by_record_id` forward pointer is set during succession.

### 5.2 Succession Chain

**MR-003** — Immutable-with-succession chain integrity
- **Class:** REQUIRED
- **Spec Reference:** §20 →7 (Immutability rule), §20 →11.3.2
- **Description:** `MembershipRecord` is append-only. A successor with `supersedes_record_id` set MUST be rejected unless the prior exists, is not already superseded, and shares the same `episode_id` + `(group_id, group_system)`. On success, `(new)-[:SUPERSEDES]->(prior)` is wired and the prior's `superseded_by_record_id` forward pointer is set. The **active** record for a `(episode_id, group_id, group_system)` tuple is the one with no `superseded_by_record_id`.
- **Failure Condition:** A prior record superseded twice, a cross-group/cross-episode succession accepted, or a prior record deleted/modified in place.

**MR-004** — `MEMBERSHIP_CHAIN` proof
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.2.3
- **Description:** A `MEMBERSHIP_CHAIN` proof MUST re-verify the ordered `content_hash` of each record oldest-first and identify the single active (terminal) record. Any broken link or invalid hash MUST yield `BROKEN_CHAIN` / `INVALID`.

**MR-005** — Membership audit events
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.4
- **Description:** `assert_membership_record()` MUST emit `MEMBERSHIP_RECORD_CREATED` unconditionally, and additionally `MEMBERSHIP_RECORD_SUPERSEDED` on any succession — carrying `old_role` + `new_role` so role-change history is queryable from the audit log alone. The `SUPERSEDED` record MUST chain directly off the `CREATED` record's `record_hash` (both describe one operation).

---

## 6. Grouping Conformance Vectors (§20 →8, Appendix A)

### 6.1 Hash Canonicalization

**CD-001** — `ConformanceDeclaration` hash
- **Class:** REQUIRED
- **Spec Reference:** §20 →8, §20 →10
- **Description:** `compute_conformance_declaration_hash()` canonicalizes, in order (from `_DECLARATION_HASH_PREIMAGE_FIELDS`): `declaration_id`, `group_id`, `group_system`, `declared_at`, `declared_by`, `declaration_version`, `capabilities`. Same §3-canonicalizer. `capabilities` is a `list[Capability]`; each canonicalizes via `model_dump()` (recursively, in list order — `capability_id` + `description`). `superseded_by` is EXCLUDED (forward pointer, §20 →10).
- **Verification Protocol:** Cross-implementation consistency check. Two conforming implementations MUST produce identical bytes for the same input tuple.
- **Failure Condition:** `superseded_by` included, capability ordering not preserved, or field order divergence.

### 6.2 SemVer Governance

**CD-002** — SemVer format enforcement
- **Class:** REQUIRED
- **Spec Reference:** §20 →8 (Gap 7)
- **Description:** `enforce_semver_format()` MUST reject any `declaration_version` that is not a strict `major.minor.patch` non-negative triplet (pre-release / build-metadata suffixes rejected), raising `GroupingGovernanceError`.

**CD-003** — Version-bump classification
- **Class:** REQUIRED
- **Spec Reference:** §20 →8 (version semantics table), Appendix A
- **Description:** `classify_version_bump(old, new)` MUST require `new > old` strictly (raise otherwise) and return `"major"` (major component changed), `"minor"` (minor changed), or `"patch"`. Level-skips (e.g. 1.0.0 → 3.0.0) are accepted as their highest changed component. Major → breaking; minor/patch → compatible.
- **Failure Condition:** A non-increasing version accepted, or a bump misclassified against the §20 →8 table.

**CD-004** — Bump audit-event selection
- **Class:** REQUIRED
- **Spec Reference:** §20 →11.4, §20 →8
- **Description:** `bump_conformance_declaration()` MUST emit `DECLARATION_SUPERSEDED` for a major bump and `DECLARATION_VERSION_BUMPED` for a minor/patch bump, wire `(old)-[:SUPERSEDED_BY]->(new)`, set the prior's `superseded_by` forward pointer, and anchor the audit event to the synthetic chain key `declaration:{group_system}:{group_id}`. Initial `register_conformance_declaration()` MUST NOT fire an audit event (only bumps do).
- **Failure Condition:** A major bump emitting `DECLARATION_VERSION_BUMPED` (or vice versa); an initial registration firing a spurious event; declaration events anchored to an episode chain instead of the synthetic key.

**CD-005** — Breaking-change reference (Appendix A)
- **Class:** RECOMMENDED
- **Spec Reference:** §20 Appendix A
- **Description:** Implementations SHOULD classify as **major** any change that renames/removes/retypes a field appearing in a `content_hash` preimage, or changes the hash algorithm / canonical serialization; as **minor** any new optional field, new `LinkType`, new `AuditEventType`, or new `LinkHealthState`; as **patch** documentation/threshold/editorial changes.

---

## 7. Governance Enforcement Matrix

Cross-Episode Linking & Grouping has **no numbered SPEC G-rules**. Governance is enforced via error taxonomies, the health/quarantine FSM, and succession-chain integrity. This matrix maps each enforcement mechanism to its vector(s).

| Mechanism | Enforcement surface | Vector(s) |
|-----------|---------------------|-----------|
| Link mutual exclusivity | `LinkGovernanceError` (`enforce_link_mutual_exclusivity`) | CEL-005 |
| Endpoint existence | `ValueError` in `write_episode_link_sync` | CEL-006 |
| Quarantine-field hash exclusion | `_HASH_PREIMAGE_FIELDS` (§20 →2) | CEL-002 |
| Link health FSM | Health-state transition rules (§20 →6) | LH-001, LH-002 |
| Per-Episode quarantine queue | Redis key discipline (§20 →11.1.4) | LH-003 |
| Quarantine escalation | `QUARANTINE_ESCALATED` (§20 →11.3.3) | LH-004 |
| Signal recording | Audit-the-decision (§20 →4, →12.2) | SG-001, SG-002, SG-003, SG-004 |
| Membership hash inclusion/exclusion | `_MEMBERSHIP_HASH_PREIMAGE_FIELDS` (§20 →7, →10) | MR-001, MR-002 |
| Membership succession integrity | Chain checks in `write_membership_record_sync` | MR-003, MR-004, MR-005 |
| Declaration forward-pointer exclusion | `_DECLARATION_HASH_PREIMAGE_FIELDS` (§20 →8, →10) | CD-001 |
| SemVer governance | `GroupingGovernanceError` (`enforce_semver_format` / `classify_version_bump`) | CD-002, CD-003, CD-004 |

---

## 8. Conformance Levels

### Level 1: Protocol Conformance (Wire + State tiers)

Implementation passes all **REQUIRED** vectors in sections 2–6 and the governance matrix in section 7. This makes two implementations interoperable — they can exchange `EpisodeLink`, `MembershipRecord`, and `ConformanceDeclaration` structures and verify each other's hashes (wire tier, §20 →12.1), and their audit logs are comparable (state tier). No claim is made about storage layout, embedding model, or scoring algorithm.

### Level 2: Full Conformance

Level 1 plus all **RECOMMENDED** vectors (CEL-007 resumption isolation, CD-005 breaking-change classification) and the storage-architecture obligations of §20 →11.1 / →11.5 (write-order invariant, active-record index, consistency-window SLA).

### Behavioral tier (sovereign — no conformance requirement)

Signal-combination algorithm, embedding-model selection, threshold-calibration strategy, and internal indexing are implementation decisions (§20 →12.1). The protocol requires only that the *decision* is recorded (audit-the-decision, §20 →12.2), which is covered by the `SG-` vectors.

---

## 9. Cross-Reference

- **SPEC.md §20** — normative protocol surface (v3.2.1); internal §1–§12 numbering cited as `§20 →N`.
- **IMPLEMENTATION-CROSS-EPISODE-LINKING.md** — Neo4j reference adapter (non-normative).
- **CONFORMANCE-BFM.md** — sibling BFM vector set (SPEC §19); shares the cross-implementation-consistency vector format.
- **`ariadne/core/hash_canonical.py`** — the shared canonicalizer that every `CEL-`/`MR-`/`CD-` hash vector references.

---

*Ariadne Protocol Cross-Episode Linking & Grouping Conformance Test Vectors are maintained by Scorched Earth Labs.*
*Vector set version: 1.0.0 | Applies to SPEC.md: v3.2.1 §20*
