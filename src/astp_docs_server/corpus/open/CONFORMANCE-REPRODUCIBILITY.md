# ASTP — Reproducibility Conformance Test Vectors

**Version:** 1.3.0
**Status:** Working Draft
**Authors:** Scorched Earth Labs
**Date:** 2026-09-18
**Applies To:** SPEC.md 5.0.0 — §5.1 Canonical Field Encoding, §5.2 Leaf Hash, §5.6 Episode Spine Leaf Set, §5.7 Episode Root, §5.8 Algorithm and Ordering Versions, §9.2 Inclusion Proof, §9.3 Reproducibility Obligation, G-1, G-40. RP-001 … RP-008 exercise the retained `spine_algorithm_version` 0 and 1 constructions, which every verifier of a 4.x seal must implement; RP-009 … RP-011 exercise `spine_algorithm_version` 2.
**Companions:** [CONFORMANCE-CONTEXT.md](CONFORMANCE-CONTEXT.md) (`spine_algorithm_version` 3 — the spine root is byte-identical to version 2, so RP-009 … RP-011 apply to a version 3 seal unchanged; the sixth root field, `context_manifest_hash`, is exercised by CM-001 … CM-010), [CONFORMANCE.md](CONFORMANCE.md) (§16 trust infrastructure), [CONFORMANCE-BFM.md](CONFORMANCE-BFM.md), [CONFORMANCE-LAYER3.md](CONFORMANCE-LAYER3.md), [CONFORMANCE-CROSS-EPISODE-LINKING.md](CONFORMANCE-CROSS-EPISODE-LINKING.md)

---

## 1. Overview

The Five-Test Gate (§9.1) is only as strong as the verifier's ability to rebuild the
sealed root. These vectors test that ability directly. They exist because the first
corpus-scale re-verification of a production deployment (2026-09-13, 62 sealed
Episodes) found that 17 of them could not be rebuilt from stored nodes under the
construction their seal claimed:

| Outcome | Episodes |
|---|---|
| Root rebuilt from stored nodes | 45 |
| Rebuilt only under an earlier tree function, which had been replaced in place | 8 |
| Rebuilt only by searching the orderings of same-timestamp signals | 4 |
| Not rebuilt under any construction — one has too many tied signals to search and had also accepted content after closure; the other is within reach of a longer search | 2 |
| In a sealed status with no seal record at all, so no root to rebuild | 3 |

Of the 57 seals that were rebuilt, none showed evidence of content tampering. The
remaining 5 could not be evaluated: 2 did not rebuild under any construction, and 3
have no root to rebuild. None of this was visible until a verifier tried to
reproduce the roots.

A conforming implementation MUST pass all vectors marked **REQUIRED**. Format follows
[CONFORMANCE.md §1](CONFORMANCE.md).

Reference implementation: `astp/core/schema.py` (`compute_spine_root_v2`,
`compute_signal_manifest_hash`, `compute_exclusion_hash`, `compute_episode_root_hash`,
`enforce_G1_write_guard`), tested in
`tests/unit/protocol/test_reproducibility_conformance.py`.

---

## 2. Spine Reproducibility (§5.6, §9.3)

