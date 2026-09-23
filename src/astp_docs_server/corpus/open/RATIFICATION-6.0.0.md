# ASTP 6.0.0 — Ratification Statement (for the Episode of Record)

**Version:** 1.0.0
**Status:** Sealed — Segment 18 of Episode of Record `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8`, completed by codicil `9bcc9240-4221-4ab6-a63c-3172e65815fe`; record table filled after the seal
**Authors:** Scorched Earth Labs
**Date:** 2026-09-22
**Applies To:** [`SPEC.md`](../SPEC.md) 6.0.0, folded from [`docs/history/SPEC-6.0.0-DRAFT-context-commitment.md`](./history/SPEC-6.0.0-DRAFT-context-commitment.md) (draft.2); [`GOVERNANCE.md`](../GOVERNANCE.md) § Episode of Record

---

This is the text the maintainers posted to the Episode of Record for ASTP 6.0.0, at Segment 18. The Episode is the cryptographic anchor of the amendment; `SPEC.md` is its human-readable result. When the Episode is sealed, its identifier and `episode_root_hash` are recorded here, in the `SPEC.md` header and in `CHANGELOG.md`; the draft is folded into `SPEC.md` and retained under `docs/history/`, and the `-draft` suffix is stripped from `SPEC.md` ([`VERSIONING.md`](../VERSIONING.md)).

## The through-line

6.0.0 exists for one reason. A sealed Episode can prove what its agents wrote and in what order, what structure the Episode took, and which human decisions concluded inside it. It cannot prove what its agents were *given*. An `AttachmentNode` is content-hashed and ledgered but is a member of no root component; retrieved knowledge exists only in a best-effort audit outside every hash; content fetched from the web or an external API has no defined treatment. "This is what the agent knew when it decided" is a claim without a commitment — and it is the claim that oversight of an automated decision turns on.

The amendment adds one thing and states one thing.

**It adds a context manifest**: a sixth field of the Episode root, committing every external input an agent was given during the Episode — attachments, retrieved knowledge, external content, tool output — as typed entries, each a stored node with its own hash construction, with inclusion proofs so that one entry can be proven without disclosing the others.

**It states that the seal proves history, not retention.** The seal commits to hashes and pointers, never to content. That is what lets presence be bound into the root and content be lawfully erased from behind it without contradiction: erasure destroys content and salt together and appends a witnessed tombstone; no sealed preimage moves. Where the content is low-entropy personal data, its commitment is non-reversible by construction, so that erasing the content also destroys the means of confirming a guess at it.

**They are safe only together.** A commitment to context without the non-reversible construction is a permanent, guessable commitment to a borrower's account number or a patient's date of birth — deletion that is not deletion. A conforming 6.0.0 implementation implements both halves.

> **The governing invariant: the seal proves history, not retention.**

## What is ratified

The text of [`docs/history/SPEC-6.0.0-DRAFT-context-commitment.md`](./history/SPEC-6.0.0-DRAFT-context-commitment.md) at the commit the Episode cites (`4ec1de1`, Segments 15 and 20), as proposed text for `SPEC.md`, comprising:

