# ASTP — Phase 3 Implementation Guide

**Version:** 2.0.0
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-19
**Applies To:** SPEC.md 5.1.0 §16 (Trust Infrastructure) and §4.6 (HITL, Appendix C). The anchor and witness constructions below are the 5.0.0 forms; the 4.x forms remain in SPEC §16.3.2 / §16.4.2 as the definitions of records already written.
**Conformance Reference:** Phase 3 Conformance Test Vectors v1.0.0

---

## 1. Purpose and Scope

This guide walks implementors through building a Phase 3 conforming implementation of ASTP. It covers the construction sequence, non-obvious design decisions, and integration points for each Phase 3 pillar.

**Audience:** Engineers implementing ASTP on a new AI architecture, or extending an existing Phase 1-2 implementation to Phase 3.

**What this guide is not:** A tutorial on cryptographic primitives, a language-specific SDK guide, or a storage adapter guide. Those are outside its scope.

**How to use this guide:** Work through sections 3–6 in order. Each section ends with a conformance checkpoint that maps to the test vectors in the Conformance Test Vectors document. Do not proceed to the next section until the current section's checkpoint passes.

---

## 2. Prerequisites

### 2.1 Phase 1-2 Conformance Required

Phase 3 is additive. It does not replace or modify Phase 1-2 machinery — it extends it. Before implementing Phase 3, your implementation MUST pass the Phase 1-2 conformance gate:

- `DeltaVerifier` five-test gate (§9.1)
- Dual Index semantics: `sequence_index` immutable and in hash, `tree_leaf_index` mutable and NOT in hash
- Leaf hash construction exactly as SPEC §5.2: the length-prefixed preimage over `node_id`, `node_type`, `schema_version`, `sequence_index`, `content_hash`, `sealed_at` and `parent_node_id`. There is no `prev_leaf_hash` — a leaf does not chain to its predecessor (SPEC §3.4.1); position is bound by `sequence_index` inside the preimage
- Spine Merkle: SHA3-256 binary Merkle tree with deterministic leaf ordering by `sequence_index`
- `ContentDelta` records written on every append
- `CrystallizationDelta` written at the crystallization boundary
- `CognitiveNode` schema with all core fields present

If your Phase 1-2 implementation is not conforming, Phase 3 will not be either — the trust infrastructure signs and chains the outputs of Phase 1-2 machinery.

### 2.2 CognitiveNode-Generic Design

Your implementation MUST be designed against `CognitiveNode`, not `Episode`. If you are extending an existing Episode-only implementation, audit your codebase for the following before proceeding:

- Any hardcoded `"episode"` string in key derivation paths → must become `node_type` parameter
- Any `episode_id` field in audit or retrieval records → must become `node_id`
- Any `episode`-scoped language in the key hierarchy → must become `node`-scoped

Phase 3 introduces `node_type` as a first-class participant in key derivation (G-16). An implementation that hard-codes `"episode"` in its key derivation will fail KH-002 and KH-006.

### 2.3 Cryptographic Dependencies

Phase 3 requires:

| Primitive | Specification |
|-----------|--------------|
| HKDF | RFC 5869, instantiated with SHA3-256 as the hash function |
| SHA3-256 | FIPS 202 |
| Signing | Ed25519 (RFC 8032) over the 32 raw bytes of a commitment — the one registered scheme (§2.5.2, §16.4.2) |
| Canonical field encoding | SPEC §5.1.1 — the byte form of every commitment; `astp.protocol.encoding` |
| Canonical JSON | RFC 8785 + NFC, where a preimage carries a document (§5.1.2); not used by the §16 commitments |

> **Note on HKDF instantiation:** RFC 5869 specifies HKDF with a pluggable hash function. ASTP uses SHA3-256, not SHA-256. Verify your HKDF library supports SHA3-256 as the underlying PRF — some libraries default to SHA-256 and require explicit configuration. This is the most common source of KH-001/KH-006 failures.

---

## 3. Key Hierarchy

### 3.1 Overview

The Phase 3 key hierarchy produces cryptographic keys at three levels: workspace, node, and seal. Each level is derived from the level above using HKDF, with type-specific context strings that prevent key confusion across node types (G-16).

```
Root Key Material
      │
      ▼ HKDF(salt=workspace_id, info="ariadne.workspace.v1")
Workspace Key
      │
      ▼ HKDF(salt=node_id, info="ariadne.node.v1:{node_type}")
Node Key
      │
      ▼ HKDF(salt=spine_root_at_seal, info="ariadne.seal.v1")
Seal Key
```

### 3.2 HKDF Parameterization

All HKDF derivations in ASTP use the following fixed parameters unless the level-specific description overrides them:

```
Hash function:  SHA3-256
Output length:  32 bytes
```

