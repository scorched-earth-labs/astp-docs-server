# ASTP — Phase 3 Conformance Test Vectors

**Version:** 1.0.0
**Status:** Working Draft
**Authors:** Scorched Earth Labs / Clotho
**Date:** 2026-04-12
**Applies To:** SPEC.md v2.3.0-draft, Phase 3 Trust Infrastructure (§16)
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

### 3.1 AnchorCommitment Construction

**TL-001** — AnchorCommitment Field Completeness
- **Class:** REQUIRED
- **Spec Reference:** §16.3.2
- **Description:** A conforming implementation MUST produce an `AnchorCommitment` containing exactly the protocol-specified fields and no payload internals.
- **Inputs:**
  ```
  node_id: "550e8400-e29b-41d4-a716-446655440000"
  node_type: "episode"
  workspace_id: "ws-test-001"
  crystallization_root: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
  crystallization_sequence: 42
  logical_clock: 1000
  wall_clock: "2026-04-12T11:00:00Z"
  protocol_version: "2.3.0"
  ```
- **Expected Output:**
  ```
  AnchorCommitment {
    node_id: "550e8400-e29b-41d4-a716-446655440000",
    node_type: "episode",
    workspace_id: "ws-test-001",
    crystallization_root: "a1b2c3d4e5f6...",
    crystallization_sequence: 42,
    logical_clock: 1000,
    wall_clock: "2026-04-12T11:00:00Z",
    protocol_version: "2.3.0"
  }
  ```
- **Failure Condition:** The `AnchorCommitment` contains payload fields (segment content, agent reasoning traces, implementation-specific metadata). Payload internals in the anchor commitment violate the protocol/implementation boundary.

---

**TL-002** — AnchorCommitment Excludes Payload Internals
- **Class:** REQUIRED
- **Spec Reference:** §16.3.2, §2.5.2
- **Description:** The `AnchorCommitment` MUST NOT contain `NodePayload` fields. The protocol anchors node structure, not node content.
- **Test:** Given a node with a richly populated payload (e.g., an `EpisodePayload` with title, participants, segment content), the `AnchorCommitment` produced at crystallization MUST contain only the fields specified in §16.3.2.
- **Failure Condition:** Any payload field appears in the `AnchorCommitment`. This is both a protocol surface violation and a potential privacy/confidentiality breach.

---

**TL-003** — Commitment Hash Determinism
- **Class:** REQUIRED
- **Spec Reference:** §16.3.3 (AnchorReceipt.commitment_hash)
- **Description:** SHA3-256 of the `AnchorCommitment` MUST be deterministic — identical inputs produce identical commitment hashes across implementations and invocations.
- **Inputs:** The `AnchorCommitment` from TL-001.
- **Expected Output:**
  ```
  commitment_hash: [implementations compute and cross-verify this value]
  ```
- **Verification Protocol:** Two independent implementations MUST produce identical `commitment_hash` for the same `AnchorCommitment`. This requires agreement on the serialization format used as input to SHA3-256 — conforming implementations MUST use canonical JSON serialization with keys in lexicographic order and no whitespace.
- **Failure Condition:** Two implementations produce different `commitment_hash` for identical `AnchorCommitment` inputs. This indicates a serialization disagreement — cross-architecture receipt verification will fail.

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

### 4.1 WitnessCommitment Construction

**WS-001** — WitnessCommitment Hash Determinism
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2
- **Description:** The `WitnessCommitment` hash MUST be deterministic across implementations. The commitment scheme (UTF-8 fields separated by `|`, then SHA3-256) MUST be applied identically.
- **Inputs:**
  ```
  node_id: "550e8400-e29b-41d4-a716-446655440000"
  node_type: "episode"
  spine_root: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
  sequence_index: 42
  logical_clock: 1000
  role: "REVIEWER"
  ```
- **Commitment Construction:**
  ```
  preimage = UTF-8("550e8400-e29b-41d4-a716-446655440000")
           | UTF-8("|")
           | UTF-8("episode")
           | UTF-8("|")
           | UTF-8("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2")
           | UTF-8("|")
           | UTF-8("42")
           | UTF-8("|")
           | UTF-8("1000")
           | UTF-8("|")
           | UTF-8("REVIEWER")

  commitment_hash = SHA3-256(preimage)
  ```
