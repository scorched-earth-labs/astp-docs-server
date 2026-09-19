# ASTP — Cross-Episode Linking & Grouping Implementation Guide

**Version:** 1.1.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md §20 (Cross-Episode Linking & Grouping), 5.1.0 (SPEC §20 as of 5.1.0; see the note in §1)

---

## 1. Purpose and Relationship to SPEC.md

> **SPEC 5.0.0 / 5.1.0 note.** SPEC §20 →2 now defines `EpisodeLink.content_hash` as `EPISODE_LINK:v2:` — binding each end's Episode root when that end was sealed at link creation, the type, exact strength, every inference signal (`LINK_SIGNAL:v2:`) in order and the threshold, with health, quarantine and `created_by` **out** of the preimage (they are lifecycle and provenance, the audit chain's). The 4.x preimage this document describes, which bound `health_state` and the quarantine fields and so changed whenever a link's health did, is retained in SPEC only as the definition of links already written; the `LINK_INTEGRITY` field snapshot is the bound set. The reference writer (`stamp_content_hash` / `write_episode_link_sync`) still stamps the 4.x form as of `astp` 0.3.0; adopting the 5.0.0 form is the next adapter change. `MembershipRecord` and `ConformanceDeclaration` hashes are unchanged. The audit records these operations write are the version 2 audit record of SPEC §8 (`GENESIS` → NULL); `GroupingSystem` reserves only `ariadne_native`.

SPEC §20 defines the protocol surface of **Cross-Episode Linking & Grouping** — how Episodes connect across time (`EpisodeLink`) and how they aggregate into external groupings (`MembershipRecord`, `ConformanceDeclaration`). §20's internal §1–§12 numbering is the original Amendment v2.0 scheme, scoped within §20; this document cites it as `§20 →N` (e.g. `§20 →2`, `§20 →11.1`). SPEC §20 is normative: it fixes the schemas, the hash preimages, the link-type taxonomy, the health/quarantine state machine, and the three-tier conformance boundary. This document describes **how Scorched Earth Labs implemented that surface** against the Neo4j reference adapter. It is not normative: another adapter (Postgres, DynamoDB, a document store) may differ in storage layout while remaining spec-conforming.

What is normative from this file:

- The **content-hash preimage field orders** (§4, §5, §6). These are wire-tier (§20 →12.1) — two conforming implementations MUST produce identical `content_hash` / `declaration_hash` bytes for the same input, so the ordered field list and the canonicalization rules are part of the protocol, not this adapter.
- The **forward-pointer-exclusion discipline**: `quarantine_resolved_at` / `quarantine_resolution` are excluded from the `EpisodeLink` hash; `superseded_by_record_id` / `superseded_by` are excluded from the `MembershipRecord` / `ConformanceDeclaration` hashes (§20 →2, →7, →8, →10).
- The **audit-anchored write rule**: every link/membership/declaration mutation advances a hash-linked `AriadneAuditRecord` chain, or it writes nothing through the operation layer.
- The **write-order invariant** (§20 →11.5.1): authoritative structural store, then append-only audit store — both synchronous — then the semantic search index and the ephemeral coordinator, asynchronously. The roles are normative; which provider fills each is not.

What is implementation-space:

- **The storage providers.** SPEC §20 →11.1 defines four storage roles and deliberately names no product. This adapter's choices are recorded in §9.
- Neo4j labels (`AriadneEpisodeLink`, `AriadneMembershipRecord`, `AriadneConformanceDeclaration`, `AriadneEpisodeGroup`), property names, constraint/index names.
- The compact string encodings of `inference_signals` and `capabilities` stored on the Neo4j node (full structured records live on the audit trail).
- The composite-scoring algorithm, embedding-model choice, and threshold values (all behavioral-tier, sovereign per §20 →12.1).
- The synthetic audit chain key for declaration events (`declaration:{group_system}:{group_id}`).

---

## 2. Module Layout

