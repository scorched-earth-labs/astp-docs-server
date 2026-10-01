# Ratification — SPEC.md 6.0.2 (Whole Document)

**Episode of Record:** 46490010-e8a7-4d79-8092-a1a82de3c93f
**Ratified by:** the maintainers, with the Clotho faculty.
**Status:** Ratified as an Episode of Record. This record is sealed in this Episode; the record table (§6) is completed from the seal in the repository file and is not edited into this Episode.
**Date:** 2026-10-01
**Authority:** GOVERNANCE.md (`efffac0`, #86) — an Episode of Record may ratify `SPEC.md` as a whole document at a version it already carries, accounting for every change since the last whole-document ratification and ruling whether each change went through the process its change class required.
**Companion ratified in the same Episode:** PROTOCOL-CONFORMANCE.md 1.0.1 (§7 below; GOVERNANCE.md `d5ae006`, #83).

---

## 1. What is ratified

`SPEC.md` version 6.0.2, **as a whole document**, by content digest:

| Property | Value |
|---|---|
| SHA3-256 (ratified = published = pledged) | `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb` |
| git blob | `571eb0f983df8c55f79eae3cf31227ba4af388ab` |
| size | 239,844 bytes |
| source | ariadne-protocol corpus at `efffac0` |

`SPEC.md` is not edited after this seal — header included. Its `Status:` line continues to name 6.0.0's Episode, which ratified the amendment's content; this is correct and required. With this ratification, for the first time in the document's history the **ratified digest, the published digest, and the digest `PATENTS.md` §4.1 pledges against are one value.**

---

## 2. The accounting

Last whole-document ratification: **5.0.0** (`ce3f569c`, `SPEC.md` at `44f764e`). Ten commits have touched `SPEC.md` since. Each is accounted for and its change class confirmed:

| Commit | PR | Change | Class | Process | Disposition |
|---|---|---|---|---|---|
| `59d100f` | #49 | 5.0.0 release | — | Own Episode | Already ratified |
| `a656ae1` | #52 | 5.1.0 | MINOR | PR (per GOVERNANCE) | Confirmed |
| `a6e6231` | #55 | proof-of-record record text | — | PR | Confirmed (see §2.1) |
| `b0e1481` | #58 | §4.6 HITL hash text alignment | errata | PR | Confirmed (see §2.1) |
| `88802db` | #59 | reference-package exception-name / example-value renames | editorial | PR | Confirmed (see §2.1) |
| `0a6f434` | #62 | reference-deployment wording | editorial | PR | Confirmed (see §2.1) |
| `e8cca7b` | #63 | 5.2.0 | MINOR | PR (per GOVERNANCE) | Confirmed |
| `72cb56e` | #67 | 6.0.0 fold | MAJOR | Own Episode | Already ratified |
| `def4e4f` | #79 | 6.0.1 | PATCH | Ruling (a) | **Errata — confirmed** |
| `990b7a2` | #80 | 6.0.2 | PATCH | Ruling (b) | **Errata — confirmed** |

Every change since 5.0.0 was decided by the process its class required; four of them (§2.1) changed `SPEC.md` without the version change `VERSIONING.md` requires.

### 2.1 Process deviation — four texts under one version string

Commits #55, #58, #59 and #62 each changed `SPEC.md` while its header read **5.1.0**, with no version change. The consequence: the string "5.1.0" named **four distinct texts** of `SPEC.md` over its life. The content classes:

- **#55** (`a6e6231`) — **Episode-of-Record record text** (proof-of-record format). Record-keeping text, not a protocol change.
- **#58** (`b0e1481`) — **errata.** It aligned §4.6's HITL hash text with the `HITL_*:v2:` constructions already ratified in 5.0.0's §5.7.1. No new construction; the §5.7.1 member row governs. (Confirmed against the §4.6 "Hash computation (5.0.0)" text and the §5.7.1 `HITL_NODE:v2:` row, which agree byte-for-byte on the three constructions.)
- **#59** (`88802db`) — **editorial.** Renames of reference-package exception names and one example value. The protocol defines no exception names; nothing a verifier or conformance profile reads changed.
- **#62** (`0a6f434`) — **editorial.** Wording about the reference deployment. Not renames; prose about the reference deployment only.

**Deviation recorded.** For the span of these four commits, a bare "5.1.0" did not identify a unique text. This is **harmless now, and does not reopen any seal**, for three independent reasons: (i) 5.1.0 was never pinned by content digest, so no ratification, pledge, or seal ever committed to a "5.1.0" text that these commits could have moved beneath; (ii) **this** Episode identifies 6.0.2 by digest (`fc0a205a…`), not by version string, so the whole-document ratification is immune to version-string ambiguity by construction; and (iii) every change to `SPEC.md` since #62 has carried a version change, and the maintainers adopt that as the rule going forward; no mechanism yet enforces it. The deviation is of process discipline, not of integrity.

---

## 3. Rulings

### (a) 6.0.1 §5.7.1 "Spine-state fields" — ERRATA (both halves)

6.0.1 did two things in §5.7.1, and both are errata.

**The sealing clause.** The constraint — *"a node whose non-nullable spine-state field is not a 32-byte hash cannot be a version 2 member, and an Episode holding one cannot seal under version 2 or 3"* — states a consequence the `BRANCH_POINT:v2:` preimage already forced in 6.0.0. `spine_merkle_snapshot` was already a non-nullable HASH field of that preimage — the field list is the §5.7.1 Episode-Root **member table**, and `spine_merkle_snapshot` is named in §19.2.1. A HASH field is 32 raw bytes (§5.1.1, type tag `0x06`: *"32 bytes — a SHA3-256 value, raw, never its hex text"*); a value that is not 32 bytes is not a valid construction input, so the branch point's `content_hash` cannot be computed, so the structural manifest and Episode root cannot be computed, so the Episode cannot seal. The clause adds no preimage, field, or vector. No semantic change.

**The value clause.** 6.0.1 also specifies *what the field holds before the seal*: the **live spine root** — the `spine_algorithm_version` 2 Merkle root over the Episode's non-ephemeral Segments through `source_segment_id` inclusive. This too is errata, because 6.0.0's §5.7.1 membership rule **already** said `spine_merkle_snapshot` *"binds a divergence to the history it left from."* 6.0.1 states the construction that expresses that binding before the seal: **6.0.0 required the binding; 6.0.1 fixes the construction that realises it.** Critically, **a verifier checks the stored value and does not recompute it** (§5.7.1: *"it is bound, not recomputed; a verifier checks the member…"*). Therefore **no existing seal's verification changes** under 6.0.1 — every seal that verified before verifies after, bit-for-bit.

**What 6.0.1 does change, and why it is still errata.** The precise effect is on *conformance of the write*, not on *verification of the seal*. Under 6.0.0, an implementation that stored some other 32-byte value in `spine_merkle_snapshot` **could seal**, and that seal **still verifies** (the verifier reads the stored value). Under 6.0.1, that write is **non-conforming** — the field is required to hold the live spine root — **though its seal still verifies.** 6.0.1 narrows the set of conforming *writes*; it moves no verification outcome. That is the signature of errata under `VERSIONING.md`: it resolves an ambiguity in what a conforming implementation must store, without changing any computed root or any seal's verification.

**Load-bearing condition recorded:** the sealing-clause half holds because `spine_merkle_snapshot` was already in the 6.0.0 `BRANCH_POINT:v2:` preimage. Had it not been, stating a sealing constraint over it would have been additive and the class would differ.

### (b) 6.0.2 §2.5.2 — ERRATA; conformance coupling INTENDED

Naming G-41–G-43 in the §2.5.2 protocol-surface table is errata: they were already MUST under §6; the listing adds no requirement word.

The row's deferral to `PROTOCOL-CONFORMANCE.md` §3, §5 for *which* rules are mandatory for a given implementation's claimed profile is **intended**. §2.5.2 commits the invariant (every conforming implementation enforces all rules mandatory for it); the companion commits per-profile membership of that mandatory set. These are distinct quantifications across a deliberate architectural seam.

**Consequence, ruled true:** a revision of `PROTOCOL-CONFORMANCE.md` can change what §2.5.2 requires of a given implementation — by changing that implementation's mandatory set — **without any byte of `SPEC.md` moving.** This is why the two documents are versioned and ratified on separate tracks (GOVERNANCE #86 and #83). The separate ratification is the governance expression of the protocol-surface / conformance-profile seam. PATCH was correct.

---

## 4. Fold fidelity (6.0.0) — established

This Episode establishes, for the first time, that the 6.0.0 fold (`72cb56e`, #67) carries the ratified draft (`2d96f279…`) verbatim: every construction, domain prefix, field list, G-41–G-43, and every MUST / SHOULD / MAY, apart from section references, adding no new requirement word. Accepted on the maintainers' hunk-by-hunk record, corroborated by spot-check against the §5.1.3 registry, the §5.7.1 / §19.2 preimages, and §6. Three findings disposed:

- **N1 — concur.** The CodicilNode `content_hash` annotation "(SHA3-256 of content)" (§4.9.3) describes the stored field; it is no protocol construction (no domain prefix, no verifier computes it, in no root). Carried verbatim correctly.
- **D1 — concur.** §12.4.1's "providing content … is a ledgered operation" reads against §4.8 / §5.7.3: the ledgered operation is the write of a context entry; a provision writing no entry is not a `CONTEXT_COMMIT`. The draft's reading governs.
- **M1 — concur.** The CM table is in `CONFORMANCE-CONTEXT.md` by the draft's §13 design (confirmed by G-42's own citation of `CONFORMANCE-CONTEXT.md CM-009`). Cite as CM-00N.

---

## 5. Known gap — recorded for the next revision

- **(d)** The Episode-identifier rule within G-40 (§6) addresses `spine_algorithm_version` 1 and 2, not 3. Not a defect in 6.0.2; a known gap carried to the next revision's list, alongside the editorial items from N1 and D1.

---

## 6. Record table — SPEC.md 6.0.2 (filled from the seal)

| Field | Value |
|---|---|
| Episode identifier | `46490010-e8a7-4d79-8092-a1a82de3c93f` |
| `spine_algorithm_version` | intended **3**; actual **3** (`ordering_version` 2, `hash_version` 2) |
| Capture posture | `all_external` (set before any context was provided); 42 context entries, none declared incomplete; context manifest `9df52db04992fd7ccb80b54dcc0b47095914df2c3df3e96cd827543ea2ecd9bf` |
| Segment count | 17 (governing text at Segment 13; the maintainers' ratification at Segment 15) |
| Sealed at | `2026-10-01T19:56:26.350454+00:00` (closed `2026-10-01T19:56:26.350454+00:00`) |
| `episode_root_hash` | `3a543f6ba5a777258d6a2066452f843c63c965574dde66bdd30ea2ccff900da8` |
| Proof of record | [`docs/proofs/episode-of-record-spec-6.0.2.46490010.full.json`](./proofs/episode-of-record-spec-6.0.2.46490010.full.json), verified with `python -m astp.core.proof_of_record verify`: spine root, signal manifest, exclusion set, structural manifest, context manifest and Episode root all reproduce |

The values in this table were written after the seal, drawn from the seal. The Episode is the anchor; this file trails it. Segment 13 carries this text whole; this file differs from it in exactly this section's heading, its filled cells and this paragraph, and in nothing normative. Segments 4 and 8 carry earlier drafts that Segments 13 and 15 record as superseded wherever they differ.

---

## 7. Companion ratification — PROTOCOL-CONFORMANCE.md 1.0.1

`PROTOCOL-CONFORMANCE.md` version 1.0.1, by content digest:

| Property | Value |
|---|---|
| SHA3-256 (ratified = published) | `dca786fa8780dd19563acf39d3369010256f7570d8212d092060a5117094236a` |
| git blob | `cc0f4eeb4f3ce880b3aab5e43a9f9c6e961ad330` |
| size | 23,853 bytes |
| state | final bytes |
| revises | published 1.0.0 (SHA3-256 `2c4f999049a2f31609f9c48bd1667faa26a6c8b10eeff72d7d8e174d749d90d1`) |
| authority | GOVERNANCE.md (`d5ae006`, #83) — self-versioned companion, ratified on its own track |

**What 1.0.1 changes relative to 1.0.0:** the header (`Version`, `Status`, `Date`); the §7.3 table's **6.0.2** row; and the §7.3 note.

**Ruling: it changes nothing conformance requires.** The revision records that 6.0.2 is a whole-document ratification and points the §7.3 row and note at this Episode's record; it adds, removes, and moves no conformance requirement, no profile, and no rule's mandatory status. It is the companion's record of this Episode's seal, not a change to what any implementation must do. Its §7.3 note says `SPEC.md` was not edited after the seal and does not name the root hash; its §7.3 row names this Episode's identifier, not a sealed value. Both the note and the row read true once this Episode seals and `SPEC.md` is unchanged.

---

*Citations use 6.0.2 section numbering. The 6.0.0 draft numbers sections differently (draft §5.3 is `SPEC.md` §4.8.3); draft numbers are not used in this record except to identify the ratified draft `2d96f279…`.*

**This text supersedes the text of Segments 4 and 8 wherever they differ.**