The `salt` and `info` parameters are level-specific and are the primary mechanism for domain separation. **The `info` string is protocol-mandatory** — it is part of the protocol surface and must be encoded exactly as specified (UTF-8, no trailing null byte, no length prefix).

### 3.3 Workspace Key Derivation

```
workspace_key = HKDF(
    ikm   = root_key_material,      # 32 bytes from your KMS/HSM
    salt  = UTF-8(workspace_id),    # e.g., "ws-prod-001"
    info  = UTF-8("ariadne.workspace.v1"),
    len   = 32
)
```

**Root key material management** is implementation-defined (§2.5.3). The protocol does not prescribe how root key material is generated, stored, or rotated — only how it is used as HKDF input. Common implementations use:
- A hardware security module (HSM) as the root key store
- A KMS-managed root key with envelope encryption for workspace keys
- A software key store for development/testing environments

> **Protocol boundary:** The root key material itself is not a protocol concept. The workspace key is the first protocol-surface artifact. Everything above the workspace key derivation is implementation space.

### 3.4 Node Key Derivation

```
node_key = HKDF(
    ikm   = workspace_key,
    salt  = UTF-8(node_id),
    info  = UTF-8("ariadne.node.v1:" + node_type),   # e.g., "ariadne.node.v1:episode"
    len   = 32
)
```

**The `node_type` MUST appear in the `info` string.** This is G-16. The colon-prefixed `node_type` in the info string is what creates cryptographic domain separation between node types. A node key derived for `node_type="episode"` is cryptographically distinct from one derived for `node_type="signal"` even with identical `node_id` and `workspace_id`.

**Registered `node_type` values for info string construction:**

| node_type | info string |
|-----------|-------------|
| `episode` | `ariadne.node.v1:episode` |
| `signal` | `ariadne.node.v1:signal` |
| `artifact` | `ariadne.node.v1:artifact` |
| `agent` | `ariadne.node.v1:agent` |

Future node types follow the same pattern: `ariadne.node.v1:{node_type}`. The protocol does not maintain a closed registry of node types — the info string construction rule is the registry.

### 3.5 Seal Key Derivation

```
seal_key = HKDF(
    ikm   = node_key,
    salt  = spine_root_at_seal,     # 32-byte hash, not UTF-8 encoded
    info  = UTF-8("ariadne.seal.v1"),
    len   = 32
)
```

**The `spine_root_at_seal` is used as raw bytes**, not hex-encoded. This is the one derivation where the salt is binary rather than a UTF-8 string. The seal key is bound to a specific node state — a seal key derived from `spine_root_1` is different from one derived from `spine_root_2`, even for the same node.

> **Why bind the seal key to the spine root?** The seal is a commitment that the node's state is frozen at a specific point. Binding the seal key to the `spine_root` means the key material itself is state-dependent — you cannot produce a valid seal for a different spine root without a different key. This makes seal forgery require either key compromise or spine root collision.

### 3.6 Key Version Management (G-15)

Each node key is associated with a `key_version` stored in a `NodeKeyRecord`. The key version is a monotonically increasing integer. Your implementation MUST enforce:

```
BEFORE writing a new NodeKeyRecord for node_id N:
    current_max = query max(key_version) WHERE node_id = N
    IF new_key_version <= current_max:
        REJECT — G-15 violation (key version rollback or duplicate)
    ELSE:
        ACCEPT and write
```

Key rotation is triggered by implementation policy (e.g., time-based, event-based). The protocol does not specify when to rotate — only that version numbers never go backward.

### 3.7 Conformance Checkpoint: Key Hierarchy

Run vectors **KH-001 through KH-006** before proceeding.

| Vector | What it verifies |
|--------|----------------|
| KH-001 | Workspace key HKDF parameterization is correct |
| KH-002 | Node type isolation: different types → different keys |
| KH-003 | Seal key binds to spine_root |
| KH-004 | Key version monotonicity enforcement (G-15) |
| KH-005 | No code path derives a node key without node_type |
| KH-006 | Cross-implementation HKDF consistency |

KH-006 requires a second conforming implementation to compare against. If you are the first implementation, publish your KH-001 output to the conformance registry and proceed — KH-006 will be verified when a second implementation is available.

---

## 4. Transparency Log Anchoring

### 4.1 Overview

Transparency log anchoring provides external, independently verifiable proof that a node's state existed at a specific point in time. The anchor is submitted at crystallization — the moment the node's state is frozen — and the resulting receipt is stored with the node.

The protocol defines the `TransparencyLogAdapter` interface (§16.3.3). Your implementation provides a concrete adapter for your chosen transparency log (a Merkle tree-based append-only log, a blockchain, a trusted timestamping service, etc.).

### 4.2 The TransparencyLogAdapter Interface