```
astp/
├── core/
│   ├── cross_episode.py         # EpisodeLink + Signal + LinkType/LinkHealthState/QuarantineResolution
│   │                            #   + hash fn + governance + Part-I operation layer (assert / propose / reject)
│   ├── grouping.py              # MembershipRecord + ConformanceDeclaration + Capability
│   │                            #   + hash fns + SemVer governance + Part-II operation layer (assert / register / bump)
│   ├── audit_chain.py           # Shared next_delta_sequence() / prior_audit_hash() over any chain_key
│   └── hash_canonical.py        # canonical_value() + hash_preimage() — the shared canonicalizer
└── adapters/
    └── neo4j/
        └── writer.py            # write_episode_link_sync / write_membership_record_sync /
                                 #   write_conformance_declaration_sync / supersede_conformance_declaration_sync
                                 #   + SCHEMA_CONSTRAINTS / SCHEMA_INDEXES
tests/unit/protocol/
├── test_cross_episode_linking.py  # EpisodeLink schema, hash, mutual-exclusivity, audit deltas, operation layer
└── test_grouping.py               # MembershipRecord / ConformanceDeclaration schema, hash, SemVer, succession
```

`astp/core/*` is the protocol-level type module — adapter modules import **from** core, never the reverse. The operation-layer functions in `cross_episode.py` / `grouping.py` defer their adapter imports to call time so the type module stays importable in schema-only environments.

---

## 3. The Canonicalizer — Shared Across All §20 Hashes

Unlike the BFM family (SPEC §19), which builds each preimage as a `PREFIX:`-tagged colon-joined string, **every §20 content hash is computed by `hash_preimage(model, ordered_fields)`** in `astp/core/hash_canonical.py`. The mechanism is:

1. For each field name in `ordered_fields` (in order), read the model attribute and pass it through `canonical_value()`.
2. Assemble an ordered `dict` field_name → canonical value.
3. Serialize with `json.dumps(preimage, sort_keys=False, separators=(",", ":"), ensure_ascii=False)`.
4. `sha3_256(serialized.encode("utf-8"))`.

`canonical_value()` normalization (this is wire-tier and MUST match across implementations):

| Python type | Canonical form |
|-------------|----------------|
| `None` | `null` (JSON) |
| `UUID` | `str(uuid)` (hyphenated hex) |
| `datetime` | UTC-normalized ISO 8601 (`astimezone(utc).isoformat()`; naive is assumed UTC) |
| `Enum` | `.value` |
| `bool` | JSON `true`/`false` (checked before `int` — bool is an `int` subclass) |
| `int` | numeric |
| `float` | `repr(value)` — round-trippable, platform-stable string |
| `str` | verbatim |
| `list` | recurse element-wise |
| `BaseModel` | `model_dump()` → recurse (this is how `Signal[]` and `Capability[]` serialize) |
| `dict` | recurse value-wise |
| anything else | `TypeError` — fail loudly, never silently stringify |

Two consequences implementers MUST honor:

- **`sort_keys=False`.** The preimage dict is serialized in the tuple's declared order, not alphabetically. The ordered field tuple *is* the canonical layout.
- **`float → repr`.** `link_strength`, `signal_weight`, `signal_value` etc. are canonicalized via `repr()`, not `%f`. An implementation that emits `"0.75"` where Python emits `"0.75"` matches; one that emits `"0.750000"` diverges. Match Python `repr(float)` semantics for wire conformance.

There is **no domain-prefix string** in any §20 hash. Domain separation is provided by the field set (each node type has a distinct ordered tuple, and `record_id`/`link_id`/`declaration_id` are the first field), not by a `PREFIX:` tag.

---

## 4. Cross-Episode Link — `EpisodeLink`

### 4.1 Public API

