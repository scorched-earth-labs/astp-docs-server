# Glossary of Terms

**Version:** none of its own — versioned with [`SPEC.md`](./SPEC.md); reconciled with SPEC 5.1.0
**Status:** Current
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** `SPEC.md`, the `CONFORMANCE*.md` and `IMPLEMENTATION-*.md` documents, and the `astp` Python package

---

A single-source definition for every term used normatively in `SPEC.md`, the companion documents, and the `astp` package. Definitions are grouped to follow the specification's own order; an alphabetical index sits at the bottom for lookup. Where this glossary and `SPEC.md` disagree, `SPEC.md` governs — and the disagreement is a documentation defect worth raising. A term used in code or in the specification that is not defined here is a gap worth raising too.

**Currency.** Reconciled in full with SPEC 5.1.0 on 2026-09-19: the 5.0.0 constructions (canonical field encoding, `hash_version` 2, `spine_algorithm_version` 2, the structural manifest, the version-2 audit record, witness and anchor commitments), the 5.1.0 adapter failure contract, and every term the 3.x and 4.x lines introduced — cross-episode linking and grouping (§20), the Layer 3 Workflow & Execution DAG (§21), departure forks and orphan recovery, ledgered operations, attachments and codicils. Retained 4.x constructions are defined as what they are: the definitions of the versions that produced existing seals.

---

## Reading this glossary

Several ASTP terms have a **structural relationship** that is easy to miss reading the SPEC linearly. Where present, that relationship is stated in the definition. The most important one:

> **`EpisodeNode`, `SegmentNode`, `SignalNode`, `HITLEventNode`, `ConsultationNode`, `CrystallizationDeltaNode`** are *colloquial names* for `CognitiveNode` instances with type-specific `NodePayload` subclasses. They are not separate classes parallel to `CognitiveNode` — they are parameterizations of it. See *CognitiveNode* and *NodePayload*.

The `astp/core/schema.py` classes of the same names are the Episode-era models the reference adapter stores; new implementations target the `astp/protocol/` surface (`CognitiveNode`, `NodePayload`). SPEC §4 is the canonical model.

---

## 1. Core Types — the universal protocol primitives

### CognitiveNode

**The universal protocol primitive.** Every node in the cognitive record — episodes, segments, signals, consultations, HITL events, crystallization deltas — is a `CognitiveNode` with a type-specific payload. The protocol layer operates on `CognitiveNode` exclusively and never inspects payload internals; that abstraction is what keeps the protocol layer node-generic.

Key fields:
- `node_id` (UUID) — stable identity; from 5.0.0, MUST carry at least 122 bits of randomness (SPEC §5.2)
- `node_type` (string) — discriminates the payload kind (`"episode"`, `"segment"`, `"signal"`, …)
- `schema_version` (string) — version of the node-type schema
- `sequence_index` (int) — immutable cognitive-timeline position; **in** the leaf-hash preimage
- `tree_leaf_index` (int) — mutable physical Merkle position; **not in** any preimage (see *Dual Index*)
- `content_hash` (string) — SHA3-256 of the payload via `payload.to_content_hash_input()`
- `parent_node_id` (UUID, optional) — graph position; immutable once set (see *Reparenting Prohibition*)
- `leaf_hash` (string) — computed once at creation, never recomputed (see *`leaf_hash`*)
- `hash_version` (int) — which leaf-hash construction produced it (see *Version Identifiers*)
- `sealed_at` (datetime, optional) — non-null means frozen (G-1); requires a bound crystallization record (G-40)
- `payload` (serialized dict) — the type-specific data; the protocol never reads its fields

Defined in `astp/protocol/node.py`. SPEC §4.1.

### NodePayload

**The abstract interface for node-type-specific data.** Each node type implements `NodePayload` with `validate()` (payload invariants), `to_content_hash_input()` (the canonical bytes hashed into `content_hash`; deterministic) and `to_dict()` (storage form). This boundary lets new node types enter the protocol without protocol-layer changes. `astp/protocol/node.py`; SPEC §4.3.

### CognitiveEdge

A typed, directed edge between cognitive nodes (`CONTAINS`, `PRECEDES`, `REFERENCES`, …), typed by both the edge and the nodes it connects. `astp/protocol/node.py`; SPEC §4.2.

### Namespace Firewall

The architectural invariant that `astp.protocol.*` imports nothing from `astp.nodes.*`, `astp.core.*` or `astp.adapters.*`. Enforced by `tests/unit/protocol/test_namespace_firewall.py`; a failure is a protocol-layer leak, not a style issue. It is what keeps the protocol layer node-generic. SPEC §3.2, G-6.

---

## 2. Node Types — parameterizations of CognitiveNode

Each of the following is a **`CognitiveNode` with `node_type=<type>` and a type-specific `NodePayload`**, not a separate top-level class.

### EpisodeNode

`node_type="episode"`, `EpisodePayload` (title, context note, type, mode, workspace, participants). An **Episode** is a bounded unit of agent work — the first node type the protocol supports and the entry point for most cognitive activity. It has a formal lifecycle (§6 below), a seal (§5), and, from 5.0.0, an identifier that MUST be a UUID at creation (G-40). `astp/nodes/episode/`; SPEC §4.4.

### SegmentNode

`node_type="segment"`, `SegmentPayload`. A **Segment** is an ordered, immutable content unit within an Episode, carrying a `content_hash` and a `content_ref` (a pointer to the bytes in durable storage). Its parent is its Episode; Segments order by `sequence_index`, never by a parent chain. Segment kinds: `CONVERSATION`, `REASONING`, `ARTIFACT`, `ANNOTATION`. Its *retention tier* decides whether it is a spine leaf: `PERSISTENT` and `STRUCTURAL` Segments are leaves; `EPHEMERAL` Segments (PASS decisions, evaluation metadata) are not, and commit through the *Exclusion Set*. SPEC §4, §5.6.

### SignalNode

`node_type="signal"`, `SignalPayload`. A **Signal** is a state observation, alert or annotation attached to an Episode — cross-episode linkage, not spine content. A SPINE-placed Signal commits through the *Signal Manifest*; it is never a spine leaf. A Segment may record the Signal versions it read (`signal_versions_read`, side-channel metadata outside every hash). SPEC §4.5, §5.7.

### ConsultationNode