```python
class TransparencyLogAdapter(ABC):

    def submit(self, commitment: AnchorCommitment) -> AnchorReceipt:
        """
        Submit an AnchorCommitment to the transparency log.
        Returns an AnchorReceipt containing the log's inclusion proof.
        MUST be called at crystallization (G-14).
        """
        ...

    def verify(self, receipt: AnchorReceipt) -> bool:
        """
        Verify that a receipt is valid against the transparency log.
        Returns True if the receipt is valid, False otherwise.
        """
        ...

    def retrieve(self, node_id: str, crystallization_root: str) -> Optional[AnchorReceipt]:
        """
        Retrieve the receipt for a specific (node_id, crystallization_root) pair.
        Returns None if no such receipt exists.
        """
        ...
```

Implement this interface for your chosen log backend. The protocol does not constrain the log technology — only the interface contract.

### 4.3 Anchor Commitment Construction

The anchor commitment is what the transparency log receives at the crystallization boundary: node structure only — **no payload internals** (TL-002). Build it from the seal you just computed, never from live node state:

```python
from astp.protocol.anchor_v2 import compute_anchor_commitment_v2

def anchor_commitment_for(seal, node, workspace_id: str, logical_clock: int, anchored_at) -> str:
    return compute_anchor_commitment_v2(
        node_id=node.node_id,
        node_type=node.node_type,
        workspace_id=workspace_id,
        root=seal.episode_root_hash,          # the outermost sealed commitment — for an Episode, the Episode root
        root_version=2,                        # the construction that produced it (spine_algorithm_version)
        crystallization_sequence=seal.leaf_count - 1,
        logical_clock=logical_clock,
        anchored_at=anchored_at,               # timezone-aware; hashed at millisecond precision
    )
```

> **Critical:** `root` MUST be the value the seal recorded, captured before any post-crystallization mutation could occur, and `root_version` MUST name the construction that produced it — a witness record for the same crystallization binds the same pair, which is what makes a log receipt and a witness record attest the same object.

### 4.4 Commitment Computation

```
anchor_commitment = SHA3-256( "ANCHOR_COMMITMENT:v2:"
    ‖ UUID(node_id) ‖ STRING(node_type) ‖ STRING(workspace_id)
    ‖ HASH(root) ‖ UINT(root_version)
    ‖ UINT(crystallization_sequence) ‖ UINT(logical_clock) ‖ TIMESTAMP(anchored_at) )
```

under the canonical field encoding of SPEC §5.1.1 — typed, self-delimiting fields behind one domain prefix; a hash enters as its 32 raw bytes, a timestamp as UTC milliseconds. There is no JSON and no field-order or whitespace question to get wrong. Expected value for the reference fixture: CONFORMANCE.md TL-001. The 4.x form (sorted JSON carrying a `protocol_version` literal and a second-truncated timestamp) is retained in SPEC §16.3.2 only as the definition of receipts already issued.

### 4.5 Wiring Anchoring to Crystallization (G-14)

The transparency log anchor submission MUST be part of the crystallization state transition. It is not a background job, a post-commit hook, or an eventually-consistent operation. The ordering requirement is:

```
1. Compute spine_root (final state)
2. Write the `CrystallizationDelta` to storage
3. Build AnchorCommitment from crystallization_root = spine_root
4. Submit AnchorCommitment to TransparencyLogAdapter → receive AnchorReceipt
5. Store AnchorReceipt on the CognitiveNode
6. Mark crystallization complete
```

If step 4 fails (log unavailable), your implementation has two protocol-compliant options:
- **Blocking:** Fail the crystallization and retry. The node remains un-crystallized until anchoring succeeds.
- **Deferred with commitment:** Write the `AnchorCommitment` to a durable queue and complete crystallization, but mark the node as `CRYSTALLIZED_PENDING_ANCHOR` until the receipt is received and stored.

The deferred option is implementation-defined. The protocol requires only that the `AnchorCommitment` submitted to the log uses the `spine_root` at crystallization time — not a later root.

### 4.6 Conformance Checkpoint: Transparency Log Anchoring

Run vectors **TL-001 through TL-007** before proceeding.

| Vector | What it verifies |
|--------|----------------|
| TL-001 | AnchorCommitment contains exactly the protocol-specified fields |
| TL-002 | AnchorCommitment excludes payload internals |
| TL-003 | Commitment hash is deterministic across implementations |
| TL-004 | Anchoring is triggered at crystallization (G-14) |
| TL-005 | crystallization_root is immutable in the anchor |
| TL-006 | Adapter submit/verify round-trip (RECOMMENDED) |
| TL-007 | Adapter retrieve by (node_id, crystallization_root) (RECOMMENDED) |

---

## 5. Witness Signatures

### 5.1 Overview

