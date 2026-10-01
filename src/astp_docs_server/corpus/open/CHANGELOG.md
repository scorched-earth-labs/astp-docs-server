# Changelog

All notable changes to ASTP (the AI State Tree Protocol). Version numbering follows [VERSIONING.md](./VERSIONING.md).

## [Unreleased]

### Ratified
- **[`PATENTS.md`](./PATENTS.md) 1.0.0**, the first versioned text of the patent policy and pledge, ratified in Episode of Record `df3434bd-6936-441c-a896-254149f2bd48` (sealed 2026-10-01 under `spine_algorithm_version` 3, `episode_root_hash` `d77bcdd639747d6f1bba806c02586c06229bd2a1c556c5c7273cb056ce0c0b15`) — [`docs/RATIFICATION-PATENTS-1.0.0.md`](./docs/RATIFICATION-PATENTS-1.0.0.md). Cited by content digest `ef288af95b5c1197f242edbe8f17859654d0f6c9f70785bb9634c4dcf564f159` as final bytes (ratified = published): the #88 text plus `Version:`, `Status:` and `Date:` header lines. No pledge term changes. The three earlier unversioned texts (#80, #81, #88) are recorded by digest, not ratified. With `SPEC.md` 6.0.2 and `PROTOCOL-CONFORMANCE.md` 1.0.1, every document a Conforming Implementation's licence rests on is now ratified by digest.
- **`SPEC.md` 6.0.2, as a whole document**, ratified in Episode of Record `46490010-e8a7-4d79-8092-a1a82de3c93f` (sealed 2026-10-01 under `spine_algorithm_version` 3, `episode_root_hash` `3a543f6ba5a777258d6a2066452f843c63c965574dde66bdd30ea2ccff900da8`) — [`docs/RATIFICATION-SPEC-6.0.2.md`](./docs/RATIFICATION-SPEC-6.0.2.md). Cited by content digest `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb`; `SPEC.md` is not edited, so for 6.0.2 the ratified digest, the published digest and the digest `PATENTS.md` §4.1 pledges against are one value, for the first time. The Episode accounts for every change since 5.0.0: 6.0.1 (§5.7.1 spine-state fields) and 6.0.2 (§2.5.2) ruled errata; the 6.0.0 fold established as faithful to the ratified draft; and four commits (#55, #58, #59, #62) recorded as having changed `SPEC.md` without the version change `VERSIONING.md` requires, harmlessly. Carried to the next revision: the CodicilNode `content_hash` annotation (§4.9.3), the `CONTEXT_COMMIT` wording (§12.4.1), and the G-40 Episode-identifier rule for version 3.
- **[`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) 1.0.1**, ratified in the same Episode by content digest `dca786fa8780dd19563acf39d3369010256f7570d8212d092060a5117094236a` (final bytes; ratified = published). Editorial: the header and §7.3 now record that the 6.0.2 digest is a ratified one. It changes nothing conformance requires.

### Reference package (`astp` 2.2.1 — `PROTOCOL_VERSION` 6.0.2)
- `astp.PROTOCOL_VERSION` names 6.0.2, the `SPEC.md` version the package implements. 6.0.2 changed no normative surface the package touches, so the constant was left at 6.0.1, as the MAJOR.MINOR comparison in `tests/unit/protocol/test_protocol_version.py` allows. But a proof of record stamps the constant into its `protocol_version` field, so proofs exported against 6.0.2 said 6.0.1 — among them the `PROTOCOL-CONFORMANCE` 1.0.0 Episode of Record's. That field is informational and outside every root; the published proof is left as exported. No other code change.

### Ratified (companion document)
- **[`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) 1.0.0**, applying to `SPEC.md` 6.0.2, ratified in Episode of Record `19d4390f-ac46-4840-bc9a-f419c6626fb4` (sealed 2026-10-01 under `spine_algorithm_version` 3, `episode_root_hash` `5918cbcd74506fec2e8eed11af3a4c6c5c32c10c571c2bf389c6efa4f730d9ce`) — [`docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md`](./docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md). The Episode cites the text by content digest (`5b8e5c2fa0baa509d2bb89a4507bca7a78dedd428e95a22f554a3ab8c3c0eacd`, the `-draft` bytes at `d5ae006`); the `Version:` and `Status:` lines were changed after the seal and nothing else, so the published file differs from the ratified bytes in exactly those two lines, by design. It ratifies the conformance definition, not `SPEC.md`: the `SPEC.md` digest `PATENTS.md` §4.1 pledges against remains a direct content digest. The first Episode of Record that is itself a conforming record under the definition it ratifies — capture posture `all_external`, a context manifest of 35 entries. Exported proof of record under `docs/proofs/`.

### Changed (companion documents, not normative protocol text)
- [`VERSIONING.md`](./VERSIONING.md) and [`GOVERNANCE.md`](./GOVERNANCE.md): [`PATENTS.md`](./PATENTS.md) carries its own `Version:` field, and each version is ratified in an Episode of Record before release, as `PROTOCOL-CONFORMANCE.md`'s are. It was the only normative document whose revisions left no anchored trace, and its §15 promise not to withdraw a granted license retroactively needs the policy text a licensee relied on to be identifiable. Its first version, 1.0.0, is ratified in its own Episode; until then `PATENTS.md` is unchanged. `GLOSSARY.md` *Episode of Record* matches.
- [`PATENTS.md`](./PATENTS.md) §4.1 now states that `SPEC.md` 6.0.2 is ratified as a whole document in Episode of Record `46490010-e8a7-4d79-8092-a1a82de3c93f`, so the pinned digest is the ratified, published and pledged digest at once. This corrects a statement overtaken by #87, which still said the digest was "a direct content digest … rather than a ratified one". §4.2 adds that the applicable `PROTOCOL-CONFORMANCE.md` version is ratified in an Episode of Record and identified there by content digest, deferring to that document's §7 for how. It deliberately adds no digest pin, because the conformance document revises on its own track. Nothing about what is pledged changes; only what can accurately be said about how the pledged text is anchored. The digest table, the digest and `SPEC.md` are unchanged.
- **Counsel review, revision 1** of the licensing and conformance documents. `SPEC.md` is unchanged, so the digest `PATENTS.md` §4.1 pledges against still holds.
  - [`PATENTS.md`](./PATENTS.md) §14: conformance, and the patent license tied to it, is determined per Specification Version. A later revision of `PROTOCOL-CONFORMANCE.md`, the Specification or another conformance document applies prospectively. It neither retroactively withdraws a license already granted nor, by itself, expands one.
  - [`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) 1.0.0-draft: §1 states that `PATENTS.md` governs the license and this document the technical requirements. §2 ties the definition to a particular Specification Version. §7 identifies the conformance requirements by this document's `Version:` and `Applies To` fields, and adds §7.1 (effect of later revisions), §7.2 (no implied expansion) and §7.3 (pinned versions). §8 has a claim state the conformance-document version.
  - [`CONTRIBUTING.md`](./CONTRIBUTING.md) gains *Specification contributions and patent disclosure*: the DCO requirement, what a normative change must disclose, that a disclosure neither warrants nor licenses, what maintainers may do before merging, employer rights, and the Apache License's continued application.
- `GLOSSARY.md` defines *Specification Version*, and *Conforming Implementation* states the conformance-document version a claim names.
- [`VERSIONING.md`](./VERSIONING.md) *Where versions are declared*: `PROTOCOL-CONFORMANCE.md` carries its own `Version:` beside its `Applies To` Specification Version, because it defines the term `PATENTS.md` §4.2 grants against and a conformance revision may be issued against an unchanged Specification Version. `IMPLEMENTATION-*.md` and the per-surface `CONFORMANCE-*.md` vector documents remain versioned-against. This resolves the conflict with counsel's `PROTOCOL-CONFORMANCE.md` §7.
- [`GOVERNANCE.md`](./GOVERNANCE.md) *Episode of Record*: an Episode of Record also ratifies each version of a normative companion document that carries its own version (today `PROTOCOL-CONFORMANCE.md`), whether or not `SPEC.md` changes, citing the text by content digest. A revision that changes no conformance requirement may be ratified by a correspondingly brief Episode that records exactly that. This authorises the Episode that ratifies `PROTOCOL-CONFORMANCE.md` 1.0.0, which `PATENTS.md` §14 already requires. `GLOSSARY.md` *Episode of Record* matches.
- [`GOVERNANCE.md`](./GOVERNANCE.md) *Episode of Record*: an Episode of Record may also ratify `SPEC.md` as a whole document at a version it already carries, whatever its change class. It changes no specification text, cites the document by content digest, and accounts for every change since the last whole-document ratification. `SPEC.md` is not edited after the seal, so the ratified, published and pinned digests are the same. This authorises the Episode that will ratify `SPEC.md` 6.0.2, the digest `PATENTS.md` §4.1 pins, which `PROTOCOL-CONFORMANCE.md` §7.3 and `PATENTS.md` §4.1 both note has not yet been ratified. `GLOSSARY.md` *Episode of Record* matches, and now lists the 6.0.0 and `PROTOCOL-CONFORMANCE.md` 1.0.0 Episodes it had omitted.

## [6.0.2] — 2026-09-26

**PATCH.** Correction: the governance-rule bound of the protocol surface.

### Fixed
- **§2.5.2 Protocol surface.** The governance row read "G-1 through G-40", so as written the non-negotiable surface left out G-41, G-42 and G-43, which 6.0.0 added — both erasure rules among them. It now names the rules by where they are defined (§6, §12.4, §19, §21) rather than by a numeric range that goes stale with each new rule, and points to [`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) for which of them a given implementation must enforce. No rule, preimage or vector changes. The reference package is unchanged (`PROTOCOL_VERSION` stays 6.0.1: a PATCH carries no new constant).

### Added (companion documents, not normative protocol text)
- **[`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) 1.0.0-draft** — the single definition of a Conforming Implementation: two required profiles (Core, Context Commitment) and five optional ones, each with its governance rules; optional to support is not optional to commit, and retrieval (§10) and rebalance (§14) bind only an implementation that does them (§3.8); how conformance is demonstrated and claimed; and what it neither requires nor establishes. A claim states the implementation's G-42 classification policy, because the record shows which construction an entry used but not the classification behind it (§5.1). Ratified as 1.0.0 in Episode of Record `19d4390f-ac46-4840-bc9a-f419c6626fb4` ([`docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md`](./docs/RATIFICATION-PROTOCOL-CONFORMANCE-1.0.0.md)).
- **[`PATENTS.md`](./PATENTS.md)** — the patent policy and pledge to Conforming Implementations, separate from the Apache license; it identifies the pledged text by the SHA3-256 digest of `SPEC.md`. **[`NOTICE`](./NOTICE)** — copyright, patent, protocol-name and trademark notices.
- **Developer Certificate of Origin.** [`DCO.txt`](./DCO.txt); `CONTRIBUTING.md` gains *Certificate of origin*; CI refuses a pull request with a commit its author has not signed off.
- `tests/unit/protocol/test_spec_digest.py` — a `SPEC.md` digest published for the current version is of `SPEC.md` as it stands.

### Changed
- `CONFORMANCE.md` is renamed **`CONFORMANCE-TRUST.md`**: it is scoped to §16, and its unqualified name implied general conformance. References updated; its content and version are unchanged.
- `GLOSSARY.md` defines *Conforming Implementation* and *Conformance Profile*, and its governance table gains G-41–G-43.

## [6.0.1] — 2026-09-24

**PATCH.** Clarification: what a spine-state field holds for a live Episode.

### Fixed
- **§5.7.1 Spine-state fields.** `spine_merkle_snapshot`, a MergePoint's `source_merkle_root` / `target_merkle_root_pre` and a BranchTerminus's `final_merkle_root` are the Episode's **live spine root** when the node is created: the `spine_algorithm_version` 2 root over the `hash_version` 2 leaves of its non-ephemeral Segments (through the `source_segment_id` for a BranchPoint), which equals the seal's `spine_root` over the same Segments. The 6.0.0 text bound `spine_merkle_snapshot` as a non-nullable HASH but did not say what it is before the seal, when no stored spine root exists — and the reference package read the (absent) stored root, so every branch of a live Episode held `""`, its `BRANCH_POINT:v2:` member could not be hashed, and the Episode could not seal under version 2 or 3. No preimage, field list or vector changes.

### Reference package (`astp` 2.2.0 — `PROTOCOL_VERSION` 6.0.1)
- **`StructuralStore.spine_segments(episode_id)`** — the Episode's spine leaves as `SegmentSealInput` (non-ephemeral, content-hashed, `parent_node_id` = the Episode). A deployment MUST return exactly what its seal reads. `InMemoryStore` implements it.
- **`astp.core.branch_operations.live_spine_root(store, episode_id, through_segment_id=None)`** — the §5.7.1 live root; None when there is no leaf.
- **`astp.core.seal_v2.spine_leaf_hashes_v2`** — the leaf construction `compute_episode_seal_v2` already used, factored out so the seal and the live root share one implementation. Seal output is unchanged (every vector reproduces).
- `create_branch` binds the live root through the source Segment; `abandon_branch` / termination binds the live root as `final_merkle_root`; `execute_merge` binds the source's and target's live roots (it refused every merge of two live Episodes, whose stored roots were empty).
- `tests/unit/protocol/test_live_spine_root.py`: the live root of a whole Episode equals the seal's `spine_root`; prefix and ephemeral handling; `create_branch` → a 64-hex snapshot whose `BRANCH_POINT:v2:` member hashes.

## [6.0.0] — 2026-09-22

**MAJOR.** The context commitment: a sealed Episode now proves what its agents were *given*. Ratified in Episode of Record `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8` (sealed 2026-09-22, `episode_root_hash` `45cd50c5d34c6d1ec49fa9a6fd7989036e2d91d624f66e9eb8e93c9904f27d3e`), which ratifies the amendment text at commit `4ec1de1` by content digest together with its reference vectors ([`docs/RATIFICATION-6.0.0.md`](./docs/RATIFICATION-6.0.0.md)). Every construction is new and versioned; every seal made under `spine_algorithm_version` 0, 1 or 2 is unchanged and stays reproducible. The governing invariant: **the seal proves history, not retention.**

### Added
- **§4.8 `ContextEntryNode`** — one node per provision of external content to one agent (`attachment` · `retrieval` · `external` · `tool_output`), or per attempted provision whose content was not captured; `CONTEXT_ENTRY:v1:` over thirteen fields (§5.7.3); provenance and content-plane fields outside the preimage (§4.8.6); the spine position the provision preceded (§4.8.2); two content constructions and one sealed bit — `CONTEXT_CONTENT:v1:` and `CONTEXT_CONTENT_SALTED:v1:` (§4.8.3); verifiability at seal (§4.8.4); declared-incomplete entries and append-only repair through `resolves` (§4.8.5).
- **§5.7.3 Context manifest** — the version 2 tree over entry hashes in ascending bytewise order, bound with the capture posture and count under `CONTEXT_MANIFEST:v1:`; a function of the set; inclusion proofs over it (§9.2); the empty manifest defined.
- **§5.7 Episode root version 3** (`EPISODE_ROOT:v3:`, six fields) selected by **`spine_algorithm_version` 3** (§5.8); the spine root is byte-identical to version 2; version 2 is retained.
- **§4.9 Erasure** — content-plane erasure (§4.9.2), `ErasureTombstone` as a `CODICIL_APPEND` codicil under `ERASURE_TOMBSTONE:v1:` (§4.9.3), the `CodicilNode` schema block (ratified by implementation), erasure of a Segment's content (§4.9.4), known limitations (§4.9.5).
- **G-41** capture posture and undeclared gaps; **G-42** non-reversible commitment for low-entropy personal data; **G-43** erasure is content-plane.
- **§12.4.1** register gains `CONTEXT_COMMIT` (Tier 1). **§11** unchanged, stated. **§21** relation to `tool_output` entries stated. §2 gains eight terms.
- **`CONFORMANCE-CONTEXT.md`** CM-001 … CM-010 (+ CC-001/002, ER3-001, G41-001) and **`vectors/6.0.0/context-commitment.json`**, generated over the ratified 5.0.0 Episode so CM-010 is shown against the ratified version 2 root. An exported proof of record for the Episode of Record is under `docs/proofs/`.
- The 5.2.0 text is retained at `docs/history/SPEC-v5.md`; the ratified amendment draft at `docs/history/SPEC-6.0.0-DRAFT-context-commitment.md`.

### Reference package (`astp` 2.0.0 — MAJOR: `PROTOCOL_VERSION` is 6.0.0)
- **`astp.core.context_v1`** implements the 6.0.0 constructions: `ContextEntryNode` and its `CONTEXT_ENTRY:v1:` hash; the plain and salted content commitments; the `CONTEXT_MANIFEST:v1:` manifest over the version 2 tree in canonical order, with inclusion proofs; Episode root version 3 (`EPISODE_ROOT:v3:`, six fields) and `compute_episode_seal_v3` under `spine_algorithm_version` 3; `ErasureTombstone` and `apply_erasure`; G-41, G-42 and G-43 enforced at the seal and at erasure. `reproduce_episode_root` dispatches version 3. Nothing sealed under 0, 1 or 2 changes.
- `tests/conformance/test_context_commitment_v1_vectors.py` reproduces every vector value from the library and from a `hashlib`-only implementation of the SPEC text. `__version__` 2.0.0; `PROTOCOL_VERSION` 6.0.0.
- **Not yet in the package** (queued for 2.1.0): `InMemoryStore` / `StructuralStore` context-entry, tombstone and posture operations; `proof_of_record` learning the sixth field. The reference deployment does not yet write context entries or seal under version 3.

### Reference package (`astp` 2.1.0 — the store and the operations)
- **`StructuralStore`** gains the context-commitment contract: `write_context_entry`, `context_entry`, `context_entries_of`, `set_capture_posture`, `capture_posture`, `tombstone_context_entry` (the stored-node half of erasure in one write). `InMemoryStore` implements it.
- **`astp.core.context_operations`**: `commit_context_entry` (refuses an Episode that admits no further provision, a duplicate, a bad `resolves`, and — G-42 — low-entropy personal data committed plain, before anything is written; ledgers `CONTEXT_COMMIT`); `set_capture_posture` (G-41; refused once sealed); `context_seal_inputs` / `episode_context_manifest_hash` (the seal-time readers, G-41 and G-42 re-applied); `erase_context_entry` (builds the tombstone over the unchanged entry hash, stores it as a `CodicilNode`, nulls the two pointers, ledgers `CODICIL_APPEND`; takes the caller's assertion that content and salt were destroyed together, and refuses without it — G-43).
- **`proof_of_record`** learns the sixth field: a `spine_algorithm_version` 3 document carries `context_manifest_hash`, `capture_posture` and `context_entry_count`, the full profile carries the stored entries, and the verifier reproduces the manifest and the root through `compute_episode_seal_v3`; an attested document says the entry list is withheld.
- **`IMPLEMENTATION-CONTEXT.md`** (new): what an implementer writes, when, from where; posture and the seal; the erasure sequence; verification and export; and the reference deployment's status (§7 — no seam writes entries yet).
- `tests/unit/adapters/test_context_operations.py`: the seven ratified entries committed through the store seal to the vector root; erasure through the store leaves it unchanged; a version 3 proof of record round-trips and fails on tampering.

## [5.2.0] — 2026-09-22

**MINOR.** Key derivation is versioned, and version 2 carries the protocol's name. No hash construction changes; every seal and every stored record is untouched.

### Changed
- **§16.2.1 Derivation version 2 (current):** `astp.workspace.v2`, `astp.node.v2:{node_type}`, `astp.seal.v2`. The `ariadne.*.v1` strings are **derivation version 1, retained** as the definition of every key derived before 5.2.0; a string is never edited, a version is added. A signed record carries the derivation version of the key that made it — `derivation_version` on `NodeKeyRecord` (§16.2.4), `key_derivation_version` on `HITLEventNode` (§4.6) — a record without one is version 1, and a verifier that re-derives a key to check a fingerprint selects the version the record names. An implementation MAY keep deriving under version 1 for a workspace whose keys it does not wish to rotate.
- **`CONFORMANCE.md` 2.1.0:** KH-001…003 state the version 2 strings; **KH-006** (new) requires version 2 by default, version 1 reproducible on request, absence read as 1, and an unknown version refused.
- `IMPLEMENTATION-PHASE3.md` §3 states both versions.

### Reference package (`astp` 1.1.0)
- `derive_workspace_key` / `derive_node_key` / `derive_seal_key` take `derivation_version=` (default `KEY_DERIVATION_VERSION_CURRENT = 2`); `derivation_info(level, version, node_type=)` exposes the strings; `NodeKeyRecord.derivation_version`; `HITLEventNode.key_derivation_version` (default 1, the value a stored event without it has). `tests/unit/protocol/test_wire_constants.py` pins both versions.

### Changed (reference package 1.0.0 — MAJOR: the protocol package names no store)
- **The reference deployment's adapter leaves the package.** `astp.adapters.neo4j` (writer, queries, crystallization, WIL, rebalance, retrieval audit, seal-input reader, `Neo4jStructuralStore`), its implementation guides (`IMPLEMENTATION-BFM.md`, `IMPLEMENTATION-CROSS-EPISODE-LINKING.md`, `IMPLEMENTATION-LAYER3.md`) and its tests move to the deployment that runs it (Ignis OS, `ignis.ariadne.astp_adapter`). The `[neo4j]` install extra is gone. `IMPLEMENTATION-PHASE3.md` stays: it describes protocol constructions, not a store.
- **`astp.core.wil` names roles only.** The provider enum (`StoreLayer`) and the coordinator key/TTL policy left with the adapter. `WriteIntentEntry.stores_involved` / `last_completed_store` are role names (§12.1), validated through `store_role_of`, which keeps the fixed 4.x correspondence (`LEGACY_STORE_VALUES`) §12.1 requires the reference implementation to publish — stored data a reader maps, never a value a writer emits. `enforce_write_order` and `enforce_provisional_state_guard` take roles or any value that resolves to one. `QDRANT_DEGRADATION_RECOVERABLE` → `SEMANTIC_INDEX_DEGRADATION_RECOVERABLE`.
- **`as_structural_store` no longer wraps a raw driver** — the store it wrapped with has left. An operation takes a `StructuralStore`; a deployment wraps its own driver. Anything else is refused at the boundary with a `TypeError`.
- **Guard:** a structural test refuses any store provider's name anywhere in the package or its tests, `LEGACY_STORE_VALUES` excepted.
- Reference implementation: `astp.adapters.memory.InMemoryStore`, for both contracts. `astp.adapters.base` and the operations modules point at it.

### Added (reference package 0.8.0 — the in-memory reference store)
- **`astp.adapters.memory.InMemoryStore`**: both adapter contracts — `ASTPAdapter` (the Phase 1 node interface) and `StructuralStore` (the operations contract) — over plain dicts. The simplest conforming implementation an implementer can read, and the store the protocol's own operations tests now run against: every branch, fork, merge, aside, soliloquy, linking, grouping and coherence test that mocked a graph driver by matching query text now exercises the operation end to end through the contract, with the store's state inspected directly. Where the reference writer applies a rule before a write — a link's endpoints must exist and respect mutual exclusivity and a sealed endpoint's root is bound; a membership record supersedes an unsuperseded prior of the same episode and group; a declaration's version is SemVer — this store applies the same rule and raises the same error. Audit deltas are stored as JSON text, as the protocol stores them (§8).
- `StructuralStore.fork_points_of(fork_id)` is the name of the read introduced as `fork_points` in 0.7.0 (a store's `fork_points` is its collection; a method cannot share the name). 0.7.0 was not published to an index.
- The Phase D orphan-recovery writer tests, which exercise the Neo4j adapter's writers directly, moved to `tests/unit/adapters/test_neo4j_orphan_writers.py`; they leave with the adapter.

### Changed (reference package 0.7.0 — the operations layer names no store)
- **`StructuralStore`** (`astp.adapters.base`): the storage contract of the operations layer — 47 synchronous operations covering what branch, fork, merge, aside, soliloquy, cross-episode linking, grouping, coherence and the audit-chain helpers read and write. The reference implementation is `astp.adapters.neo4j.store.Neo4jStructuralStore`, which delegates to the existing writer and runs, unchanged, the reads the operations layer used to run itself.
- `astp.core.branch_operations`, `cross_episode`, `grouping`, `coherence` and `audit_chain` take a `store` (any `StructuralStore`) where they took a driver, and import nothing from the adapter package. A raw driver of the reference store is still accepted — it is wrapped — for one release. `CoherenceFingerprintRegistry` likewise. Two structural tests guard the cut: nothing under `astp/core`, `astp/protocol` or `astp/nodes` imports `astp.adapters.neo4j` or opens a store session.
- `astp.core.ordering.content_hashes_in_sequence_order` — the pure helper moved out of the adapter's query module (still importable from there).
- Not in this release: `astp.core.wil` still carries the vendor store enum and the coordinator key policy; they leave with the adapter.

### Changed (reference package 0.6.0 — the public API carries the protocol's name)
- `ASTPAdapter`, `ASTPProtocolError`, `ASTPGovernanceError`, `ASTP_SCHEMA_VERSION` and `initialize_astp_schema` replace the `Ariadne*` / `ARIADNE_*` / `initialize_ariadne_schema` names. The old names remain importable as aliases of the new ones for callers written before 0.6.0; no behaviour changes. Docstrings, comments and log prefixes say ASTP.
- `GroupingSystem.ASTP_NATIVE` (`"astp_native"`) is the protocol's reserved grouping value. `ARIADNE_NATIVE` (`"ariadne_native"`) is retained as the value carried by records written before 0.6.0 — `group_system` is in the MembershipRecord hash preimage (SPEC §20 →7), so those records keep it.
- `ASTP_PROVISIONAL_WINDOW_HOURS` and `ASTP_IMPLICIT_CRYSTALLIZATION_ON_ARCHIVE` are the configuration names; the `ARIADNE_`-prefixed names are still honoured when the new ones are unset.
- **Not renamed, deliberately** (`tests/unit/protocol/test_wire_constants.py` guards them): the HKDF `info` strings (`ariadne.workspace.v1`, `ariadne.node.v1:{type}`, `ariadne.seal.v1`) — key-derivation inputs; the `ariadne::` coordinator key prefixes and the `Ariadne*` graph labels, constraint and index names — they name data in deployed stores. Each is a versioned migration of its own.

### Reference deployment — cutover landed
- The paired ignis-os change named by 5.1.0 (ignis-os #138, 2026-09-19) routes the crystallize handler through `compute_episode_seal_v2` and the verifier through `reproduce_episode_root`; the reference deployment seals under `spine_algorithm_version` 2. The 5.1.0 condition on `SPINE_ALGORITHM_VERSION_CURRENT` is therefore met, and the constant still reads `1` — by design, not by lag. It is the identifier of the retained version 1 construction (`compute_spine_root_v2(episode_id=…)`, the adaptive tree), which the deployment's version 1 fallback (a non-UUID identifier; a terminal HITL event stored without its context) and every verifier of a 4.x seal select by it; flipping it would stamp `2` on version 1 roots. A version 2 seal takes its identifiers from `SealV2` (`seal_v2.SPINE_ALGORITHM_VERSION_2`), never from a constant. The constant's comment now says so; its name is kept for API compatibility.

### Docs (errata — no normative change)
- Stale 4.x claims that 5.0.0 made false, found by a claim-level re-sweep: §2 *Causal Anchor*, §4.6 *Hash computation* and *Spine participation*, and §19.2.3 said no sealed root commits to a concluded HITL event or a BranchPoint and gave the 4.x `HITL_CTX:` / `HITL_RES:` / `NODE:` constructions as current. Each now states the `spine_algorithm_version` 2 position (structural-manifest member, §5.7.1; `HITL_CONTEXT:v2:` / `HITL_RESOLUTION:v2:` / `HITL_NODE:v2:`) and scopes the old claim to versions 0 and 1 as retained forms. `IMPLEMENTATION-PHASE3.md` Appendix C, `IMPLEMENTATION-BFM.md` §1 and §6.4, `CONFORMANCE-BFM.md` SL-002/SL-003, `IMPLEMENTATION-CROSS-EPISODE-LINKING.md` §5.1 and `CONFORMANCE-CROSS-EPISODE-LINKING.md` CEL-001/CEL-003 label their 4.x prefixes and preimages as retained where the body still described them as current.
- **§4.7 states what the seal covers for an AttachmentNode**: `content_hash` detects substitution of the attached bytes; the node is not a spine leaf and not a member of any Episode root component, so no sealed root detects its addition or removal after the seal, and the `ATTACHMENT_COMMIT` ledger entry does not close that gap. Binding attachments into the root is a MAJOR change and is not made here. GLOSSARY entry aligned.

### Changed (reference package 0.5.0 — the side-channel and link writers stamp the 5.0.0 content hashes)
- `create_aside` / `close_aside` / `create_soliloquy` / `conclude_soliloquy` stamp `ASIDE:v2:`, `ASIDE_TERMINUS:v2:`, `SOLILOQUY:v2:`, `DELIBERATION_CHAIN:v2:` and `SOLILOQUY_CONCLUSION:v2:` (SPEC §19.4). The parent Segment is bound by identity **and content**, so an aside or soliloquy whose parent is not a UUID, or does not exist, is refused (a precondition refusal, `None`); the deliberation chain and an aside's produced content are hashed by the Segments' content hashes in `sequence_index` order; the merge target of a conclusion must be a UUID. `AsideSegmentNode.parent_hash` is now populated. The 4.x hash functions remain for verifying nodes already written.
- `EpisodeLink.content_hash` is `EPISODE_LINK:v2:` (SPEC §20 →2): `write_episode_link_sync` fills the new `source_episode_root` / `target_episode_root` fields from the graph (each end's Episode root when that end is sealed) and stamps over them; the hash no longer moves with health or quarantine. `compute_episode_link_content_hash_4x` is retained for links written before 5.0.0.
- `astp.adapters.neo4j.queries.segment_content_hashes_sync` / `content_hashes_in_sequence_order`.

### Added (reference package 0.4.0 — proofs of record)
- **`astp.core.proof_of_record`**: the `astp-proof-of-record/1` document format (`full` / `attested` profiles), `build_proof_of_record`, `verify_proof_of_record`, and `python -m astp.core.proof_of_record verify <file>`. The verifier reproduces every root the profile allows under the seal's §5.8 identifiers and reports what it checked, what the profile withholds, and what failed; it never reports a claim it could not rebuild. Pre-4.3.0 seals (spine root only) are represented honestly.
- **`vectors/5.0.0/seal-constructions.json`** `status` field no longer reads "DRAFT — not ratified". No value changed. As with the `-draft` suffix on `SPEC.md`, the digest the Episode of Record cites (`60e30400…`) is of the file's pre-edit bytes, by design; the values are identical.
- **`docs/proofs/`**: exported proofs of record for the 4.0.0 and 5.0.0 Episodes of Record, each verified from a clean environment with only the package installed. The SPEC header, README and GLOSSARY no longer say none is published.

## [5.1.0] — 2026-09-19

**MINOR.** The reference adapter's failure contract, and the implementation consequences 5.0.0 carried to the adapter work (§19 of the amendment draft). No canonical form changes; every 5.0.0 seal and every 4.x seal is untouched.

### Changed
- **§15 item 7 restated as a contract.** A writer or reader that cannot complete raises a typed error, chained to the store's; it never returns a default, logs and continues, or gates itself on a feature flag. Whether to call the adapter is the host's decision.

### Reference package (`astp` 0.3.0)
- **No feature flag.** `ARIADNE_ENABLED` and `_ariadne_guard` are gone — 121 flag guards removed across the Neo4j adapter and `core.wil`. A host that ran with the flag off now decides, at its own boundary, whether to call the adapter.
- **Nothing swallowed.** Every `except Exception` in the adapter and operation modules raises `AdapterWriteError` (store failure) or `BranchOperationError` (an operation that failed after it began), chained; `AriadneProtocolError` subclasses pass through unwrapped. `next_delta_sequence` / `prior_audit_hash` refuse to guess a chain head (§8.2) instead of restarting at `GENESIS`; `_write_branch_wil` raises, so a `COMPLETE` entry is never ledgered for a write that did not happen (G-39). Precondition refusals in `branch_operations` still return `None` after logging, so a caller can tell *refused* from *failed*. A structural test guards both properties over the source.
- **`ESCALATED` is terminal in the resolution writer** (`hitl_terminal_status`): an escalation is recorded as `escalated`, never `resolved` (§4.6, §5.7.1).
- **G-40 write boundary:** `require_episode_uuid` / `EpisodeIdentifierError`; `create_episode_node` refuses a non-UUID identifier. A legacy Episode is still read and sealed under version 1 (`episode_ref`, 5.0.0 #50).
- **`SealNode.countersignature`** replaces `mnemosyne_countersignature` (the 4.x name is accepted on input and readable as a property; the graph property keeps its stored name). **`GroupingSystem`** keeps only `ariadne_native` — vendors are named by their `ConformanceDeclaration`.
- **The seal, as a runtime computes it:** `astp.core.seal_v2.compute_episode_seal_v2(episode_id, segments, …) → SealV2` seals under `spine_algorithm_version` 2 from the six stored fields of each Segment and returns the roots *with the identifiers that name the construction*, so a delta is stamped from the result and never from a module constant; `reproduce_episode_root(spine_algorithm_version=…)` rebuilds an Episode root under whichever version a seal record names. `SPINE_ALGORITHM_VERSION_CURRENT` stays `1` until the reference deployment's seal path adopts `compute_episode_seal_v2` (paired ignis-os change); flipping the constant first would stamp version-2 identifiers on version-1 roots.

### Cutover (reference deployment)
Paired with ignis-os: drop the `_ariadne_guard` imports; route the crystallize handler through `compute_episode_seal_v2` and the verifier through `reproduce_episode_root`; enforce `require_episode_uuid` at `POST /api/episodes`; handle `AdapterWriteError` / `BranchOperationError` at the call sites that previously relied on `None`. Pull the protocol checkout only together with that change.

## [5.0.0] — 2026-09-18

**MAJOR.** Every hash construction of the 4.x line is replaced by a **new versioned construction**, and every rule written for a human reader is restated as one a verifier can execute against stored state. The discipline the constructions now share, and the reason this version exists: **every commitment binds exactly its claim, and every rule is executable against stored state.** No sealed record becomes unverifiable: the 4.x constructions are retained in `SPEC.md` as the definitions of `hash_version` 1 and `spine_algorithm_version` 0 and 1, selected by the §5.8 identifiers, and the retained text is the 4.5.0 text. Deliberated and ruled, unit by unit, in design Episode `4b9a779e-be46-4d61-872e-fd76545aa901`; the amendment draft from which this text was folded is retained at [`docs/history/SPEC-5.0.0-DRAFT-seal-constructions.md`](./docs/history/SPEC-5.0.0-DRAFT-seal-constructions.md). **Episode of Record:** `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`, sealed 2026-09-18 under `spine_algorithm_version` 1, `episode_root_hash` `3649bff4b96a17c99bb108ec23f4e6f8e41a455d9d38c98d6f32111800afe48a`; it ratifies `SPEC.md` at `44f764e` by content digest (`c2e13d0ee60f7db95d185ec2f8079d38c9f087f7168a3b613aada6bc0a6b8a8d`, the `-draft`-suffixed bytes — the suffix was stripped in this release commit, after the seal, with no normative change).

**What 4.x got wrong, in one sentence each.** The spine root bound content and order only (the position-binding leaf hash existed and the seal never used it). Hash values entered the tree as hex text. `sealed_at` was in a preimage computed before any seal exists. Branch, fork, merge and concluded-HITL nodes were committed into no root. Colon- and pipe-joined preimages collided (`("obj:alice","bob")` = `("obj","alice:bob")`) and `NODE:` was reused across unrelated constructions. Audit records had two schemas, two hash forms and two `"GENESIS"` strings, one hashing sorted JSON over an unsorted stored document. The aside bound a `parent_hash` that was never populated; the soliloquy's two hash policies differed in nothing a verifier could use; the deliberation chain hashed identifiers, not content; the link hash bound mutable health state and so committed to nothing stable; `FINGERPRINT:` was defined and never called. The witness commitment bound neither the witness nor the time, and an empty signature passed G-12, so a threshold could be met by one unauthenticated writer. The anchor hashed a literal `"2.3.0"`.

### Changed (canonical form — every item is a new versioned construction)
- **§5.1 One hash function; §5.1.1 canonical field encoding.** SHA3-256 only. Every 5.0.0 construction is `SHA3-256(prefix ‖ enc(fields))` over ten typed, self-delimiting field encodings (NULL, BYTES, STRING/NFC, UINT, UUID, TIMESTAMP ms, HASH raw, LIST, BOOL, FLOAT binary64); order-independent sets are `prefix ‖ u32be(n) ‖ sorted raw members`, no sentinel. One domain prefix per construction and version (§5.1.3 registry). §5.1.2 **canonical JSON**: RFC 8785 + NFC, stored as hashed.
- **§5.2 Leaf hash `hash_version` 2** (`LEAF_HASH:v2:`): no `sealed_at`; absent parent is NULL, not the nil UUID. Pre-5.0.0 Segments are sealed from their stored fields, never from a stored version 1 leaf hash. `node_id` MUST carry ≥122 bits of randomness (new; effective on ratification).
- **§5.3–§5.6 Spine `spine_algorithm_version` 2**: leaf input is the leaf hash, raw bytes under `TREE_LEAF:v2:` / `TREE_NODE:v2:`, no Episode-identifier leaf; the spine, the five-test-gate tree and the chain-proof tree are one tree. **`spine_algorithm_version` 2 selects the entire seal construction** — read it as *seal construction version*; there is deliberately no separate Episode-root identifier.
- **§5.7 Episode root version 2** (`EPISODE_ROOT:v2:`): binds the Episode's **UUID** and four components — spine root, signal manifest (`SIGNAL_MANIFEST:v2:`), **structural manifest** (`STRUCTURAL_MANIFEST:v1:`, new) and exclusion set (`EXCLUSION:v2:`). §5.7.1 the **membership rule** (bound iff removal would deceive about structure; commentary and provenance out, with the named actor exception for asides and soliloquies), the seven member constructions, `ESCALATED` terminal, and the rule that a structural node written after a seal is committed by the next crystallization and references the earlier seal.
- **§8 Audit record `AUDIT_RECORD:v2:`**: one schema, seventeen bound fields, NULL genesis, deltas as canonical JSON bytes stored as hashed, `chain_key`/`affected_nodes` deliberately STRING; chain verification (sequence without gap, prior-hash linkage, every hash recomputes); a writer that cannot read the chain head fails rather than guesses.
- **§9.2 Inclusion proof over the version 2 tree**: `{leaf_index, leaf_count, leaf_hash, siblings, spine_root}`, path shape derived by the verifier, size deliberately unbound (the seal record's claim); 4.x proofs frozen in their own form and never re-issued.
- **§16.3.2 Anchor `ANCHOR_COMMITMENT:v2:`** and **§16.4 Witness `WITNESS_COMMITMENT:v2:`**: bind the witness, the time and the node's *outermost sealed commitment* with its version; Ed25519 over the raw commitment is the one registered scheme (an extensible registry with one entry). **G-12** validity: recompute ∧ fingerprint ∧ signature ∧ witness ≠ author. **G-11** threshold: a maximum bipartite matching between distinct names and distinct keys. §17.2 vectors W5–W9.
- **§19.4 `ASIDE:v2:`, `ASIDE_TERMINUS:v2:`, `SOLILOQUY:v2:`, `DELIBERATION_CHAIN:v2:` (over content hashes, in order), `SOLILOQUY_CONCLUSION:v2:`**; `SoliloquyContentHashPolicy` retired. **§19.5.1** the coherence fingerprint has no content hash; `FINGERPRINT:` retired with no successor.
- **§20 §2 `EPISODE_LINK:v2:`** with `LINK_SIGNAL:v2:`: binds each end's Episode identifier and its **Episode root when that end was sealed at link creation** (NULL otherwise; sealed-end-NULL nonconformant; `retroactive ⇒` source root present), type, exact strength, signals in order, threshold; health, quarantine and `created_by` out. New fields `source_episode_root`, `target_episode_root`. `LINK_INTEGRITY` field snapshot updated.

### Changed (rules)
- **G-40 (new): Sealed requires a record; Episode identifiers are UUIDs.** A non-null `sealed_at` with no bound crystallization record is `NO_CRYSTAL`, never sealed — stated on the stored outcome, not a code path. A late seal is ordinary lifecycle: `sealed_at ≥ closed_at` is the only ordering constraint. Non-UUID Episode identifiers are refused at creation; an implementation holding one seals it under version 1 *before* closing the write boundary. G-1 cross-references.
- **§4.6** `ESCALATED` concludes its gate; a resolution writer MUST NOT record an escalation as `RESOLVED`.
- **§12.1** storage roles are recorded by role (`durable_content`, `authoritative_structural`, `ephemeral_coordinator`, `semantic_index`); 4.x ledger values are stored data, mapped at read time.
- **§2.5.2** the signing scheme is protocol surface (Ed25519), no longer "implementation-defined subject to minimum security requirements".
- **§19.3.7** the recovered point written after a seal follows §5.7.1.

### Added (reference package)
- `astp.protocol.encoding`, `canonical_json`, `audit_v2`, `witness_v2`, `anchor_v2`; `compute_leaf_hash_v2`, `compute_merkle_root_v2`, `InclusionProofV2`; `astp.core.seal_v2` (sets, structural members, Episode root v2, `check_seal_record`), `astp.core.content_hash_v2`; `StoreRole` / `store_role_of`. `astp.PROTOCOL_VERSION` is `5.0.0`. The reference adapter's *write path* still seals under `spine_algorithm_version` 1; adopting version 2 at seal time, the adapter failure contract, the `ESCALATED` resolution writer, the UUID write boundary, the `countersignature` field rename and the removal of vendor values from `GroupingSystem` are the paired adapter change that follows ratification.
- **Vectors** [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json), generated never hand-edited, every value checked twice — against the package and against a from-prose reference that imports nothing from it (RFC 8785's own appendix example; RFC 8032 §7.1 signing keys).

### Documents
- `SPEC.md` 4.5.0 retained as [`docs/history/SPEC-v4.md`](./docs/history/SPEC-v4.md). `GLOSSARY.md`: *Canonical Field Encoding*, *Canonical JSON*, *Structural Manifest*, *Membership Rule*, *Outermost Sealed Commitment*, *Late Seal*, *Witness Validity*, *Chain Key*; `leaf_hash`, *Episode Root*, *Signal Manifest*, *Exclusion Set*, *Spine Leaf Set* and *Version Identifiers* brought to 5.0.0.

### Fixed (reference package — conformance to existing text)

- `verify_proof_chain` verified each link's inclusion proof against the root *the proof* named, never against the link's own `spine_root`, so a chain whose links carried valid proofs for unrelated trees verified. §16.5.3 (1) has always required the proof to verify against `link.spine_root`; the reference implementation now does.

## [4.5.0] — 2026-09-17

**MINOR.** `resolved_signal_order` — an optional annotation that records the order of same-timestamp Signals a seal made under `ordering_version` 1 depended on. Additive: nothing already conformant changes, and no sealed root changes.

4.4.1 stated that `ordering_version` 1 does not determine that order, so such a seal is reproducible only by search. This release says what an implementation may do once the search has succeeded: write down what it found, so the next verifier checks one ordering instead of looking for it.

### Added
- **§5.8.1 `resolved_signal_order`.** An annotation on the `CrystallizationDelta`, not a version identifier — an identifier names a construction, the annotation supplies an input the construction left undetermined. It is outside every hash preimage; written by a verification run, never by a re-seal; and **checked, never trusted**: a verifier MUST NOT use it unless it is a reordering of the Episode's stored SPINE-placed Signal hashes that reproduces `sealed_chain_root`, and MUST ignore one that is not. A false annotation cannot make a root verify; it can only fail to help. It has no meaning under `ordering_version` 2 and MUST be ignored there. Its absence carries no adverse inference — a seal resolved by search reproduces to the same root as an annotated one. Because the listed values are unsalted content hashes, an exported proof that withholds the leaf list MUST withhold the annotation too. §9.3 refers to it.
- **`CONFORMANCE-REPRODUCIBILITY.md` 1.2.0 — RP-005 … RP-008**, with expected digests: an admissible annotation reproduces a tie-order seal under both `spine_algorithm_version` values (RP-005); a wrong order, a foreign hash, and a correct order over a tampered record are each inadmissible (RP-006); an `ordering_version` 2 seal ignores a stray annotation (RP-007); a seal resolved by search is reported as reproduced, and is kept distinct from a root that no ordering reproduces (RP-008).
- **`GLOSSARY.md`:** *Resolved Signal Order*.
- Reference package: `reproduce_spine_root` — the §9.3 selection of a reproduction function from a seal's §5.8 identifiers, refusing identifiers it does not know — and `check_resolved_signal_order`. The tests pin the RP-005 … RP-008 digests.

### Changed (editorial)
- The `SPEC.md` header and the README name the 4.0.0 Episode of Record, `458fb62b-faee-4e42-9f92-c63187c1b59a`. Since 4.3.1 they had said, accurately, that its identifier was not published; the Episode existed and had simply never been cited. They still say what is true of the proof: the Episode's root reproduces, and an exported proof of record has not yet been published.

### Provenance
- Admitted on a demonstration rather than on argument: on 2026-09-17 the reference deployment recorded the annotation for its four tie-order seals — among them the 4.0.0 Episode of Record — and a clean verification run then reproduced all four from the recorded order, with no search.

## [4.4.1] — 2026-09-17

**PATCH (errata).** The spine and Episode-root constructions are now stated byte-exactly, **as the reference implementation has always built them**. No construction changes; no sealed root changes. Where the text and the code disagreed, the text is corrected to the code, because §9.3 obliges a verifier to reproduce existing seals and the code is what made them. Constructions that should be different are a matter for the next MAJOR, not for an erratum.

### Corrected
- **§5.3 / §5.4** state what was unwritten: hash values enter the tree as 64-character lowercase hex strings, ASCII-encoded (not as raw bytes — §5.2 differs, and says so); nodes pair from the left; an unpaired node is carried up unchanged, neither duplicated nor re-hashed; a single-leaf tree's root is that leaf's hash; the root of an empty list is undefined and MUST be refused.
- **§5.4 / §5.6 — the spine's leaf inputs are Segment `content_hash` values, not §5.2 leaf hashes.** The text read as a tree over position-binding leaf hashes; only the tree of §9 and §16.5 is that. The two are the same algorithm over different inputs and give different roots. §5.6 now says plainly what the spine root therefore binds (content and order) and does not (a Segment's `node_id`, type, schema version or parent).
- **§5.6 — the Episode-identifier leaf.** Under `spine_algorithm_version` 1 the first leaf is `SHA3-256(episode_id)`. §5.6 said "Nothing else is a spine leaf" and `CONFORMANCE-REPRODUCIBILITY.md` RP-001 said "and nothing else", while RP-001's own inputs included an `episode_id` and every seal made under version 1 contains the leaf. §9.3 lists the Episode's identifier among what a verifier needs.
- **§5.8 defines its version values**, which it had only named: `spine_algorithm_version` 0 and 1 are the same tree and differ by that one leaf; `ordering_version` 1 and 2 are given as exact leaf lists. It also states that **`ordering_version` 1 does not determine a leaf order** — arrival time is not total, and the order in which tied Signals were folded in is recorded nowhere — so such a seal may be reproducible only by search, and §9.3 is scoped accordingly.
- **§5.7** states the encoding, sort order, separator and empty-set bytes of the manifest, exclusion and Episode-root constructions.
- **HITL events and BranchPoints are not spine leaves, and never were.** §2, §4.6 and §19.2.3 said a resolved HITL `node_hash` "participates in the Merkle spine as a causal anchor leaf" and that a BranchPoint's `content_hash` "is included in the spine chain"; `IMPLEMENTATION-PHASE3.md` made the former a MUST. No seal has ever included either, and both statements contradicted §5.6. They are corrected. §5.6 records the consequence without softening it: as of this version no sealed root commits to those nodes, so removing one changes no root.
- **`IMPLEMENTATION-PHASE3.md` (now 1.1.1)** listed, as a prerequisite an implementation MUST pass, a leaf hash of `SHA3-256(sequence_index ‖ content_hash ‖ prev_leaf_hash)`. That is not §5.2 and never was: a leaf does not chain to its predecessor (§3.4.1). It now states the §5.2 preimage. It also named a `CrystallizationRecord` type; the type is `CrystallizationDelta`.
- **`content_hash` is unsalted**, and §5.6 says so: a published list of spine leaves lets anyone test a guess at a Segment's content.
- **Corpus figures** in the 4.3.0 entry below and in `CONFORMANCE-REPRODUCIBILITY.md` accounted for 58 of 62 Episodes and stated "no evidence of content tampering" without scope. The breakdown is 45 + 8 + 4 + 2 + 3; the finding holds for the 57 seals that were rebuilt, and the other 5 could not be evaluated.

### Added (conformance)
- `CONFORMANCE-REPRODUCIBILITY.md` RP-001 and RP-002 now carry **expected digests** — the first in any conformance document here — for the spine root under both algorithm versions, the signal manifest (five members, four members, empty), the empty exclusion set, and the Episode root.
- The reference tests pin those digests, and separately re-implement §5.3–§5.8 from the prose with `hashlib` alone and compare it with the library across tree sizes, so that the specification text and the code cannot drift apart again unnoticed.

### Changed (editorial)
- Companion documents that were re-dated in 4.3.1 without a version change have their dates restored: a document's date moves with its version.
- The reference function `compute_spine_root_v2` documents that `episode_id` selects the algorithm version and that reproducing a seal requires it. Behaviour is unchanged.

## [4.4.0] — 2026-09-17

**MINOR.** Storage is specified as roles, not providers. Every implementation that conformed to 4.3.x conforms to 4.4.0 unchanged; implementations built on other providers, which the text of §20 had excluded by naming products, now can.

§2.5.3 has always said a storage adapter may be "any conforming ASI implementation", and §12.1 has always named storage by role — durable content store, authoritative structural store, ephemeral coordinator, semantic search index. §20, written as a standalone amendment against one deployment, named that deployment's products in normative text instead. This release makes §20 say what the rest of the specification already meant.

### Changed
- **§20 →11.1 Storage Architecture** defines four roles — authoritative structural store, append-only audit store, semantic search index, ephemeral coordinator — with the consistency obligation of each, and states that the provider filling a role is the implementer's choice and that one system may fill several. The obligations themselves are unchanged: the structural store is the single source of truth, the audit store is append-only and authoritative for the event log, the index is derived and eventually consistent, and the coordinator is always reconstructable.
- **§20 →11.1.2** lists the structural record types and relationships in provider-neutral notation (it was a schema in one graph database's query language). The active-record index obligation is unchanged.
- **§20 →11.1.3** requires two separate vector spaces and fixes their payload fields, including the two threshold-at-index fields that make a discovery decision auditable. **Collection names, dimensionality, distance metric and embedding model are now implementation choices.** Still required: embeddings from different model families MUST NOT be mixed within one vector space.
- **§20 →11.1.4** requires a quarantine queue **scoped per Episode**, threshold calibration state and a link-health cache, all reconstructable. **Key names and data structures are now implementation choices.** A single global quarantine queue remains non-conforming. The §20 conformance checklist and `CONFORMANCE-CROSS-EPISODE-LINKING.md` LH-003 state the scope rule instead of a literal key.
- **§20 →11.2.1, →11.4, →11.5 and the §21 audit event registry** name the role a record lives in ("structural store", "audit store") instead of a product. The write path order and the consistency-window SLA are unchanged.
- **§21 Appendix A** (non-normative notes on one adapter) is now a pointer to `IMPLEMENTATION-LAYER3.md` §6, which already carried the same material. §10.5 and §13 no longer give products as examples.

### Changed (companion documents)
- `IMPLEMENTATION-CROSS-EPISODE-LINKING.md` §9 maps the four roles to the providers the reference deployment uses, and records that deployment's search-index layout and coordinator keys — the material removed from §20 — marked as its own choices. Its statement of the write order is corrected to the one §20 →11.5.1 specifies and the code follows (structural store, then audit store); it previously gave the reverse.
- `IMPLEMENTATION-PHASE3.md`: the HITL conformance list no longer requires a particular graph label. `GLOSSARY.md` §8 describes the WIL stores as roles.

### Notes
- The reference package's `StoreLayer` members and values still carry provider names. They are written into ledger entries, so renaming them is a stored-data change and is left for the next MAJOR.

## [4.3.1] — 2026-09-17

**PATCH (errata).** Editorial pass over `SPEC.md` and the companion documents ahead of public release. **No normative change:** no hash construction, governance rule, field, state or requirement is altered, and every 4.3.0-conformant implementation is 4.3.1-conformant unchanged.

### Changed (editorial — `SPEC.md`)
- **Header.** Replaced with the standard block (Version, Status, Authors, Date, Supersedes — now naming `SPEC-v3.md` as well as `SPEC-v1.md`). The version-by-version narrative that had accumulated in the `Status` field is removed; every release it described already has an entry in this file. The header now states the BCP 14 (RFC 2119, RFC 8174) reading of the requirement keywords, which the document had used without citing, and states plainly that the Episode of Record identifier for 4.0.0 is not yet published.
- **§18 Version History** is now a pointer to this file. Details that existed only in that table were carried into the corresponding entries below (2.0.0–2.5.0-draft, 3.4.0, 4.0.0). §18's rows for 2.0.0–2.3.0 carried a `-draft` suffix that this file's headings omit; the dates agree.
- **§22 References** lists the public standards the text relies on (FIPS 202, RFC 2119, RFC 8174, RFC 5869, RFC 8032, RFC 9562, SemVer 2.0.0) in place of a list of unpublished internal design documents. §5.1 cites FIPS 202 for SHA3-256. Two references to an unpublished proof-system label ("P2") in §5.4 and §9.2 now describe the property (position-binding) in words.
- **§3.4** pointed at the former amendment document as "the authoritative reference" for Layer 3; it now points at §21 of this document, which is where that text has lived since 3.2.1.
- **§2.5.2** said "Governance rules G-1 through G-16"; the range is G-1 through G-39.
- **Cross-references corrected:** §5.6 "(§4.1 dual index)" → §3.3 and G-3; G-24 "§5 Step 8 of the build spec" (an unpublished document) → §19.3.3, where the three assertions are defined; §19.3.7 "§19.3.5 STEP 6" → §19.3.5 (that section has no numbered steps); §21 Appendix B "§13.2" → §13 item 2.
- **Cross-references removed because no correct target exists:** "codicil (§4.9)" in §4.4.1 and G-1 — there is no §4.9; both now cite the registered `CODICIL_APPEND` operation (§12.4.1) instead. "(§7)" for the crystallization lock in §4.4.1 (§7 is Delta Records; the lock has no section of its own — the text now cites §4.6 and G-18 for the HITL guard). "(§8)" in §5.6 (§8 is the audit chain). "(§4.4)" for Segment `content_ref` in §4.7 (§4.4 is Episode). Defining the codicil, the crystallization lock and the Segment schema is left to a later release.
- **Review residue removed from normative text** with the substance kept: internal review labels in §19 and §20 (gap numbers, review-round numbers, a decision number, a scenario label — including the label in the §20 §9 heading) and the names of internal reviewers. Cross-Episode ordering timestamps in §20 §11.5.3 and the §20 checklist, previously attributed to a named internal component, now read "timestamps assigned by a workspace-wide monotonic timestamp authority". The §20 §11.3.3 heading is now "Quarantine Escalation". A personal name in §20 §11.2.6 is generalized to "the ratifying human principal".
- **§21.** The `WORKFLOW_CLOSED` trigger named a downstream product's tool; it now names the `close_workflow` operation of §21 §10. Normative text that named the downstream runtime now says "reference implementation", and the non-normative Appendix A says once what that runtime (Ignis OS) is. The provisional version numerals attached to two deferred items in §21 §13 (both numerals have since been used for other releases) are dropped; the items remain deferred to "a future amendment".
- **Removed:** the stale "Amendment v3.0.0 — Working Draft … Pending ratification" footer at the end of §21; a doubled `## 13. Spine Tip Cache` heading.
- **Removed (orphan paragraph):** a paragraph in §20 §11.3.1 on "Reverse delta for `SECTION_SUPERSESSION`". Neither `SECTION_SUPERSESSION` nor `supersedes_clause` is defined or used anywhere else in the specification or the reference implementation, so the paragraph's requirement could not be implemented or tested. It is retained in the historical amendment text under `docs/history/`.

### Changed (editorial — other documents)
- **Historical documents moved to `docs/history/`**, each with a uniform banner saying it is retained for provenance, what superseded it and when: `VISION.md`, `SPEC-v1.md`, `SPEC-v3.md`, `AMENDMENT-v2.0-CROSS-EPISODE-LINKING.md`, `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md`. `AMENDMENT-v3.0`'s status line said "Working Draft"; it now records that the amendment was published as SPEC 3.1.0 and folded into §21 at 3.2.1. `VERSIONING.md`'s retention rule names the new location.
- **Headers.** `GLOSSARY.md`, `VERSIONING.md` and `IMPLEMENTATION-BFM.md` gain the standard header block. `IMPLEMENTATION-PHASE3.md`'s header said 1.0.0 / SPEC v2.3.0-draft while its footer said 1.1.0 / v2.4.0-draft; the header now agrees with the footer. `CONFORMANCE.md` and `IMPLEMENTATION-PHASE3.md` state that they were written against the 2.x drafts and have not yet been re-verified against 4.x.
- **`GLOSSARY.md`** states which SPEC version it was last fully reconciled with (`2.5.0-draft`) and that reconciliation with 4.x is in progress. Its "Conformance Test Vectors" entry no longer says byte-level vectors live in `tests/`.
- **`README.md`.** The Conformance Testing section described a three-layer framework in `astp.core.contracts` that adapters "must pass"; nothing in the package or the test suite uses that module. The section now describes what exists: the `CONFORMANCE*.md` requirement documents and the reference test suite, with machine-readable vectors planned and not shipped. Installation is `pip install -e ".[neo4j,dev]"` from a checkout (Python >= 3.11; distribution and import name are both `astp`). Copyright line and an explicit statement that specification text and code are both Apache-2.0.
- **`CONFORMANCE.md`** no longer refers to a conformance registry at an unspecified location, or to a separate ASI conformance suite; neither exists. Reference values will be published as vector files in this repository in a later release.
- Example identifiers in the implementation guides are neutral (`agent-a`, `human-1`); stale absolute test counts and notes-to-self are removed from the guides and from this file; review labels are removed from `CONFORMANCE-CROSS-EPISODE-LINKING.md` and `CONFORMANCE-BFM.md`.
- **This file:** the 0.1.0-draft date now agrees with the document it describes (2026-04-07); a link to a non-public repository and references to downstream internals are removed.

### Changed (reference package — no protocol change)

- The Python import package is renamed `ariadne` → `astp`, matching the distribution name (package version 0.2.0). `from ariadne.…` becomes `from astp.…`; nothing else about the API moves.
- **Not renamed, deliberately:** the HKDF `info` strings (`ariadne.workspace.v1`, `ariadne.node.v1:{node_type}`, `ariadne.seal.v1`), the coordinator key prefix (`ariadne::`), the graph labels (`Ariadne*`), the `ARIADNE_ENABLED` flag, and the `Ariadne*` class names. The first three are inputs to derived keys or names of stored data; `tests/unit/protocol/test_wire_constants.py` pins them.
- `astp.PROTOCOL_VERSION` names the `SPEC.md` version the package implements; a test compares its MAJOR.MINOR with this specification's `Version:` field. `astp.__version__` remains the package's own version.
- `sha3_256` is defined in `astp.protocol.hashing` (still importable from `astp.core.schema`), so that `astp.protocol` imports nothing from `astp.core` or `astp.adapters`. The test suite now enforces that as well as the `astp.nodes` firewall, including relative and dynamic imports.
- Importing `astp.nodes` registers both shipped node types (`episode`, `segment`); previously `segment` was registered only when its subpackage was imported directly.
- Removed the unused module `astp.core.contracts`. Added `py.typed`, PEP 639 licence metadata and a `MANIFEST.in`; the sdist now carries the specification, the companion documents and the tests.
- Every test file passes when run on its own; CI checks this.

## [4.3.0] — 2026-09-13

**MINOR.** Reproducibility. Motivated by the first corpus-scale re-verification of the
reference deployment's 62 sealed Episodes (2026-09-13): 45 spine roots rebuilt from
stored nodes; 8 rebuildable only under the pre-2026-04-01 tree function (the
function had been replaced in place before the versioning rule existed); 4 rebuildable
only by searching orderings of same-timestamp signals (the seal ordered SPINE signals by
arrival time — an ordering key signals do not reliably have); 2 not rebuilt under any
construction (one of them also holds a post-closure append that the reference G-1 guard
did not refuse, because it covered SEALING/SEALED/ARCHIVED but not CLOSED); and 3 in a
sealed status with no seal record, so no root to rebuild. Of the 57 that were rebuilt,
none showed evidence of content tampering; the other 5 could not be evaluated.
*(Figures corrected in 4.4.1: this entry originally accounted for 58 of the 62 and
stated the tampering finding without that scope.)* Every item below is additive.

### Added
- **§5.6 Episode Spine Leaf Set** — the spine is the Episode's non-ephemeral Segments in
  `sequence_index` order and nothing else; signals are not spine leaves. `sequence_index`
  is the sole ordering key and is total, so no tiebreak exists to get wrong.
- **§5.7 Episode Root** — publishes the three-component root
  `SHA3-256("NODE:" ‖ spine_root ‖ signal_manifest_hash ‖ exclusion_hash)` (previously an
  internal design). The signal manifest and exclusion set are order-independent sets
  with domain-separated constructions and empty-set sentinels.
- **§5.8 Version identifiers** — optional `hash_version` on `CognitiveNode`,
  `spine_algorithm_version` and `ordering_version` on `CrystallizationDelta`. Outside every
  hash preimage; absent means pre-4.3.0. Backfill is an annotation, never a re-seal.
- **§9.3 Reproducibility obligation** — a verifier holding only stored nodes MUST be able to
  recompute the sealed roots; a stored-root lookup is not a verification.
- **`CONFORMANCE-REPRODUCIBILITY.md`** — new `RP-*` family (RP-001…RP-004) and
  `tests/unit/protocol/test_reproducibility_conformance.py`.
- Reference implementation: `compute_spine_root_v2`, `compute_signal_manifest_hash`,
  `compute_exclusion_hash`, version constants; `compute_spine_hash` (ordering version 1)
  is retained unchanged so historical seals remain reproducible.

### Changed
- **G-1** — states that appends are refused from `CLOSING_PENDING_SEAL` onward, including
  `CLOSED`, `CRYSTALLIZATION_PENDING`, `SEALING`, `SEALED`, `ARCHIVED`; codicils are the sole
  sanctioned post-closure append. Reference `enforce_G1_write_guard` widened to match
  (`G1_FROZEN_STATES`). This is a clarification of §4.4.1, which already said a `CLOSED`
  Episode admits only codicils.

### Changed (editorial — no normative change)
- **Public naming residue.** The four `CONFORMANCE*.md` titles and their intro/footer lines still said "Ariadne Protocol"; they now say ASTP, matching the SPEC/README rebrand (v3.2.2 era). Code identifiers, package paths, HKDF info strings, Redis key prefixes and Neo4j labels are unchanged by design — "Ariadne" remains the internal codename.
- **README drift.** The README restated the protocol version (`3.2.2`, while SPEC was 4.2.1) and the governance range ("G-1 through G-9", while SPEC defines through G-39). Both now defer to `SPEC.md` instead of restating it. The package structure tree now shows the `protocol/` and `nodes/` layers and the namespace firewall.

### Clarified (errata — PATCH)
- **Segment parentage vs. proof-chain parentage.** New §3.4.1 states explicitly that a Segment's `parent_node_id` is its **`EpisodeNode`** (an upward anchor), that segments order by `sequence_index` with no segment→segment edge, and that the canonical materialization is an ordered `(Episode)-[:CONTAINS {sequence_index}]->(Segment)` fan-out (derive next/prev at read time, don't persist a chain). A reciprocal note at §16.5.3 distinguishes this from the proof-chain rule `B.parent_node_id == A.node_id`, which links whole nodes causally (e.g. episode→episode). **No canonical-form change** — this clarifies existing semantics (G-2 reparenting prohibition; §5.2 leaf-hash preimage). Surfaced by a reference-implementation question: an adapter graph showed a segment→segment containment chain instead of the canonical episode→segment fan-out.

## [4.2.1] — 2026-08-21

**PATCH.** `write_attachment_node_sync` — sync variant of `create_attachment_node`, for callers that are not async and cannot become so without restructuring their caller in turn. Exists for the same reason `write_document_node_sync` does, and writes the same node and edge, so the two variants are indistinguishable in the graph.

Documents its own limit: a caller performing an attachment owes an `ATTACHMENT_COMMIT` entry under G-39, and this function cannot produce one because write-intent coordination is async by necessity. A sync caller must surface that its write is unledgered rather than absorb the gap (§12.4.2).

## [4.2.0] — 2026-08-21

**MINOR.** Restores `CONSULTATION_COMMIT` to the §12.4.1 register (Tier 1) and corrects a contradiction.

v3.5.0 removed the operation on the stated ground that "the protocol does not define" consultation. **It does, and always has:** G-8 and G-9 have governed consultation since v1, and `compute_consultation_node_hash` / `compute_exchange_chain_hash` are protocol hash functions. SPEC.md asserted both positions at once until now.

- One operation covers the consultation node, its ordered exchange entries and the consulted agent's participation record — they commit together, so they are one operation rather than three.
- **Collaboration gets no separate operation.** It is a `ConsultationType`, so a collaborative session commits as a consultation and the type distinguishes it; a second register name would encode in the ledger what the node already records.
- §12.4 clarifies that an operation's **tier turns on whether an interruption leaves recoverable work, not on store count** — a multi-record write to one store is Tier 1 when a partial write leaves a chain stopping mid-sequence. The register already assigned tiers this way; the definitions had said "more than one store".
- Reference implementation gains `create_consultation_node`, `create_exchange_entry_node`, `create_consultation_participant_node` and `execute_consultation_commit`. These were the last abstract adapter methods without implementations, and they were unimplemented only because of the same mistaken premise.

**Additive** — no existing operation, node or conformance requirement changes.

## [4.1.1] — 2026-08-20

**PATCH.** `create_amendment_link_node` — the last abstract adapter method with no Neo4j implementation.

`AriadneAdapter.create_amendment_link` was declared and left `...`, so consumers reopening a sealed Episode wrote their own node and edges. Same gap as codicils, closure records, episode-status transitions and attachments; this closes the set.

Writes the node and **both** edges — `AMENDS` to the source, `PRODUCES` to the new Episode. The link is not symmetric: following provenance backwards wants the source, asking "what came of this" wants the amendment, and one edge would make the other direction a scan. G-1 is deliberately not enforced — the source is sealed *by definition*, which is the precondition for amending it, not an obstacle.

**Known gap recorded, not closed:** `create_consultation`, `create_exchange_entry` and `create_consultation_participant` remain abstract with no implementation. v3.5.0 retired consultation from the protocol but removed only its WIL operations and `SegmentType` members — these three methods and the `ConsultationNode` / `ExchangeEntry` / `ConsultationParticipantNode` types survived, and appear nowhere in SPEC.md. Finishing that removal is a cross-repository migration, because downstream consumers import these types from the protocol schema. Pinned by test so the gap cannot grow.

## [4.1.0] — 2026-08-20

**MINOR.** SPEC §4.7 `AttachmentNode` — external content injected into an Episode's context, recorded so the injection is verifiable after the fact.

- Narrow by design: episode, content hash, media type, locator, who and when.
- **Kind is a property, not a node type.** A document, an image and an audio file are one node distinguished by `media_type`. Separate node types per artifact kind would contradict §1 ("agnostic to node type") and force a protocol revision for every new format.
- `content_hash` is over the content **as received**, never an extraction — hashing text pulled from a PDF proves the extraction unchanged while leaving the PDF unverified.
- `ATTACHMENT_COMMIT` registered (Tier 1), with writer and coordinated write.

**Additive** — no existing node, operation or conformance requirement changes. `DocumentNode` remains as legacy in the reference implementation; its docstring claimed protocol status the specification never conferred, and its `drive_url` / `content_text` / `char_count` fields are precisely why that claim was untrue.

## [4.0.0] — 2026-08-20

**MAJOR.** Ledgering obligations (SPEC §12.4.2), deferred since 3.4.0. Requires a ratifying **Episode of Record**. *(Episode of Record: `458fb62b-faee-4e42-9f92-c63187c1b59a`, sealed 2026-08-22 — cited here from 4.5.0 onward; the release did not name it at the time.)*

- **G-39** — an implementation MUST record a ledger entry for every §12.4.1 operation it performs. Performing one without an entry is a conformance violation, not a degraded mode.
- Scoped to operations *performed*: an implementation owes nothing for capabilities it does not implement.
- Ledger writes MAY be best-effort with respect to availability, but a gap MUST be surfaced rather than absorbed — the distinction is between an implementation that cannot record and knows it, and one that does not record and cannot tell.
- **Consequence:** a missing entry from a conforming implementation now means the operation did not occur. That inference was explicitly unavailable before. It remains unavailable for records written prior to this version, and an implementation MUST NOT retroactively assert coverage over a period it did not have it.
- Tier 1 entries with `completed_at=null` past the provisional window continue to record an interrupted write — strictly more information than either a completed entry or none.

**Breaking.** Every 3.x-conformant implementation that performs a registered operation without ledgering it becomes non-conformant. `SPEC.md` at 3.5.1 retained as `SPEC-v3.md` (now [`docs/history/SPEC-v3.md`](./docs/history/SPEC-v3.md)).

## [3.5.1] — 2026-08-20

**PATCH (errata).** SPEC §4.4.1 Episode Lifecycle States.

The prior one-line list read "ACTIVE, REBALANCING, SEALING, SEALED, SEALING_FAILED, REBALANCE_FAILED, ARCHIVED, EXPIRED". Four of those states have never existed in any implementation; seven real ones were missing, including the entire closure workflow. Four of eleven overlapped.

Written 2026-04-09, two days *after* the enum it was describing already carried the states it omitted — wrong on the day it was authored, not drift. Replaced with the closed set as a table, plus: **crystallization is a fact recorded by a `CrystallizationDelta`, not a state**; an implementation MUST NOT infer it from `episode_status`, and MAY restore the pre-lock status, which is required for correctness mid-closure.

## [3.5.0] — 2026-08-19

**MINOR.** Retires `CONSULTATION_COMMIT` and `COLLABORATION_COMMIT` from the §12.4.1 register, and the never-used `SegmentType.CONSULTATION` / `COLLABORATION` members.

Both describe multi-agent interaction patterns the protocol does not define; registering their operations extended the protocol's vocabulary to cover behaviour it does not specify. Implementations that ledger them namespace them (for example `vendor:CONSULTATION_COMMIT`) under the §12.4.1 prefix rule. No conformant implementation affected — neither operation was ever emitted by the reference implementation, and the segment types had no writer and zero instances.

## [3.4.0] — 2026-08-18

**MINOR.** Write Intent Log operation register (SPEC §12.4).

§12 defined *how* a write intent is recorded but never *which* operations record one, so the vocabulary existed only as a Python enum documented nowhere normative. Adds the closed register of all operation values and the two entry forms: **Tier 1 coordinated write** (multi-store, full three-phase §12.2 protocol, `completed_at=null` past the provisional window is a recovery candidate) and **Tier 2 ledger record** (single authoritative store, one completed entry at commit, never a recovery candidate).

New governance rules **G-37** and **G-38** constrain the *form* of an entry whenever one is written; neither compels an entry to exist. §12.4.2 deferred that obligation to 4.0.0.

§12.4.1 closes the register against extension values that lack an implementation namespace prefix, and records that `SEGMENT_COMMIT` and `SIGNAL_COMMIT` are not interchangeable. §12.4.2 states that, while the obligation is deferred, a verifier MUST NOT infer from a missing entry that an operation did not occur.

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
`test_phase2_operations.py` — `TestForkOrphanRecovery` (6): marker hash determinism + satellite (no `parent_hash`), dedup-on-`fork_id`, Class-A append-only flag, Class-B retroactive append (backdated anchor + byte-identical hash), Class-B unanchored, Class-C status correction.

## [3.2.2] — 2026-07-04

**PATCH.** Prose errata — the §20/§21 hash-preimage descriptions were reconciled to the reference implementation. **No canonical-form change; the code was already correct** — only the SPEC prose was wrong, so every v3.2.1-conformant implementation remains conformant unchanged. Surfaced while authoring the §20/§21 implementation & conformance companion docs.

### Corrected (errata)
- **§20 hash algorithm.** `EpisodeLink.content_hash`, `MembershipRecord.content_hash`, and `ConformanceDeclaration.declaration_hash` are computed with **SHA3-256**, not SHA-256 — consistent with the §5 "all hashing uses SHA3-256, no exceptions" commitment and the `hash_canonical.py` implementation. The prose said "SHA-256".
- **§20 MembershipRecord preimage.** The preimage binds `supersedes_record_id` and `succession_reason` in addition to the seven fields the prose listed (per `_MEMBERSHIP_HASH_PREIMAGE_FIELDS`).
- **§20 EpisodeLink exclusions.** The preimage **includes** `health_state` and `health_checked_at`; it excludes only `quarantine_resolved_at` and `quarantine_resolution` (set after the hash, on quarantine exit). The prose had the exclusion list inverted.
- **§21 Form-B attribution.** The reference implementation serializes in declared field order and hashes with SHA3-256 — not key-sorted JSON with SHA-256. §21 §8 still leaves the Layer-3 byte-form implementation-open; this only corrects the description of what the reference implementation does.

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
`test_phase2_operations.py` — `TestCreateDepartureFork`, `TestDepartureForkFSM`.

## [3.1.0] — 2026-06-07

**MINOR.** Layer 3 Workflow & Execution DAG codification. Additive on top of v3.0.0.

### Added
- **Layer 3 — Workflow & Execution DAG.** Source: `AMENDMENT-v3.0-WORKFLOW-EXECUTION-DAG.md` (amendment file retains its authoring numeral; canonical SPEC version per `VERSIONING.md` is v3.1.0).
- New node types: `WorkflowDeclaration`, `ExecutionNode`, `SkillInvocation`. Pydantic implementation in `ariadne/core/workflow_execution.py`.
- Three-Merkle-layer model formally specified in SPEC §3.4 Persistence Layer Model — Layer 1 Spine, Layer 2 episode content, Layer 3 Workflow & Execution DAG.
- New `CognitiveDeltaType` variants in `branching.py` for Layer 3 delta records.
- **Cognitive Implementation Authority (CIA)** — sole-writer pattern per workspace; wire-tier conformance principle. Only the designated CIA may write each Layer 3 node type.
- New unit tests across the protocol suite.

### Invariants
- **Layer 3 is cryptographically isolated from Spine integrity.** Layer 3 nodes reference Layers 1/2 by ID only; they MUST NOT participate in Spine hash computation. No future Layer-3 change can retroactively force a MAJOR bump on Spine grounds — structural separation is the guarantee.
- `ExecutionNode` and `SkillInvocationNode` are immutable after creation. The only mutable Layer 3 field is `WorkflowDeclaration.status` (and `status_updated_at`).
- Hash byte-form left open at protocol layer per amendment §3 — each conformant implementation may choose its serialization, provided the canonical form is consistent within that implementation.

### Notes
- Layer 3 is the formal protocol surface for the autonomous-process audit trail.

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
- v2.5.0-draft was never finalized as v2.5.0 — main moved directly to the v3.x line. v2.5.x is therefore not a maintenance line going forward; new work targets v3.x.

## [2.5.0-draft] — 2026-04-21

Working Draft. Phase 1-3 (node system) + Phase 4 (HITL) implemented; Branch/Fork/Merge Taxonomy §19 Phases 1-4 implemented.

### Added
- **Branch/Fork/Merge Taxonomy** — formal taxonomy of episode branching, forking, and merging events. SPEC §19. Includes prescriptive enforcement, resolution primitives (fork, merge, conflict surface), social/internal primitives (aside, soliloquy), and coherence-fingerprint write intercepts.
- BranchPoint/BranchTerminus (§19.2); ForkPoint/MergePoint/BranchReturn with three-Merkle-root verification (§19.3); AsideSegment/SoliloquySegment with the HASH_PLACEHOLDER content policy (§19.4); CoherenceFingerprint write-intercept state machine and ConfirmationCache (§19.5).
- Governance rules **G-19 through G-29**. Delta types `BRANCH_CREATED`/`ABANDONED`, `FORK_CREATED`/`RESOLVED`, `MERGE_EXECUTED`, `ASIDE_OPENED`/`CLOSED`, `SOLILOQUY_INITIATED`/`CONCLUDED`. AuditRecord chain integrity (`prior_audit_hash`), IntentRecord idempotency, derived lifecycle state (§19.2.4).
- `CONFORMANCE-BFM.md` — conformance vectors for the BFM Taxonomy.
- `IMPLEMENTATION-BFM.md` — implementation guide for BFM Taxonomy.
- `list_episodes_for_user` query.

## [2.4.0-draft] — 2026-04-16

### Added
- **HITL Protocol Amendment** — Phase 1 through Phase 4. Human-in-the-loop decision gates as first-class protocol nodes.
  - `HITLEventNode` — two-phase lifecycle (INVOKED → RESOLVED / TIMED_OUT). Participates in the Merkle spine as a causal anchor.
  - `PENDING_HITL` crystallization guard — blocks sealing during active human review.
  - Two-layer Ed25519 cryptographic attestation.
  - HITL Merkle spine participation and advisory gates (`CONDITIONALLY_VALID`); `HITL_GATE` edges (BLOCKS / FOLLOWS); `pending_hitl_ref` segment tagging.
  - Governance rules **G-17** (invocation before resolution) and **G-18** (crystallization block). Schema version 1.2.0. SPEC §4.6.
- Implementation Guide updates to incorporate HITL guidance.

## [2.3.0] — 2026-04-12

### Added
- **Phase 3 trust infrastructure** — node key hierarchy (§16.2), transparency log anchoring (§16.3), witness signatures (§16.4), cross-node chain proof (§16.5). Governance rules **G-11 through G-16**.
- **Protocol Boundary** documentation (§2.5) — clarifies what is normative protocol vs. implementation latitude.

## [2.2.0] — 2026-04-12

### Added
- **Phase 2 observability** — retrieval audit records (§11.1), `signal_versions_read` segment metadata (§4.5).
- Spine tip cache (§13) and rebalance events (§14).

## [2.1.0] — 2026-04-10

### Added
- **Retrieval coordination protocol** — the cross-agent retrieval surface: snapshot isolation (§10.4), tail write advisory (§10.5), HITL re-validation gate (§10.6), side-effect contract (§11).

## [2.0.0] — 2026-04-09 (pre-changelog history, inferred from `SPEC.md` introduction)

### Changed (BREAKING)
- **Protocol primitive becomes `CognitiveNode`, not `Episode`.** Episodes are the first *parameterization* of the protocol, not a precondition of it. Future node types (signals, agents, artifacts) slot into the same framework with zero protocol-layer changes.
- **Dual Index invariant**: `sequence_index` (immutable temporal position, hash-included) vs. `tree_leaf_index` (mutable structural position, hash-excluded). The epistemological core of the v2 line.
- Position-binding leaf hash, the five-test gate, and the namespace firewall.

## [0.1.0-draft] — 2026-04-07

Original spec. Episode-centric model. Retained as [`docs/history/SPEC-v1.md`](./docs/history/SPEC-v1.md) for historical reference; superseded by the v2.x line.