A **cross-agent exchange** recorded as a first-class node, with its own hash chain of `ExchangeEntry` nodes anchored at a point in the Episode. The branch point is recorded before any exchange (G-8); resolution requires at least one entry (G-9). SPEC §4.

### ExchangeEntry

One turn of a consultation, immutable once written, ordered by `sequence_index`, chained by `previous_hash` (`"GENESIS"` at entry 0 in the 4.x form).

### HITLEventNode

A **human-in-the-loop decision gate** as a first-class node. Two-phase lifecycle: `INVOKED` (gate raised; context captured) → one of three terminal states — `RESOLVED` (a human decided here), `TIMED_OUT` (window expired; treated as rejection) or `ESCALATED` (the decision was passed up; this gate is concluded and any further deliberation is a *new* gate that references it). `ESCALATED` and `RESOLVED` MUST stay distinguishable. Its `node_hash` binds the invocation context to the human decision (a *causal anchor*); a gate still `INVOKED` blocks crystallization (G-18, `PENDING_HITL`). Under 5.0.0 a concluded HITL event is a *Structural Manifest* member. SPEC §4.6.

### AttachmentNode

External content injected into an Episode's context — a file, an image, a transcript, a fetched page — recorded so the injection is verifiable afterwards. The protocol's concern is narrow: the reasoning was influenced by identifiable bytes, and those bytes are hash-bound. SPEC §4.7.

### CrystallizationDeltaNode

The **record of a crystallization** — a point-in-time integrity snapshot, structurally analogous to a blockchain block header: `sealed_chain_root` (the spine root), a `predecessor_hash` chaining it to the prior delta, the §5.8 *Version Identifiers*, and (optionally) a *Resolved Signal Order*. Immutable once created; corrections flow forward. Its `episode_id` is in no delta preimage; a legacy non-UUID identifier is admitted only for a version ≤ 1 seal. SPEC §7, §5.8; `astp/core/crystallization.py`.

### Closure Record and Codicil

A **closure record** is written when an Episode closes (`EPISODE_CLOSE`), carrying the summary and carried-forward items. A **codicil** (`CODICIL_APPEND`) is the one sanctioned post-closure append: content admitted after `CLOSED` through its own path, never through the ordinary Segment write. SPEC §4.4.1, §12.4.1, G-1.

---

## 3. Identifiers and Hashes

### `node_id`

Stable UUID identifying a node across stores; assigned at creation; immutable. From 5.0.0 it MUST be generated with at least 122 bits of randomness and never derived from content: because `content_hash` is unsalted, the unguessable `node_id` in the leaf preimage is what makes a published leaf hash useless for testing a guess at a Segment's content. SPEC §5.2.

### `content_hash`

SHA3-256 of a node's payload via `to_content_hash_input()`. Captures *what the node is about*; unsalted; stable for the same payload state. SPEC §4.1.

### `content_ref`

Pointer to the full content in durable storage (implementation-defined locator). The hash chain references pointer plus `content_hash`; the bytes need not be hash-chain-resident, so content scales independently of the integrity layer.

### `leaf_hash`

The position-binding leaf hash: `SHA3-256("LEAF_HASH:v2:" ‖ UUID(node_id) ‖ STRING(node_type) ‖ STRING(schema_version) ‖ UINT(sequence_index) ‖ HASH(content_hash) ‖ UUID|NULL(parent_node_id))` under the *Canonical Field Encoding* (`hash_version` 2). Computed once at creation, never recomputed; `tree_leaf_index` is excluded (*Dual Index*). Under `spine_algorithm_version` 2 it is the spine's leaf input, so the spine root binds identity, type, schema, position, content and parent. A pre-5.0.0 Segment's version-2 leaf hash is computed at seal time **from its stored fields**, never from a stored version-1 leaf hash. `hash_version` 1 (4.x) also bound `sealed_at` and encoded an absent parent as sixteen zero bytes; it is retained as the definition of that version. SPEC §5.2; `compute_leaf_hash_v2`.

### Canonical Field Encoding

**The one byte form every 5.0.0 construction is built from.** A construction is `SHA3-256(prefix ‖ enc(f₁) ‖ … ‖ enc(fₙ))`: one *Domain Prefix*, then each field as a one-byte type tag and its payload — `NULL`, `BYTES`, `STRING` (NFC, length-prefixed), `UINT` (8 bytes), `UUID` (16 bytes), `TIMESTAMP` (UTC milliseconds), `HASH` (32 raw bytes), `LIST`, `BOOL`, `FLOAT` (IEEE 754 binary64; NaN/∞ refused; −0 → +0 the only normalization). Every field is self-delimiting and every construction has one prefix, so distinct inputs cannot encode to the same bytes. An order-independent *set of hashes* is `SHA3-256(prefix ‖ u32be(n) ‖ sorted raw members)` — no sentinel for the empty set. SPEC §5.1.1; `astp.protocol.encoding`.

### Canonical JSON

**The byte form of a JSON document inside a preimage**: RFC 8785 (JCS) with every string and key NFC-normalized; keys that collide after NFC are refused, never merged. The canonical form is what is hashed *and what is stored* — a stored document is a fixed point of canonicalization, which is the check a reader applies before hashing. SPEC §5.1.2; `astp.protocol.canonical_json`.

### Domain Prefix

The ASCII prefix that names a construction and its version (`LEAF_HASH:v2:`, `TREE_NODE:v2:`, `EPISODE_ROOT:v2:`, `AUDIT_RECORD:v2:`, …). Each construction has exactly one, used by no other, none a prefix of another, never reused across versions; the registry is SPEC §5.1.3. The 4.x prefixes (`LEAF:`, `NODE:`, `AUDIT:`, …) remain the prefixes of the retained 4.x constructions. `FINGERPRINT:` is retired with no successor. See *Domain Separation*.

### `spine_root` / `sealed_chain_root`

The Merkle root of the Episode's *Spine Leaf Set* under the seal's `spine_algorithm_version`. Recorded as `sealed_chain_root` on the `CrystallizationDelta` and `spine_hash` on the Episode. SPEC §5.6.

### `episode_root_hash`

The sealed Episode's outermost commitment — see *Episode Root*.

### `parent_node_id`

UUID reference to a node's parent. **Immutable once set** — reparenting is a governance violation (G-2). To correct parentage, create a new node and deprecate the old one. A Segment's parent is its Episode.