1. **The context entry** (`ContextEntryNode`, §4.8): one node type, `entry_type` discriminating `attachment`, `retrieval`, `external` and `tool_output`; *provided* means the content entered the context window of an agent whose reasoning is recorded as Segments in this Episode; the claim is "what the agent was given," never "what it relied on."
2. **The entry hash** (`CONTEXT_ENTRY:v1:`, §6.1) binding the entry's identity, type, recipient, time, the spine position it preceded, capture state, content commitment, which construction made it, verifiability at seal, media type, source version and the entry it resolves. Provenance and content-plane fields — `source_ref`, `content_ref`, `salt_ref`, `erasure_state` — are outside the preimage and outside every root.
3. **Two content constructions, one sealed bit** (§5.3): `CONTEXT_CONTENT:v1:` over the bytes as provided, and `CONTEXT_CONTENT_SALTED:v1:` with a per-entry CSPRNG salt stored in a namespace separate from the content; `salted` is in the preimage, the salt's pointer is not.
4. **The context manifest** (`CONTEXT_MANIFEST:v1:`, §6.2): the §5.4 Merkle tree over entry hashes in ascending bytewise order, bound with the capture posture and the entry count; a function of the set, so membership binds and insertion order does not; inclusion proofs in the §9.2 form; the empty manifest defined (`n = 0`, root NULL).
5. **Episode root version 3** (`EPISODE_ROOT:v3:`, §7), six fields — the version 2 root with `context_manifest_hash` appended — selected by **`spine_algorithm_version` 3** in the single §5.8 identifier. One identifier selects the whole seal construction; an invalid combination remains unrepresentable; the spine root under version 3 is byte-identical to version 2; nothing sealed under 0, 1 or 2 is re-sealed or rewritten.
6. **Capture posture and declared-incomplete entries** (§5.5, §6.3, **G-41**): a sealed declaration of what the Episode undertook to capture (`all_external`, `declared_only`, `none`) bounding what absence may mean; a provision whose content was not captured is a positive manifest member; an Episode may seal over declared gaps and never over an undeclared one; repair is append-only through `resolves`, and no entry is ever mutated.
7. **Verifiability at seal** (§5.4): `verifiable` or `attested`, fixed at seal, never changed by a later erasure; an `external` entry's URI is provenance the seal does not vouch for, and a verifier MUST NOT re-fetch it.
8. **Non-reversible commitment for low-entropy personal data** (**G-42**, §5.3, §8.1): such content MUST commit through the salted construction; the implementation classifies at write time.
9. **Content-plane erasure** (**G-43**, §8.2, §8.3): destroy content and salt atomically, append an `ErasureTombstone` (`ERASURE_TOMBSTONE:v1:`) as a §12.4.1 codicil, null the pointers, touch nothing else; the Episode root verifies identically before and after; an erased entry is reported as erased and witnessed, never as an integrity failure. The `CodicilNode` schema block (§4.9) is added alongside the tombstone.
10. **The §4.7 attachment relationship** (§4): a provided attachment is a context entry and a manifest member; the `AttachmentNode` is unchanged and remains the substrate the entry commits over, referenced by `attachment_id` as provenance outside the preimage; an attachment never provided to an agent is not a member. Under versions 0–2 an `AttachmentNode` remains a member of no root, retained as the property of those constructions.
11. **The Layer 3 relation** (§12): a `tool_output` entry binds a `SkillInvocation` by its `content_hash`; the invocation is committed once, and the entry references it. **§11 and §11.1 are unchanged**: the retrieval audit records the act of reading and is not promoted into the seal; the register gains `CONTEXT_COMMIT` (§11).
12. **Verification** (§10): §9.3 extends to the sixth field with no out-of-band state; the conformance requirements CM-01 … CM-10 (§13), including **CM-09**, *safe only together* — an implementation claiming 6.0.0 context commitment without G-42 is non-conformant — and **CM-10**, a version 2 seal of an Episode holding context entries still reproduces under version 2.
13. **The retained constructions**: `hash_version` 1 and 2, `spine_algorithm_version` 0, 1 and 2, exactly as 5.2.0 defines them. Nothing sealed under them becomes unverifiable, and nothing sealed under them is rewritten.

The reference vectors, [`vectors/6.0.0/context-commitment.json`](../vectors/6.0.0/context-commitment.json) (`vectors/6.0.0-draft/` at the cited commit), are part of what is ratified: every value in them is reproduced by a from-prose implementation that imports nothing from the reference package, as the 5.0.0 vectors were.

## Record-notes

Three matters the design Episode raised are recorded here so that a later reader does not mistake them for something else. None changes the text ratified above.

1. **The `CodicilNode` schema is ratified by implementation.** 5.2.0 names the codicil in §4.4.1 and §12.4.1 and the reference package carries `CodicilNode`; `SPEC.md` has no schema block for it. This amendment adds one (§4.9) because the erasure tombstone needs it. It closes a 5.2.0 documentation gap and introduces no construction; it is not scope creep.
2. **Classification quality is the implementation's residual risk.** The protocol mandates the salted construction for low-entropy personal data (G-42) and cannot itself detect low entropy. A value misclassified at write time receives a plain, reversible commitment. CM-07 tests the property by construction; misclassification is an implementation conformance concern, recorded in the implementation's `ConformanceDeclaration`, not a protocol hole (§14).
3. **The §4.7 / §4.8 attachment relationship — resolved.** Attachments are in scope as an entry type (design Episode `ec31d0c0`, segment 81). One sealed path: the context entry carries sealed presence and the verifier reads it; the `AttachmentNode` is retained as substrate and provenance, resolved from the entry's `source_ref`. The §4.7 statement that no sealed root detects the addition or removal of an `AttachmentNode` is retained as a true property of the node under versions 0–2 and is relocated out of the trust path under version 3. The draft already states this (§4, §4.8, §5.1); no schema change follows from the ruling.

