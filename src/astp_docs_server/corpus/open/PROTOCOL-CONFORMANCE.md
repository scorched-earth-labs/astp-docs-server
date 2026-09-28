# ASTP — Protocol Conformance

**Version:** 1.0.0-draft
**Status:** DRAFT — pending ratification in an Episode of Record. No open item blocks it; see §11.
**Authors:** Scorched Earth Labs
**Date:** 2026-09-26
**Applies To:** [`SPEC.md`](./SPEC.md) 6.0.2
**Companions:** the per-surface conformance vector documents listed in §4.

---

## 1. What this document is

`SPEC.md` is the normative protocol. The `CONFORMANCE-*.md` documents state test
vectors for individual feature surfaces. Neither answers, in one place, the
question this document answers:

> **What is a Conforming Implementation of ASTP?**

This document is the single referent for that term. It defines conformance,
enumerates the normative requirement set, states how conformance is
demonstrated, and states plainly what conformance does not require and does not
establish.

It is **normative as to the definition of conformance** and non-normative as to
everything else: where this document and `SPEC.md` disagree about a protocol
requirement, `SPEC.md` governs and this document is in error.

> **This document carries legal weight.**
> [`PATENTS.md`](./PATENTS.md) §4.2 grants a royalty-free patent license to a
> Conforming Implementation and defines that term by reference to this document.
> A change here changes the scope of that grant. This document is therefore
> governed by [`VERSIONING.md`](./VERSIONING.md) and ratified in an Episode of
> Record like any other normative change, and `PATENTS.md` §15 applies to it:
> a later narrowing does not withdraw a license already granted.

---

## 2. Definition

A **Conforming Implementation** is a software or hardware/software system,
service, or library that:

1. implements every **REQUIRED** provision of the conformance profile it claims
   (§3), as those provisions are stated in `SPEC.md` at the version it claims
   (§7);
2. enforces every governance rule in force for that profile (§5);
3. reproduces the pinned digests for every construction its profile exercises
   (§6);
4. states which profile and which Specification version it claims (§8); and
5. does not represent OPTIONAL, RECOMMENDED, or non-normative material as
   REQUIRED, and does not represent a lower profile as a higher one.

Conformance does **not** require use of the reference implementation, and an
implementation may be proprietary, closed-source, commercial, hosted, or
embedded. No determination, certification, approval, or other act of Scorched
Earth Labs is a condition of an implementation being conforming.

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY and OPTIONAL are interpreted as in BCP 14 [RFC 2119] [RFC 8174]
when, and only when, they appear in all capitals.

---

## 3. Conformance profiles

ASTP spans feature surfaces that are genuinely independent: an implementation
may commit context without ever branching, or seal Episodes without a Layer 3.
Conformance is therefore defined in profiles.

**Two profiles are REQUIRED of every Conforming Implementation: Core and Context
Commitment.** The remaining surfaces are OPTIONAL to support, subject to §3.8.

The reasoning is stated so that a later reader can weigh it. Core alone would
make conformance cheap to claim while permitting an implementation that cannot
prove what its agents were given — which is the property the protocol exists to
provide, and the one a relying party will assume a conforming implementation
has. Requiring every surface would set a bar almost nothing clears, narrowing
the patent grant to the point of being nominal. Core plus Context Commitment is
the smallest set under which the term means what a relying party would take it
to mean.

### 3.1 Core — REQUIRED

The integrity substrate. No ASTP claim is meaningful without it.

