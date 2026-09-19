# Versioning

**Version:** none of its own — this policy is versioned with [`SPEC.md`](./SPEC.md) (see "Where versions are declared")
**Status:** Stable
**Authors:** Scorched Earth Labs
**Date:** 2026-09-17
**Applies To:** every version of `SPEC.md` and its companion documents

---

ASTP uses [Semantic Versioning](https://semver.org/) — three-segment `MAJOR.MINOR.PATCH`. No fourth segment.

## The rule

- **MAJOR** — Any change to canonical form: hash preimages, serialization, required fields, anything that invalidates an existing conformant implementation. Conformance-breaking by definition.
- **MINOR** — Additive surface: new optional node types, new edge types, new query surface, new fields with safe defaults. Existing implementations remain conformant; new ones gain capability.
- **PATCH** — Errata: spec wording, clarifications, ambiguity resolution. No semantic change.

That's the policy. Everything else (compatibility expectations, deprecation, what "conformant" means) follows from it.

## Where versions are declared

`SPEC.md` is the canonical version source. The `**Version:**` field at the top of that file IS the protocol version.

- `docs/history/SPEC-v{MAJOR}.md` retains prior major-version specs for historical reference (e.g., [`docs/history/SPEC-v1.md`](./docs/history/SPEC-v1.md) is the original `0.1.0-draft`, superseded by the v2.x line in `SPEC.md`; [`docs/history/SPEC-v3.md`](./docs/history/SPEC-v3.md) is the 3.x line at 3.5.1; [`docs/history/SPEC-v4.md`](./docs/history/SPEC-v4.md) is the 4.x line at 4.5.0). The 2.x line has no retained file. The former standalone amendment documents are kept in the same directory, for provenance only.
- Implementation Guides (`IMPLEMENTATION-*.md`), Conformance documents (`CONFORMANCE*.md`), and any other artifacts are versioned-against, not versioned-independently. They describe behavior at a specific protocol version (e.g. "this guide applies to ASTP v3.4.0"); they do not carry their own independent version numbers.

## Current version

Read it from `SPEC.md` — the `**Version:**` field at the top of that file. This
document deliberately does not restate it.

A version repeated in a second place is a second thing to forget. This section
previously read `2.5.0-draft` long after `SPEC.md` had moved to the 3.x line,
and nothing in the repository could notice the disagreement. "`SPEC.md` is the
canonical version source" is only true if nothing else claims to be.

Once a version ships, its line is errata-only: no new amendments, no feature
additions to a released version. Subsequent feature work goes to the next
MAJOR or MINOR.

## History

Tracked in [`CHANGELOG.md`](./CHANGELOG.md). Each version's entry describes the additions, changes, and (for MAJOR bumps) breaks since the prior version.

## What counts as breaking

For ASTP specifically, MAJOR bumps require an **Episode of Record** — a ratifying Episode that anchors the change cryptographically. The Episode is the authoritative cognitive artifact; the spec document is the human-readable description.

Specific change categories that **always** require a MAJOR bump:

- Hash preimage construction (leaf hash, Merkle Spine, position-binding fields, domain separation).
- Required fields on any persisted node type.
- Canonical serialization byte form for any hashed field.
- Governance rule semantics (G-1 through G-N).
- Removal or renaming of any normative node type, edge type, or interface method.

Specific change categories that are typically MINOR:

- New optional node types or edge types.
- New optional fields with safe defaults on existing node types.
- New query surface that doesn't change existing query semantics.
- Implementation-defined extension points (where the protocol explicitly leaves a decision to the implementer).

If unsure: ask whether an existing conformant implementation continues to conform without changes. If yes, MINOR. If no, MAJOR.

## Pre-release tags

A `-draft` suffix on a version (e.g., `2.5.0-draft`) indicates the version is still in active spec development and not yet finalized. Once finalized, the `-draft` is stripped and the version is tagged in git. Draft versions are not stable references for external implementers — they may change without an explicit version bump.

## Compatibility expectations

- **Within a MAJOR version**, all implementations conformant to `MAJOR.MINOR.PATCH` must remain conformant to `MAJOR.(MINOR+1).0` and `MAJOR.MINOR.(PATCH+1)`. New conformant features may be added; existing semantics do not change.
- **Across MAJOR versions**, conformance is not preserved. Implementations targeting v2.x cannot expect to be conformant to v3.x without explicit migration.

## How to bump

1. Identify the change category (MAJOR / MINOR / PATCH) using the rule above.
2. For MAJOR bumps: open a ratifying Episode of Record, complete the amendment, and update `SPEC.md` with the integrated material. Move the prior version's `SPEC.md` to `docs/history/SPEC-v{PRIOR_MAJOR}.md`, with the historical banner the other files there carry.
3. For MINOR / PATCH bumps: update `SPEC.md` in place; no historical retention file needed.
4. Update `CHANGELOG.md` with the version entry.
5. Update the `**Version:**` field at the top of `SPEC.md`.
6. When finalizing a `-draft`: strip the `-draft` suffix and tag the commit in git (`git tag vMAJOR.MINOR.PATCH`).