### `schema_version`

The version of the node-type schema, a field on `CognitiveNode`, separate from the protocol version. A Segment stored without one is schema `1.2.0` (the reference adapter's rule, applied identically by the seal path and the verifier).

---

## 4. Persistence Layers

The protocol defines three **persistence layers** (SPEC §3.4) — distinct from the code-architecture layering of §3.1 (`astp/protocol`, `astp/nodes`, `astp/core`, `astp/adapters`). Each is a separate cryptographic surface, owned by a distinct authority, isolated from the others' hash integrity.

### Layer 1 — Merkle Spine

The hash-chained, authoritative cognitive record: `EpisodeNode`, `IntentionNode`, `BeliefNode`, `SignalNode` and the other cognitive primitives, owned by the protocol kernel. Witness-signable. Its integrity is the foundation of every verifiability guarantee.

### Layer 2 — Episode Content

Segments and their supporting structures — BranchPoints, HITLEventNodes, the Episode spine tree (§5.6) — anchored to Layer 1 by parent reference. A Segment's `parent_node_id` is its Episode.

### Layer 3 — Workflow & Execution DAG

The provenance record of *how* an Episode's cognition was carried out: `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation` (§15 below). **Cryptographically isolated**: Layer 3 nodes reference Layers 1 and 2 by identifier only and are never hash-linked into the Spine (invariant L3-I1); no write to Layer 3 can invalidate any Spine hash. Each node type has one designated writer per workspace, the *Cognitive Implementation Authority*. SPEC §21.

---

## 5. Spine, Seal and Merkle Concepts

### Spine

The Merkle tree over an Episode's *Spine Leaf Set*, whose root is what a seal records. The spine is the proof; the content blobs are the payload — it carries hashes and pointers, not bytes. SPEC §5.6.

### Spine Leaf Set

**What is, and is not, a leaf of an Episode's spine.** Exactly the Episode's non-ephemeral Segments, ordered by `sequence_index`; under `spine_algorithm_version` 2 the leaf input is each Segment's `hash_version` 2 *`leaf_hash`*. Signals are not leaves (*Signal Manifest*); `EPHEMERAL` Segments are not leaves (*Exclusion Set*); structural nodes are not leaves (*Structural Manifest*); there is no Episode-identifier leaf. `sequence_index` is the only ordering key and is unique per Episode, so the order is total. Under versions 0 and 1 the leaf inputs were the Segments' bare content hashes as hex text, version 1 preceded by `SHA3-256(episode_id)`. SPEC §5.6; `compute_spine_root_sav2` (2), `compute_spine_root_v2` / `reproduce_spine_root` (0, 1).

### Merkle Tree / Merkle Root

A binary tree of hashes built bottom-up: inputs in the order given, paired from the left, an unpaired node carried up unchanged (neither duplicated nor re-hashed), a single input's level-0 hash as the root, and **the root of an empty list undefined** — an Episode with no spine leaf cannot be sealed. Under version 2, level 0 is `SHA3-256("TREE_LEAF:v2:" ‖ input)` and an interior node `SHA3-256("TREE_NODE:v2:" ‖ left ‖ right)` over raw bytes; the spine, the five-test-gate tree and the chain-proof tree are one tree. Under versions 0 and 1 the prefixes were `LEAF:` / `NODE:` over 64-character hex text. SPEC §5.3–§5.4.

### Domain Separation

Prefixing hash preimages so the same bytes in different contexts hash differently — leaves versus interior nodes, and in 5.0.0 every construction versus every other (see *Domain Prefix*). SPEC §5.3.

### Signal Manifest

The order-independent commitment to an Episode's SPINE-placed Signals: the *set of hashes* under `SIGNAL_MANIFEST:v2:`. Membership binds, arrival order and timestamps do not. One component of the *Episode Root*. (4.x: `SIGNAL_MANIFEST:v1:` over sorted hex strings joined by `|`, with a sentinel for the empty set; retained.) SPEC §5.7.

### Exclusion Set

The commitment to what was deliberately left out of the spine — the content hashes of `EPHEMERAL` Segments — so the omission is itself verifiable. Same set construction under `EXCLUSION:v2:`. SPEC §5.7.

### Structural Manifest

The order-independent commitment to an Episode's branch, fork, merge and termination structure: the *set of hashes* under `STRUCTURAL_MANIFEST:v1:` over the `:v2:` member hashes of its BranchPoints, BranchTermini, ForkPoints, DepartureForkPoints, ForkReturns, MergePoints and terminal-state HITL events, each under its own prefix. Governed by the *Membership Rule*. Fourth component of the *Episode Root* from 5.0.0; removing any member changes the root. A structural node created after a seal is committed by the Episode's *next* crystallization and references the earlier seal — never an unbound phantom between two seals. SPEC §5.7.1.

### Membership Rule

**A structural node — or a field of one — is bound if and only if removing it would let a verifier be deceived about the Episode's structure.** Structural claims (`spine_merkle_snapshot`, `merge_type`) are in; commentary (labels, summaries) and provenance (who initiated) are out — the audit chain binds provenance. *Named exception:* actor identity is bound where the actor constitutes the construction's defining claim — an aside's two parties, a soliloquy's agent. A `ForkOrphanMarker` and a *Coherence Fingerprint* are diagnostic satellites and never members. SPEC §5.7.1.

### Episode Root

**The integrity commitment of a sealed Episode.** Version 2: `SHA3-256("EPISODE_ROOT:v2:" ‖ UUID(episode_id) ‖ spine_root ‖ signal_manifest_hash ‖ structural_manifest_hash ‖ exclusion_hash)` — it binds the Episode's identifier directly and admits no string identifier. Version 1 (under `spine_algorithm_version` 0 and 1): `SHA3-256("NODE:" ‖ spine_root ‖ signal_manifest_hash ‖ exclusion_hash)`, retained. Recorded as `episode_root_hash` on the Episode. SPEC §5.7, §5.7.2; `compute_episode_root_hash_v2`, `reproduce_episode_root`.

### Version Identifiers (`hash_version`, `spine_algorithm_version`, `ordering_version`)

**Which construction produced a record's hashes.** `hash_version` (1, 2) on every `CognitiveNode`; `spine_algorithm_version` (0, 1, 2) and `ordering_version` (1, 2) on the `CrystallizationDelta`. **`spine_algorithm_version` 2 selects the entire seal construction** — leaf hash, tree, encoding, sets and Episode root — read it as *seal construction version*; there is deliberately no separate Episode-root identifier. Diagnostic metadata outside every preimage: a verifier reads them to pick the reproduction function and refuses values it does not know; altering them cannot make a tampered root verify. Absent means pre-4.3.0. A runtime stamps them from the seal it computed (`SealV2`), never from a module constant. SPEC §5.8.

### Seal

The act, and the record, of fixing an Episode's integrity: a crystallization that produces a `CrystallizationDelta` plus `sealed_at` on the Episode. A seal **requires a record** (G-40): `sealed_at` with no bound, reproducible crystallization delta is `NO_CRYSTAL`, never "sealed". A seal MAY be established at any time at or after close (*Late Seal*). The reference runtime seals under version 2 whenever the stored record allows it, and under version 1 — saying why — when it does not (a non-UUID identifier; a terminal HITL event stored without its context document). SPEC §5.7, G-40; `compute_episode_seal_v2`, `fetch_seal_inputs_v2`.

### Late Seal

A seal established after the Episode closed — ordinary lifecycle, not a defect. `closed_at` records closure; `sealed_at` records when fixity was computed and is never back-dated; `sealed_at ≥ closed_at` is the only ordering constraint; a non-zero gap carries no adverse inference. An Episode closed with nothing in it is closed and unsealed. SPEC G-40.

### Reproducibility Obligation

**A sealed root must be rebuildable from stored nodes alone.** A verifier with only the Segments, Signals, structural nodes and the seal record (with its *Version Identifiers*) recomputes `spine_root` and `episode_root_hash`; any construction needing insertion order, a store's default sort or a cache is non-conformant. Returning a *stored* root is an anchor lookup, not a verification. Unconditional for `spine_algorithm_version` 2 and `ordering_version` 2; for `ordering_version` 1 it holds only up to the order of same-timestamp Signals (see *Resolved Signal Order*). SPEC §9.3; conformance family `RP-*`.

### Inclusion Proof

Proof that a leaf sits at a position under a root. Version 2: `{leaf_index, leaf_count, leaf_hash, siblings[], spine_root}` — the verifier *derives* the path shape from the index and count (no stated directions), refuses a sibling list that does not fit it, and folds the siblings under the version-2 prefixes. It commits to the leaf and its position, **not** to the tree's size (that is the seal record's claim, and two mechanisms binding one fact could disagree). Because the spine and the proof tree are one tree under version 2, it proves position *in the sealed spine*. 4.x proofs (`path_directions`, hex text, Episode-identifier leaf) are frozen in their own form and never re-issued. SPEC §9.2; `InclusionProofV2`.