- **Expected Output:**
  ```
  commitment_hash: [implementations compute and cross-verify this value]
  ```
- **Verification Protocol:** Two independent conforming implementations MUST produce identical `commitment_hash` for these inputs.
- **Failure Condition:** Different implementations produce different `commitment_hash`. This means witness records from one implementation cannot be verified by another — cross-architecture witness verification is broken.

---

**WS-002** — WitnessCommitment Binds to Specific spine_root
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2
- **Description:** A witness commitment for spine_root R1 MUST be cryptographically distinct from a commitment for spine_root R2, even if all other fields are identical.
- **Inputs:** Same as WS-001, but with two spine_root values:
  ```
  spine_root_1: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
  spine_root_2: "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"
  ```
- **Expected Output:**
  ```
  commitment_hash(spine_root_1) != commitment_hash(spine_root_2)
  ```
- **Failure Condition:** Both spine roots produce the same commitment hash. A witness signature would then be valid for any spine root, defeating the purpose of the witness record.

---

**WS-003** — WitnessCommitment Binds to Role
- **Class:** REQUIRED
- **Spec Reference:** §16.4.2, §16.4.4
- **Description:** A witness commitment for role REVIEWER MUST be cryptographically distinct from a commitment for role AUDITOR, even if all other fields are identical.
- **Inputs:** Same as WS-001, but with two role values:
  ```
  role_1: "REVIEWER"
  role_2: "AUDITOR"
  ```
- **Expected Output:**
  ```
  commitment_hash(role_1) != commitment_hash(role_2)
  ```
- **Failure Condition:** Both roles produce the same commitment hash. Role confusion becomes possible — a REVIEWER signature could be presented as an AUDITOR signature.

---

### 4.2 WitnessRecord Integrity (G-12)

**WS-004** — Commitment Hash Verification (G-12)
- **Class:** REQUIRED
- **Spec Reference:** §16.4.3, G-12
- **Description:** A conforming implementation MUST reject a `WitnessRecord` where `commitment_hash` does not match the recomputed `WitnessCommitment` over the record's fields.
- **Setup:** A valid `WitnessRecord` with correct `commitment_hash`.
- **Inputs:**
  ```
  Variant A: WitnessRecord with correct commitment_hash (valid)
  Variant B: WitnessRecord with commitment_hash mutated by 1 bit (tampered)
  Variant C: WitnessRecord with spine_root field changed but commitment_hash unchanged (field/hash mismatch)
  ```
- **Expected Output:**
  ```
  Variant A: VALID
  Variant B: INVALID — commitment_hash does not match recomputed value (G-12)
  Variant C: INVALID — commitment_hash does not match recomputed value (G-12)
  ```
- **Failure Condition:** Variant B or C is accepted as valid. A non-conforming implementation that skips commitment hash verification cannot detect tampered witness records.

---

**WS-005** — Invalid WitnessRecords Do Not Count Toward Threshold (G-11, G-12)
- **Class:** REQUIRED
- **Spec Reference:** G-11, G-12
- **Description:** Invalid `WitnessRecord` entries MUST NOT count toward the `min_counter_signatures` threshold for sealing.
- **Setup:**
  ```
  workspace policy: min_counter_signatures = 2 for node_type="episode"
  WitnessRecord_1: valid (commitment_hash correct, signature valid)
  WitnessRecord_2: invalid (commitment_hash tampered — G-12 violation)
  WitnessRecord_3: invalid (duplicate witness_id as WitnessRecord_1 — same witness, not distinct)
  ```
- **Test:** Attempt to seal the node with WitnessRecord_1 + WitnessRecord_2.
- **Expected Output:**
  ```
  seal_attempt: REJECTED — only 1 valid witness record with distinct witness_id (threshold requires 2)
  ```
- **Failure Condition:** The seal succeeds with 1 valid + 1 invalid witness record. A non-conforming implementation that counts invalid records toward the threshold allows threshold bypass.

---

**WS-006** — Witness Threshold Requires Distinct witness_id Values (G-11)
- **Class:** REQUIRED
- **Spec Reference:** G-11
- **Description:** Multiple `WitnessRecord` entries from the same `witness_id` count as ONE witness toward the threshold, regardless of how many records exist.
- **Setup:**
  ```
  workspace policy: min_counter_signatures = 2
  WitnessRecord_1: { witness_id: "agent-alpha", role: "REVIEWER", ... }  (valid)
  WitnessRecord_2: { witness_id: "agent-alpha", role: "AUDITOR", ... }   (valid, same agent)
  ```