```python
from astp.core.cross_episode import (
    EpisodeLink, Signal, LinkType, LinkHealthState, QuarantineResolution,
    assert_episode_link,
    propose_link_candidate, record_candidate_rejection, record_link_rejection,
    RejectionReason,
    compute_episode_link_content_hash, stamp_content_hash,
    enforce_link_mutual_exclusivity, LinkGovernanceError,
)

link = EpisodeLink(
    source_episode=src_uuid,
    target_episode=tgt_uuid,
    created_by="agent-a",
    link_type=LinkType.CONTINUES_FROM,
    link_strength=0.87,
    is_inferred=False,
    inference_signals=[Signal(signal_type=..., signal_weight=..., signal_value=...)],
    inference_threshold=0.75,
    retroactive=False,
)

# Operation-layer entry point — writes the node AND advances the audit chain.
# Faculty / server code MUST call this, NOT write_episode_link_sync directly.
link = assert_episode_link(driver, link, session_id=None, explicit_reason="user reason")
```

Phase-2 discovery emits **audit-only** events (no `EpisodeLink` node created):

```python
audit_id = propose_link_candidate(driver, source_episode=..., target_episode=...,
    proposed_link_type=LinkType.INFORMED_BY, composite_score=0.81,
    inference_signals=[...], discovery_threshold=0.75, auto_accept_threshold=0.90,
    proposing_agent="agent-b")                             # → LINK_PROPOSED (score in [DISCOVERY, AUTO_ACCEPT))

record_candidate_rejection(driver, ..., composite_score=0.62,
    discovery_threshold=0.75, detecting_agent="agent-b")  # → CANDIDATE_REJECTED (score < DISCOVERY)

record_link_rejection(driver, proposed_audit_event_id=audit_id, ...,
    rejecting_agent="human-1", rejection_reason=RejectionReason.NOT_RELATED)  # → LINK_REJECTED
```

### 4.2 Content-Hash Preimage (wire-tier — `compute_episode_link_content_hash`)

Ground truth: `_HASH_PREIMAGE_FIELDS` in `cross_episode.py`. Ordered field list, hashed via §3's canonicalizer:

```
link_id, source_episode, target_episode, created_at, created_by,
link_type, link_strength, is_inferred, inference_signals,
inference_threshold, retroactive, health_state, health_checked_at,
source_version, target_version, quarantine_reason, quarantined_at
```

**Excluded** (per §20 →2 hash-preimage note): `quarantine_resolved_at`, `quarantine_resolution`. These are lifecycle annotations set when a quarantine *exits*; including them would invalidate the hash on every quarantine close. The audit log (§20 →5, →11.4) is authoritative for resolution events; the content hash commits to the link **as asserted**, not **as later resolved**.

Note that mutable health-state fields (`health_state`, `health_checked_at`) **are** in the preimage — so drift detection can be cryptographically tied to the link's anchor state at write time. Re-stamping after a health transition therefore produces a new hash (this is intentional, not a violation of `quarantine_resolved_at` exclusion — the two are distinct concerns). This matches the §20 →11.2.2 `LINK_INTEGRITY` proof field snapshot exactly.

### 4.3 Governance — Mutual Exclusivity (§20 →3)

`enforce_link_mutual_exclusivity(new_type, existing_types_for_pair)` raises `LinkGovernanceError` if the new type collides on the same `(source, target)` pair. There are **no numbered SPEC G-rules** for §20 — governance is the `LinkGovernanceError` taxonomy plus the health-state FSM, not a G-catalog. The exclusion set (from `_MUTUALLY_EXCLUSIVE_LINK_TYPES`):

| Pair | Rule |
|------|------|
| `{CONTINUES_FROM, SUPERSEDES}` | mutually exclusive |
| `{CONTINUES_FROM, BRANCHES_FROM}` | mutually exclusive |

`SUPERSEDES` and `BRANCHES_FROM` are **not** mutually exclusive with each other; all other link types compose freely. The caller must scope `existing_types_for_pair` to the same `(source, target)` pair — the adapter does this by querying existing `LINKED_TO` edges before the write.