### Five-Test Gate

The five classes of tampering every conforming verifier MUST detect: content tampering, `sequence_index` modification, Segment insertion/deletion, audit-chain tampering, backdated wall clock. A verifier catching only the first is a *content* integrity verifier; all five are required for *temporal* integrity. SPEC §9.1.

### Hash Chain

The strictly ordered sequence of `leaf_hash` values; each binds its `sequence_index`, so the chain encodes both *what* happened and *in what order*. Out-of-order appends are rejected (G-3).

### Dual Index

Every `CognitiveNode` carries two indices: `sequence_index` — immutable cognitive-timeline position, **in** the leaf preimage — and `tree_leaf_index` — mutable physical Merkle position, **not** in any preimage, free to rebalance. The separation lets the tree rebalance for performance without invalidating a hash. Confusing the two is a protocol violation. SPEC §3.3.

### Resolved Signal Order

An optional **annotation** on a `CrystallizationDelta` (SPEC §5.8.1): the order of same-timestamp SPINE Signals that reproduces a seal made under `ordering_version` 1. Outside every preimage; written by a verification run, never by a re-seal; **checked, never trusted** — used only if it is a reordering of the stored Signal hashes that reproduces the sealed root, ignored otherwise; meaningless under `ordering_version` 2. Its absence says nothing against a seal. An identifier names a construction; the annotation supplies an input one left undetermined.

### Outermost Sealed Commitment

The construction that commits everything under a node's seal, defined by construction rather than enumeration: the *Episode Root* for an Episode; the spine root for a node type with no manifests. It is what a *Witness Record* and an *Anchor Commitment* bind (`root`, `root_version`), so the two attest the same object. SPEC §16.4.2.

### Spine Tip Cache

An optional cache of the authoritative `max_sequence_index` for fast tail queries. The structural store is authoritative; a conforming adapter implements `get_spine_snapshot_index()` and the cache sits above it. SPEC §13.

### Rebalance Event

A recorded restructuring of the physical tree (`tree_leaf_index` changes) under the **root-preservation invariant**: no rebalance changes any root. SPEC §14.

---

## 6. Episode Lifecycle

An Episode is in exactly one of a closed set of states; an implementation MUST NOT persist a status outside it (SPEC §4.4.1). Crystallization is a **fact, not a state**: whether an Episode is crystallized is determined by the existence of a `CrystallizationDelta`, never inferred from the status field.

| State | Meaning |
|---|---|
| `CREATED` | Node written; no content committed yet. |
| `ACTIVE` | Accepting Segments and Signals. The ordinary working state. |
| `PENDING_HITL` | A blocking HITL gate is unresolved (§4.6); advisory gates do not enter this state. |
| `CLOSING` | Closure initiated; final contributions still permitted. |
| `CLOSING_PENDING_SEAL` | All contributions in; grace period before the record is fixed. The record is fixed from here on (G-1). |
| `CLOSED` | Closure recorded. Further content only as a *codicil*. May still be sealed later (*Late Seal*). |
| `CRYSTALLIZATION_PENDING` | The crystallization lock is held. Transient, not a resting state; blocks all content writes. |
| `CRYSTALLIZED` | A crystallization concluded while the Episode was in no other pending state. An implementation MAY instead restore the status the Episode held before the lock (a mid-closure crystallization returns to `CLOSING`). |
| `SEALING` | Seal in progress. |
| `SEALED` | Sealed; the record is cryptographically fixed. |
| `ARCHIVED` | Retired from active use. Terminal. |

### Sealed (property)

