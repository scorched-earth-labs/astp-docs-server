# ASTP — Phase 3 Conformance Test Vectors

**Version:** 2.0.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md 5.1.0 §16 (Trust Infrastructure), G-11–G-16. The anchor and witness vectors (§3.1, §4) are the 5.0.0 constructions (`ANCHOR_COMMITMENT:v2:`, `WITNESS_COMMITMENT:v2:`), with expected values pinned in [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json); the 4.x forms are retained in SPEC §16.3.2 and §16.4.2 as the definitions of records already written and are not vectors here.
**Companion:** [CONFORMANCE-BFM.md](CONFORMANCE-BFM.md) covers SPEC §19 (Branch/Fork/Merge/Aside/Soliloquy/CoherenceFingerprint).

---

## 1. Overview

This document specifies the conformance test vectors for Phase 3 Trust Infrastructure (§16) of ASTP (the AI State Tree Protocol). For the BFM feature family (§19), see the companion document [CONFORMANCE-BFM.md](CONFORMANCE-BFM.md). A conforming implementation MUST pass all vectors marked **REQUIRED**. Vectors marked **RECOMMENDED** test behaviors that conforming implementations SHOULD support.

**Test vector format:**

Each vector specifies:
- **ID** — stable identifier for referencing in test harnesses
- **Spec Reference** — the SPEC.md section being tested
- **Class** — REQUIRED or RECOMMENDED
- **Description** — what property is being verified
- **Inputs** — exact input values (hex-encoded where applicable)
- **Expected Output** — exact expected result
- **Failure Condition** — what a non-conforming result looks like

All hex values are lowercase. All string fields are UTF-8 encoded unless otherwise noted. All integer fields use big-endian byte order unless otherwise noted.

---

## 2. Key Hierarchy Vectors (§16.2)

### 2.1 HKDF Derivation Correctness

**KH-001** — Workspace Key Derivation
- **Class:** REQUIRED
- **Spec Reference:** §16.2.1
- **Description:** Workspace key is correctly derived from root key material using HKDF-SHA3-256 with the protocol-specified info string.
- **Inputs:**
  ```
  root_key_material: 0000000000000000000000000000000000000000000000000000000000000000
  workspace_id: "ws-test-001"
  hkdf_salt: UTF-8("ws-test-001")
  hkdf_info: UTF-8("ariadne.workspace.v1")
  hkdf_length: 32 bytes
  ```
- **Expected Output:**
  ```
  workspace_key: [implementation computes and pins this value]
  ```
- **Verification Protocol:** Two independent implementations using identical inputs MUST produce identical `workspace_key` bytes. This vector is a cross-implementation consistency check, not a fixed expected value — implementations MUST publish their computed value for this input set and verify it matches other conforming implementations.
- **Failure Condition:** Two conforming implementations produce different `workspace_key` bytes for identical inputs. This indicates an HKDF parameterization difference (wrong hash algorithm, wrong info encoding, wrong salt encoding) — a protocol surface violation.

---

**KH-002** — Node Key Derivation with Type Isolation
- **Class:** REQUIRED
- **Spec Reference:** §16.2.1, §16.2 (type isolation), G-16
- **Description:** Node keys for different `node_type` values are cryptographically distinct, even with identical `node_id` and `workspace_id`.
- **Inputs:**
  ```
  workspace_key: [derived from KH-001]
  node_id: "550e8400-e29b-41d4-a716-446655440000"
  workspace_id: "ws-test-001"

  Derivation A:
    hkdf_salt: UTF-8("550e8400-e29b-41d4-a716-446655440000")
    hkdf_info: UTF-8("ariadne.node.v1:episode")
    hkdf_length: 32 bytes

  Derivation B:
    hkdf_salt: UTF-8("550e8400-e29b-41d4-a716-446655440000")
    hkdf_info: UTF-8("ariadne.node.v1:signal")
    hkdf_length: 32 bytes

  Derivation C:
    hkdf_salt: UTF-8("550e8400-e29b-41d4-a716-446655440000")
    hkdf_info: UTF-8("ariadne.node.v1:artifact")
    hkdf_length: 32 bytes
  ```