### 4.4 Writes per `assert_episode_link()`

1. `write_episode_link_sync(driver, link)` — validates both endpoints exist as `AriadneEpisode`, runs mutual-exclusivity against existing `LINKED_TO` edges, stamps `content_hash` if absent, then `CREATE (:AriadneEpisodeLink {...})` + `MERGE (s)-[:LINKED_TO {via: link_id}]->(t)`.
2. Build a `LinkAcceptedDelta` (forward + `reverse_delete_link_id`).
3. `next_delta_sequence` + `prior_audit_hash` on the **source episode** chain (the episode asserting the relationship owns the audit entry).
4. `AuditRecord(delta_type=LINK_ACCEPTED, ...)`, `record_hash = compute_audit_record_hash(...)`, `write_audit_record_sync`.

Phase 1 treats every successful assertion as `LINK_ACCEPTED` with `trigger_context=HUMAN_EXPLICIT`. Phase 2's discovery sweep switches to `AGENT_DETECTED` via `propose_link_candidate`. The discovery events (`LINK_PROPOSED`, `CANDIDATE_REJECTED`, `LINK_REJECTED`) are **append-only** and carry the full signal breakdown + threshold values in effect (the audit-the-decision pattern, §20 →12.2) so post-hoc threshold calibration needs no model re-run.

### 4.5 Link Health & Quarantine FSM (§20 →6, →11.3.1)

The health state is the governance surface (there is no G-number). States: `VALID`, `STALE`, `FROZEN`, `BROKEN`, `QUARANTINED`. Transitions (from §20 →6):

```
VALID       → STALE | FROZEN | BROKEN | QUARANTINED
STALE       → BROKEN | QUARANTINED
QUARANTINED → VALID   (resolution CONFIRMED)
QUARANTINED → BROKEN  (resolution DISSOLVED)
QUARANTINED → ESCALATED (TTL exceeded — §20 →11.3.3; remains QUARANTINED, human review required)
BROKEN      → QUARANTINED (re-evaluation)
```

There is **no automatic** `QUARANTINED → BROKEN`: exit from quarantine requires an explicit `QuarantineResolution` (`CONFIRMED` / `DISSOLVED` / `ESCALATED`). A major-version advance of the target routes to human review and does **not** auto-transition to `BROKEN`. The quarantine queue is keyed **per-Episode** (`ariadne:quarantine:queue:{episode_id}`) — a global queue is non-conforming (§20 →11.1.4). Resolution sets `quarantine_resolved_at` + `quarantine_resolution` (both hash-excluded) and emits `LINK_QUARANTINE_RESOLVED`; TTL breach emits `QUARANTINE_ESCALATED`.

---

## 5. Episode Grouping — `MembershipRecord`

### 5.1 Public API

```python
from astp.core.grouping import (
    MembershipRecord, MembershipRole, GroupingSystem,
    assert_membership_record,
    compute_membership_record_content_hash, stamp_membership_record_hash,
)

record = MembershipRecord(
    episode_id=ep_uuid, group_id="col-42", group_system="sel-thermyt:Collection",
    asserted_by="agent-c", membership_role=MembershipRole.PRIMARY,
    supersedes_record_id=None, succession_reason=None,
)
record = assert_membership_record(driver, record, explicit_reason="...")
```

### 5.2 Content-Hash Preimage (wire-tier — `compute_membership_record_content_hash`)

Ground truth: `_MEMBERSHIP_HASH_PREIMAGE_FIELDS` in `grouping.py`. Ordered field list:

```
record_id, episode_id, group_id, group_system, asserted_at,
asserted_by, membership_role, supersedes_record_id, succession_reason
```

**Included** per §20 →7: `membership_role` — role is a content characterization, so a role change requires a **new** record via succession, not an in-place edit. `supersedes_record_id` is included as the record's commitment to its predecessor in the chain. **Excluded** per §20 →10 (forward-pointer exclusion): `superseded_by_record_id` — it is set by a *later* succession and would invalidate a sealed record's hash.