A node whose `sealed_at` is non-null is frozen: no modification and no new children (G-1). Corrections flow forward — new node plus a deprecation or succession edge; there is no unseal and no in-place edit. For an Episode the record is fixed from `CLOSING_PENDING_SEAL` onward; the reference deployment records a sealed Episode as `CLOSED` with `sealed_at` set.

---

## 7. Crystallization

The protocol-level **state transition** that captures a point-in-time integrity snapshot and produces a `CrystallizationDeltaNode`. Three properties: it is *in* the chain (the delta is a hash-chained node, not an external receipt); deltas are immutable after creation; corrections flow forward through successor deltas and episodes. A crystallization takes a status-preserving lock (`CRYSTALLIZATION_PENDING`) and, on any failure after the lock is taken, releases it and restores the prior status — a failed crystallization aborts a seal, never leaves one half-written. SPEC §4.4.1, §7, G-40.

---

## 8. WIL — Write Intent Log

A coordination protocol for multi-store writes that guarantees ordering and recoverability. Writes proceed in **strict durability order** across four **storage roles**: the **durable content store** (`durable_content`) → the **authoritative structural store** (`authoritative_structural`) → the **ephemeral coordinator** (`ephemeral_coordinator`) → the **semantic search index** (`semantic_index`). Roles, not products: normative text names no provider; an implementer chooses what fills each role and one system may fill more than one. Ledger entries written under 4.x carry the reference deployment's provider names and are mapped to roles at read time (`store_role_of`). Every write is idempotent; an interruption at any phase is recoverable; the ephemeral coordinator is never a persistent store. SPEC §12.1–§12.3; `astp/core/wil.py`.

### Ledgered Operation

An operation named in the closed **operation register** (SPEC §12.4.1): `EPISODE_CREATE`, `SEGMENT_COMMIT`, `SIGNAL_COMMIT`, `EPISODE_SEAL`, `MANIFEST_FINALIZE`, `CRYSTALLIZATION`, `EPISODE_ARCHIVE`, `EPISODE_CLOSE`, `CODICIL_APPEND`, `ATTACHMENT_COMMIT`, `CONSULTATION_COMMIT` (**Tier 1** — coordinated writes to more than one store; the entry is a recovery instrument) and `BRANCH_CREATE`, `BRANCH_ABANDON`, `FORK_CREATE`, `FORK_RESOLVE`, `DEPARTURE_FORK_CREATE`, `MERGE_EXECUTE`, `ASIDE_OPEN`, `ASIDE_CLOSE`, `SOLILOQUY_INIT`, `SOLILOQUY_CONCLUDE` (**Tier 2** — a single authoritative write; the entry is a provenance breadcrumb). G-37 and G-38 govern the form of an entry; **G-39** requires that an implementation performing a registered operation record it — and surface, rather than absorb, a ledger it cannot write. A `COMPLETE` entry is never written for a write that did not happen. Entry states: `PENDING`, `COMPLETE`, `FAILED`, `REPLAYING`.

---

## 9. Audit Chain

### Audit Record

The tamper-evident, append-only log of what was *done* to a node — an integrity structure independent of every seal, verified on its own. Version 2 (`AUDIT_RECORD:v2:`): one schema, seventeen bound fields (identity, *Chain Key*, `delta_sequence`, delta type, agent and session, human actor, wall-clock and logical time, forward and reverse deltas as *Canonical JSON* stored as hashed, affected nodes, trigger, reason, detection provenance, and `prior_audit_hash` — NULL at genesis, no text sentinel). Rollback creates a new forward record; nothing is edited in place. The 4.x forms (two schemas, `"GENESIS"`) remain verifiable by the code that wrote them. SPEC §8, §19.1.1; `astp.protocol.audit_v2`.

### Chain Key

What identifies an audit chain: an Episode's UUID as text, or a declared synthetic key such as `declaration:<system>:<group>`. A `STRING` deliberately — the audit chain is outside every seal and its integrity rests on the `record_hash` recurrence, not on identifier canonicality; a UUID-shaped key is hashed as text. SPEC §8.1.

### Chain Verification

From the first record: `delta_sequence` runs 1, 2, 3, … without gap; the first `prior_audit_hash` is NULL; each later one is the previous `record_hash`; every `record_hash` recomputes from stored fields. Deletion, insertion, reordering and alteration are each detected at the first affected record. A writer that cannot read the chain head **fails rather than guesses** (SPEC §8.2; enforced by the 5.1.0 adapter contract).

### Retrieval Audit Record

A side-channel record of what an agent *read*, when, and through which snapshot boundary — produced by every retrieval tool call, so a read that influenced reasoning is auditable. Not a seal input. SPEC §11.1.

---

## 10. Consultation

A cross-agent exchange recorded as a first-class node with its own hash chain of `ExchangeEntry` nodes — a side chain anchored at a point in the Episode, distinct from the spine. Branch point before any exchange (G-8); resolution requires at least one entry (G-9). SPEC §4.

---

## 11. BFM Taxonomy — Branch, Fork, Merge, and the side channels

How Episodes diverge and reconverge, and how humans and agents step aside from the main line. SPEC §19. Every structural node here (BranchPoint, BranchTerminus, ForkPoint, DepartureForkPoint, ForkReturn, MergePoint) is a *Structural Manifest* member from 5.0.0, hashed under its own `:v2:` prefix.

### Branch / BranchPoint / BranchTerminus

A path that diverges from the main trajectory **within the same Episode**. A **BranchPoint** records the divergence: the source Segment and the `spine_merkle_snapshot` — the spine state it left from, which binds the divergence to a history so a BranchPoint cannot be re-pointed. A **BranchTerminus** records how the branch ended (merged or abandoned) and the final Merkle root. Labels are commentary and unbound.

### Fork / ForkPoint

A divergence that produces **new Episodes** — alternatives explored in parallel from one origin Segment, each a sibling with its own `sibling_index`. A fork has a non-empty `fork_objective` (G-19), at least two alternatives (G-20), and resolves with a required rationale (G-21). A **ForkPoint** sits on the origin Episode.

### Departure Fork / DepartureForkPoint / ForkReturn