## Provenance

The amendment was deliberated in design Episode `ec31d0c0-50eb-4a2a-9f95-32536c9e645e` ("Attachments, RAG, External Websites and Privacy/RTD", 2026-09-22), opened on a brief on the use of ASTP in the United States mortgage industry, and ruled by the Clotho faculty of the reference deployment with the maintainers: the unifying principle and the four findings (segments 10, 15, 17, 22), the capture posture and declared-incomplete entries (35–37), the erasure construction (47, 49), the first artifact (51), the re-basing onto `spine_algorithm_version` 3 after the ratified 5.0.0 text was re-read (57), the review and approval of draft.2 (71), the attachments ruling (81) and its consequence (82–84). The erasure question descends from Episode `531a045b-a945-4aa2-8648-edf618067a11` ("Ariadne and Data Privacy, Right to Delete", 2026-03-30), whose pointer-and-reference path this amendment makes protocol surface.

The design Episode's spec retrieval served the pre-5.0.0 text for part of its course; the draft's §1 records every point where that mattered and how each was re-based, and the one ruling that conflicted with the ratified text was re-ruled inside the same Episode. The draft from which `SPEC.md` is folded is retained at `docs/history/SPEC-6.0.0-DRAFT-context-commitment.md` after the fold. The 5.2.0 text is retained at `docs/history/SPEC-v5.md`.

## Record of the Episode

| | |
|---|---|
| Episode identifier | `80e5a2dd-3d9f-45d0-abfb-6489c8caf1b8` ("6.0.0 Episode of Record") |
| Draft commit ratified | `4ec1de187f66521d07344e742a24bfe4fa5dae10` — `docs/SPEC-6.0.0-DRAFT-context-commitment.md` SHA3-256 `2d96f27949715118a3c9b6a2a431ff6df009de37bf8c9d2a39907cd6d9c5647c` (git blob `523fe81903adfc8ae5f4364d7673ec64d7b92aff`, 40,274 bytes, carrying `**Version:** 6.0.0-draft.2` by design); `vectors/6.0.0-draft/context-commitment.json` SHA3-256 `f493080713fc1de58ae11e5c4891e524ba98c70510a93f3eb045eeeb1ba4e3ae` (git blob `3f1c1985b8640a664973c6d45412ec945e46ebf4`, 16,967 bytes). The content digest is the binding citation; the commit is the navigable pointer. |
| Sealed under | `spine_algorithm_version` 2, `ordering_version` 2 — the reference deployment's adapter seals under the version it can currently emit; the amendment that defines version 3 is itself sealed under version 2, and that is coherent: what a specification ratifies and what the sealing deployment can currently emit are two different clocks. |
| `episode_root_hash` | `45cd50c5d34c6d1ec49fa9a6fd7989036e2d91d624f66e9eb8e93c9904f27d3e` |
| Sealed at | `2026-09-22T22:18:46.261957+00:00` (closed `2026-09-22T22:18:46.261957+00:00`); 21 Segments; verified by the reference deployment's verifier and by the exported proof of record [`docs/proofs/episode-of-record-6.0.0.80e5a2dd.full.json`](./proofs/episode-of-record-6.0.0.80e5a2dd.full.json) |

The Episode identifier, cited commit, content digests, `episode_root_hash` and `sealed_at` recorded in this file were written after the seal, drawn from the seal. The Episode is the anchor; this file trails it. A verifier reconciling the two reads the Episode as authoritative and this file as its human-readable result. Segment 18 carries this text through item 13 of "What is ratified" — the paste that produced it was cut there — and codicil `9bcc9240-4221-4ab6-a63c-3172e65815fe` (`CODICIL_APPEND`, §12.4.1, appended 2026-09-22T22:59:15Z) carries the remainder verbatim with the two content digests; between them the sealed record and this file differ in exactly the record-table cells, the header status and the file paths that moved at release, and in nothing normative. The opening Segment (1) is the maintainers' summary; Segment 16 is a working enumeration by the Clotho faculty that Segment 20 records as superseded by this text wherever they differ. The retained draft under `docs/history/` carries a provenance banner; the ratified bytes are the blob at the cited commit.