> Note: SPEC §20 →7's prose enumerates a shorter set (`record_id + episode_id + group_id + group_system + asserted_at + asserted_by + membership_role`). The implementation additionally binds `supersedes_record_id` and `succession_reason` so the record cryptographically commits to *which* predecessor it supersedes and *why*. This is the ground-truth preimage; see flagged discrepancy in §10.

### 5.3 Immutable-with-Succession Lifecycle (§20 →11.3.2)

`MembershipRecord` nodes are append-only. Role/state changes create a new record with `supersedes_record_id` → prior; the writer sets the prior's `superseded_by_record_id` forward pointer and wires `(new)-[:SUPERSEDES]->(prior)`. The **active** record for an `(episode_id, group_id, group_system)` tuple is the one with no `superseded_by_record_id`. Succession is irreversible; prior records are never deleted. Chain-integrity is enforced at write time: the prior must exist, must not already be superseded, and must share the same episode + `(group_id, group_system)`.

### 5.4 Writes per `assert_membership_record()`

1. `write_membership_record_sync` — episode-exists check, hash stamp, succession-integrity check, `CREATE (:AriadneMembershipRecord {...})`, `MERGE (e)-[:MEMBER_OF {via: record_id}]->(:AriadneEpisodeGroup)` (group node stub-merged — the grouping itself may live outside Ariadne), and on succession `MERGE (new)-[:SUPERSEDES]->(prior)` + set prior forward pointer.
2. `MEMBERSHIP_RECORD_CREATED` audit (always) on the episode chain.
3. On succession only: `MEMBERSHIP_RECORD_SUPERSEDED` audit, chained directly off the just-written `CREATED` record's `record_hash`, carrying `old_role` (fetched from the prior node) + `new_role` so role-change history is queryable from the audit log alone.

---

## 6. Grouping Conformance — `ConformanceDeclaration`

### 6.1 Public API

```python
from astp.core.grouping import (
    ConformanceDeclaration, Capability,
    register_conformance_declaration, bump_conformance_declaration,
    enforce_semver_format, classify_version_bump,
    compute_conformance_declaration_hash, stamp_conformance_declaration_hash,
    GroupingGovernanceError,
)

decl = ConformanceDeclaration(
    group_id="col-42", group_system="sel-thermyt:Collection", declared_by="agent-d",
    declaration_version="1.0.0",
    capabilities=[Capability(capability_id="supports_archival")],
)
register_conformance_declaration(driver, decl)          # initial — no audit event (§20 →11.4)

new_decl, bump_kind = bump_conformance_declaration(
    driver, new_declaration=decl_v2, prior_declaration_id=str(decl.declaration_id),
    prior_version="1.0.0")                                # → DECLARATION_VERSION_BUMPED | DECLARATION_SUPERSEDED
```

### 6.2 Content-Hash Preimage (wire-tier — `compute_conformance_declaration_hash`)

Ground truth: `_DECLARATION_HASH_PREIMAGE_FIELDS` in `grouping.py`. Ordered field list:

```
declaration_id, group_id, group_system, declared_at, declared_by,
declaration_version, capabilities
```

**Excluded** per §20 →10: `superseded_by` (forward pointer). `capabilities` is a `list[Capability]`; each `Capability` canonicalizes via `model_dump()` → recurse (§3), so the preimage includes `capability_id` + `description` per capability, in list order.

### 6.3 SemVer Governance (§20 →8, Appendix A)

`enforce_semver_format(version)` parses a strict `major.minor.patch` triplet (pre-release / build-metadata suffixes rejected) → `GroupingGovernanceError` on failure. `classify_version_bump(old, new)` returns `"major"` / `"minor"` / `"patch"`, requiring `new > old` strictly (raises otherwise); level-skips are accepted (real histories skip). The bump kind selects the audit event:

