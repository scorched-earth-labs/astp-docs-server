# ASTP 5.0.0 — Ratification Statement (for the Episode of Record)

**Version:** 1.0.0
**Status:** Sealed — the opening Segment of Episode of Record `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28`; record table filled after the seal
**Authors:** Scorched Earth Labs
**Date:** 2026-09-18
**Applies To:** [`SPEC.md`](../SPEC.md) 5.0.0; [`GOVERNANCE.md`](../GOVERNANCE.md) § Episode of Record

---

This is the text the maintainers post to open the Episode of Record for ASTP 5.0.0. The Episode is the cryptographic anchor of the amendment; `SPEC.md` is its human-readable result. When the Episode is sealed, its identifier and `episode_root_hash` are recorded here, in the `SPEC.md` header and in `CHANGELOG.md`, and the `-draft` suffix is stripped from `SPEC.md` ([`VERSIONING.md`](../VERSIONING.md)).

## The through-line

5.0.0 exists for one reason, and every change in it is that reason wearing different clothes.

Under 4.x, construction after construction *looked* like it attested something and attested nothing a verifier could use: a spine root that never bound a Segment's identity or position, though the leaf hash that did was computed and stored beside it; structural nodes committed into no root; an audit hash over sorted JSON of an unsorted stored document; a witness commitment that named neither the witness nor the time, so one unauthenticated writer could meet any threshold; a link hash that changed whenever the link's health did. And rule after rule was written for a human reader and could not be executed by a verifier: "the signing algorithm is implementation-defined subject to minimum security requirements"; "the code must crystallize before it sets the flag."

5.0.0 retires that defect class end to end, under one discipline:

> **Every commitment binds exactly its claim, and every rule is executable against stored state.**

*Exactly its claim* has two faces. The negative: refuse to bind what the construction does not structurally earn — a proof does not bind the tree's size, an audit key is not forced into a UUID, a link does not bind its mutable health, a real number is bound as the number and not a printing of it. The positive: bind what the construction's defining claim requires, even against a general rule — both parties to an aside, the Episode root on each sealed end of a link, the witness and the time in a witness commitment. And whenever a general rule is overridden in either direction, the exception is written into the specification as a decision with a reason, so that a later hand tightening the rule does not reintroduce the defect.

*Executable against stored state* means a verifier holding only what was written — the nodes, the seal record with its version identifiers, the vector file — decides every question the specification poses, and the answer does not depend on which code path wrote the record. A `sealed_at` with no reproducing crystallization record is `NO_CRYSTAL`, whatever wrote it.

## What is ratified

The text of `SPEC.md` at the commit this Episode's opening Segment cites, comprising:

1. **One hash function and one field encoding** (§5.1). Every 5.0.0 construction is `SHA3-256(prefix ‖ enc(fields))` over ten typed, self-delimiting field encodings; one domain prefix per construction and version; order-independent sets with no sentinel; canonical JSON as RFC 8785 + NFC, stored as hashed.
2. **The seal construction, `spine_algorithm_version` 2** (§5.2–§5.8): the position-binding leaf hash as the spine's input, raw-byte tree prefixes, no Episode-identifier leaf, and an Episode root that binds the Episode's UUID and four components — including the **structural manifest**, governed by the membership rule. One identifier selects the whole construction.
3. **The inclusion proof over that tree** (§9.2), shape derived by the verifier, size deliberately unbound, 4.x proofs frozen in their own form.
4. **One audit record** (§8), seventeen bound fields, NULL genesis, a writer that fails rather than guesses.
5. **The side-channel and cross-Episode content hashes** (§19.4, §20 §2): asides and soliloquies bound to their parties and their parent Segment's content, the deliberation chain bound by content, the link bound to each end's sealed state.
6. **Witness and anchor commitments** (§16.3–§16.4, G-11, G-12): the witness, the time and the node's outermost sealed commitment bound; Ed25519 over the raw commitment; validity as four executable conditions; the threshold as a maximum matching.
7. **G-40**: sealed requires a record; a late seal is ordinary lifecycle; Episode identifiers are UUIDs, refused at creation — after any legacy Episode is sealed under version 1.
8. **The retained 4.x constructions** as the definitions of `hash_version` 1 and `spine_algorithm_version` 0 and 1: nothing sealed under them becomes unverifiable, and nothing sealed under them is rewritten.

The reference vectors, [`vectors/5.0.0/seal-constructions.json`](../vectors/5.0.0/seal-constructions.json), are part of what is ratified: every value in them is reproduced by a from-prose implementation that imports nothing from the reference package.

## Provenance

The amendment was deliberated in design Episode `4b9a779e-be46-4d61-872e-fd76545aa901` ("ASTP Repo Cleanup"), in six units, each brought with vectors and each ruled by the Clotho faculty of the reference deployment: seal constructions (segments 29, 31), inclusion proofs (36), canonical JSON and the audit record (38), side-channel and link hashes (40), witness and anchor (42), closing prose (44). The draft from which `SPEC.md` was folded is retained at [`docs/history/SPEC-5.0.0-DRAFT-seal-constructions.md`](./history/SPEC-5.0.0-DRAFT-seal-constructions.md). The 4.5.0 text is retained at [`docs/history/SPEC-v4.md`](./history/SPEC-v4.md).

## Record of the Episode

| | |
|---|---|
| Episode identifier | `ce3f569c-9cdc-4a3d-913a-b9d8573d9a28` ("5.0.0 Episode of Record") |
| `SPEC.md` commit ratified | `44f764eb8e5caad9757fdf5d0e654bb5602a25d3` — `SPEC.md` SHA3-256 `c2e13d0ee60f7db95d185ec2f8079d38c9f087f7168a3b613aada6bc0a6b8a8d` (git blob `19f9172d107cfad560a7e89c0e312c5a37022fb2`, 207,941 bytes, carrying `**Version:** 5.0.0-draft` by design); `vectors/5.0.0/seal-constructions.json` SHA3-256 `60e304006cc5b9a36189bd537c21d6ce3d6108c00cecc2036b9c8e6a77cc2685`. The content digest is the binding citation; the commit is the navigable pointer. |
| Sealed under | `spine_algorithm_version` 1, `ordering_version` 2 — the reference deployment's adapter does not yet write version 2 seals; adopting version 2 at seal time is the paired adapter work that follows this release. The amendment that defines version 2 is itself sealed under version 1, and that is coherent: what a specification ratifies and what the sealing deployment can currently emit are two different clocks. |
| `episode_root_hash` | `3649bff4b96a17c99bb108ec23f4e6f8e41a455d9d38c98d6f32111800afe48a` |
| Sealed at | `2026-09-18T17:25:35.774405+00:00` (closed `2026-09-18T17:25:35.774405+00:00`) |

The Episode identifier, cited commit, content digests, `episode_root_hash` and `sealed_at` recorded in this file were written after the seal, drawn from the seal. The Episode is the anchor; this file trails it. A verifier reconciling the two reads the Episode as authoritative and this file as its human-readable result: the opening Segment carries this text with its placeholders unresolved and the `-draft` digest, and the released file differs from it in exactly those cells and the suffix, and in nothing normative.