- **Expected Output:**
  ```
  node_key_A != node_key_B
  node_key_A != node_key_C
  node_key_B != node_key_C
  ```
- **Failure Condition:** Any two derivations produce identical keys. This indicates `node_type` is not participating in the HKDF context string — a G-16 violation.

---

**KH-003** — Seal Key Derivation Binds to spine_root
- **Class:** REQUIRED
- **Spec Reference:** §16.2.1, §16.2.2
- **Description:** Seal key derivation incorporates `spine_root_at_seal`. Different spine roots produce different seal keys for the same node.
- **Inputs:**
  ```
  node_key: [derived from KH-002, Derivation A]

  Derivation A (spine_root_1):
    hkdf_salt: hex_decode("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2")
    hkdf_info: UTF-8("ariadne.seal.v1")
    hkdf_length: 32 bytes

  Derivation B (spine_root_2, one bit different):
    hkdf_salt: hex_decode("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b3")
    hkdf_info: UTF-8("ariadne.seal.v1")
    hkdf_length: 32 bytes
  ```
- **Expected Output:**
  ```
  seal_key_A != seal_key_B
  ```
- **Failure Condition:** Both derivations produce the same seal key. This indicates `spine_root` is not participating in the seal key derivation — the Seal Commitment Key is not bound to node state.

---

**KH-004** — Key Version Monotonicity Enforcement (G-15)
- **Class:** REQUIRED
- **Spec Reference:** §16.2.4, G-15
- **Description:** A conforming implementation MUST reject a `NodeKeyRecord` write where `key_version` is less than the current maximum for that `node_id`.
- **Setup:**
  ```
  Existing NodeKeyRecord: { node_id: "550e8400-...", key_version: 3, ... }
  ```
- **Inputs:**
  ```
  Attempt A: NodeKeyRecord { node_id: "550e8400-...", key_version: 2, ... }  (rollback)
  Attempt B: NodeKeyRecord { node_id: "550e8400-...", key_version: 3, ... }  (duplicate)
  Attempt C: NodeKeyRecord { node_id: "550e8400-...", key_version: 4, ... }  (valid increment)
  ```
- **Expected Output:**
  ```
  Attempt A: REJECTED — key_version rollback (G-15 violation)
  Attempt B: REJECTED — key_version duplicate (not strictly increasing)
  Attempt C: ACCEPTED
  ```
- **Failure Condition:** Attempt A or B is accepted. A non-conforming implementation that accepts key version rollback enables key confusion attacks.

---

**KH-005** — Node Type Absent from Key Derivation (G-16 Violation Detection)
- **Class:** REQUIRED
- **Spec Reference:** G-16
- **Description:** An implementation MUST detect and reject node key derivations that omit `node_type` from the HKDF info string.
- **Note:** This vector tests the implementation's *self-enforcement* of G-16. The mechanism for enforcement is implementation-defined (e.g., the key derivation function could be the only code path, making omission impossible by construction). The conformance requirement is that no conforming implementation produces a node key without `node_type` in the info string — not that it actively detects externally-supplied non-conforming keys.
- **Expected Behavior:** A conforming implementation has no code path that derives a node key without `node_type` in the HKDF info string. Code review or AST analysis of the key derivation module is an acceptable conformance verification method for this vector.

---

### 2.2 Cross-Implementation Key Consistency

**KH-006** — Cross-Implementation HKDF Consistency
- **Class:** REQUIRED
- **Spec Reference:** §16.2.1, §2.5.4
- **Description:** Two independent conforming implementations MUST produce identical key material for identical inputs at every level of the derivation hierarchy.
- **Test Protocol:**
  1. Implementation A computes: workspace_key, node_key (episode), node_key (signal), seal_key using the inputs from KH-001 through KH-003
  2. Implementation B computes the same derivations with identical inputs
  3. Compare all outputs byte-for-byte
- **Expected Output:** All outputs match exactly across implementations.
- **Failure Condition:** Any output differs. This indicates an HKDF parameterization inconsistency — the two implementations will produce incompatible key material and cannot verify each other's signatures.

