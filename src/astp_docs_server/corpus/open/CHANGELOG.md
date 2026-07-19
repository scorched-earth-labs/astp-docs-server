# Changelog

All notable changes to the Ariadne protocol. Version numbering follows [VERSIONING.md](./VERSIONING.md).

## [Unreleased]

The next change-set queues here.

### Clarified (errata — PATCH)
- **Segment parentage vs. proof-chain parentage.** New §3.4.1 states explicitly that a Segment's `parent_node_id` is its **`EpisodeNode`** (an upward anchor), that segments order by `sequence_index` with no segment→segment edge, and that the canonical materialization is an ordered `(Episode)-[:CONTAINS {sequence_index}]->(Segment)` fan-out (derive next/prev at read time, don't persist a chain). A reciprocal note at §16.5.3 distinguishes this from the proof-chain rule `B.parent_node_id == A.node_id`, which links whole nodes causally (e.g. episode→episode). **No canonical-form change** — this clarifies existing semantics (G-2 reparenting prohibition; §5.2 leaf-hash preimage). Surfaced by a reference-implementation question ([ariadne-samples #1](https://github.com/scorched-earth-labs/ariadne-samples/issues/1)): an adapter graph showed a segment→segment containment chain instead of the canonical episode→segment fan-out.

## [3.3.0] — 2026-07-05

**MINOR.** Departure-fork orphan recovery (SPEC §19.3.7). Additive on top of v3.2.x — no breaking changes; every v3.2.x-conformant implementation remains conformant. The runtime enforcement layer for the §19.3.5 producer invariants: it catches partial-failure states the producers couldn't prevent (a crash between the two writes, a rolled-back status).

### Added
- **`ForkOrphanMarker`** — a non-chained diagnostic satellite recording a detection event. Self-hashed (domain `FORK_ORPHAN_MARKER:`) for tamper-evidence, but NOT a member of the origin spine's Merkle chain (no `parent_hash`; writing it never alters the origin episode's root/tip). Read-only after write; deduplicated one-per-orphaned-fork (keyed on `fork_id`); excluded from departure-registry queries. New `OrphanClass` enum (`CLASS_A..D`).
- **Four orphan classes** — A (dangling `DepartureForkPointNode`, no episode), B (unanchored fork episode, no point), C (`ForkReturnNode` present but fork not `COMPLETED`), D (stale `ACTIVE` fork).
- **The one permitted retroactive spine write** (Class B) — `write_retroactive_departure_fork_point_sync` appends the missing `DepartureForkPointNode` using the fork episode's stored `fork_origin_spine_tip_hash` as the point's `spine_tip_hash_at_departure` (cross-verify holds by construction), gated by a hash-consistency check (escalate, don't write, on mismatch). Byte-identical to an on-time write; `retroactive`/`orphan_recovery_timestamp` are diagnostic metadata outside the hash preimage. Mirrors RETROACTIVE branch declaration.
- **Recovery write-primitives** (protocol exposes the writes; the consumer orchestrates detection): `write_fork_orphan_marker_sync`, `mark_departure_fork_point_orphaned_sync` (Class A), `write_retroactive_departure_fork_point_sync` + `mark_fork_episode_unanchored_sync` (Class B), `correct_fork_status_by_orphan_recovery_sync` (Class C).
- **New diagnostic fields** — on `DepartureForkPointNode`: `orphaned`, `retroactive`, `orphan_recovery_timestamp`; on the fork `EpisodeNode`: `fork_orphaned`, `fork_orphan_class` (`UNANCHORED`), `status_corrected_by_orphan_recovery`, `status_corrected_at`. New `ForkOrphanClass` enum. None participate in any content hash.

### Not normative
- **Detection cadence.** Whether/how often an implementation scans for orphans is operational hygiene, not protocol conformance. Only the shape of a conformant *recovery* (the node, the field mutations, the retroactive-write discipline) is normative.

### Tests
`test_phase2_operations.py` — `TestForkOrphanRecovery` (6): marker hash determinism + satellite (no `parent_hash`), dedup-on-`fork_id`, Class-A append-only flag, Class-B retroactive append (backdated anchor + byte-identical hash), Class-B unanchored, Class-C status correction. Full protocol suite: **309 passing**.

## [3.2.2] — 2026-07-04

**PATCH.** Prose errata — the §20/§21 hash-preimage descriptions were reconciled to the reference implementation. **No canonical-form change; the code was already correct** — only the SPEC prose was wrong, so every v3.2.1-conformant implementation remains conformant unchanged. Surfaced while authoring the §20/§21 implementation & conformance companion docs.

### Corrected (errata)
- **§20 hash algorithm.** `EpisodeLink.content_hash`, `MembershipRecord.content_hash`, and `ConformanceDeclaration.declaration_hash` are computed with **SHA3-256**, not SHA-256 — consistent with the §5 "all hashing uses SHA3-256, no exceptions" commitment and the `hash_canonical.py` implementation. The prose said "SHA-256".
- **§20 MembershipRecord preimage.** The preimage binds `supersedes_record_id` and `succession_reason` in addition to the seven fields the prose listed (per `_MEMBERSHIP_HASH_PREIMAGE_FIELDS`).
- **§20 EpisodeLink exclusions.** The preimage **includes** `health_state` and `health_checked_at`; it excludes only `quarantine_resolved_at` and `quarantine_resolution` (set after the hash, on quarantine exit). The prose had the exclusion list inverted.
- **§21 Form-B attribution.** The Ignis reference implementation serializes in declared field order and hashes with SHA3-256 — not key-sorted JSON with SHA-256. §21 §8 still leaves the Layer-3 byte-form implementation-open; this only corrects the description of what the reference implementation does.

## [3.2.1] — 2026-07-04

**PATCH.** SPEC integration pass — editorial only, no normative change. The full protocol surface now lives in the SPEC body; the two standalone amendment documents are retired to provenance-only historical references.

### Changed (editorial)
- **Cross-episode linking + grouping** folded into SPEC **§20** (was `AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`, canonical SPEC v3.0.0).
- **Layer 3 Workflow & Execution DAG** folded into SPEC **§21** (was `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`, canonical SPEC v3.1.0). References section moved to §22.
- The amendment's CIA conformance rule was renumbered from its authoring numeral **G-19** (which collided with the BFM Taxonomy's G-19) to **G-36**, keeping the governance-rule namespace contiguous (G-1…G-36).
- Status line + §18 Version History updated; the amendment files carry historical-reference banners pointing at their in-body sections.

### Notes
- No hash preimage, serialization, or required-field changes. Every v3.2.0-conformant implementation is v3.2.1-conformant unchanged.

## [3.2.0] — 2026-07-04

**MINOR.** Phase D departure-fork lifecycle. Additive on top of v3.1.0 — no breaking changes. Defined in the SPEC body (§19.3.5–19.3.6), not as a standalone amendment.

### Added
- **`create_departure_fork()`** — a single **directional departure**: one topic diverges into a new Episode while the originating Episode *continues*. Distinct from the speculative `create_fork()` (N siblings, resolve→promote/discard). Atomic: fork Episode (ACTIVE + immutable provenance) + `DepartureForkPointNode` on the origin spine (`FORK_ORIGIN`) + `DEPARTURE_FORK_CREATED` audit.
- **Lifecycle FSM** — `ACTIVE → COMPLETED | ABANDONED`. `complete_departure_fork()` (fork's own agent), `abandon_departure_fork()` (origin agent / system stub-cleanup). Resumption (re-entering the origin while the fork stays ACTIVE) is a non-event.
- **`declare_fork_return()`** — a **declarative** return (origin asserts incorporation across two independent spines; never the branch's structural merge). Writes `ForkReturnNode` on the origin spine + `FORK_RETURN`/`RETURNED_FROM` edges + `DEPARTURE_FORK_RETURNED` audit. `return_type ∈ {INCORPORATED, ACKNOWLEDGED, SUPERSEDED}`.
- **New nodes/domains** — `DepartureForkPointNode` (`DEPARTURE_FORK_POINT:`), `ForkReturnNode` (`FORK_RETURN:`). **New deltas** — `DEPARTURE_FORK_CREATED` / `_COMPLETED` / `_ABANDONED` / `_RETURNED`. **New edges** — `FORK_RETURN`, `RETURNED_FROM`. **Immutable Episode fork provenance** fields (§19.3.6).
- **Governance G-30 through G-35** — the backdating integrity invariant (G-30: `spine_tip_hash_at_departure` == the fork Episode's `fork_origin_spine_tip_hash`), non-empty objective, trigger whitelist, `AGENT_ESCALATION` requires a trigger segment, return-requires-COMPLETED, one-return-per-fork.

### Tests
`test_phase2_operations.py` — `TestCreateDepartureFork`, `TestDepartureForkFSM`. Full protocol suite: 298 passing.

## [3.1.0] — 2026-06-07

**MINOR.** Layer 3 Workflow & Execution DAG codification. Additive on top of v3.0.0.

### Added
- **Layer 3 — Workflow & Execution DAG.** Source: `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md` (amendment file retains its authoring numeral; canonical SPEC version per `VERSIONING.md` is v3.1.0).
- New node types: `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation`. Pydantic implementation in `ariadne/core/workflow_execution.py`.
- Three-Merkle-layer model formally specified in SPEC §3.4 Persistence Layer Model — Layer 1 Spine, Layer 2 episode content, Layer 3 Workflow & Execution DAG.
- New `CognitiveDeltaType` variants in `branching.py` for Layer 3 delta records.
- **Cognitive Implementation Authority (CIA)** — sole-writer pattern per workspace; wire-tier conformance principle. Only the designated CIA may write each Layer 3 node type.
- 40 new unit tests across the protocol suite.

### Invariants
- **Layer 3 is cryptographically isolated from Spine integrity.** Layer 3 nodes reference Layers 1/2 by ID only; they MUST NOT participate in Spine hash computation. No future Layer-3 change can retroactively force a MAJOR bump on Spine grounds — structural separation is the guarantee.
- `ExecutionNode` and `SkillInvocationNode` are immutable after creation. The only mutable Layer 3 field is `WorkflowDeclaration.status` (and `status_updated_at`).
- Hash byte-form left open at protocol layer per amendment §3 — each conformant implementation may choose its serialization, provided the canonical form is consistent within that implementation.

### Notes
- Layer 3 is the formal protocol surface for the autonomous-process audit trail; downstream consumers writing here include the Ignis Delegation Runner.
- The amendment was previously held on a private branch under the Chinese Wall agreement; the wall was lifted 2026-06-07 and the surface is now public.

## [3.0.0] — 2026-06-07

**MAJOR.** Cross-episode linking + grouping interface. Breaking hash preimage changes on three node types.

### Added
- **Cross-episode linking (Phase 1).** Source: `AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md` (amendment file retains its authoring numeral; canonical SPEC version per `VERSIONING.md` is v3.0.0).
- `EpisodeLink` schema with `LinkType`, `LinkHealthState`, `Signal`/`SignalType` machinery, and `QuarantineResolution`. Neo4j adapter for cross-episode link reads/writes.
- `LINK_*` audit events + `assert_episode_link` operation. `LinkAcceptedDelta` for delta-record stream.
- `LinkGovernanceError` taxonomy for governance-layer failures.
- **Cross-episode discovery (Phase 2).** Link-proposal primitives + calibration loop for adapter-side discovery against existing episode corpora.
- **Grouping (Phase 1).** `MembershipRecord` as protocol-owned grouping artifact. `ConformanceDeclaration` for downstream conformance assertions. Succession-chain governance for both. Adapter-level grouping support.
- **Audit-the-decision pattern** for behavioral-tier implementation choices (SPEC §12 framing).
- **Three-tier conformance taxonomy** — wire / state / behavioral — formalized in the amendment.
- Shared core modules: `audit_chain.py`, `hash_canonical.py`, `constants.py` (refactor lifted duplicated helpers).

### Breaking changes (canonical form)
- Hash preimage changes on `EpisodeLink`, `MembershipRecord`, `ConformanceDeclaration`. Existing v2.x implementations are not wire-conformant against v3.0. See amendment Appendix A for the per-node breaking-change reference.

### Notes
- The amendment was previously held on a private branch under the Chinese Wall agreement; the wall was lifted 2026-06-07 and the surface is now public.
- v2.5.0-draft was never finalized as v2.5.0 — main moved directly to the v3.x line. v2.5.x is therefore not a maintenance line going forward; new work targets v3.x.

## [2.5.0-draft] — 2026-04-21

Working Draft. Phase 1-3 (node system) + Phase 4 (HITL) implemented; Branch/Fork/Merge Taxonomy §19 Phases 1-4 implemented.

### Added
- **Branch/Fork/Merge Taxonomy** — formal taxonomy of episode branching, forking, and merging events. SPEC §19. Includes prescriptive enforcement, resolution primitives (fork, merge, conflict surface), social/internal primitives (aside, soliloquy), and coherence-fingerprint write intercepts.
- `CONFORMANCE-BFM.md` — conformance vectors for the BFM Taxonomy.
- `IMPLEMENTATION-BFM.md` — implementation guide for BFM Taxonomy.
- `list_episodes_for_user` query.

## [2.4.0-draft] — 2026-04-16

### Added
- **HITL Protocol Amendment** — Phase 1 through Phase 4. Human-in-the-loop decision gates as first-class protocol nodes.
  - `HITLEventNode` — two-phase lifecycle (INVOKED → RESOLVED / TIMED_OUT). Participates in the Merkle spine as a causal anchor.
  - `PENDING_HITL` crystallization guard — blocks sealing during active human review.
  - Two-layer Ed25519 cryptographic attestation.
  - HITL Merkle spine participation and advisory gates.
- Implementation Guide updates to incorporate HITL guidance.

## [2.3.0] — 2026-04-12

### Added
- **Phase 3 trust infrastructure** — keys, anchoring, witnesses, chain proofs.
- **Protocol Boundary** documentation — clarifies what is normative protocol vs. implementation latitude.

## [2.2.0] — 2026-04-12

### Added
- **Phase 2 observability** — retrieval audit, `signal_versions_read` segment metadata.
- Caching and rebalance events.

## [2.1.0] — 2026-04-10

### Added
- **Retrieval coordination protocol** — the cross-agent retrieval surface.

## [2.0.0] — 2026-04 (pre-changelog history, inferred from `SPEC.md` introduction)

### Changed (BREAKING)
- **Protocol primitive becomes `CognitiveNode`, not `Episode`.** Episodes are the first *parameterization* of the protocol, not a precondition of it. Future node types (signals, agents, artifacts) slot into the same framework with zero protocol-layer changes.
- **Dual Index invariant**: `sequence_index` (immutable temporal position, hash-included) vs. `tree_leaf_index` (mutable structural position, hash-excluded). The epistemological core of the v2 line.

## [0.1.0-draft] — 2026-04-08

Original spec. Episode-centric model. Retained as `SPEC-v1.md` for historical reference; superseded by the v2.x line.