| Surface | `SPEC.md` |
|---|---|
| CognitiveNode, CognitiveEdge, NodePayload interface | §4.1–§4.3 |
| Episode and Segment model, lifecycle | §4.4–§4.5 |
| Canonical field encoding and canonical JSON | §5.1.1–§5.1.2 |
| Domain separation; the prefix registry | §5.1.3, §5.3 |
| Position-binding leaf hash | §5.2 |
| Merkle tree construction | §5.4–§5.5 |
| Spine leaf set | §5.6 |
| Episode root and its manifests | §5.7, §5.7.1 |
| Algorithm and ordering version identifiers | §5.8 |
| Delta records | §7 |
| Tamper-evident audit chain | §8 |
| Five-test gate; inclusion proof; reproducibility obligation | §9.1–§9.3 |
| Retrieval side-effect contract | §11 |
| Write Intent Log; ledgered operations | §12 |
| Adapter requirements | §15 |
| Dual-index invariant; namespace firewall | §3.2–§3.3 |

Governance: **G-1 – G-10, G-37 – G-40.**

### 3.2 Context Commitment — REQUIRED

What the Episode's agents were given, and lawful erasure of it. This is the
6.0.0 surface, and its two halves are safe only together: a commitment to
context without the non-reversible construction is a permanent, guessable
commitment to personal data.

| Surface | `SPEC.md` |
|---|---|
| ContextEntryNode | §4.8 |
| Erasure — content plane, tombstone, codicil | §4.9 |
| Episode root version 3; context manifest | §5.7, §5.7.3 |
| `spine_algorithm_version` 3 | §5.8 |

Governance: **G-41, G-42, G-43.**

An implementation that seals only under `spine_algorithm_version` 0, 1 or 2 is
not conforming to this version of the Specification. Those constructions are
retained and seals made under them remain verifiable — that is a property of the
retained constructions, not a conformance claim about the implementation that
made them.

### 3.3 Trust Infrastructure — OPTIONAL

Key hierarchy, transparency-log anchoring, witness signatures, cross-node chain
proofs. `SPEC.md` §16. Governance: **G-11 – G-16.**

### 3.4 Human-in-the-Loop — OPTIONAL

HITLEventNode and its two-phase lifecycle. `SPEC.md` §4.6. Governance:
**G-17, G-18.**

### 3.5 Branch / Fork / Merge — OPTIONAL

Branch, fork, departure fork, merge, aside, soliloquy. `SPEC.md` §19.
Governance: **G-19 – G-35.**

### 3.6 Cross-Episode Linking and Grouping — OPTIONAL

`SPEC.md` §20, including its inline rules.

### 3.7 Layer 3 — Workflow and Execution DAG — OPTIONAL

`SPEC.md` §21. Governance: **G-36.** Layer 3 is hash-isolated from the Spine:
an implementation with no Layer 3 is a valid implementation at Layers 1 and 2,
and Layer 3's byte form is not governed by §5.1.

### 3.8 Optional to support, required to commit

A surface being OPTIONAL means an implementation need not support it. It does
**not** mean an implementation that supports it may record it loosely.

An implementation that writes any node which §5.7.1 makes a structural-manifest
member — a BranchPoint, BranchTerminus, ForkPoint, DepartureForkPoint,
ForkReturn, MergePoint, or a HITL event in a terminal state — MUST commit it as
that section requires. An implementation that writes such nodes without
committing them produces an Episode root that is wrong rather than merely
incomplete, and is non-conforming at Core, because §5.7 is a Core requirement.

The same principle applies generally: a supported surface is held to its
requirements in full. Two provisions of `SPEC.md` bind only an implementation
that does what they govern, and are held to that standard here rather than
listed in any profile:

- **Agent-directed retrieval (§10).** An implementation that serves agent
  retrieval MUST provide the operations of §10 with their node scoping and
  verbatim-content rule, and MUST read each agent turn against a consistent
  snapshot (§10.4). The tail write advisory (§10.5) and the HITL re-validation
  gate (§10.6) bind it at the strength `SPEC.md` gives them, no more. An
  implementation that writes and seals but serves no agent retrieval is not
  bound by §10.
- **Rebalance (§14).** An implementation that rebalances its tree MUST record
  each rebalance as §14 requires and MUST preserve the root across it (§14.1).
  An implementation that never rebalances never triggers §14.