Witness signatures provide multi-party attestation that a node's state was observed and verified at a specific point. The witness record includes a cryptographic commitment that binds the witness to a specific `spine_root`, `sequence_index`, and role — preventing a witness record from being replayed against a different node state.

### 5.2 Witness Commitment Construction

A witness record is a claim by one party about what it saw: **this witness** saw **this root** for **this node** at **this time**, in **this role**. The commitment binds all five:

```
witness_commitment = SHA3-256( "WITNESS_COMMITMENT:v2:"
    ‖ STRING(witness_id) ‖ UUID(node_id) ‖ STRING(node_type)
    ‖ HASH(root) ‖ UINT(root_version)
    ‖ UINT(sequence_index) ‖ UINT(logical_clock) ‖ TIMESTAMP(witnessed_at)
    ‖ STRING(role) ‖ STRING(role_detail) | NULL )
```

`root` is the node's outermost sealed commitment (the Episode root for an Episode; the spine root for a node type with no manifests) and `root_version` the construction that produced it. Because `witness_id` and `witnessed_at` are bound, two witnesses of one root have two commitments, and a record copied under another name is cryptographically invalid rather than merely uncounted (WS-005).

```python
from astp.protocol.witness_v2 import sign_witness_record_v2

record = sign_witness_record_v2(
    private_key,                                  # Ed25519PrivateKey
    witness_id="reviewer-7", node_id=node.node_id, node_type=node.node_type,
    root=seal.episode_root_hash, root_version=2,
    sequence_index=seal.leaf_count - 1, logical_clock=logical_clock,
    witnessed_at=now, role="REVIEWER", role_detail=None,
)
# record.commitment_hash, record.signature (64 bytes over the raw commitment),
# record.public_key (32 bytes), record.public_key_fingerprint (SHA3-256 of it)
```

The signature is Ed25519 over the 32 raw bytes of the commitment — `Sign(sk, bytes.fromhex(commitment_hash))`, the same form as the HITL signatures of §4.6. `ed25519` is the one registered scheme; the registry is extensible by amendment and the commitment is scheme-independent. The 4.x pipe-delimited commitment (`node_id|node_type|spine_root|sequence_index|logical_clock|role`) bound neither the witness nor the time and is retained in SPEC §16.4.2 only as the definition of records already written.

### 5.3 WitnessRecord Lifecycle

A `WitnessRecord` is created when an agent or external system witnesses a node state. The lifecycle is:

```
1. Witness observes the node at sequence_index S with spine_root R
2. Witness constructs WitnessCommitment preimage from (node_id, node_type, R, S, clock, role)
3. Witness computes commitment_hash = SHA3-256(preimage)
4. Witness signs commitment_hash with their private key → signature
5. WitnessRecord { witness_id, node_id, spine_root, sequence_index,
                   logical_clock, role, commitment_hash, signature,
                   witnessed_at } is submitted to the implementation
6. Implementation verifies: recompute commitment_hash from fields, compare to submitted value (G-12)
7. Implementation verifies: signature over commitment_hash using witness's public key
8. If both pass: store WitnessRecord and count toward threshold
```

### 5.4 Witness Validity (G-12)

On receipt of a `WitnessRecord`, verify it before storing it as valid or counting it. Validity is four executable conditions, checked in order, the first failure reported:

```python
from astp.protocol.witness_v2 import check_witness_record_v2, WitnessInvalid

try:
    check_witness_record_v2(record, node_author=node.authored_by)
except WitnessInvalid as why:
    store_as_invalid(record, reason=str(why))   # recorded, never valid, never counted
else:
    store_as_valid(record)
```

1. `commitment_hash` recomputes from the record's fields.
2. `public_key_fingerprint == SHA3-256(public_key)`.
3. `signature` verifies under `public_key` over the raw commitment, under the registered scheme the record names.
4. `witness_id != node.authored_by` — a party cannot witness its own claim; a self-witness is not an attestation.

Whether the named key belongs to the named witness is your workspace key registry's question — outside the preimage and outside G-12. Check it at the same point, as policy.

### 5.5 Threshold Enforcement (G-11)

The threshold value is workspace-configured per node type; **how you count is protocol-fixed**. Each valid record is an edge between a name (`witness_id`) and a key (`public_key_fingerprint`); the count is the size of a **maximum bipartite matching** — one key cannot count twice under two names, one name cannot count twice under two keys, and the answer must not depend on record order.

```python
from astp.protocol.witness_v2 import enforce_witness_threshold_v2

enforce_witness_threshold_v2(valid_records, node_author=node.authored_by,
                             min_counter_signatures=policy.min_counter_signatures[node.node_type])
```

**Common implementation mistakes:** counting rows; deduplicating names only (a keyholder registers twice); deduplicating keys only (one identity with two keys double-counts); a greedy pass (A/k₁, A/k₂, B/k₁ admit two witnesses — A/k₂ and B/k₁ — and greedy finds one). CONFORMANCE.md WS-008 pins the cases.

