# Ratification of `PATENTS.md` 1.0.0

**Document ratified:** `PATENTS.md` — Patent Policy and Patent Pledge
**Version:** 1.0.0
**Status:** Ratified — Episode of Record `df3434bd-6936-441c-a896-254149f2bd48`
**Ratified by:** the maintainers, with the Clotho faculty
**Date:** 2026-10-01
**Protocol:** ASTP — the AI State Tree Protocol
**Maintainer:** Scorched Earth Labs, LLC

---

## 1. What is ratified

This record ratifies `PATENTS.md` version **1.0.0**, the first versioned text of
the ASTP patent policy and pledge, as a whole document by its final bytes.

| Field | Value |
|---|---|
| Ratified text | `PATENTS.md` 1.0.0, final bytes |
| SHA3-256 digest | `ef288af95b5c1197f242edbe8f17859654d0f6c9f70785bb9634c4dcf564f159` |
| git blob | `e95a0eaaa53c305d0c70fce843e41c683b0f667e` |
| Size | 14,768 bytes |

The ratified digest and the published digest are one value: the file is not in
the repository until release, and nothing changes after the seal.

The digest, not the version string, is the binding identification of the text
ratified. Any party may verify it:

```bash
python3 -c "import hashlib,sys; print(hashlib.sha3_256(open(sys.argv[1],'rb').read()).hexdigest())" PATENTS.md
```

## 2. How 1.0.0 differs from the prior published text

1.0.0 is the text at `1a25e50`
(SHA3-256 `43feb887c5f84692b632163041f74e8170837244294ab281a0428d6c1aa5c04f`)
with exactly three header lines added:

- `Version: 1.0.0`
- a `Status:` line naming this Episode of Record
- `Date: 2026-10-01`

Every other byte is unchanged, including every pledge term and the §4.1
`SPEC.md` digest table (`6.0.2 →`
`fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb`). The
pledge substance is identical to the counsel-reviewed text (#81). **No pledge
term changes in this Episode.**

## 3. Scope

`PATENTS.md` is the patent policy, not a conformance document. This Episode
ratifies neither `SPEC.md` nor `PROTOCOL-CONFORMANCE.md`; both are already
ratified in their own Episodes of Record (`46490010` and `19d4390f`
respectively). This record brings `PATENTS.md` into versioning alignment with
the other normative protocol documents: it now carries its own version, ratified
in an Episode of Record before release, under `VERSIONING.md` and `GOVERNANCE.md`
at `1a25e50` (#89).

## 4. Why this matters

§15 bars an amendment from retroactively withdrawing a patent license already
granted to a Conforming Implementation. A licensee can rely on that guarantee
only if the policy text relied upon is identifiable. From 1.0.0 onward it is
identified by version and by content digest in a sealed record. This completes
the identification chain under a Conforming Implementation's license:

- **Specification** — `SPEC.md` 6.0.2, Episode of Record `46490010`
- **Conformance definition** — `PROTOCOL-CONFORMANCE.md` 1.0.1, Episode of Record `46490010`
- **Policy the grant is made under** — `PATENTS.md` 1.0.0, this Episode of Record

## 5. Unversioned texts before 1.0.0 — identified, not ratified

Recorded by digest so they remain identifiable. **These are not ratified by this
Episode.** Anything granted while one of them was in force is governed by that
text and by §15, not by this record.

| Commit | Ref | Date | SHA3-256 | Size |
|---|---|---|---|---|
| `990b7a2` | #80 | 2026-09-26 | `4026665e7d4d8854a77c4625e72bb05b6cd006ea7eba73c46e959d847e6145b9` | 12,434 bytes |
| `a072341` | #81 (counsel review) | 2026-09-29 | `e83ba33b38ae2efa5be6af03e3820870231bf15d0cea38d72418d2ea42554ace` | 13,928 bytes |
| `276cc25` | #88 | 2026-10-01 | `43feb887c5f84692b632163041f74e8170837244294ab281a0428d6c1aa5c04f` | 14,557 bytes |

The `276cc25` text is also the text at `1a25e50`, which 1.0.0 extends with the
three header lines.

## 6. Rulings recorded

1. **1.0.0 is the published text plus the three header lines, and changes no
   pledge term.** §4.1, §4.2, and §15 were read whole and confirmed to read as
   stated; the §4.1 digest table is unchanged.
2. **The three unversioned texts are identified, not ratified.** Anything
   granted while one was in force is governed by that text and by §15, not by
   this Episode.

## 7. Record of Episode of Record

Filled from the seal. The values below are taken from the sealed record, not reconstructed.

| Field | Value |
|---|---|
| Episode identifier | `df3434bd-6936-441c-a896-254149f2bd48` |
| `spine_algorithm_version` | intended 3 — actual: **3** (`ordering_version` 2, `hash_version` 2) |
| Capture posture | `all_external` (set before any context was provided); 6 context entries, none declared incomplete; context manifest `2afa42caad2b4233d752c00017a3c950f0be77f78a2882d3c5b393e9cc6528c1`. The attachment entry for `PATENTS-1.0.0.md` is unsalted and `verifiable`, and commits to exactly the ratified bytes. |
| Segment count | 8 (ruling and record text at Segment 4; the maintainers' ratification at Segment 6) |
| Sealed at | `2026-10-01T21:09:53.833374+00:00` (closed `2026-10-01T21:09:53.833374+00:00`) |
| `episode_root_hash` | `d77bcdd639747d6f1bba806c02586c06229bd2a1c556c5c7273cb056ce0c0b15` |
| Proof of record | [`docs/proofs/episode-of-record-patents-1.0.0.df3434bd.full.json`](./proofs/episode-of-record-patents-1.0.0.df3434bd.full.json), verified with `python -m astp.core.proof_of_record verify`: all six roots, including the context manifest, reproduce |

The Episode is the anchor; this file trails it. Segment 4 carries this text whole; this file differs from it in exactly this section's opening sentence and filled cells and this paragraph, and in nothing normative.

## 8. Supersession

This record supersedes any earlier draft of the ratification of `PATENTS.md`
1.0.0 in this Episode.