The spine tip cache (§13) is a SHOULD, and `SPEC.md` calls it "a performance
optimization, not a source of truth"; declining it does not affect conformance.
The authoritative spine-tip query that §13 and §15 require is part of Core
through §15.

---

## 4. Conformance vectors by surface

Each document states inputs and the property a conforming implementation must
exhibit, by requirement class (REQUIRED / RECOMMENDED).

| Surface | Document | Pinned digests |
|---|---|---|
| Seal constructions, spine, Episode root, reproducibility | [`CONFORMANCE-REPRODUCIBILITY.md`](./CONFORMANCE-REPRODUCIBILITY.md) | [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json) |
| Context commitment, erasure, root version 3 | [`CONFORMANCE-CONTEXT.md`](./CONFORMANCE-CONTEXT.md) | [`vectors/6.0.0/context-commitment.json`](./vectors/6.0.0/context-commitment.json) |
| Trust infrastructure (§16) | [`CONFORMANCE-TRUST.md`](./CONFORMANCE-TRUST.md) | [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json) |
| Branch / fork / merge / aside / soliloquy (§19) | [`CONFORMANCE-BFM.md`](./CONFORMANCE-BFM.md) | [`vectors/5.0.0/seal-constructions.json`](./vectors/5.0.0/seal-constructions.json) |
| Cross-episode linking and grouping (§20) | [`CONFORMANCE-CROSS-EPISODE-LINKING.md`](./CONFORMANCE-CROSS-EPISODE-LINKING.md) | — byte layouts, not golden values |
| Layer 3 (§21) | [`CONFORMANCE-LAYER3.md`](./CONFORMANCE-LAYER3.md) | — byte form is the implementation's (§21 §8) |

`SPEC.md` §17 additionally states the five-test gate (§17.1), the Phase 3
prescriptive vectors K1–K3 / W1–W9 / T1–T3 / C1–C4 (§17.2), and the
cross-architecture interoperability test (§17.3).

---

## 5. Governance rules

A Conforming Implementation enforces every governance rule in force for its
profile. Rules are normative where defined in `SPEC.md`; this table is an index.

| Rules | Subject | Defined | Profile |
|---|---|---|---|
| G-1 – G-6 | Write guard, reparenting, sequence and clock monotonicity, node-type registration, namespace firewall | §6 | Core |
| G-7 – G-9 | Signal governance | §6 | Core |
| G-10 | Structural delta content invariant | §6 | Core |
| G-11 – G-16 | Witness threshold and validity, chain root, anchoring timing, key version, node type in derivation | §6 | Trust Infrastructure |
| G-17 – G-18 | HITL invocation before resolution; crystallization block | §6 | HITL |
| G-19 – G-35 | Branch, fork, departure fork, merge, aside, soliloquy, fingerprint invariants | §19 | BFM |
| G-36 | CIA declaration | §21 | Layer 3 |
| G-37 – G-39 | Ledgering obligations by operation tier | §12.4 | Core |
| G-40 | Sealed requires a record; Episode identifiers are UUIDs | §6 | Core |
| G-41 | Capture posture and undeclared gaps | §6 | Context Commitment |
| G-42 | Non-reversible commitment for low-entropy personal data | §6 | Context Commitment |
| G-43 | Erasure is content-plane | §6 | Context Commitment |

### 5.1 G-42 and classification

G-42 requires the `CONTEXT_CONTENT_SALTED:v1:` construction where a context
entry's content is personal data and low-entropy. Both are determinations the
implementation makes about its own data. A verifier reading the record can
confirm which construction was used; it cannot confirm that the classification
behind that choice was sound, because the classification is not in the record.

This is a disclosure gap, not a gap in the rule. An implementation that commits
plainly personal, plainly guessable content under the unsalted construction is
non-conforming, and that is observable. What is not observable is where a
borderline line was drawn.

A conformance claim therefore states the implementation's classification
policy — the rule by which it determines that content is personal and
low-entropy — precisely enough that a reader applying it to an entry reaches the
same determination (§8). A relying party evaluates the policy and can check any
entry's construction against it. An implementation that will not state its
policy has not made an evaluable claim.