### 5.6 Witness Roles

| Role | Semantics |
|------|-----------|
| `REVIEWER` | The witness reviewed and approved the node content |
| `AUDITOR` | The witness performed an audit of the node's integrity |
| `COUNTER_SIGNER` | The witness co-signed the node as a required party |
| `OBSERVER` | The witness observed the node state without approval semantics |
| `CUSTOM` | Implementation-defined semantics; `role_detail` SHOULD be non-empty |

The role participates in the `WitnessCommitment` hash (WS-003). A signature with role `REVIEWER` cannot be presented as a signature with role `AUDITOR` — the commitment hashes will differ and verification will fail.

### 5.7 Conformance Checkpoint: Witness Signatures

Run vectors **WS-001 through WS-007** before proceeding.

| Vector | What it verifies |
|--------|----------------|
| WS-001 | WitnessCommitment hash is deterministic across implementations |
| WS-002 | Commitment binds to specific spine_root |
| WS-003 | Commitment binds to role |
| WS-004 | Commitment hash verification (G-12) |
| WS-005 | Invalid records do not count toward threshold |
| WS-006 | Threshold requires distinct witness_id values |
| WS-007 | CUSTOM role advisory (RECOMMENDED) |

---

## 6. Cross-Node Chain Proofs

### 6.1 Overview

A `ProofChain` is a verifiable sequence of `CognitiveNode` states that establishes causal ordering across nodes. It is the mechanism for proving that a sequence of cognitive events occurred in a specific order — across node boundaries, across node types, and across AI architectures.

A `ProofChain` is self-contained: a verifier needs only the chain data and the ASTP Merkle algorithm to verify it. No access to the originating implementation's storage or key material is required.

### 6.2 ProofLink Construction

Each link in a `ProofChain` represents one `CognitiveNode` in the causal sequence:

```python
@dataclass
class ProofLink:
    node_id:         str           # The CognitiveNode this link represents
    node_type:       str           # Type of the node (protocol-generic)
    spine_root:      str           # spine_root at the time of chain construction
    sequence_index:  int           # sequence_index at the time of chain construction
    logical_clock:   int           # Logical clock value
    inclusion_proof: InclusionProof  # Merkle inclusion proof per §9.2
    parent_node_id:  Optional[str]   # Causal parent, or null for chain head
    anchor_receipt:  Optional[AnchorReceipt]  # For cross-architecture temporal ordering
```

The `inclusion_proof` is the Merkle inclusion proof for the node's `spine_root` in the tree — the same proof structure used in Phase 1-2 (§9.2). This is what makes the link verifiable without external state.

### 6.3 Chain Root Computation

The `chain_root` is SHA3-256 of the concatenated `spine_root` values of all links, in chain order:

```python
def compute_chain_root(links: List[ProofLink]) -> bytes:
    concatenated = b""
    for link in links:
        concatenated += bytes.fromhex(link.spine_root)
    return sha3_256(concatenated)
```

This is a simple concatenation hash, not a Merkle tree. The chain root binds the entire sequence of node states — any modification to any link's `spine_root` changes the chain root (G-13).

### 6.4 Causal Ordering

Causal ordering in a `ProofChain` is established by `parent_node_id`, not by comparing `sequence_index` or `logical_clock` values across nodes. The causal order rule is:

```
For consecutive links[i] and links[i+1]:
    links[i+1].parent_node_id == links[i].node_id
    OR
    links[i].node_id is reachable from links[i+1] via the parent_node_id chain
```

> **Critical:** `sequence_index` is intra-node. It is the position of a segment within a node's spine. Do NOT compare `sequence_index` values across nodes to establish causal order. A node with `sequence_index=5` may be causally later than a node with `sequence_index=42` — they are in different nodes.

For cross-architecture chains where logical clocks are incommensurable, use `anchor_receipt.log_timestamp` to establish temporal ordering (CP-008). Two nodes from different AI architectures have independent logical clocks — comparing them directly is meaningless. The transparency log timestamp provides an architecture-neutral ordering basis.

### 6.5 ProofChain Construction

```python
def build_proof_chain(
    chain_id: str,
    nodes: List[CognitiveNode],
    causal_order: List[Tuple[str, Optional[str]]]  # [(node_id, parent_node_id), ...]
) -> ProofChain:

    links = []
    for node_id, parent_node_id in causal_order:
        node = lookup_node(node_id)
        links.append(ProofLink(
            node_id         = node.node_id,
            node_type       = node.node_type,
            spine_root      = node.spine_root,
            sequence_index  = node.sequence_index,
            logical_clock   = node.logical_clock,
            inclusion_proof = generate_inclusion_proof(node),  # §9.2
            parent_node_id  = parent_node_id,
            anchor_receipt  = node.anchor_receipt  # may be None
        ))

    return ProofChain(
        chain_id         = chain_id,
        links            = links,
        chain_root       = compute_chain_root(links),
        created_at       = utc_now_iso8601(),
        protocol_version = "5.1.0"
    )
```