---

## 3. Transparency Log Anchoring Vectors (§16.3)

### 3.1 Anchor Commitment Construction

Fixture (from the vector file): node `550e8400-e29b-41d4-a716-446655440000` (`episode`), workspace `ws-1`, `root` `13be960d1618ebc39541c6deec0d9c86f5ff8c4609538e8091f2644f52625ec7` with `root_version` 2, `crystallization_sequence` 7, `logical_clock` 9, `anchored_at` `2026-01-01T00:02:00.123000+00:00`.

**TL-001** — Anchor Commitment Construction
- **Class:** REQUIRED
- **Spec Reference:** §16.3.2, §5.1.1
- **Description:** `anchor_commitment = SHA3-256("ANCHOR_COMMITMENT:v2:" ‖ UUID(node_id) ‖ STRING(node_type) ‖ STRING(workspace_id) ‖ HASH(root) ‖ UINT(root_version) ‖ UINT(crystallization_sequence) ‖ UINT(logical_clock) ‖ TIMESTAMP(anchored_at))` under the canonical field encoding. `root` is the node's outermost sealed commitment — the Episode root for an Episode — and `root_version` names its construction, exactly as for the witness commitment, so a log receipt and a witness record attest the same object.
- **Expected Output:**
  ```
  anchor_commitment: 31ed0b8b98715bbef656a67914fb7110518ed3beaf69384e149aa189e5edf04f
  ```
- **Failure Condition:** Any other value; a commitment that varies with a `protocol_version` string or a second-truncated timestamp (the 4.x form); a commitment computed over hex text rather than the 32 raw bytes of `root`.

---

**TL-002** — Anchor Commitment Excludes Payload Internals
- **Class:** REQUIRED
- **Spec Reference:** §16.3.2, §2.5.2
- **Description:** The commitment is a function of exactly the eight fields above. Given a node with a richly populated payload, no payload field enters the preimage.
- **Failure Condition:** Any payload field changes the commitment. This is both a protocol-surface violation and a confidentiality breach.

---

**TL-003** — Commitment Determinism Across Implementations
- **Class:** REQUIRED
- **Spec Reference:** §16.3.2, §5.1.1
- **Description:** Two independent implementations produce TL-001's value from the fixture. Because the preimage is the §5.1.1 field encoding — typed, self-delimiting, one domain prefix — there is no serialization to agree on beyond the specification.
- **Failure Condition:** Differing commitments for identical inputs.

---

### 3.2 Anchor Timing Enforcement

**TL-004** — Anchoring at Crystallization Boundary (G-14)
- **Class:** REQUIRED
- **Spec Reference:** §16.3.1, G-14
- **Description:** A conforming implementation MUST trigger transparency log anchoring at crystallization. Anchoring that does not occur at crystallization does not satisfy G-14.
- **Test Protocol:**
  1. Create a CognitiveNode and append segments until crystallization threshold
  2. Trigger crystallization
  3. Verify that a transparency log anchor submission is initiated as part of the crystallization state transition
  4. Verify that the `AnchorCommitment.crystallization_root` matches the `spine_root` at the time of crystallization
- **Expected Output:**
  ```
  anchor_submission_triggered: true
  anchor_commitment.crystallization_root == node.spine_root_at_crystallization
  ```
- **Failure Condition:** Anchoring is triggered before crystallization (premature), after crystallization completes as a separate async operation with no ordering guarantee (untimely), or not at all (absent). All three are G-14 violations.

---

**TL-005** — Crystallization Root Immutability in Anchor
- **Class:** REQUIRED
- **Spec Reference:** §16.3.1, §16.3.2
- **Description:** The `crystallization_root` in the `AnchorCommitment` MUST equal the `spine_root` at the moment of crystallization. Post-crystallization spine changes (if any are permitted by the implementation) MUST NOT alter the anchored root.
- **Inputs:**
  ```
  spine_root_at_crystallization: "a1b2c3d4..."
  spine_root_after_crystallization: "b2c3d4e5..."  (hypothetical post-crystallization change)
  ```