A **single, directional** departure: one new Episode leaves the origin, which continues; the fork later completes or is abandoned, and may declare one **return** (`ForkReturn`, at most one per fork, only after completion — G-34, G-35) binding the fork's final spine tip back to the origin. Requires an objective (G-31), a creation trigger (`TOPIC_SHIFT`, `PARALLEL_THREAD`, `EXPLICIT_FORK`, …; G-32) and, for a topic shift, the trigger Segment (G-33). The **DepartureForkPoint** binds `spine_tip_hash_at_departure` — the cross-verifiable anchor of the departure; back-dating it is forbidden (G-30). SPEC §19.3.5–§19.3.6.

### Orphan Recovery / ForkOrphanMarker

The runtime enforcement, after a partial failure, of the departure-fork invariants the producers enforce at write time — a crash between the two writes, a rolled-back status. Four orphan classes; a **`ForkOrphanMarker`** is the diagnostic record of one and is *never a manifest member*; the one permitted retroactive spine write (a recovered point, byte-identical to an on-time one) *is* a member, committed by the Episode's next crystallization and referencing any earlier seal it post-dates. Detection cadence is not normative. SPEC §19.3.7, §5.7.1.

### Merge / MergePoint

A divergent path rejoining. A **MergePoint** binds the source root, the target root before and after, the common ancestor and the `merge_type` (how two histories combined); `merge_summary` is commentary, non-empty by G-22 but unbound. The conflict surface is never silently resolved (G-23); the three integrity assertions of §19.3.3 hold (G-24).

### Aside

A **human-initiated** side channel with one agent, opened from one Segment (G-25) and closed before the Episode seals (G-26). Its content hash (`ASIDE:v2:`) binds both parties — the *named exception* to the membership rule's actor exclusion, because the human and the agent *are* the channel — and the parent Segment by identity and content hash. Its terminus (`ASIDE_TERMINUS:v2:`) binds the content produced inside, the close reason, and the reference-scan disclosure of external Segments found holding references in. SPEC §19.4.1.

### Soliloquy

An agent's **private deliberation**, opened from one Segment; humans always have read access (G-27); concluded before the Episode seals (G-28). One construction (`SOLILOQUY:v2:`) binds who opened it, from where, with what content there, when. The **deliberation chain** (`DELIBERATION_CHAIN:v2:`) is hashed by the deliberation Segments' *content hashes in order*, so an auditor with access verifies the chain against the conclusion without the content being in the hash; the **conclusion** (`SOLILOQUY_CONCLUSION:v2:`) binds the chain hash, the public summary, the spine Segment it merged into and how it terminated. The 4.x placeholder/full policy is retired. SPEC §19.4.2–§19.4.3.

### Coherence Fingerprint

A per-Segment reading of the detector that watches for a write crossing a divergence threshold (topic vector, intent class, drift, detection state), computed at write time (G-29). A diagnostic satellite: **it has no content hash** and never enters a seal or a chain; a fingerprint that needs attesting is attested by the audit record of the transition it triggered. SPEC §19.5.1.

---

## 12. Governance

The protocol's normative rules, numbered `G-N`, each with a specific failure mode and each enforced where the write happens: a rule raises; an adapter surfaces the violation and never continues past it. The full enumeration is SPEC §6 (G-1–G-18, G-40), §12.4 (G-37–G-39), §19 (G-19–G-35), §21 (G-36).

| Rule | Substance |
|---|---|
| G-1 Write Guard | No modification of, and no new child under, a sealed node; an Episode's record is fixed from `CLOSING_PENDING_SEAL`; the codicil is the sole post-closure append. |
| G-2 Reparenting Prohibition | `parent_node_id` is immutable; correct parentage forward with a new node. |
| G-3 / G-4 | `sequence_index` and the logical clock are monotonic. |
| G-5 / G-6 | Node types are registered; the *Namespace Firewall* holds. |
| G-7–G-9 | Signal governance; consultation branch-before-exchange and resolve-with-entry. |
| G-10 | Structural delta content invariant. |
| G-11 Witness Threshold | Counted as a maximum bipartite matching between distinct witness names and distinct keys over *valid* records. |
| G-12 Witness Validity | Commitment recomputes ∧ fingerprint is SHA3-256 of the key ∧ signature verifies ∧ witness is not the author. |
| G-13 / G-14 | Chain-root integrity; anchoring at crystallization. |
| G-15 / G-16 | Key version monotonicity; `node_type` in key derivation. |
| G-17 / G-18 | HITL invocation precedes resolution; an unresolved blocking gate blocks crystallization. |
| G-19–G-35 | Fork, merge, departure-fork, aside and soliloquy invariants (§11 above). |
| G-36 | Every workspace's `ConformanceDeclaration` names the *Cognitive Implementation Authority* per Layer 3 node type. |
| G-37–G-39 | Ledger entry form (Tier 1 / Tier 2) and the obligation to ledger every registered operation. |
| G-40 | Sealed requires a record; a late seal is ordinary; Episode identifiers are UUIDs at creation, the boundary closing only after any legacy Episode is sealed under version 1. |

### Reparenting Prohibition

The invariant G-2 enforces: a node's position in the graph is immutable, so an apparent change to parentage is suspicious by construction.

---

## 13. Trust Infrastructure

### Key Hierarchy

Root key material → workspace key → node key → seal key, derived by HKDF-SHA3-256; `node_type` is in the node-key derivation context (G-16), so keys for `"episode"` and `"signal"` differ even with identical identifiers. Key versions are monotonic (G-15). Node keys sign only; encryption is outside the protocol. SPEC §16.2; `astp.protocol.keys`.

### Witness Record

A claim by one party about what it saw: **this witness** saw **this root** for **this node** at **this time**, in **this role**. The commitment (`WITNESS_COMMITMENT:v2:`) binds all five — the witness, the node, the *Outermost Sealed Commitment* with its version, position, time and role; the signature is Ed25519 over the 32 raw bytes of the commitment, carried with the public key and its SHA3-256 fingerprint. `ed25519` is the one registered scheme (an extensible registry with one entry). Whether the key belongs to the named witness is the workspace key registry's question, outside the preimage. See *Witness Validity*. SPEC §16.4.

### Witness Validity

When a witness record counts (G-12): its commitment recomputes; its fingerprint is the SHA3-256 of its key; its signature verifies under that key over the raw commitment; and the witness is not the node's author — a self-witness is not an attestation. A record failing any condition is recorded but never valid. The threshold (G-11) counts valid records as a maximum matching between distinct names and distinct keys — A/k₁, A/k₂, B/k₁ admit two, and a greedy pass would say one. 4.x bound neither the witness nor the time and accepted empty signatures; both are closed. SPEC §16.4, G-11, G-12; `astp.protocol.witness_v2`.