### 6.6 ProofChain Verification Algorithm

The verification algorithm is protocol-mandatory. All conforming implementations MUST implement it identically:

```python
def verify_proof_chain(chain: ProofChain) -> VerificationResult:

    if len(chain.links) == 0:
        return VerificationResult(valid=False, reason="empty chain")

    # Condition 1: Verify each link's inclusion proof
    for i, link in enumerate(chain.links):
        if not verify_inclusion_proof(link.spine_root, link.inclusion_proof):
            return VerificationResult(
                valid=False,
                reason=f"link {i} inclusion proof verification failed"
            )

    # Condition 2: Verify causal ordering
    for i in range(1, len(chain.links)):
        prev = chain.links[i - 1]
        curr = chain.links[i]
        if curr.parent_node_id != prev.node_id:
            # Check if prev.node_id is reachable via parent chain
            if not is_ancestor(prev.node_id, curr.parent_node_id, chain.links):
                return VerificationResult(
                    valid=False,
                    reason=f"causal order violation — link {i} has no causal relationship to link {i-1}"
                )

    # Condition 3: Temporal consistency (cross-architecture)
    # If anchor_receipts are present, log_timestamps must be non-decreasing
    receipted_links = [l for l in chain.links if l.anchor_receipt is not None]
    for i in range(1, len(receipted_links)):
        if receipted_links[i].anchor_receipt.log_timestamp < receipted_links[i-1].anchor_receipt.log_timestamp:
            return VerificationResult(
                valid=False,
                reason=f"temporal consistency violation — anchor timestamps out of order"
            )

    # Condition 4: Chain root integrity (G-13)
    expected_root = compute_chain_root(chain.links)
    if chain.chain_root != expected_root:
        return VerificationResult(
            valid=False,
            reason="chain_root integrity failure (G-13)"
        )

    return VerificationResult(valid=True)
```

### 6.7 Cross-Architecture Considerations

When constructing or verifying a `ProofChain` that spans multiple AI architectures:

1. **Type-agnostic:** The verification algorithm does not inspect `node_type`. A chain with mixed node types (e.g., `signal` → `episode` → `artifact`) is valid if the causal ordering and inclusion proofs are correct (CP-006).

2. **Incommensurable logical clocks:** Do not compare `logical_clock` values across architecture boundaries. Use `anchor_receipt.log_timestamp` for cross-architecture temporal ordering (CP-008). If a link has no `anchor_receipt`, temporal ordering relative to links from other architectures is undefined.

3. **Self-contained verification:** The chain must be verifiable using only the ASTP protocol surface — SHA3-256 and the Merkle algorithm from §5. An implementation that requires access to the originating architecture's storage or key material to verify a chain is non-conforming (CP-007).

4. **Serialization for exchange:** When exchanging a `ProofChain` between architectures, use the canonical JSON serialization (Appendix A of the Conformance Test Vectors). Both the chain structure and the `InclusionProof` fields must be serialized canonically to ensure the `chain_root` is reproducible by the receiving implementation.

### 6.8 Conformance Checkpoint: Cross-Node Chain Proofs

Run vectors **CP-001 through CP-008** before declaring Phase 3 conformance.

| Vector | What it verifies |
|--------|----------------|
| CP-001 | Single-link chain (degenerate case) |
| CP-002 | Two-link chain with direct parentage; sequence_index NOT compared cross-node |
| CP-003 | Chain root integrity (G-13) |
| CP-004 | Causal order violation detection |
| CP-005 | Inclusion proof failure invalidates link |
| CP-006 | Chain spanning multiple node types |
| CP-007 | Cross-architecture proof verification |
| CP-008 | Temporal ordering via anchor_receipt (RECOMMENDED) |

---

## 7. Integration Sequence

Implement Phase 3 in the following order. Each step has a hard dependency on the previous step.