- **Test:** Attempt to seal with WitnessRecord_1 + WitnessRecord_2.
- **Expected Output:**
  ```
  seal_attempt: REJECTED — only 1 distinct witness_id (threshold requires 2 distinct)
  ```
- **Failure Condition:** The seal succeeds. A single agent witnessing twice should not satisfy a two-witness threshold — that defeats the purpose of multi-party witness requirements.

---

**WS-007** — CUSTOM Role Requires role_detail
- **Class:** RECOMMENDED
- **Spec Reference:** §16.4.4
- **Description:** A `WitnessRecord` with `role=CUSTOM` SHOULD include a non-empty `role_detail` field describing the implementation-defined witness semantics.
- **Inputs:**
  ```
  Variant A: { role: "CUSTOM", role_detail: "consensus-quorum-v1" }  (valid)
  Variant B: { role: "CUSTOM", role_detail: null }                   (missing detail)
  Variant C: { role: "CUSTOM", role_detail: "" }                     (empty detail)
  ```
- **Expected Output:**
  ```
  Variant A: ACCEPTED
  Variant B: WARNING — CUSTOM role without role_detail
  Variant C: WARNING — CUSTOM role with empty role_detail
  ```
- **Note:** This is RECOMMENDED, not REQUIRED. Implementations MAY treat Variants B and C as errors. The protocol does not mandate rejection, but conforming implementations SHOULD surface the missing detail as a diagnostic.

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
    protocol_version: "2.3.0"
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
2. The output is published to the ASTP conformance registry (location TBD)
3. Implementations compare their output against all published values
4. Discrepancies trigger an investigation into HKDF parameterization, serialization format, or encoding differences

The first implementation to publish a value for a given vector establishes the **reference value**. Subsequent implementations that produce a different value are non-conforming until the discrepancy is resolved (either the new implementation corrects its parameterization, or a spec ambiguity is identified and resolved via a spec errata).

---

## 9. Out of Scope

The following are explicitly NOT covered by these conformance vectors:

- **Storage adapter conformance** — covered by the ASI conformance suite (separate document)
- **Phase 1-2 verification** — covered by the existing `DeltaVerifier` five-test gate (§9.1)
- **Signing algorithm correctness** — implementation-defined (§2.5.3); implementations are responsible for their own signing algorithm conformance
- **Transparency log availability** — the `TransparencyLogAdapter` interface is tested for correct behavior, not for log availability or latency
- **Key management security** — HSM, KMS, and key storage security are implementation concerns, not protocol concerns

---

## Appendix A: Canonical Serialization for Commitment Hashing

For vectors requiring deterministic hash computation across implementations (TL-003, WS-001), the following canonical serialization MUST be used:

**AnchorCommitment serialization:** JSON with keys in lexicographic order, no whitespace, datetime fields in ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`), integer fields as JSON numbers.

**WitnessCommitment serialization:** Pipe-delimited UTF-8 string as specified in §16.4.2. Field order is fixed: `node_id|node_type|spine_root|sequence_index|logical_clock|role`. Integer fields are serialized as their decimal string representation.

These serialization rules are protocol-mandatory for commitment hashing. Implementations that use different serialization (e.g., protobuf, CBOR, whitespace-formatted JSON) will produce non-matching commitment hashes and fail cross-architecture verification.

---

## Appendix B: Reference Test Node

The following `CognitiveNode` is used as the reference node across multiple test vectors:

```
node_id:          "550e8400-e29b-41d4-a716-446655440000"
node_type:        "episode"
schema_version:   "2.0.0"
sequence_index:   42
tree_leaf_index:  7
content_hash:     "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
authored_by:      "agent-test-001"
created_at:       "2026-04-12T10:00:00Z"
sealed_at:        "2026-04-12T11:00:00Z"
parent_node_id:   null
workspace_id:     "ws-test-001"
```

The leaf hash for this reference node (computed per §5.2) is:
```
leaf_hash: [implementations compute and cross-verify per KH-006 protocol]
```

---

*ASTP Conformance Test Vectors are maintained by Scorched Earth Labs.*
*Vector set version: 1.0.0 | Applies to SPEC.md: v2.3.0-draft*