**RP-001** — Spine Root From Stored Nodes Only
- **Class:** REQUIRED
- **Spec Reference:** §5.6, §9.3
- **Description:** The spine root is a function of the Episode's non-ephemeral Segment content hashes in `sequence_index` order and, under `spine_algorithm_version` 1, the Episode's identifier (the Episode-identifier leaf, §5.6) — and nothing else. Two verifiers holding the same stored Segments and the same `episode_id` produce the same root; any state not on the nodes (insertion order, a store's default sort, a cache, the signals) plays no part.
- **Inputs:**
  ```
  segment_content_hashes (sequence_index order): 7 hashes, SHA3-256("leaf-0") … SHA3-256("leaf-6")
  episode_id: "550e8400-e29b-41d4-a716-446655440000"
  spine_algorithm_version: 1
  ordering_version: 2
  ```
- **Expected Output:**
  ```
  SHA3-256("leaf-0")                         aa6c290f56f0f7eb3a8da563ae72efc5d10cc89b88a3112c612d8e3825e20aad
  Episode-identifier leaf input
    SHA3-256(episode_id)                     0bdfe537564300a840a9b2279b3c4d0c8ca0e0c3b0c3d9c95c105852f991f222
  spine_root  (spine_algorithm_version 1)    3cdbc3f20a909338a55a5b9687d72ce4b6f74ad1d3784a377c91b1bba06f2491
  spine_root  (spine_algorithm_version 0,
               same seven inputs)            0654211304f104a768b81432567776c7f13f65b97e4937f114f5c65e8dbc5fed
  ```
  Hash values enter the tree as 64-character lowercase hex strings, ASCII-encoded (§5.3); an unpaired node is carried up unchanged (§5.4). The root is **not** equal to the `ordering_version` 1 root computed with any signals included; it differs when the segment order is permuted; an empty leaf set is refused.
- **Failure Condition:** Either root differs from the value above; the root changes when signals are added; the root is order-insensitive; an empty leaf set yields a root.

---

## 3. Signal Manifest (§5.7)

**RP-002** — Signal Manifest Is a Set
- **Class:** REQUIRED
- **Spec Reference:** §5.7
- **Description:** The signal manifest hash depends only on the *set* of SPINE-placed signal content hashes. Arrival order, timestamps, and duplicates do not change it; membership does. The empty manifest is well defined and distinct from the empty exclusion set. The Episode root changes when any component changes.
- **Inputs:**
  ```
  signal_content_hashes: 5 hashes, SHA3-256("leaf-100") … SHA3-256("leaf-104"), presented in five different orders
  construction: SHA3-256("SIGNAL_MANIFEST:v1:" || sorted hashes joined by "|"); empty → SHA3-256("SIGNAL_MANIFEST:v1:EMPTY")
  exclusion: SHA3-256("EXCLUSION:v1:" || …); empty → SHA3-256("EXCLUSION:v1:EMPTY")
  episode_root_hash = SHA3-256("NODE:" || spine_root || signal_manifest_hash || exclusion_hash)
  ```
- **Expected Output:**
  ```
  signal_manifest_hash (the five hashes, any order, with or without duplicates)
                                             0a4a4582ad36da24dcd21853b07ed97d13a8c223cf14845588861d9d5786b670
  signal_manifest_hash (SHA3-256("leaf-104") removed)
                                             5b73a9aa0cf76aaa0399dce72733b48d5e441b7f236dc063d570eecdde5ff22d
  signal_manifest_hash (empty)               5188531fe69daafc79126dfa880419494179ca220d60d5dda2fee8279d4ae847
  exclusion_hash (empty)                     45849be4da47e279538916284a2ac74cd6acd60a67b9a8982992f97afa149be6
  episode_root_hash  (RP-001 spine_root under spine_algorithm_version 1,
                      the five-member manifest, empty exclusion set)
                                             49c1b61c22d00c185dceca5eb39f65bd88c2666281444687c59c48b0b199d7fe
  ```
  The Episode root differs when the manifest or the exclusion set differs.
- **Failure Condition:** Any value differs from the one above; any ordering-dependence; duplicates altering the hash; a root insensitive to a component.

---

## 4. Version Identifiers (§5.8)

**RP-003** — Version Tags Select the Function and Stay Out of the Preimage
- **Class:** REQUIRED
- **Spec Reference:** §5.8
- **Description:** A seal record carries `spine_algorithm_version` and `ordering_version`; a `CognitiveNode` carries `hash_version`. They are recorded and retrievable, default to absent (seal) / `1` (node) so pre-4.3.0 records read as legacy, and are **outside** every hash preimage: two seal records differing only in tags have the same content hash, and two nodes differing only in `hash_version` have the same leaf hash.
- **Inputs:**
  ```
  CrystallizationDelta A: sealed_chain_root R, spine_algorithm_version 1, ordering_version 2
  CrystallizationDelta B: sealed_chain_root R, no version tags
  CognitiveNode N1: hash_version 1 (default);  N2: identical fields, hash_version 7
  ```
- **Expected Output:** A reports (1, 2); B reports (None, None); `content_hash(A) == content_hash(B)`; `leaf_hash(N1) == leaf_hash(N2)`.
- **Failure Condition:** Tags not persisted; tags entering a preimage (content or leaf hash differs by tag alone); a tagless record read as current rather than legacy.

---

## 5. Fixed Record (G-1)

**RP-004** — A Closed Episode Refuses Content
- **Class:** REQUIRED
- **Spec Reference:** G-1, §4.4.1
- **Description:** A Segment or Signal commit against an Episode whose record is fixed MUST be refused with a governance error. Fixed means `CLOSING_PENDING_SEAL`, `CLOSED`, `CRYSTALLIZATION_PENDING`, `SEALING`, `SEALED`, `ARCHIVED`. Open means `CREATED`, `ACTIVE`, `PENDING_HITL`, `CLOSING`, `CRYSTALLIZED`. Codicils are exempt and use their own path.
- **Inputs:** each `EpisodeStatus` value, presented to the write guard.
- **Expected Output:** governance error for every fixed state — **`CLOSED` included**; no error for every open state.
- **Failure Condition:** Any fixed state admits a commit. (The reference guard before 4.3.0 admitted `CLOSED`; the production corpus holds one post-closure append as a result.)

---

## 6. Resolved Signal Order (§5.8.1)

These vectors share one fixture. Segments: the seven of RP-001. SPINE-placed Signals: the five of RP-002, `SHA3-256("leaf-100")` … `SHA3-256("leaf-104")`, stored in that (arrival) order, of which the middle three — `leaf-101`, `leaf-102`, `leaf-103` — share a timestamp. At seal time the Signals were folded in the order `leaf-100, leaf-103, leaf-101, leaf-102, leaf-104`. `episode_id` as in RP-001. `ordering_version` 1.

```
sealed_chain_root, spine_algorithm_version 1     1dda20e990cf757302e67f96173703a2a0f846feb2c6c0f34870a2e173aeed33
sealed_chain_root, spine_algorithm_version 0     863ded60b9adce9cf3703b8892c5bf5263fa09153a81aa21778517789f9aa2c2
root under the stored (arrival) order, version 1 2ff4e255c1e7470aa8a30a8b1fbde6cecb690e1d4ffaefb31a0ae26b6fce44ba   (≠ sealed: the seal is a tie-order seal)
```

**RP-005** — An Admissible Annotation Reproduces the Seal Without a Search
- **Class:** REQUIRED for implementations that read or write `resolved_signal_order`
- **Spec Reference:** §5.8.1, §9.3
- **Description:** Given the fixture and `resolved_signal_order = [leaf-100, leaf-103, leaf-101, leaf-102, leaf-104]` (as content hashes), a verifier recomputes the spine once, under the seal's identifiers, and obtains the sealed root — for `spine_algorithm_version` 1 and, with the corresponding sealed root, for version 0.
- **Expected Output:** the two `sealed_chain_root` values above; the annotation is reported admissible; no ordering other than the recorded one is tried.
- **Failure Condition:** Either root differs; the verifier searches despite an admissible annotation.

**RP-006** — An Annotation Is Checked, Never Trusted
- **Class:** REQUIRED for implementations that read `resolved_signal_order`
- **Spec Reference:** §5.8.1
- **Description:** Three inadmissible annotations against the `spine_algorithm_version` 1 fixture. (a) *Wrong order:* `[leaf-100, leaf-101, leaf-103, leaf-102, leaf-104]` — a reordering of the stored Signals that does not reproduce the root. (b) *Foreign hash:* the correct order with its last entry replaced by `SHA3-256("x")`, which is not a Signal of the Episode. (c) *Tampered record:* the correct order, but the first Segment's content hash replaced by `SHA3-256("t")`.
- **Expected Output:** each annotation is reported inadmissible and is ignored. In (a) and (b) the verifier proceeds as if no annotation were present and may still reproduce the seal by search. In (c) the seal does not reproduce under any order: the correct annotation does not rescue a tampered record.
- **Failure Condition:** Any of the three is accepted; (c) verifies.

**RP-007** — An `ordering_version` 2 Seal Ignores a Stray Annotation
- **Class:** REQUIRED for implementations that read `resolved_signal_order`
- **Spec Reference:** §5.8.1
- **Description:** A seal tagged `ordering_version` 2 over the RP-001 segments (sealed root as in RP-001, `spine_algorithm_version` 1) whose delta nonetheless carries a `resolved_signal_order`.
- **Expected Output:** the annotation is ignored; the seal verifies exactly as RP-001, to `3cdbc3f20a909338a55a5b9687d72ce4b6f74ad1d3784a377c91b1bba06f2491`.
- **Failure Condition:** The annotation alters the recomputation or the outcome.

**RP-008** — Absence of an Annotation Carries No Adverse Inference
- **Class:** REQUIRED
- **Spec Reference:** §5.8.1, §9.3
- **Description:** The `spine_algorithm_version` 1 fixture with **no** annotation. Searching the orderings of the tied group (3! = 6) finds the sealed order. Separately, the same fixture with a sealed root that no ordering reproduces.
- **Expected Output:** the first seal reproduces to the same `sealed_chain_root` as in RP-005 and is reported as reproduced — no weaker for having been found by search. The second is reported as not reproducible. The two outcomes MUST be distinguishable: "reproduced without an annotation" is not "could not be reproduced".
- **Failure Condition:** A search-resolved seal is reported as weaker than, or different in root from, an annotated one; the two outcomes are conflated.

---

## 6a. Seal Construction Version 2 (SPEC 5.0.0 §5.1–§5.7, §9.2)

The machine-readable vector file is [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json), regenerated by `vectors/5.0.0/generate.py` and never edited by hand. Every value in it is checked twice by the reference tests (`tests/conformance/test_*_v2_vectors.py`): against the package, and against a from-prose reference written from `SPEC.md` with `hashlib` alone. Fixture: `episode_id` `550e8400-e29b-41d4-a716-446655440000`; seven Segments with fixed `node_id`s `00000000-0000-4000-8000-00000000000i` and `content_hash = SHA3-256("leaf-i")`, `sequence_index` i, `schema_version` `"1.2.0"`, parent = the Episode; five SPINE-placed Signals; seven structural members; empty exclusion set. (Fixed `node_id`s are for reproducibility only; real `node_id`s MUST be random, SPEC §5.2.)

**RP-009** — Version 2 Leaf Hash and Spine Root
- **Requirement:** REQUIRED
- **Spec Reference:** §5.1.1, §5.2, §5.4, §5.6
- **Description:** From the fixture's stored fields, a verifier computes each Segment's `hash_version` 2 leaf hash under `LEAF_HASH:v2:` and the spine root under `TREE_LEAF:v2:` / `TREE_NODE:v2:` over raw bytes, with no Episode-identifier leaf.
- **Expected:**
```
leaf_hash (hash_version 2), segment 0        25b617f0d7ac09871f88ce7e2851cc8f50b48305dee51d081b62a5f21ed84935
spine_root (spine_algorithm_version 2), n=1  5e06ac5629faf452aa18836dcf3f33565db0cd2d8749b482c65365b9273b576e
spine_root (spine_algorithm_version 2), n=7  4420e38a22409317822ac14e3d5bc8069e6556c0fc08928290f76d23396daa01
```
- **Failure Condition:** Any other value; computing a leaf hash from a stored version 1 leaf hash rather than from the fields; accepting hex-text tree inputs under version 2; computing a root for an empty leaf list.

**RP-010** — Version 2 Sets and Episode Root
- **Requirement:** REQUIRED
- **Spec Reference:** §5.1.1 (sets), §5.7, §5.7.1
- **Description:** The signal manifest, the structural manifest over the fixture's seven members, the empty exclusion set, and the Episode root over the Episode's UUID and the four components.
- **Expected:**
```
signal_manifest_hash (v2), five members       70dbc8e8f2e87b63e49187979b14ad56ba11219b42be132015c23dcad36acb43
exclusion_hash (v2), empty                    ddea405cc1729ebf63d93b16d723873ad02f9f64af3cc159bf86e5f999b02ce1
structural_manifest_hash, seven members       0a4b777227b87ee0d6c8efd5b2e9a5fc05c02e61d677f2460f868ab06779b537
episode_root_hash (v2)                        f0511b4d1be172554b9f87ec64d400d24a1409f1742ad72f628bf5ab7b7d33f0
```
- **Failure Condition:** Any other value; a set that depends on member order; an empty set hashed with a sentinel; removing a structural member leaving the Episode root unchanged; an Episode root computed over a string identifier.

**RP-011** — Version 2 Inclusion Proof
- **Requirement:** REQUIRED
- **Spec Reference:** §9.2
- **Description:** For the seven-leaf spine, a proof for leaf 3 carries three siblings and a proof for leaf 6 carries two; each verifies against the n=7 root at its own position and at no other; a proof whose sibling count does not fit the shape derived from `leaf_index` and `leaf_count` is refused. The vector file's `inclusion_proofs_v2` fixes the sibling lists.
- **Failure Condition:** A proof verifying at a position other than its own; a proof accepted with a sibling count the shape does not admit; a verifier that requires stated path directions for a version 2 proof, or derives them for a 4.x proof.

## 7. Governance Rule Enforcement Matrix

| Governance Rule | Description | Test Vectors | Class |
|----------------|-------------|-------------|-------|
| **G-1** | Write guard — no appends to a fixed record | RP-004 | REQUIRED |
| §9.3 | Reproducibility obligation | RP-001, RP-002, RP-003 | REQUIRED |
| §5.8.1 | `resolved_signal_order` is checked, never trusted; absence carries no inference | RP-005, RP-006, RP-007, RP-008 | REQUIRED (RP-005–007 for implementations that use the annotation) |

## 8. Out of Scope

- How an implementation finds the order of same-timestamp Signals for an `ordering_version` 1 seal (search strategy, caps, scheduling). §6 covers what may be recorded once it is found and how a recorded order must be checked; a seal whose tied groups are too large to search, and which has no admissible annotation, is not reproducible, and no vector requires otherwise.
- Re-sealing of historical records. Prohibited by §5.8 — a re-seal is a post-closure mutation.

---

*ASTP Reproducibility Conformance Test Vectors are maintained by Scorched Earth Labs.*