- **Expected Output:**
  ```
  anchor_commitment.crystallization_root: "a1b2c3d4..."  (the crystallization-time value)
  ```
- **Failure Condition:** `anchor_commitment.crystallization_root` reflects a post-crystallization spine state. The anchor must be a snapshot of the crystallization moment, not a live reference.

---

### 3.3 TransparencyLogAdapter Interface Conformance

**TL-006** — Adapter submit/verify Round-Trip
- **Class:** RECOMMENDED
- **Spec Reference:** §16.3.3
- **Description:** A conforming `TransparencyLogAdapter` implementation MUST support a submit → verify round-trip: a receipt produced by `submit()` MUST be verifiable by `verify()`.
- **Test Protocol:**
  1. Call `adapter.submit(anchor_commitment)` → receive `receipt`
  2. Call `adapter.verify(receipt)` → expect `true`
  3. Mutate one byte of `receipt.commitment_hash` → call `adapter.verify(mutated_receipt)` → expect `false`
- **Expected Output:**
  ```
  verify(receipt): true
  verify(mutated_receipt): false
  ```
- **Failure Condition:** `verify()` returns `true` for a mutated receipt, or `false` for a valid receipt.

---

**TL-007** — Adapter retrieve by node_id and crystallization_root
- **Class:** RECOMMENDED
- **Spec Reference:** §16.3.3
- **Description:** `adapter.retrieve(node_id, crystallization_root)` MUST return the receipt previously submitted for that node and root, or `None` if no such receipt exists.
- **Test Protocol:**
  1. Submit an anchor for node_id="A", crystallization_root="R1"
  2. `retrieve("A", "R1")` → expect the submitted receipt
  3. `retrieve("A", "R2")` → expect `None` (different root)
  4. `retrieve("B", "R1")` → expect `None` (different node)
- **Failure Condition:** `retrieve()` returns a receipt for a non-matching (node_id, crystallization_root) pair, or fails to return the correct receipt for a matching pair.

---

## 4. Witness Signature Vectors (§16.4)

Fixture (from the vector file): two records over the same node (`550e8400-e29b-41d4-a716-446655440000`, `episode`, `root` `13be960d1618ebc39541c6deec0d9c86f5ff8c4609538e8091f2644f52625ec7`, `root_version` 2, `sequence_index` 7, `logical_clock` 9, `witnessed_at` `2026-01-01T00:01:00.123000Z`), signed with the RFC 8032 §7.1 TEST 1 and TEST 2 secret keys — Ed25519 signatures are deterministic, so the signatures reproduce to the byte and the public keys are the RFC's.

| | witness-1 | witness-2 |
|---|---|---|
| `role` / `role_detail` | `SEAL_WITNESS` / NULL | `CUSTOM` / `notary` |
| `public_key` | `d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a` | `3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c` |
| `public_key_fingerprint` | `054f341a2fa584bb0c540fbf5232fcef6f76c5d5eb6a0663bacf8ccccf0d092b` | `b4f403514003c9ce67e0c3552e21ebfde117f88a550a03f1a387bfb495c0a35d` |
| `commitment_hash` | `7eaf9a74f7f6e83f7637cead3dbbb023b0a6c7fe56148b6833b9b3b64b63cf40` | `ab96bc7d5dce90af96a84393a332012d021830f666a4c690c92847667c3c83df` |
| `signature` | `fd5c273e0113a5e72e381da28895e04d904c396aa08edc18cf73e90ea47552cefe7f3dd4187640de8accf378ca38025884575082aff93cecdb71b41b3e43f303` | `647e093ffe0cf8c009957093d73727a53a8cc073b9bdb51a1bc085885f7a25a3c24059887913aee7483fe4517b34c58b61ab3e0be2b5fa6341d33461cceb860d` |

### 4.1 Witness Commitment Construction

