# Ratification — AI State Tree Protocol: Protocol Conformance 1.0.0

**Episode of Record:** `19d4390f-ac46-4840-bc9a-f419c6626fb4`
**Status:** Sealed — the statement at Segment 14 of the Episode of Record, ratified by the maintainers at Segment 16; the Record of the Episode (§11) filled after the seal
**Ratifies:** `PROTOCOL-CONFORMANCE.md` version **1.0.0** (the draft bytes bearing `Version: 1.0.0-draft`, cited by digest below)
**Applies To:** `SPEC.md` **6.0.2**
**Date of record:** 2026-10-01
**Ratified by:** the maintainers, with the Clotho faculty
**Protocol:** the AI State Tree Protocol (ASTP)
**Capture posture:** `all_external` (set before any context was provided)
**Intended sealing construction:** `spine_algorithm_version` 3 (the header states the intended seal; the Record of the Episode, §11, records the actual one)

---

## 0. What this Episode is, and is not

This is an **Episode of Record for a companion document**, not an amendment to `SPEC.md`. No `SPEC.md` text changes here. It ratifies a self-versioned normative companion — `PROTOCOL-CONFORMANCE.md` — in the same manner as any other normative protocol change, per `PATENTS.md` §14 and `VERSIONING.md`.

**Two versions, two jobs.** This Episode ratifies **conformance version 1.0.0**. **6.0.2** is the *Specification Version the conformance definition applies to* — not what this Episode ratifies. Where this Episode's title or focus pointer reads "6.0.2," **this section governs its scope**: 6.0.2 is the `Applies To` target, recorded so the definition is bound to a known protocol text; it is not itself ratified here. The title/focus slip is noted and governed in §9.

**On the draft suffix, and why the published file will not match the ratified digest.** The ratified bytes carry `Version: 1.0.0-draft` and `Status: DRAFT — pending ratification in an Episode of Record`. This Episode is that act. It ratifies **the draft's bytes**, identified by the content digest in §1, *as* version 1.0.0. Publication will edit the `Version:` line to `1.0.0` and the `Status:` line to a released status. **Those two lines are part of the hashed content**, so the published file's digest will differ from `5b8e…eacd` *by design*. The record names those lines as the whole of the delta — the same discipline the 6.0.0 record used when it ratified a draft's bytes and named the lines that publication would change. The binding citation is the draft bytes; `5b8e…eacd` is not expected to match the published file, and a verifier who recomputes the published file's digest should expect the difference to reduce exactly to the `Version:` and `Status:` lines.

## 1. Binding citations

The **content digest is the binding citation**; the commit is a navigable pointer.

| Document | SHA3-256 | Role |
|---|---|---|
| `PROTOCOL-CONFORMANCE.md` (draft bytes) | `5b8e5c2fa0baa509d2bb89a4507bca7a78dedd428e95a22f554a3ab8c3c0eacd` | **Ratified text** (conformance 1.0.0) |
| `SPEC.md` 6.0.2 | `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb` | **Applies-To identification** of the protocol text the definition is bound to |

Navigable pointer: commit `d5ae006`.

Per §7.3, the `SPEC.md` digest above remains a **direct content digest** of the published file — verifiable by anyone, matching `PATENTS.md` §4.1 and `PROTOCOL-CONFORMANCE.md` §7.3. **This Episode does not ratify `SPEC.md`.** If a ratified digest of the whole specification is ever wanted, `SPEC.md` needs its own Episode of Record. Sealing the conformance digest here is what makes §7's last sentence true: where an Episode of Record records a conformance version, the recorded document digest identifies the exact conformance text.

## 2. The profile structure, and why Context Commitment is REQUIRED

Conformance is defined in **profiles** because ASTP spans genuinely independent feature surfaces — an implementation may commit context without branching, or seal without a Layer 3.

**Two profiles are REQUIRED of every Conforming Implementation: Core and Context Commitment** (§3). All remaining surfaces are OPTIONAL to support, subject to §3.8.

The floor is reasoned, and the reasoning is sealed so a later reader can weigh it:

- **Core alone is too little.** It would make conformance cheap to claim while permitting an implementation that cannot prove what its agents were given — the very property the protocol exists to provide, and the one a relying party assumes a conforming implementation has.
- **Every surface is too much.** It would set a bar almost nothing clears, narrowing the patent grant to the nominal.
- **Core + Context Commitment** is the smallest set under which the term "Conforming Implementation" means what a relying party would take it to mean.

**Why Context Commitment is REQUIRED and not optional (§3.2).** This is the 6.0.0 surface, and its two halves are safe only together: a commitment to context *without* the non-reversible construction is a permanent, guessable commitment to personal data. Splitting them would let an implementation claim the valuable half (provable context) while shedding the protective half (lawful, non-reversible erasure). The surface is therefore indivisible at the conformance floor. Its members, as the ratified §3.2 lists them: `ContextEntryNode` (§4.8), erasure — content plane / tombstone / codicil (§4.9), Episode root version 3 and context manifest (§5.7, §5.7.3), and `spine_algorithm_version` 3 (§5.8). Governance: **G-41, G-42, G-43**. (The salted non-reversible construction G-42 lives *within* the §4.8 surface, at §4.8.3; it is not a separate §3.2 row, and its pledge scope is treated in §3.)

An implementation that seals only under `spine_algorithm_version` 0, 1, or 2 is **not conforming** to this Specification Version. Those constructions are retained and their seals remain verifiable — a property of the retained constructions, not a conformance claim about the implementation that made them.

## 3. Pledge scope over the erasure unit (L9) — DECIDED

**Decision: the non-reversible erasure unit stays mandatory and inside the pledge.** The unit is **erasure (§4.9, G-43) together with the salted construction it depends on (§4.8.3, G-42)** — pledged and mandatory as one indivisible unit. It is a member of the REQUIRED Context Commitment profile; it is not optional, and it is not carved out of the `PATENTS.md` §4.2 grant.

Erasure and its salted construction are a single mechanism, not two: G-43 destroys lawfully only because G-42 made the content non-reversible in the first place. Treating them as one unit is the honest scope — the decision binds and pledges them together.

**Reasoning.** The §3.2 "safe only together" property is the whole basis of the decision. The erasure unit is not an accessory to context commitment — it is the half that makes the other half lawful to hold. A commitment to context whose personal-data content cannot be made non-reversible (G-42) and lawfully destroyed (G-43) is a standing liability dressed as an integrity feature. If the pledge covered the commitment but not the erasure unit, the patent grant would protect precisely the construction a relying party cannot safely deploy, and withhold protection from the construction that makes deployment lawful. The grant must rest on the safe-together whole or it rests on nothing a relying party can use.

**Two rejected alternatives, recorded with their defects — each phrased over the whole unit (§4.9/G-43 + §4.8.3/G-42):**

1. **Make the erasure unit OPTIONAL (demote §4.9/§4.8.3 out of the REQUIRED profile).**
   *Rejected.* This re-splits the two halves §3.2 holds inseparable. It would permit a "Conforming Implementation" that commits context and can neither make it non-reversible nor lawfully erase it — a permanent, guessable commitment to personal data wearing the conformance label. It makes the term mean less than a relying party would take it to mean, which §3's floor exists to prevent.

2. **Keep the erasure unit REQUIRED but carve it out of the §4.2 pledge.**
   *Rejected.* This is subtler and worse. The implementation would be obligated to build the salted non-reversible construction (§4.8.3/G-42) and the erasure mechanism (§4.9/G-43) but would receive no patent assurance for the construction that discharges the obligation. It would single out, for exclusion from the grant, the one unit whose purpose is to make the pledged whole lawful to operate — leaving implementers obligated and unprotected on exactly the privacy-critical path. The pledge must cover the mechanism its own safety argument depends on.