| Bump | Event | Effect |
|------|-------|--------|
| major | `DECLARATION_SUPERSEDED` | breaking — existing `MembershipRecord`s retain reference to the prior version |
| minor / patch | `DECLARATION_VERSION_BUMPED` | compatible — existing records remain valid against either version |

Declaration audit events anchor to a **synthetic chain key** `declaration:{group_system}:{group_id}` (declarations have no natural episode home) — same chain machinery, different namespace. Initial registration fires **no** audit event; only bumps do (§20 →11.4).

---

## 7. Audit-Chain Substrate

All §20 operation-layer functions advance a tamper-evident audit chain via `astp/core/audit_chain.py`:

- `next_delta_sequence(driver, chain_key)` → next monotonic per-chain sequence (1 for empty; per §20 →11.5.3 sequences are within-Episode completeness proof, never cross-Episode ordering).
- `prior_audit_hash(driver, chain_key)` → hash of the most recent record on the chain (the 4.x helpers return the text `"GENESIS"` for an empty chain; a version 2 audit record carries NULL).

Since astp 0.3.0 both **raise** `AdapterWriteError` on a store failure rather than falling through to a default: a writer that cannot read the chain head must not guess a sequence or a prior hash (SPEC §8.2), because a guessed GENESIS mid-chain forges a chain restart. The operation that needed the record fails; the host decides whether to retry.

`AuditRecord.record_hash` is computed by `compute_audit_record_hash(audit_id, delta_sequence, delta_type, agent_id, wall_clock_time.isoformat(), json.dumps(forward_delta, default=str, sort_keys=True), prior_audit_hash)` — note the forward-delta serialization here uses `sort_keys=True` (audit-chain convention), distinct from the `sort_keys=False` content-hash canonicalizer of §3.

---

## 8. Neo4j Schema Additions Summary

### 8.1 Node Labels & Constraints

| Label | Unique constraint on |
|-------|----------------------|
| `AriadneEpisodeLink` | `link_id` |
| `AriadneMembershipRecord` | `record_id` |
| `AriadneConformanceDeclaration` | `declaration_id` |
| `AriadneEpisodeGroup` | (stub node, merged on `{group_id, group_system}`) |

### 8.2 Indexes

`AriadneEpisodeLink` on `health_state`, `source_episode`, `target_episode`.
`AriadneMembershipRecord` on `episode_id`, `group_id`, `group_system`.
`AriadneConformanceDeclaration` on `group_system`, `group_id`.
Full list in `adapters/neo4j/writer.py` `SCHEMA_CONSTRAINTS` / `SCHEMA_INDEXES`.

### 8.3 Edge Types

| Edge | Shape |
|------|-------|
| `LINKED_TO {via: link_id}` | `(:AriadneEpisode)→(:AriadneEpisode)` |
| `MEMBER_OF {via: record_id}` | `(:AriadneEpisode)→(:AriadneEpisodeGroup)` |
| `SUPERSEDES` | `(new:AriadneMembershipRecord)→(prior)` |
| `SUPERSEDED_BY` | `(old:AriadneConformanceDeclaration)→(new)` |

### 8.4 Compact Property Encodings (implementation-space)

`inference_signals` and `capabilities` are stored on the Neo4j node as string lists (Neo4j property graph does not store nested maps cleanly). The full structured records live on the audit trail and are hashed from the Pydantic models, **not** from these compact strings — so the compact form is a display/index convenience, not the integrity source.

---

## 9. Storage Architecture & Write-Order Invariant (§20 →11.1, →11.5)

SPEC §20 →11.1 defines four storage **roles** and the obligations of each. It names no provider: any system that meets a role's obligations may fill it, and one system may fill several. The table maps those roles to what the reference deployment uses. The right-hand column is this deployment's choice and carries no conformance weight.