**WS-001** — Witness Commitment
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2, §5.1.1
- **Description:** `witness_commitment = SHA3-256("WITNESS_COMMITMENT:v2:" ‖ STRING(witness_id) ‖ UUID(node_id) ‖ STRING(node_type) ‖ HASH(root) ‖ UINT(root_version) ‖ UINT(sequence_index) ‖ UINT(logical_clock) ‖ TIMESTAMP(witnessed_at) ‖ STRING(role) ‖ STRING(role_detail)|NULL)`. It binds the witness and the time: two witnesses of the same root have different commitments.
- **Expected Output:** the two `commitment_hash` values above.
- **Failure Condition:** Any other value; a commitment that does not change when `witness_id` or `witnessed_at` changes (the 4.x form).

---

**WS-002** — The Commitment Binds the Outermost Sealed Commitment and Its Version
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2
- **Description:** Changing `root` or `root_version` changes the commitment; an Episode root is never compared against a spine root and the mismatch called a forgery.
- **Failure Condition:** A commitment insensitive to either.

---

**WS-003** — Signature Form
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2, §4.6
- **Description:** `signature = Ed25519.Sign(sk, bytes.fromhex(commitment_hash))` — over the 32 raw bytes, the same form as HITL signatures. `public_key_fingerprint = SHA3-256(public_key)`. `signature_scheme` is `ed25519`, the one registered scheme.
- **Expected Output:** the two signatures above verify under the RFC 8032 public keys.
- **Failure Condition:** A signature over the hex text of the commitment; a record naming an unregistered scheme treated as valid.

### 4.2 Witness Validity and Threshold (G-12, G-11)

**WS-004** — Validity Is Four Executable Conditions (G-12)
- **Class:** REQUIRED
- **Spec Reference:** G-12
- **Description:** A record is valid iff: its commitment recomputes from its fields; `public_key_fingerprint` is SHA3-256 of `public_key`; the signature verifies under `public_key` over the raw commitment; `witness_id` is not the node's `authored_by`. A verifier reports the first condition that failed.
- **Test:** each of the two fixture records is valid for `authored_by = "author"`; each condition, failed on its own, makes it invalid.

---

**WS-005** — A Copied Record Is Cryptographically Invalid (G-12)
- **Class:** REQUIRED
- **Spec Reference:** G-12, §16.4.2
- **Description:** witness-1's record copied under `witness_id = "someone-else"` **with its commitment recomputed for the new name** fails *signature verification*: the signature was made over a commitment that named the original witness. A copy that does not recompute the commitment fails earlier, at recomputation. Either way the copy is invalid, not merely uncounted — this is the hole the 4.x commitment left open.
- **Failure Condition:** A copied record accepted as valid.

---

**WS-006** — An Empty or Unverifiable Signature Is Invalid (G-12)
- **Class:** REQUIRED
- **Spec Reference:** G-12
- **Description:** A record whose `signature` is empty, or does not verify, is invalid and MUST NOT count toward any threshold. (4.x let an empty signature pass.)

---

**WS-007** — Author-Distinctness (G-12)
- **Class:** REQUIRED
- **Spec Reference:** G-12
- **Description:** A record whose `witness_id` equals the node's `authored_by` is invalid — a self-witness is not an attestation.

---

**WS-008** — Threshold Counts a Maximum Matching of Distinct Names and Distinct Keys (G-11)
- **Class:** REQUIRED
- **Spec Reference:** G-11
- **Description:** With valid records A/k₁, A/k₂ and B/k₁, the count is **2** (A/k₂ and B/k₁). A/k₁ twice counts 1; A/k₁ and A/k₂ count 1; A/k₁ and B/k₁ count 1. A greedy pass that takes A/k₁ first finds 1 for the first case and is non-conformant.
- **Failure Condition:** Any count other than these; a count that depends on record order.

---

**WS-009** — CUSTOM Role Carries `role_detail`, and It Is Bound
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2, §16.4.4
- **Description:** witness-2's `CUSTOM` role has `role_detail` `notary`; changing it changes the commitment. A `CUSTOM` role with NULL `role_detail` is a different (and unhelpful) claim, not an error of form.

---

## 5. Cross-Node Chain Proof Vectors (§16.5)

### 5.1 ProofChain Construction

