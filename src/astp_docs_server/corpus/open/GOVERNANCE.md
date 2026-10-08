# Governance

How changes to ASTP are proposed, decided, and recorded. The versioning rule itself is in [`VERSIONING.md`](./VERSIONING.md); the mechanics of contributing are in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Who decides

ASTP is maintained by Scorched Earth Labs. The maintainers decide what is merged, what version a change carries, and when a version is released. Anyone may propose a change, review one, or argue against one; discussion happens in the open on this repository's issues and pull requests.

This is a single-maintainer-organization project today. If independent implementations appear, the maintainers expect to widen this — implementers are the people a breaking change costs most — and any such change will be made by amending this document through a pull request.

## How a change is decided

**Errata (PATCH).** A pull request. A maintainer merges it when the text is right and no existing conformant implementation is affected.

**Additive surface (MINOR).** Open an issue describing the problem and the proposed surface before writing specification text. Once a maintainer agrees the design, a pull request adds it to `SPEC.md`, with conformance requirements for the new surface and an entry in `CHANGELOG.md`.

**Canonical form (MAJOR).** A change to a hash preimage, a serialization, a required field, the semantics of a governance rule, or the removal or renaming of normative surface. The process is:

1. **Proposal.** An issue that states what is wrong with the current construction, what replaces it, and what happens to records sealed under the old one. A proposal that would make existing sealed records unverifiable will not be accepted; breaking constructions are introduced as new versions alongside the old.
2. **Amendment draft.** A pull request containing the revised `SPEC.md` text, new or changed conformance requirements with expected values, and the migration notes. The prior major version of `SPEC.md` is retained under `docs/history/`.
3. **Review period.** The pull request stays open for comment. Maintainers respond to objections on the record before deciding.
4. **Ratification.** The maintainers ratify the amendment in an Episode of Record (below) and merge.
5. **Release.** The version is tagged and the `CHANGELOG.md` entry cites the Episode of Record.

## Episode of Record

An Episode of Record is an ASTP Episode, opened by the maintainers, in which a MAJOR change is deliberated and ratified. It is the protocol recording its own amendment: the deliberation is sealed, and the seal commits to what was decided. The specification text is the human-readable result; the Episode is the anchor for it. The term is defined in [`GLOSSARY.md`](./GLOSSARY.md).

Outside contributors do not need to run ASTP, or have access to any deployment, to propose or shape a MAJOR change. The proposal, the draft, and the review all happen in this repository. Opening and sealing the Episode of Record is the maintainers' step.

An Episode of Record also ratifies a normative companion document that carries its own version under [`VERSIONING.md`](./VERSIONING.md) — today, [`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md), whose definition of a Conforming Implementation is what [`PATENTS.md`](./PATENTS.md) §4.2 grants against, and `PATENTS.md` itself, the policy that grant is made under. Each version of such a document is ratified in an Episode of Record before it is released, whether or not `SPEC.md` changes with it, and the Episode cites the text it ratifies by content digest. Where a revision changes nothing that conformance requires (an editorial correction, for instance), the ratifying Episode may record that fact and be correspondingly brief: it still seals the revised text's digest, but there is no decision to deliberate.

An Episode of Record may also ratify `SPEC.md` as a whole document at a version it already carries, whatever that version's change class. Such an Episode changes no specification text. It cites the document by content digest, and it accounts for every change since the last whole-document ratification, ruling for each whether it was made under the process its change class required. `SPEC.md` is not edited after the seal, so for that version the ratified digest, the digest of the published file and any digest pinned elsewhere are the same.

## Releases

A release is a git tag `vMAJOR.MINOR.PATCH` on the commit whose `SPEC.md` carries that version. The reference package `astp` is versioned separately from the protocol; the protocol version a given package implements is exposed as `astp.PROTOCOL_VERSION`.

A change confined to the package — packaging metadata, CI, non-normative documentation, or `astp.__version__` itself — is a package release, not a protocol release. It carries no `vMAJOR.MINOR.PATCH` tag and needs no Episode of Record, provided `SPEC.md` and `astp.PROTOCOL_VERSION` are unchanged.

## Changing this document

By pull request, decided by the maintainers, with the same open review as any other change.