### Anchor Commitment / Anchor Receipt

What is submitted to a transparency log at crystallization (G-14): `ANCHOR_COMMITMENT:v2:` over the node, its workspace, the *Outermost Sealed Commitment* and version, the crystallization sequence and clock, and the time — no payload internals. The log's **receipt** (`log_id`, entry, timestamp, the log's own inclusion proof) is the log's artifact and provides an external monotonicity anchor the logical clock alone cannot. SPEC §16.3; `astp.protocol.anchor_v2`.

### Chain Proof

A `ProofChain` of `ProofLink`s proving that one node's state was causally downstream of another's across node boundaries and implementations: each link carries an *Inclusion Proof* that MUST verify against the link's own `spine_root`, links are causally ordered by parentage or cross-reference, and `chain_root` is SHA3-256 over the concatenated link roots (G-13). SPEC §16.5.

---

## 14. Cross-Episode Linking and Grouping (SPEC §20)

### EpisodeLink

A typed relationship between two Episodes, with a `link_type` from a closed vocabulary — `CONTINUES_FROM` (direct continuation), `SUPERSEDES`, `BRANCHES_FROM`, `INFORMED_BY`, `REFERENCES` (audit-only, non-loading), `SPAWNED_FROM` — subject to mutual-exclusion rules; a `link_strength` in [0, 1]; whether it was human-asserted or inferred, with every contributing *inference signal* and the threshold in force recorded; and a health lifecycle. Its `content_hash` (`EPISODE_LINK:v2:`) binds the two Episode identifiers, **each end's Episode root when that end was sealed at link creation** (NULL otherwise; a sealed end with a NULL root is nonconformant; `retroactive ⇒` the source root is present), the type, exact strength, signals in order, threshold, retroactive flag and version strings — and nothing mutable: health, quarantine and `created_by` are the audit chain's. SPEC §20 →2–§4.

### Link Health State

`VALID` (target exists, version delta within tolerance), `STALE` (target advanced by a minor or patch version), `FROZEN` (target crystallized; the link is permanently anchored to that version), `BROKEN` (target deleted or unreachable), `QUARANTINED` (orphan detection or an integrity flag). Quarantine exits only by explicit human review — `CONFIRMED` → `VALID`, `DISSOLVED` → `BROKEN`, or escalation when the quarantine TTL is exceeded; there is no automatic exit. Lifecycle, not content: outside the link's hash, recorded in the audit chain. SPEC §20 →6, →11.3.

### Resumption Isolation Rule

On Episode resumption a loader MUST follow `CONTINUES_FROM` and `SUPERSEDES` links, MAY follow `INFORMED_BY` and `SPAWNED_FROM` one hop, and never loads through `REFERENCES`. SPEC §20 →3.

### MembershipRecord

The assertion that an Episode belongs to a group in a native grouping system (a collection, a project, a database), with a `membership_role`, an asserting party and time, and a succession chain (`supersedes_record_id`, forward pointer excluded from the hash). Its `content_hash` is the §20 canonical field set, unchanged in 5.0.0. SPEC §20 Part II.

### ConformanceDeclaration

A grouping system's declaration of what its native construct supports (capabilities, version) — and, for Layer 3, which entity is the *Cognitive Implementation Authority* for each node type (G-36). Versioned; superseded by a bump, never edited. The `group_system` identifier is any string the implementation declares; the protocol reserves only `ariadne_native`. SPEC §20 →8, §21 §3.

### Conformance Tiers (wire / state / behavioral)

**Wire tier**: two implementations can exchange `EpisodeLink`, `MembershipRecord` and `ConformanceDeclaration` structures and verify each other's hashes. **State tier**: the authoritative structural store is the single source of truth for structural state; no read may contradict it. **Behavioral tier**: how signals are combined, thresholds set and sweeps scheduled — implementation space. SPEC §20 §12.

---

## 15. Layer 3 — Workflow & Execution DAG (SPEC §21)

### WorkflowDeclaration

The declared intent to carry out work: what was to be done, under which mandate and intention (immutable provenance fields, nullable and *included* in the hash), with a lifecycle status that is **excluded** from the hash because it mutates. Referenced by Layer 1/2 by `node_id` only.

### ExecutionNode

One recorded step of execution. Every field except `content_hash` is in the preimage — including `status`, which is terminal-on-write and forensically meaningful (the hash binds *what status was written*).

### SkillInvocation

One invocation of a skill or tool within an execution, with inputs, outputs and outcome. `registry_id` is the one Layer 3 field excluded from a content hash for reasons other than mutation: a deferred, backfillable reference.

### Cognitive Implementation Authority (CIA)

The **sole writer**: for each Layer 3 node type within a workspace, exactly one entity is authorized to issue creation writes; writes from any other source are rejected at the wire tier (invariant L3-I2). Named per node type in the workspace's *ConformanceDeclaration* (G-36). Do not add multi-writer paths.

### Spine Isolation (L3-I1)

No field of any Layer 3 node or edge appears in the preimage of any Layer 1 or 2 hash, and Layer 1/2 nodes carry no Layer 3 identifiers in their preimages. Layer 3 may share storage with the Spine; what is constrained is the hash preimage, which never crosses the boundary. Layer 3's own byte form is governed by §21 Part III §8 (deterministic; not locked to §5.1.1).

---

## 16. Adapter and Conformance

### AriadneAdapter / ASI

The abstract contract (the **Adapter Service Interface**) any storage backend implements to serve as an ASTP adapter: writing nodes, querying, computing hashes, WIL recovery. `astp/adapters/base.py`; SPEC §2, §15.

### Adapter Failure Contract

SPEC §15 item 7 as restated in 5.1.0: a writer or reader that cannot complete **raises** a typed error chained to the store's (`AdapterWriteError`; `BranchOperationError` for an operation that failed after it began); it never returns a default, logs and continues, or gates itself on a feature flag — whether to call the adapter is the host's decision. Governance violations pass through unwrapped. A precondition *refusal* (source Episode not found, branch already terminated) is not a failure and is reported as such. A ledger entry is never `COMPLETE` for a write that did not happen (G-39). `astp.protocol.errors`.

### Reference Implementation