An implementation MAY apply `CONTEXT_CONTENT_SALTED:v1:` to all context content,
which removes the judgment entirely, at the cost of requiring the salt to verify
any content against its `content_hash`.

Committing the declaration to the record, rather than stating it in
documentation, would make this verifiable rather than merely disclosed. It
requires a new construction and is a candidate for the next MAJOR (§11).

---

## 6. How conformance is demonstrated

**Conformance is demonstrated by reproduction.** An implementation demonstrates
conformance by:

1. **Reproducing the pinned digests.** For every construction its profile
   exercises, computing the construction over the vector inputs in `vectors/`
   and obtaining the pinned value, byte for byte. The pinned values are
   generated by `vectors/*/generate.py` and are checked in the reference test
   suite against a from-prose reference that imports nothing from the package.
2. **Exhibiting the required properties.** For each REQUIRED vector in the
   applicable conformance document, exhibiting the stated property — that a
   tampered record fails, that a threshold rejects, that an erased entry is
   reported as erased rather than failed.
3. **Passing the five-test gate** (§9.1) and, where interoperability is claimed,
   the cross-architecture test (§17.3).
4. **Reproducing an Episode root from stored nodes alone** (§9.3). A
   construction that requires state not present on the nodes — insertion order,
   a store's default sort, a cache — is non-conformant.

> **What does not exist yet.** There is no adapter-parameterized harness that a
> third-party implementation can run against these vectors to produce a
> pass/fail result. Until there is, conformance is self-demonstrated by the
> steps above and is checkable by a relying party only by inspection. This is a
> known gap, stated here rather than papered over, and closing it is the
> highest-priority conformance work.

An independent party can, today, verify a **sealed record** produced by any
implementation, using the reference package alone and without access to the
producing system:

```bash
python -m astp.core.proof_of_record verify <proof-file>
```

That is a different and weaker claim than verifying that an implementation
conforms. It verifies one record; it does not audit a system.

---

## 7. Versioned conformance

Conformance is always to a stated version of `SPEC.md`. That file's `Version:`
field is the protocol version; it is restated nowhere else so it cannot drift.

The binding identification of the text conformed to is the **SHA3-256 digest of
`SPEC.md`**, which any party can compute and which `PATENTS.md` §4.1 pledges
against:

```bash
python3 -c "import hashlib,sys; print(hashlib.sha3_256(open(sys.argv[1],'rb').read()).hexdigest())" SPEC.md
```

| Protocol version | SHA3-256 digest of `SPEC.md` | Episode of Record |
|---|---|---|
| 6.0.2 | `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb` | 6.0.0: `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8` ([`docs/RATIFICATION-6.0.0.md`](./docs/RATIFICATION-6.0.0.md)) |
| 5.0.0 | see [`docs/RATIFICATION-5.0.0.md`](./docs/RATIFICATION-5.0.0.md) | `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28` |

> **What the 6.0.0 Episode of Record ratified.** It ratified the amendment draft
> (`docs/history/SPEC-6.0.0-DRAFT-context-commitment.md`) by content digest, as
> proposed text for `SPEC.md`. It did not seal a digest of `SPEC.md` as a whole
> document, as the 5.0.0 Episode did. The digest above is therefore a direct
> content digest of the published file, verifiable by anyone, rather than a
> ratified one. Both are sound identifications of a text; they differ in whether
> the protocol's own ratification machinery sealed them. If a ratified digest of
> the whole specification is wanted, `SPEC.md` needs its own Episode of Record.

---

## 8. Claiming conformance

An implementation claiming conformance states, in documentation a relying party
can read:

- the **profiles** claimed (§3) — at minimum Core and Context Commitment;
- the **Specification version and digest** conformed to (§7);
- the `spine_algorithm_version`, `ordering_version` and `hash_version` it
  **writes** under, and those it can **read and verify**;