**CP-001** — Single-Link Chain (Baseline)
- **Class:** REQUIRED
- **Spec Reference:** §16.5.2
- **Description:** A `ProofChain` with a single link is the degenerate case. It MUST pass chain root integrity verification.
- **Inputs:**
  ```
  Link_0: {
    node_id: "550e8400-e29b-41d4-a716-446655440000",
    node_type: "episode",
    spine_root: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    sequence_index: 42,
    inclusion_proof: [valid InclusionProof per §9.2],
    parent_node_id: null
  }

  ProofChain: {
    chain_id: "chain-001",
    links: [Link_0],
    chain_root: SHA3-256(Link_0.spine_root),
    created_at: "2026-04-12T11:00:00Z",
    protocol_version: "5.1.0"
  }
  ```
- **Expected Output:**
  ```
  chain_valid: true
  ```
- **Failure Condition:** A single-link chain with correct `chain_root` is rejected. The verification algorithm must handle the degenerate case.

---

**CP-002** — Two-Link Chain with Direct Parentage
- **Class:** REQUIRED
- **Spec Reference:** §16.5.2, §16.5.3
- **Description:** A two-link chain where `links[1].parent_node_id == links[0].node_id` is a valid causally-ordered chain.
- **Inputs:**
  ```
  Link_0: {
    node_id: "node-A",
    node_type: "episode",
    spine_root: "root-A",
    sequence_index: 10,
    inclusion_proof: [valid],
    parent_node_id: null
  }

  Link_1: {
    node_id: "node-B",
    node_type: "episode",
    spine_root: "root-B",
    sequence_index: 5,
    inclusion_proof: [valid],
    parent_node_id: "node-A"   ← direct parentage to Link_0
  }

  chain_root = SHA3-256(UTF-8("root-A") | UTF-8("root-B"))
  ```
- **Expected Output:**
  ```
  chain_valid: true
  causal_order_satisfied: true  (B.parent_node_id == A.node_id)
  ```
- **Failure Condition:** The chain is rejected despite valid inclusion proofs and correct parentage. Note that `Link_1.sequence_index` (5) is less than `Link_0.sequence_index` (10) — this is valid because sequence_index is intra-node, not cross-node. The causal order is established by parentage, not by comparing sequence indices across nodes.

---

**CP-003** — Chain Root Integrity (G-13)
- **Class:** REQUIRED
- **Spec Reference:** §16.5.3 (condition 4), G-13
- **Description:** A `ProofChain` with an incorrect `chain_root` MUST be rejected, regardless of individual link validity.
- **Inputs:**
  ```
  ProofChain with:
    links: [Link_0, Link_1]  (both individually valid)
    chain_root: [incorrect value — not SHA3-256 of concatenated spine_roots]
  ```
- **Expected Output:**
  ```
  chain_valid: false
  rejection_reason: "chain_root integrity failure (G-13)"
  ```
- **Failure Condition:** The chain is accepted despite an incorrect `chain_root`. A non-conforming implementation that skips chain root verification cannot detect chain tampering.

---

**CP-004** — Causal Order Violation Detection
- **Class:** REQUIRED
- **Spec Reference:** §16.5.3 (condition 2)
- **Description:** A `ProofChain` where consecutive links have no causal relationship (no parentage, no cross-reference) MUST be rejected.
- **Inputs:**
  ```
  Link_0: { node_id: "node-A", parent_node_id: null, ... }
  Link_1: { node_id: "node-B", parent_node_id: "node-C", ... }  ← parent is neither node-A nor in the chain
  chain_root: [correct SHA3-256 of concatenated spine_roots]
  ```
- **Expected Output:**
  ```
  chain_valid: false
  rejection_reason: "causal order violation — link 1 has no causal relationship to link 0"
  ```
- **Failure Condition:** The chain is accepted. A non-conforming implementation that skips causal order verification accepts fabricated proof chains.

---

**CP-005** — Inclusion Proof Failure Invalidates Link
- **Class:** REQUIRED
- **Spec Reference:** §16.5.3 (condition 1)
- **Description:** A `ProofChain` where any link's `inclusion_proof` fails verification MUST be rejected, even if all other aspects of the chain are valid.
- **Inputs:**
  ```
  ProofChain with:
    Link_0: valid inclusion_proof
    Link_1: tampered inclusion_proof (one sibling hash modified)
    chain_root: correct
    causal_order: correct
  ```