```
Step 1: Key Hierarchy
    ├── Implement HKDF with SHA3-256
    ├── Implement workspace key derivation
    ├── Implement node key derivation (with node_type in info string)
    ├── Implement seal key derivation (spine_root as binary salt)
    ├── Implement NodeKeyRecord with key_version monotonicity (G-15)
    └── ✓ CHECKPOINT: Pass KH-001 through KH-006

Step 2: Transparency Log Anchoring
    ├── Implement TransparencyLogAdapter interface
    ├── Implement AnchorCommitment construction (no payload fields)
    ├── Implement canonical JSON serialization for commitment hashing
    ├── Wire adapter.submit() into crystallization state transition (G-14)
    ├── Store AnchorReceipt on CognitiveNode post-crystallization
    └── ✓ CHECKPOINT: Pass TL-001 through TL-007

Step 3: Witness Signatures
    ├── Implement the WITNESS_COMMITMENT:v2: construction (§5.2)
    ├── Implement the four validity conditions on WitnessRecord receipt (G-12)
    ├── Implement threshold counting as a maximum matching of names × keys (G-11)
    └── ✓ CHECKPOINT: Pass WS-001 through WS-009

Step 4: Cross-Node Chain Proofs
    ├── Implement ProofLink construction with InclusionProof
    ├── Implement chain_root computation (concatenated spine_roots)
    ├── Implement ProofChain verification algorithm (all 4 conditions)
    ├── Implement cross-architecture temporal ordering via anchor_receipt
    └── ✓ CHECKPOINT: Pass CP-001 through CP-008

Step 5: Governance Rule Audit
    └── Verify G-11 through G-16 enforcement per the Governance Rule Matrix
        (Conformance Test Vectors §6)
```

---

## 8. Common Implementation Mistakes

| Mistake | Consequence | Detection |
|---------|-------------|-----------|
| HKDF with SHA-256 instead of SHA3-256 | KH-006 failure — cross-implementation key mismatch | KH-001 cross-comparison |
| `node_type` absent from HKDF info string | G-16 violation — key confusion across node types | KH-002, KH-005 |
| `spine_root` hex-encoded in seal key HKDF salt | KH-003 failure — seal key not bound to node state | KH-003 |
| AnchorCommitment includes payload fields | TL-002 failure — privacy/protocol boundary violation | TL-001, TL-002 |
| Whitespace in canonical JSON | TL-003 failure — commitment hash mismatch | TL-003 cross-comparison |
| Anchoring as async background job | G-14 violation — anchor may use wrong crystallization_root | TL-004, TL-005 |
| Counting WitnessRecord rows for threshold | G-11 violation — single agent satisfies multi-party threshold | WS-006 |
| Accepting WitnessRecord without commitment hash verification | G-12 violation — tampered records accepted | WS-004, WS-005 |
| Comparing sequence_index across nodes for causal order | CP-002 failure — valid cross-node chains rejected | CP-002 |
| Comparing logical_clock across architectures | CP-008 failure — valid cross-architecture chains rejected | CP-008 |
| Chain verification requires external state | CP-007 failure — chain is not self-contained | CP-007 |

---

## 9. Governance Rule Summary

| Rule | Description | Implementation Requirement |
|------|-------------|--------------------------|
| G-11 | Witness threshold (workspace-configured) | `count_valid_witnesses()` counts distinct `witness_id` values; threshold is per `node_type` |
| G-12 | Witness commitment integrity | Recompute `commitment_hash` from fields on every `WitnessRecord` receipt; reject mismatches |
| G-13 | Chain root integrity | `verify_proof_chain()` condition 4: recompute `chain_root` and compare |
| G-14 | Anchoring at crystallization | `adapter.submit()` called synchronously within the crystallization state transition |
| G-15 | Key version monotonicity | `NodeKeyRecord` write rejected if `key_version <= current_max` |
| G-16 | Node type in key derivation | HKDF info string for node key MUST include `node_type`; no code path omits it |

---

## Appendix A: Pseudocode Index

| Section | Pseudocode |
|---------|-----------|
| §3.3 | Workspace key HKDF derivation |
| §3.4 | Node key HKDF derivation |
| §3.5 | Seal key HKDF derivation |
| §3.6 | Key version monotonicity enforcement |
| §4.3 | AnchorCommitment construction |
| §4.4 | Canonical JSON serialization example |
| §5.2 | WitnessCommitment construction |
| §5.4 | WitnessRecord commitment hash verification |
| §5.5 | Witness threshold counting |
| §6.3 | Chain root computation |
| §6.5 | ProofChain construction |
| §6.6 | ProofChain verification algorithm |

---

## Appendix B: Phase 3 Conformance Declaration

An implementation declaring Phase 3 conformance MUST:

1. Pass all REQUIRED vectors in the Phase 3 Conformance Test Vectors (v2.0.0)
2. Publish cross-implementation consistency values for KH-001, KH-006, WS-001, and TL-003 to the conformance registry
3. Declare a conformance level: **Level 1** (REQUIRED vectors only) or **Level 2** (REQUIRED + RECOMMENDED)
4. Reference the SPEC.md version and Conformance Test Vectors version against which conformance was verified

Conformance declarations are per-version. A declaration against one SPEC version does not imply conformance against a later MAJOR.

---

## Appendix C: Phase 4 — HITL Event Integration

**Added:** 2.4.0 (2026-04-16); terminal states and the resolution writer restated at 5.0.0 (§4.6).

