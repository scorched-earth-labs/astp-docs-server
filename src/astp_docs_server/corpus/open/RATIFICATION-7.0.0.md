# Ratification — SPEC.md 7.0.0 (Whole Document), PROTOCOL-CONFORMANCE.md 1.1.0, PATENTS.md 1.1.0

**Episode of Record:** a2aa7ef2-8775-4ad7-964e-9678f712796b
**Ratified by:** the maintainers, with the Clotho faculty.
**Status:** Ratified as an Episode of Record. The governing text is the Episode's opening text (Segment 1); the maintainers' ratifications are Segments 16 and 18. This file is written after the seal, from the Episode, and is not itself in it; the record table (§6) is filled from the seal.
**Date:** 2026-10-20
**Authority:** GOVERNANCE.md — a change to the semantics of a governance rule is MAJOR, a MAJOR release is ratified in an Episode of Record, and an Episode of Record may ratify `SPEC.md` as a whole document. Each version of a self-versioned companion document (`PROTOCOL-CONFORMANCE.md`, `PATENTS.md`) is ratified in an Episode of Record.

---

## 1. What is ratified

Three texts, each by content digest, as committed at `cb91e69` (astp #101). None of the three files is edited after this seal, header included, so for each the ratified digest and the published digest are one value.

| Document | SHA3-256 (ratified = published) | git blob | Size |
|---|---|---|---|
| `SPEC.md` 7.0.0, as a whole document | `51d1584879142baaee123e732a76310d7f8ccb96f3790001755a79c7a23cb6ab` | `9f21e1eeb733ab90d845cf1a371066faffdab13d` | 244,744 bytes |
| `PROTOCOL-CONFORMANCE.md` 1.1.0 | `a6137608972fac84a837032a8c8eeea37172db8d7996327bd0328739f3404389` | `3f6c32c456dbba29b49126fc92961bab76ff5bd7` | 24,606 bytes |
| `PATENTS.md` 1.1.0 | `9bd35783960166255f80931b3964b842b62880ede95d6806fb3e5d86addafeb6` | `79b669cebaeb89a1f7625fb3f8919aca9bbdbf2a` | 15,394 bytes |

Both companions pin the `SPEC.md` digest above: `PROTOCOL-CONFORMANCE.md` in §7.3, `PATENTS.md` in §4.1. For 7.0.0, as for 6.0.2, the ratified digest, the published digest and the digest `PATENTS.md` §4.1 pledges against are one value.

**Cited, not separately ratified:** `CONFORMANCE-LAYER3.md` 1.2.0, the vectors for what 7.0.0 adds (L3-009, L3-010): SHA3-256 `9ecdbbfd032ef4af6fb7e055f68a6d7aa7b40d41ce5abee410cd97cc4e7ecb65`, git blob `877b1fbf3528b4de4ea4693f5f46f448631186af`.

**Retained:** `docs/history/SPEC-v6.md` is 6.0.2 byte for byte (SHA3-256 `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb`).

---

## 2. The accounting

Last whole-document ratification of `SPEC.md`: **6.0.2**, Episode of Record `46490010-e8a7-4d79-8092-a1a82de3c93f`, `SPEC.md` at `efffac0`. No commit touched `SPEC.md` between that ratification and this amendment. The changes since are three commits on `spec/7.0.0`:

| Commit | Change | Files |
|---|---|---|
| `efd54e5` | the 7.0.0 text | `SPEC.md`, `docs/history/SPEC-v6.md`, `CONFORMANCE-LAYER3.md` |
| `d0ddf42` | the companions | `PROTOCOL-CONFORMANCE.md`, `PATENTS.md` |
| `cb91e69` | this Episode's identifier and the pinned digests | `SPEC.md`, `PROTOCOL-CONFORMANCE.md`, `PATENTS.md`, `CONFORMANCE-LAYER3.md` |

The companions' last ratified texts are `PROTOCOL-CONFORMANCE.md` 1.0.1 (`dca786fa…236a`, Episode `46490010`) and `PATENTS.md` 1.0.0 (`ef288af9…f159`, Episode `df3434bd`). Neither was edited between its ratification and `d0ddf42`.

---

## 3. Rulings

Each ruling was put in the opening text, concurred in by Clotho on the full text (Segments 11–12, restated at 15), and ratified by the maintainers (Segments 16 and 18).

1. **Change class: MAJOR.** The letter of 6.0.2 permitted a Layer 3 creation write against a frozen Episode; 7.0.0 forbids it. Calling that a clarification would let an implementer skip a conformance re-check.
2. **`close_workflow` after a freeze is permitted.** It changes `status` on an existing node within L3-I4 and creates none, so a frozen Episode's record does not grow.
3. **No retroactive effect.** The 26 workflows and 1,490 `ExecutionNode`s filed under `phase-a-doc-campaign` after that Episode closed stay where they are; codicil `9289d262` explains them. An Episode sealed under 6.0.2 that holds such nodes was conformant then and is not made non-conformant (`PROTOCOL-CONFORMANCE.md` §7.1).
4. **The editorial items** — the §6 pointer, N1 (§4.9.3) and D1 (§12.4.1) — change wording only. N1 and D1 were ruled in Episode `46490010`.
5. **Companion classes.** `PROTOCOL-CONFORMANCE.md` 1.1.0 and `PATENTS.md` 1.1.0 are MINOR: each adds coverage of a new Specification Version. `PROTOCOL-CONFORMANCE.md` 1.0.1 remains the conformance definition for 6.0.2, and `PATENTS.md` keeps every 6.0.2 statement. Neither touches the §15 wording, so no counsel pass is needed.

**Out of scope:** the G-40 Episode-identifier rule for `spine_algorithm_version` 3, which stays on the next-revision list; and any new signing, attestation or cross-anchoring mechanism. The Episode's own seal and its context manifest are the record.

---

## 4. What the faculty was given

The Episode's capture posture is `all_external`, set before any context was provided. Its context manifest is therefore the record of exactly what Clotho read.

- **The companions** were each provided whole, as one context entry apiece, and each entry is *verifiable*: the attachment's content hash equals the ratified digest in §1.
- **`SPEC.md` was attached twice.** The first attachment (`32619dbd`, content hash `145fa972…`) was cut at 50,000 characters by an upload defect in the reference deployment and carries a truncation marker; its hash is of a text that never existed, and it is **not** the ratified text. Segment 1, the governing text, carries this copy. The defect was fixed (ignis-os #239) and `SPEC.md` was attached again whole (`5573d236`, Segment 5); that attachment's content hash, computed at upload, is the ratified digest `51d15848…cb6ab`.
- **Clotho read the second attachment in five pages** of 60,000 characters (the last 1,550), recorded as five *attested* context entries; only a single whole-document read is recorded as *verifiable*. Each page's content commitment was recomputed from `SPEC.md` at `cb91e69` and matches, and the five pages concatenate to exactly the ratified bytes. The faculty was therefore given the whole ratified text, and the sealed manifest proves it.
- Clotho's Segment 12 is an artifact, and the artifact was stored as an Episode attachment; its text is also in the Segment.
- In Segment 11 Clotho named a "PROTOCOL-CONFORMANCE §11.2.6" approval-key requirement. No such section exists (§11 is *Open items*), and Clotho withdrew it in Segment 15. No signature beyond this record is required.

All 13 context entries are captured and none is declared incomplete: the 8 attachment entries above (3 at the opening, provided before Segment 3; 5 page reads, provided before Segment 6) and 5 knowledge retrievals at 17:33:20, provided while Clotho answered Segment 13 and shown to her as the recalled knowledge in Segment 14. The reference deployment recorded those five as provided to `ignis` rather than `clotho`, with no spine position, and the recall drew on Ignis's knowledge (four Stratum I notes and one Ignis Stratum II note). That is a defect in the deployment's recall attribution, not in this record: the entries are in the manifest, committed by the seal, and none of the five bears on what is ratified. It is to be fixed in the deployment; this record does not depend on it.

---

## 5. Known gap — recorded for the next revision

- The Episode-identifier rule within G-40 (§6) addresses `spine_algorithm_version` 1 and 2, not 3. Carried from Episode `46490010`; not a defect in 7.0.0.

---

## 6. Record table (filled from the seal)

| Field | Value |
|---|---|
| Episode identifier | `a2aa7ef2-8775-4ad7-964e-9678f712796b` |
| `spine_algorithm_version` | intended **3**; actual **3** (`ordering_version` 2, `hash_version` 2) |
| Capture posture | `all_external` (set before any context was provided); 13 context entries (8 attachment, 5 retrieval; 2 verifiable, 11 attested), none declared incomplete; context manifest `f1fde791018a4eb26c721122f6d116804b19168ef835715681f5c353b99140b6` |
| Segment count | 20 (governing text at Segment 1; the maintainers' ratifications at Segments 16 and 18) |
| Branch points | one, `topic_shift`, recorded automatically at Segment 13 (`f3ba5858-048e-4930-9d8f-c9833f22dc8e`) |
| Sealed at | `2026-10-20T23:57:04.518342+00:00` (closed `2026-10-20T23:57:04.518342+00:00`) |
| `episode_root_hash` | `1776e2187ad370af8ccdbf3a495fdacb164422e7c9e6dee414b687f58236a2f9` |
| Proof of record | [`docs/proofs/episode-of-record-7.0.0.a2aa7ef2.full.json`](./proofs/episode-of-record-7.0.0.a2aa7ef2.full.json), verified with `python -m astp.core.proof_of_record verify`: spine root, signal manifest, exclusion set, structural manifest, context manifest and Episode root all reproduce |

The values in this table were written after the seal, drawn from the seal. The Episode is the anchor; this file trails it.