- **Expected Output:**
  ```
  chain_valid: false
  rejection_reason: "link 1 inclusion proof verification failed"
  ```
- **Failure Condition:** The chain is accepted despite a failed inclusion proof. This means the chain does not actually prove the claimed node states.

---

### 5.2 Cross-Type Chain Proof

**CP-006** — Chain Spanning Multiple Node Types
- **Class:** REQUIRED
- **Spec Reference:** §16.5.1, §2.5.4
- **Description:** A `ProofChain` MUST support links with different `node_type` values. The verification algorithm is type-agnostic.
- **Inputs:**
  ```
  Link_0: { node_id: "signal-001", node_type: "signal", spine_root: "root-S", ... }
  Link_1: { node_id: "episode-001", node_type: "episode", spine_root: "root-E",
            parent_node_id: "signal-001", ... }
  ```
- **Expected Output:**
  ```
  chain_valid: true
  ```
- **Failure Condition:** The chain is rejected because links have different `node_type` values. A non-conforming implementation that enforces type homogeneity in proof chains violates the CognitiveNode-generic design principle.

---

### 5.3 Cross-Architecture Chain Proof

**CP-007** — Cross-Architecture Proof Verification
- **Class:** REQUIRED
- **Spec Reference:** §16.5.4, §2.5.4
- **Description:** A `ProofChain` generated by Implementation A MUST be verifiable by Implementation B using only protocol-surface primitives (SHA3-256, Merkle algorithm from §5).
- **Test Protocol:**
  1. Implementation A generates a `ProofChain` with two links, each with valid inclusion proofs
  2. Implementation A serializes the `ProofChain` to a canonical format
  3. Implementation B deserializes and verifies the `ProofChain`
  4. Implementation B MUST NOT require access to Implementation A's internal state, storage, or key material to verify the chain
- **Expected Output:**
  ```
  Implementation B verification result: chain_valid: true
  ```
- **Failure Condition:** Implementation B cannot verify the chain, or requires Implementation A's internal state to do so. The chain proof must be self-contained and verifiable from the protocol surface alone.

---

**CP-008** — Temporal Ordering via anchor_receipt When Logical Clocks Are Incommensurable
- **Class:** RECOMMENDED
- **Spec Reference:** §16.5.3 (condition 3), §16.5.4
- **Description:** When a `ProofChain` spans nodes from different AI architectures with independent logical clocks, `anchor_receipt.log_timestamp` values MUST be used to establish temporal ordering.
- **Inputs:**
  ```
  Link_0: {
    node_id: "arch-A-node-1",
    logical_clock: 5000,              ← Architecture A's clock
    anchor_receipt: { log_timestamp: "2026-04-12T10:00:00Z" }
  }
  Link_1: {
    node_id: "arch-B-node-1",
    logical_clock: 100,               ← Architecture B's independent clock (lower value, later time)
    anchor_receipt: { log_timestamp: "2026-04-12T11:00:00Z" }
  }
  ```
- **Expected Output:**
  ```
  temporal_order: Link_0 precedes Link_1
  ordering_basis: anchor_receipt.log_timestamp (logical clocks incommensurable across architectures)
  chain_valid: true
  ```
- **Failure Condition:** The chain is rejected because `Link_1.logical_clock < Link_0.logical_clock`. A non-conforming implementation that applies intra-architecture logical clock comparison across architecture boundaries will incorrectly reject valid cross-architecture chains.

---

## 6. Governance Rule Enforcement Matrix

The following matrix maps each Phase 3 governance rule to the test vectors that verify its enforcement. A conforming implementation MUST pass all REQUIRED vectors for each rule.