- its **G-42 classification policy**, stated as §5.1 requires;
- any REQUIRED vector it does not pass, and why;
- for behavioral-tier choices, the audit records it writes in lieu of a mandated
  algorithm (`SPEC.md` §20 §12.2).

> `SPEC.md` §20 §8 defines a `ConformanceDeclaration` node, but it is scoped to
> grouping systems and its capability list is grouping-specific. It is not a
> general conformance declaration, and a claim under this section is made in
> documentation rather than as a protocol artifact. Generalizing that node so a
> conformance claim is itself a verifiable record would be a meaningfully
> stronger position; it is a MAJOR change and is deferred. See §11.

---

## 9. What conformance does not require

- **Use of the reference implementation.** An independent implementation in any
  language, on any storage substrate, is conforming if it meets §2.
- **A particular storage technology.** Graph, relational, key-value, document,
  append-only file — the protocol constrains the hash preimage and the
  governance rules, not the substrate (§2.5.3).
- **A particular cognitive architecture.** BDI, ReAct, chain-of-thought, SOAR,
  or a model not yet devised. ASTP records *that* an agent reasoned and *what*
  resulted, never *how* (§1).
- **Behavioral-tier agreement.** Scoring algorithms, embedding model choice,
  threshold tuning and internal indexing are sovereign (§20 §12.1). The
  protocol mandates the audit record, not the value (§20 §12.2).
- **Drift or coherence detection.** No provision of `SPEC.md` requires an
  implementation to detect topic drift, re-anchor, or maintain a coherence
  fingerprint. §19.5 describes the structures an implementation that chooses to
  do so records; it does not mandate doing so. An implementation that never
  detects drift is fully conforming.
- **Byte-identical hashes across implementations.** Two conforming
  implementations that select different retained construction versions produce
  different digests for the same logical content. Cross-implementation
  *verifiability* is required; cross-implementation hash *equality* is not.
- **Open source.** See [`PATENTS.md`](./PATENTS.md) §7.

---

## 10. What conformance does not establish

Conformance is a statement about the integrity and completeness of a record. By
itself it does not establish that:

- an AI output was correct, complete, or suitable for its use;
- the underlying data or documents were truthful, authentic, or representative;
- a model or system was unbiased, or compliant with any law or regulation;
- a human review recorded at a HITL gate was thoughtful, independent, or
  substantively adequate;
- the implementation captured everything it ought to have captured — the
  context manifest commits the *capture posture* and any *declared* gap (G-41),
  which makes an undeclared gap a conformance violation rather than an
  invisible one, but no cryptographic construction can prove that an
  implementation recorded an input it never recorded. The same holds for G-42:
  the record shows which construction each entry used, not that the
  classification behind it was sound. G-42 is the one governance rule whose
  trigger a verifier cannot check independently, and the claim discloses the
  policy instead (§5.1);
- the thresholds, controls or escalation paths chosen were appropriate.

Each of those requires governance, validation, and human judgment beyond the
integrity of a record. Implementations and relying parties should not represent
protocol conformance as establishing any of them.

---

## 11. Open items

None blocks ratification. The rename of `CONFORMANCE.md` to
`CONFORMANCE-TRUST.md`, which the §4 table assumes, was made when this document
was introduced.

Deferred, tracked, not blocking:

1. **§5.1 — commit the G-42 classification declaration to the record**, so the
   policy in force when an entry was written is verifiable rather than disclosed.
   It needs a new construction. MAJOR.
2. **§8 — generalize `ConformanceDeclaration`** so a conformance claim is a
   verifiable protocol artifact rather than a documentation paragraph. MAJOR.
   Items 1 and 2 both make a claim into a record, and would naturally land in
   the same MAJOR.
3. **§6 — the adapter-parameterized harness.** The highest-priority conformance
   work after ratification.

---

*ASTP (AI State Tree Protocol) is developed by Scorched Earth Labs.*