| Role (normative, §20 →11.1.1) | Obligation | Reference deployment |
|------|------|------|
| Authoritative structural store | structural ground truth; synchronous writes; single source of truth | Neo4j |
| Append-only audit store | authoritative event log; synchronous writes; never modified | blob storage |
| Semantic search index | link-candidate discovery; eventually consistent; derived | QDrant |
| Ephemeral coordinator | caches and queues; always reconstructable | Redis |

**Write-order invariant (§20 →11.5.1): structural store → audit store → search index → coordinator.** `assert_episode_link()` writes the link record and then the audit record, in that order. The first two writes are atomic from the protocol's perspective — a write that lands in the structural store but fails in the audit store is a partial write and MUST be retried or rolled back. Propagation to the search index and the coordinator is asynchronous within the consistency-window SLA (typical < 60s, max 5 minutes; §20 →11.5.2). No read on structural data may serve a response that contradicts the structural store; divergence of the index or the coordinator is a consistency error, not an alternative view.

### 9.1 Reference deployment — search index layout

§20 →11.1.3 requires two separate vector spaces and fixes their payload fields. Collection names, dimensionality, distance metric and embedding model are this deployment's choices:

| Vector space (§20 →11.1.3) | Collection | Dimensions | Distance |
|------|------|------|------|
| Episode content | `episode_content_vectors` | 1536 | Cosine |
| Participant context | `participant_context_vectors` | 768 | Cosine |

Payload fields are as the specification lists them, stored as keyword fields except `indexed_at` (datetime) and the two `*_threshold_at_index` fields (float). The two collections use different embedding models of different sizes; embeddings from different model families are never mixed within a collection, which is the one constraint §20 →11.1.3 places on model choice.

### 9.2 Reference deployment — coordinator keys

§20 →11.1.4 requires a quarantine queue scoped per Episode, threshold calibration state, and a link-health cache, all reconstructable. Key names and data structures are this deployment's choices:

```
ariadne:quarantine:queue:{episode_id}    sorted set   score = quarantine deadline (Unix timestamp)
ariadne:quarantine:ttl                   string       default TTL in seconds
ariadne:calibration:thresholds           hash         current DISCOVERY_THRESHOLD, AUTO_ACCEPT_THRESHOLD
ariadne:calibration:history:{date}       list         daily calibration snapshots
ariadne:link:health:{link_id}            hash         cached health_state + checked_at
```

Verification proof types (§20 →11.2): `LINK_INTEGRITY` (content_hash matches canonical fields — the §4.2 field set), `MEMBERSHIP_CHAIN` (succession chain unbroken + hashes valid), `DECLARATION_COMPATIBILITY` (version transition compatible/breaking), `AUDIT_COMPLETENESS` (all required audit events present). Non-existence proofs are a flagged gap (§20 →11.2.1, →12.3).

---

## 10. Forward Compatibility & Deferred Items

Deliberate scope limits, forward-compatible with future amendment (§20 →12.3):

1. **Non-existence proofs.** Proof that *no* `EpisodeLink` exists between two Episodes needs additional Merkle commitments not introduced here (§20 →11.2.1). Deferred.
2. **Per-Episode encryption key derivation.** `MembershipRecord` content is required to be encrypted at rest with a per-Episode key, but the key-derivation mechanism is aspirational pending a future amendment (§20 →11.2.7). The requirement stands; the mechanism is deferred.
3. **Behavioral-tier calibration protocol.** Threshold tuning (`DISCOVERY_THRESHOLD` = 0.75, `AUTO_ACCEPT_THRESHOLD` = 0.90) is sovereign (§20 →12.1). The audit-the-decision events already record threshold values at inference time; a cross-implementation calibration-reporting standard is a future non-required item.
4. **Compact vs. structured signal storage.** The Neo4j node's compact `inference_signals` / `capabilities` strings are lossy relative to the audit-trail structured records. A future adapter with native nested-map support may store the full structure on the node without protocol impact — the hash is computed from the model, so wire conformance is unaffected.

---

*Developed by Scorched Earth Labs. See SPEC.md §20 for the normative protocol surface.*