| Governance Rule | Description | Test Vectors | Class |
|----------------|-------------|-------------|-------|
| **G-11** | Witness threshold (workspace-configured) | WS-005, WS-006 | REQUIRED |
| **G-12** | Witness commitment integrity | WS-004, WS-005 | REQUIRED |
| **G-13** | Chain root integrity | CP-003 | REQUIRED |
| **G-14** | Anchoring at crystallization | TL-004, TL-005 | REQUIRED |
| **G-15** | Key version monotonicity | KH-004 | REQUIRED |
| **G-16** | Node type in key derivation | KH-002, KH-005, KH-006 | REQUIRED |

---

## 7. Conformance Levels

A conforming implementation declares one of two conformance levels:

### Level 1: Protocol Conformance
The implementation passes all REQUIRED vectors. It correctly implements the protocol surface: key derivation, anchor commitment construction, witness commitment construction, witness record integrity, and chain proof verification.

### Level 2: Full Conformance
The implementation passes all REQUIRED and RECOMMENDED vectors. It additionally implements the `TransparencyLogAdapter` round-trip (TL-006, TL-007), the `CUSTOM` role advisory (WS-007), and cross-architecture temporal ordering via anchor receipts (CP-008).

---

## 8. Test Vector Publication Protocol

For vectors that require cross-implementation consistency (KH-001, KH-006, WS-001, TL-003), the verification protocol is:

1. Each conforming implementation computes the specified output for the given inputs
2. The output is published. No ASTP conformance registry exists yet; reference values will be published as vector files in this repository in a later release
3. Implementations compare their output against all published values
4. Discrepancies trigger an investigation into HKDF parameterization, serialization format, or encoding differences

The first implementation to publish a value for a given vector establishes the **reference value**. Subsequent implementations that produce a different value are non-conforming until the discrepancy is resolved (either the new implementation corrects its parameterization, or a spec ambiguity is identified and resolved via a spec errata).

---

## 9. Out of Scope

The following are explicitly NOT covered by these conformance vectors:

- **Storage adapter conformance** — not covered here. No ASI conformance suite has been published; adapter requirements are stated in SPEC §15
- **Phase 1-2 verification** — covered by the existing `DeltaVerifier` five-test gate (§9.1)
- **Signing algorithm correctness** — implementation-defined (§2.5.3); implementations are responsible for their own signing algorithm conformance
- **Transparency log availability** — the `TransparencyLogAdapter` interface is tested for correct behavior, not for log availability or latency
- **Key management security** — HSM, KMS, and key storage security are implementation concerns, not protocol concerns

---

## Appendix A: Canonical Serialization for Commitment Hashing

Every commitment in this document is built with the canonical field encoding of SPEC §5.1.1: one domain prefix, then each field as a one-byte type tag and its payload. There is no JSON, no delimiter and no textual rendering of a number or a hash anywhere in a preimage; a hash enters as its 32 raw bytes and a timestamp as UTC milliseconds. The reference tests reproduce every vector here with `hashlib` and a from-prose encoder that imports nothing from the `astp` package (`tests/conformance/test_witness_anchor_v2_vectors.py`).

The 4.x serializations (sorted JSON for the anchor commitment; pipe-delimited UTF-8 for the witness commitment) remain the definitions of records written under 4.x (SPEC §16.3.2, §16.4.2) and are not used for new records.

---

## Appendix B: Reference Fixture

The reference fixture for the anchor and witness vectors is the one the vector file uses throughout: Episode `550e8400-e29b-41d4-a716-446655440000`, seven Segments with fixed `node_id`s `00000000-0000-4000-8000-00000000000i` and `content_hash = SHA3-256("leaf-i")`, `schema_version` `1.2.0`, parent the Episode. Its `hash_version` 2 leaf hashes, `spine_algorithm_version` 2 spine root, manifests and Episode root are pinned in `vectors/5.0.0/seal-constructions.json` and in [`CONFORMANCE-REPRODUCIBILITY.md`](./CONFORMANCE-REPRODUCIBILITY.md) RP-009–RP-011. Fixed `node_id`s are for reproducibility only; real `node_id`s MUST be random (SPEC §5.2).

---

*ASTP Conformance Test Vectors are maintained by Scorched Earth Labs.*
*Vector set version: 2.0.0 | Written against SPEC.md 5.1.0*