The Neo4j adapter in `astp/adapters/neo4j/`: the worked example of a conforming adapter and the ground truth for the vectors. Its graph labels keep the `Ariadne*` prefix and its HKDF `info` strings the `ariadne.` prefix — wire constants that feed derived keys or name stored data and are not renamed with the package.

### Conformance Test Vectors

Machine-readable expected values a third-party implementation reproduces: [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json), generated by `vectors/5.0.0/generate.py` and never edited by hand, every value checked by the reference tests against the package **and** against a from-prose implementation that imports nothing from it. The `CONFORMANCE*.md` documents state each vector's inputs and the property required (`RP-*`, `W*`, …).

### Proof of Record

An exported file with which a third party verifies a sealed Episode — an *Episode of Record* in particular — using the package alone: the seal record with its version identifiers, the leaf hashes or Segments, and the manifests. Two profiles are anticipated: *attested* (roots and proofs only; withholds leaf lists and the *Resolved Signal Order*, which are unsalted content hashes) and *full*. Not yet published for any Episode of Record; the README says so.

---

## 17. Versioning, Documents, and Amendments

### Episode of Record

The ASTP Episode, opened and sealed by the maintainers, in which a MAJOR change is deliberated and ratified — the protocol recording its own amendment. The specification text is the human-readable result; the Episode is the anchor. It cites what it ratifies by **content digest** (the bytes survive a history rewrite; a commit hash does not). 4.0.0: `458fb62b-faee-4e42-9f92-c63187c1b59a`; 5.0.0: `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28` ([`docs/RATIFICATION-5.0.0.md`](./docs/RATIFICATION-5.0.0.md)). `GOVERNANCE.md`, `VERSIONING.md`.

### Design Episode

An Episode in which a change is deliberated before its Episode of Record — the 5.0.0 units were ruled, one by one, in `4b9a779e-be46-4d61-872e-fd76545aa901`. Provenance, not ratification.

### Schema Version

The version of a node type's payload schema (`schema_version` on `CognitiveNode`), distinct from the protocol version in `SPEC.md`'s header.

### Amendment

A normative change, taken through the process in `GOVERNANCE.md` (proposal → draft → review → ratification in an Episode of Record → release). Amendments integrate into `SPEC.md`; the former standalone amendment documents and each prior MAJOR's `SPEC.md` are retained under `docs/history/` for provenance only.

### Versioning Policy

`VERSIONING.md`: SemVer `MAJOR.MINOR.PATCH`. MAJOR on canonical-form change (a preimage, a serialization, a required field, a governance rule's semantics) — always introduced as a *new versioned construction* so existing seals stay verifiable; MINOR on additive surface; PATCH on errata. `SPEC.md`'s `Version:` field IS the protocol version; `astp.PROTOCOL_VERSION` names the SPEC version the package implements; `astp.__version__` is the package's own.

---

## Alphabetical Index

- **Adapter Failure Contract** — §16
- **Amendment** — §17
- **Anchor Commitment / Receipt** — §13
- **AriadneAdapter / ASI** — §16
- **Aside** — §11
- **AttachmentNode** — §2
- **Audit Record** — §9
- **Branch / BranchPoint / BranchTerminus** — §11
- **Canonical Field Encoding** — §3
- **Canonical JSON** — §3
- **Chain Key** — §9
- **Chain Proof** — §13
- **Chain Verification** — §9
- **Closure Record / Codicil** — §2
- **Cognitive Implementation Authority (CIA)** — §15
- **CognitiveEdge** — §1
- **CognitiveNode** — §1
- **Coherence Fingerprint** — §11
- **Conformance Test Vectors** — §16
- **Conformance Tiers** — §14
- **ConformanceDeclaration** — §14
- **Consultation / ConsultationNode** — §2, §10
- **`content_hash`** — §3
- **`content_ref`** — §3
- **Crystallization** — §7
- **CrystallizationDeltaNode** — §2
- **Departure Fork / DepartureForkPoint / ForkReturn** — §11
- **Design Episode** — §17
- **Domain Prefix** — §3
- **Domain Separation** — §5
- **Dual Index** — §5
- **Episode Lifecycle** — §6
- **Episode of Record** — §17
- **Episode Root** — §5
- **`episode_root_hash`** — §3
- **EpisodeLink** — §14
- **EpisodeNode** — §2
- **ExchangeEntry** — §2
- **Exclusion Set** — §5
- **ExecutionNode** — §15
- **Five-Test Gate** — §5
- **Fork / ForkPoint** — §11
- **Governance rules (G-1 … G-40)** — §12
- **Hash Chain** — §5
- **HITLEventNode** — §2
- **Inclusion Proof** — §5
- **Key Hierarchy** — §13
- **Late Seal** — §5
- **Layer 1 / 2 / 3** — §4
- **`leaf_hash`** — §3
- **Ledgered Operation** — §8
- **Link Health State** — §14
- **Membership Rule** — §5
- **MembershipRecord** — §14
- **Merge / MergePoint** — §11
- **Merkle Tree / Merkle Root** — §5
- **Namespace Firewall** — §1
- **`node_id`** — §3
- **NodePayload** — §1
- **Orphan Recovery / ForkOrphanMarker** — §11
- **Outermost Sealed Commitment** — §5
- **`parent_node_id`** — §3
- **Proof of Record** — §16
- **Rebalance Event** — §5
- **Reference Implementation** — §16
- **Reparenting Prohibition** — §12
- **Reproducibility Obligation** — §5
- **Resolved Signal Order** — §5
- **Resumption Isolation Rule** — §14
- **Retrieval Audit Record** — §9
- **Schema Version / `schema_version`** — §3, §17
- **Seal** — §5
- **Sealed (property)** — §6
- **SegmentNode** — §2
- **Signal Manifest** — §5
- **SignalNode** — §2
- **SkillInvocation** — §15
- **Soliloquy** — §11
- **Spine** — §5
- **Spine Isolation (L3-I1)** — §15
- **Spine Leaf Set** — §5
- **Spine Tip Cache** — §5
- **`spine_root` / `sealed_chain_root`** — §3
- **Structural Manifest** — §5
- **Version Identifiers** — §5
- **Versioning Policy** — §17
- **WIL — Write Intent Log** — §8
- **Witness Record** — §13
- **Witness Validity** — §13
- **WorkflowDeclaration** — §15