The decision therefore keeps the erasure unit (§4.9/G-43 + §4.8.3/G-42) **mandatory** (via §3.2) and **pledged** (within §4.2's grant against the definition of a Conforming Implementation).

## 4. §3.8 — optional to support, required to commit

A surface being OPTIONAL means an implementation **need not support it**. It does **not** mean an implementation that supports it may record it loosely. A supported surface is held to its requirements in full.

- Any node that §5.7.1 makes a **structural-manifest member** — BranchPoint, BranchTerminus, ForkPoint, DepartureForkPoint, ForkReturn, MergePoint, or a HITL event in a terminal state — MUST be committed as §5.7 requires. Writing such a node without committing it produces an Episode root that is **wrong, not merely incomplete**, and is **non-conforming at Core**, because §5.7 is a Core requirement.

**Two conditional bindings** — provisions that bind only an implementation that does what they govern, held to that standard here rather than listed in any profile:

- **Agent-directed retrieval (§10).** An implementation that serves agent retrieval MUST provide §10's operations with their node scoping and verbatim-content rule, and MUST read each agent turn against a consistent snapshot (§10.4). The tail-write advisory (§10.5) and the HITL re-validation gate (§10.6) bind at the strength `SPEC.md` gives them, no more. An implementation that writes and seals but serves no agent retrieval is not bound by §10.
- **Rebalance (§14).** An implementation that rebalances its tree MUST record each rebalance as §14 requires and MUST preserve the root across it (§14.1). An implementation that never rebalances never triggers §14.

The spine-tip cache (§13) is a SHOULD — "a performance optimization, not a source of truth"; declining it does not affect conformance. The authoritative spine-tip query §13 and §15 require is part of Core through §15.

## 5. §11 open items — deliberately deferred, non-blocking

**None blocks ratification.** Recorded here as deliberately deferred:

1. **§5.1 — commit the G-42 classification declaration to the record**, so the policy in force when an entry was written is verifiable rather than disclosed. Needs a new construction. **MAJOR.**
2. **§8 — generalize `ConformanceDeclaration`** so a conformance claim is a verifiable protocol artifact rather than a documentation paragraph. **MAJOR.** (Items 1 and 2 both turn a claim into a record and would naturally land in the same MAJOR.)
3. **§6 — the adapter-parameterized harness.** The highest-priority conformance work after ratification.

The `CONFORMANCE.md` → `CONFORMANCE-TRUST.md` rename the §4 table assumes was already made when this document was introduced.

## 6. Authority

This is not a MAJOR change, so it is not the case `GOVERNANCE.md` originally described. The authority for ratifying a self-versioned companion in an Episode of Record is:

- **`PATENTS.md` §14** (a072341, PR #81): the conformance document is "ratified in an Episode of Record in the same manner as other normative protocol changes."
- **`VERSIONING.md`** (d225083, PR #82): `PROTOCOL-CONFORMANCE.md` carries its own `Version:` alongside `Applies To`, and is ratified in an Episode of Record like any other normative change.
- **`GOVERNANCE.md`** (d5ae006, PR #83): an Episode of Record ratifies each version of a self-versioned companion document before release, whether or not `SPEC.md` changes, citing it by content digest. `GLOSSARY.md` and `CHANGELOG.md` match.

## 7. Why now — before publication

`PATENTS.md` §4.2 grants its patent license against **this document's definition** of a Conforming Implementation, and §14 makes a license, once granted, irrevocable against later revision. The definition the pledge rests on must be anchored in the record **before** the pledge is published, not after. Anchoring the digest here is also what makes §7's last sentence true.

## 8. Record conditions

- **Capture posture:** `all_external`, set before any context was provided.
- **Sealing construction:** `spine_algorithm_version` 3 — making this the first Episode of Record that is itself a conforming record under the very definition it ratifies. The intended value is in the header; the actual sealed value is recorded in §11.
- **Spec and conformance text:** reached through the indexed corpus at `d5ae006`; nothing is attached. The binding citations in §1 are content digests, independent of the retrieval path.

## 9. Record-notes

(a) **Title and focus scope slip.** This Episode's title ("6.0.2 Episode of Record") and focus pointer ("Ratify ASTP v6.0.2 as the Episode of Record") name 6.0.2 as if it were the thing ratified. It is not. **§0 governs**: 6.0.2 is the `Applies To` Specification Version; the ratified artifact is conformance **1.0.0**. The slip is recorded here rather than silently corrected, so the record is honest about the container it was written in.

(b) **Corpus-retrieval provenance.** The spec and conformance text were reached through the indexed corpus. Those retrievals carry their commit **only in `source_ref`** (commit `d5ae006`); they carry **no `source_version_hash`**. Verification therefore does not run through a retrieval-layer hash. Instead, the committed chunk content hashes are checkable against the file as it stands at `d5ae006`, and the §1 binding citations are full-file content digests independent of the retrieval path. A verifier grounds on the §1 digests and the file at the named commit, not on the retrieval metadata.

## 10. Provenance

This record was produced in **this Episode**, `19d4390f-ac46-4840-bc9a-f419c6626fb4`, type `compliance`, from the ratification case presented by the maintainers (Devin) and the corpus retrievals pulled within it. It has no parent Episode. The reasoning in §§2–7 is grounded in retrievals of `PROTOCOL-CONFORMANCE.md` and `SPEC.md` at `d5ae006` performed in this Episode.

## 11. Record of the Episode

*Filled after the seal, from the seal. The header states the intended seal; this table records the actual one.*

- **Episode identifier:** `19d4390f-ac46-4840-bc9a-f419c6626fb4`
- **Ratified text:** `PROTOCOL-CONFORMANCE.md` at `d5ae006`
  - SHA3-256: `5b8e5c2fa0baa509d2bb89a4507bca7a78dedd428e95a22f554a3ab8c3c0eacd`
  - git blob: `2ab3f3505f68484e4208d63243f1d1237edef915`
  - size: 23,476 bytes
  - carries `Version: 1.0.0-draft` **by design** (see §0; publication edits the `Version:` and `Status:` lines, changing the digest)
- **Applies To:** `SPEC.md` 6.0.2
  - SHA3-256: `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb`
  - git blob: `571eb0f983df8c55f79eae3cf31227ba4af388ab`
  - size: 239,844 bytes
- **Sealed under:** `spine_algorithm_version` 3, `ordering_version` 2, `hash_version` 2 — the intended construction. This is the first Episode of Record that is itself a conforming record under the definition it ratifies: capture posture `all_external`, 35 context entries, none declared incomplete, context manifest `590255b80ddd969d4e439378390ace9333186e1a8df66786b79d6a0232d2bb80`.
- **`episode_root_hash`:** `5918cbcd74506fec2e8eed11af3a4c6c5c32c10c571c2bf389c6efa4f730d9ce`
- **Sealed at:** `2026-10-01T16:39:22.642023+00:00` (closed `2026-10-01T16:39:22.642023+00:00`)
- **Segment count:** 18
- **Proof of record:** [`docs/proofs/episode-of-record-protocol-conformance-1.0.0.19d4390f.full.json`](./proofs/episode-of-record-protocol-conformance-1.0.0.19d4390f.full.json), verified with `python -m astp.core.proof_of_record verify` — spine root, signal manifest, exclusion set, structural manifest, context manifest and Episode root all reproduce.

The seal values in this section were written after the seal, drawn from the seal. The Episode is the anchor; this file trails it. Segment 14 carries this text whole (no codicil was needed); this file differs from it in exactly the `Status:` line of the header and this section's filled values and closing paragraph, and in nothing normative. Segments 5 and 9 carry earlier drafts that Segments 14 and 16 record as superseded wherever they differ.

---

**Ratified.** `PROTOCOL-CONFORMANCE.md` 1.0.0, content digest `5b8e5c2f…eacd` (the draft bytes), applying to `SPEC.md` 6.0.2 (digest `fc0a205a…e0cb`), is the conformance definition of record. Publication edits the `Version:` and `Status:` lines; the published file's digest will differ from the ratified digest by exactly those two lines. This text supersedes the drafts in Segments 5 and 9 wherever they differ.