Phase 4 adds Human-in-the-Loop (HITL) events as first-class nodes in the ASTP State Tree. HITL events record human oversight decisions with cryptographic attestation and Merkle spine participation.

### C.1 Implementation Sequence

Phase 4 builds on Phase 3 infrastructure. Implement in this order:

1. **Schema types** — Add `HITLEventNode`, `HITLGateType`, `HITLDecision`, `HITLNodeStatus` enums and model. Add hash functions: `compute_hitl_context_hash`, `compute_hitl_resolution_hash`, `compute_hitl_node_hash` with domain-separated prefixes (`HITL_CTX:`, `HITL_RES:`).

2. **Storage layer** — Add `AriadneHITLEvent` constraint and indexes. Implement `write_hitl_event_invocation_sync` (creates INVOKED node + HITL_GATE edge) and `write_hitl_event_resolution_sync` (updates INVOKED → RESOLVED with MATCH + SET).

3. **Crystallization guard** — Add `PENDING_HITL` to `EpisodeStatus`. Extend `enforce_crystallization_lock_guard` to reject `PENDING_HITL`. Modify `acquire_crystallization_lock` to query for pending HITL events before acquiring.

4. **Episode status transitions** — On blocking gate invocation (APPROVAL_REQUIRED, COMPLIANCE_CHECKPOINT), transition episode to `PENDING_HITL`. On resolution, if no remaining pending gates, transition back to `ACTIVE`.

5. **Cryptographic attestation** — Sign `context_hash` with the agent's Ed25519 key at invocation. Sign `resolution_hash` with the human's Ed25519 key at resolution. Both use the Phase 3 HKDF key hierarchy with `entity_type` parameter ("agent" or "user").

6. **No spine participation** — A resolved HITL event's `node_hash` records the decision; it is **not** a spine leaf. The spine is the Episode's non-ephemeral Segments and nothing else (SPEC §5.6), and no seal has ever included HITL hashes. Do not pass them to the spine computation.

7. **Advisory gates** — For `REVIEW_ADVISORY` gates, tag segments written during the pending interval with `pending_hitl_ref`. These segments are `CONDITIONALLY_VALID` until the gate resolves. Advisory gates do NOT block crystallization or set `PENDING_HITL`.

### C.2 Key Design Constraints

- **Two-phase lifecycle:** HITL events are the only node type that permits post-creation mutation — `INVOKED` → one of the terminal states `RESOLVED`, `TIMED_OUT`, `ESCALATED`. The exception is narrow and enforced by G-17. `ESCALATED` concludes *this* gate (the recorded decision is the escalation; further deliberation is a new gate that references it) and MUST NOT be written as `RESOLVED`: the resolution writer records the status the decision concludes the gate with (`hitl_terminal_status`). A concluded event is a structural-manifest member under a version 2 seal (§5.7.1), so its context document (`context_json`) is stored on the node at invocation — an event stored without it cannot enter a version 2 seal.
- **Recording failures are loud:** the adapter writers raise (SPEC §15 item 7); whether the operational HITL path proceeds when the record cannot be written is the host's policy, and a host that proceeds logs the gap at error level — a decision that is not on the record is not silently one that is.
- **Timeout as event:** `TIMED_OUT` is a recorded terminal status with the same structural weight as `REJECTED`. System timeouts are recorded with `resolved_by: "system_timeout"` and no human signature.
- **Gate type mapping:** Map operational HITL types to protocol gate types: `MUST → APPROVAL_REQUIRED`, `SHOULD/CAN → REVIEW_ADVISORY`, `INFORMED → not recorded`.

### C.3 Governance Rules

- **G-17:** Resolution hash prohibited on INVOKED status nodes (enforces two-phase lifecycle).
- **G-18:** Episodes with pending blocking HITL events cannot acquire crystallization locks.

### C.4 Conformance Checkpoint

A Phase 4 conforming implementation MUST:

1. Record HITL events with the correct two-phase lifecycle (the reference adapter stores them under the `AriadneHITLEvent` label; the representation is an adapter choice)
2. Compute `context_hash`, `resolution_hash`, `node_hash` with correct domain-separated prefixes
3. Enforce G-17 (no resolution on INVOKED nodes)
4. Enforce G-18 (crystallization blocked by pending blocking HITL)
5. Keep resolved HITL `node_hash` values out of the spine computation (SPEC §5.6)
6. Sign invocation with agent key and resolution with human key (using Phase 3 HKDF hierarchy)
7. Tag segments written during advisory gates with `pending_hitl_ref`

---

*ASTP Implementation Guide is maintained by Scorched Earth Labs.*
*Guide version: 2.0.0 | Written against SPEC.md 5.1.0 | Conformance Vectors: v2.0.0*