# Patent Policy and Patent Pledge

**Version:** 1.0.0
**Status:** Stable — ratified in Episode of Record `df3434bd-6936-441c-a896-254149f2bd48` ([`docs/RATIFICATION-PATENTS-1.0.0.md`](./docs/RATIFICATION-PATENTS-1.0.0.md))
**Date:** 2026-10-01
**Protocol:** ASTP — the AI State Tree Protocol
**Maintainer:** Scorched Earth Labs, LLC
**License:** Apache License, Version 2.0

---

## 1. Purpose

This document describes the patent rights associated with ASTP, the AI State
Tree Protocol (the "Protocol"), including the relationship between the Apache
License, Version 2.0, and the separate patent commitment made by Scorched Earth
Labs, LLC ("Scorched Earth Labs").

The purpose of this policy is to permit broad implementation and adoption of the
Protocol while preserving the ability of Scorched Earth Labs to develop, own,
license, commercialize, and enforce patent rights concerning technology that is
outside the scope of this patent pledge.

This document does not modify the Apache License, Version 2.0.

## 2. Copyright and Open-Source License

The reference implementation, protocol documentation, and other materials
identified as being licensed under the Apache License, Version 2.0 are licensed
under that license.

The Apache License governs copyright rights and includes its own patent license.
Nothing in this document limits, expands, or otherwise modifies the rights
granted under the Apache License.

The complete Apache License, Version 2.0, is provided in the
[`LICENSE.txt`](./LICENSE.txt) file.

## 3. Separate Patent Pledge

Subject to the terms and conditions of this document, Scorched Earth Labs, LLC
hereby grants to each person or entity that implements the Specification a
perpetual, worldwide, non-exclusive, royalty-free, non-transferable (except as
permitted below) patent license under the Licensed Patents to make, have made,
use, offer to sell, sell, import, and otherwise transfer a Conforming
Implementation.

This patent pledge is separate from, and in addition to, any patent license
provided by the Apache License.

## 4. Definitions

### 4.1 "Specification"

"Specification" means the normative technical specification contained in this
repository as [`SPEC.md`](./SPEC.md), identified by protocol version and by the
SHA3-256 digest of its text:

| Protocol version | SHA3-256 digest of `SPEC.md` |
|---|---|
| 6.0.2 | `fc0a205ad4b7a0a04e1b5f2583ebc02184d3e33885915aef62bed1ec1d38e0cb` |

and any later version expressly designated by Scorched Earth Labs as being
covered by this patent pledge.

The digest, not the version string, is the binding identification of the text
pledged. Any party may verify it:

```bash
python3 -c "import hashlib,sys; print(hashlib.sha3_256(open(sys.argv[1],'rb').read()).hexdigest())" SPEC.md
```

`SPEC.md` 6.0.2 is ratified as a whole document in Episode of Record
`46490010-e8a7-4d79-8092-a1a82de3c93f`
([`docs/RATIFICATION-SPEC-6.0.2.md`](./docs/RATIFICATION-SPEC-6.0.2.md)). The
digest above is therefore the ratified digest, the published digest and the
pledged digest, which are one value. An exported proof of record is published
under [`docs/proofs/`](./docs/proofs/) and verifies with the reference package
alone.

Before 6.0.2, whole-document ratification did not apply to `SPEC.md`: the 6.0.0
Episode of Record ratified the amendment draft
(`docs/history/SPEC-6.0.0-DRAFT-context-commitment.md`) as proposed text rather
than the published file. That history is retained in the ratification records
and does not affect the identification above.

The Specification is `SPEC.md` alone. The non-normative implementation guides
(`IMPLEMENTATION-*.md`), the historical documents retained under `docs/history/`
for provenance, and any example, proposal, issue, discussion, or experimental
feature are **not** part of the Specification, and a document does not become
part of the Specification merely because it appears in this repository.

The conformance requirement documents (`CONFORMANCE-*.md`) and the machine-
readable vectors under `vectors/` state how the Specification's requirements are
tested. They are referenced by `PROTOCOL-CONFORMANCE.md` in determining whether
an implementation conforms; they do not add requirements to the Specification.

### 4.2 "Conforming Implementation"

"Conforming Implementation" means an implementation that satisfies the
definition of that term in [`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md)
for the applicable version of the Specification.

That document is the single, public, objective statement of what conformance
requires. In summary, and without limiting it: an implementation conforms when
it implements every REQUIRED provision of the conformance profile it claims,
enforces the governance rules in force for that profile, reproduces the pinned
digests for the constructions that profile exercises, states the profile and
Specification version it claims, and does not represent optional or
non-normative material as required.

The applicable version of that document is ratified in an Episode of Record and
identified there by content digest, so the definition this pledge grants against
is fixed in a sealed record rather than only in a published file. Which version
applies, and how it is identified, is stated in `PROTOCOL-CONFORMANCE.md` §7.

An implementation may be proprietary, closed-source, commercial, hosted,
embedded, or otherwise non-open-source and may nevertheless qualify as a
Conforming Implementation.

Conformance does not require use of the reference implementation, and no
determination, certification, approval, or other act of Scorched Earth Labs is a
condition of an implementation being a Conforming Implementation.

### 4.3 "Licensed Patents"

"Licensed Patents" means patent applications and patents owned or controlled by
Scorched Earth Labs, LLC, including patents issuing from applications claiming
priority to the patent applications referenced in this document, to the extent
that such patents contain one or more Necessary Claims.

### 4.4 "Necessary Claim"

"Necessary Claim" means a claim of a Licensed Patent that necessarily would be
infringed by an implementation of a mandatory requirement of the applicable
Specification, where there is no technically feasible manner to satisfy that
mandatory requirement while avoiding infringement of that claim.

A claim is not a Necessary Claim merely because:

1. it covers the general subject matter of artificial intelligence,
   cryptographic systems, data persistence, databases, distributed systems,
   software agents, or related technology;
2. it covers an optional feature;
3. it covers a particular commercial product or service;
4. it covers an implementation technique that is not required by the
   Specification; or
5. the same result can be achieved by implementing the Specification without
   practicing the claimed subject matter.

This definition is intended to distinguish technology required to conform to the
Specification from optional implementations, improvements, applications, and
technologies outside the Specification.

## 5. Scope of the Patent Pledge

The patent license granted under this document applies only to Necessary Claims
and only to the extent that the claim is practiced by a Conforming
Implementation of the applicable Specification.

The patent pledge does not grant a license to:

1. patents that are not Licensed Patents;
2. patent claims that are not Necessary Claims;
3. technology outside the applicable Specification;
4. optional features that are not required for conformance;
5. proprietary commercial services or products merely because they interact with
   a Conforming Implementation;
6. improvements that are not required for conformance;
7. independent inventions that are not required to implement the Specification;
   or
8. trademarks, copyrights, trade secrets, or other intellectual property rights.

## 6. Independent Implementations

The patent pledge is not limited to implementations derived from, copied from, or
linked to the reference implementation.

A party may implement the Specification independently, using different source
code, programming languages, databases, storage technologies, cryptographic
libraries, hardware, or system architecture.

If the resulting implementation satisfies the applicable mandatory requirements
of the Specification, it may qualify as a Conforming Implementation and receive
the patent license described in this document.

## 7. Proprietary Implementations

Nothing in this patent policy requires an implementation to be open source.

A proprietary implementation may be a Conforming Implementation if it satisfies
the applicable mandatory requirements of the Specification.

Conversely, the mere use of a proprietary product or service that interacts with
the Protocol does not itself make that product or service a Conforming
Implementation.

## 8. Reference Implementation and Specification Are Distinct

The reference implementation is licensed under the Apache License, Version 2.0.

The Specification describes the technical requirements of the Protocol.

The patent pledge applies to Conforming Implementations of the Specification and
is not conditioned upon copying, modifying, distributing, or otherwise using the
reference implementation.

## 9. No General Patent License

Except for the express patent rights stated in this document and the patent
rights expressly granted by the Apache License, no patent license is granted by
implication, estoppel, exhaustion, or otherwise.

In particular, publication of the Specification does not constitute a grant of a
license to patents owned by third parties.

Each implementer remains responsible for evaluating its own use of the Protocol
and any additional technology incorporated into its product or service.

## 10. Patent Retaliation

The patent license granted under this document terminates with respect to a
party, upon written notice, if that party initiates patent litigation against
Scorched Earth Labs, LLC or an entity implementing the applicable Specification,
alleging that a Conforming Implementation infringes a patent.

This provision does not apply to:

1. defensive assertions made solely in response to a patent claim brought
   against the asserting party;
2. patent counterclaims or defenses reasonably necessary to defend against
   patent litigation initiated by another party; or
3. proceedings in which the asserting party does not seek a judgment,
   injunction, damages, or other relief based on patent infringement.

Termination under this section applies only to the patent rights granted under
this document and does not alter rights independently granted under the Apache
License or another written agreement.

## 11. Transfer

The patent license granted to a Conforming Implementation may be exercised by
successors and assigns of that implementation as part of the transfer of the
implementation or the business in which it is incorporated, provided that the
transferee remains subject to the terms of this patent policy.

No party receiving rights under this policy receives the right to sublicense
Scorched Earth Labs' patents independently of a Conforming Implementation.

## 12. No Warranty

The patent pledge is provided without warranty.

Scorched Earth Labs does not warrant that:

1. any patent application will issue as a patent;
2. any issued patent will contain claims corresponding to the technology
   described in the Specification;
3. any particular implementation will qualify as a Conforming Implementation;
4. the Protocol is free from third-party patent rights; or
5. use of the Protocol does not infringe patents or other rights owned by third
   parties.

## 13. Patent Application Notice

Certain technology described by the Protocol is the subject of patent
applications filed by or on behalf of Scorched Earth Labs, LLC.

Only patent rights actually identified as Licensed Patents and containing
Necessary Claims are subject to the patent pledge.

## 14. Relationship to Conformance Documentation

[`PROTOCOL-CONFORMANCE.md`](./PROTOCOL-CONFORMANCE.md) defines "Conforming
Implementation" for the purposes of §4.2 of this policy. Conformance is
determined with respect to a particular Specification Version and the
conformance requirements applicable to that Specification Version, as set forth
in `PROTOCOL-CONFORMANCE.md` and the corresponding normative Specification and
conformance documents.

For purposes of this patent pledge, the conformance requirements applicable to
an implementation are those in effect for the specific Specification Version
under which the implementation qualifies as a Conforming Implementation. A later
revision of `PROTOCOL-CONFORMANCE.md`, the Specification, or another normative
conformance document does not retroactively change whether an implementation
qualified as a Conforming Implementation under an earlier Specification Version.

`PROTOCOL-CONFORMANCE.md` and the corresponding normative conformance documents
are governed by [`VERSIONING.md`](./VERSIONING.md) and are ratified in an Episode
of Record in the same manner as other normative protocol changes. Scorched Earth
Labs may modify, clarify, supplement, or replace technical conformance
requirements through publication of a new Specification Version, but any such
change applies prospectively to implementations claiming conformance to the new
or revised Specification Version.

A patent license previously granted under this policy with respect to a
Conforming Implementation shall not be retroactively terminated, diminished, or
otherwise altered by a later change to `PROTOCOL-CONFORMANCE.md`, the
Specification, or another normative conformance document, except as expressly
provided by the terms of the patent pledge applicable to that previously granted
license.

A later Specification Version does not, by itself, expand the scope of a patent
license previously granted with respect to an earlier Specification Version. An
implementation claiming conformance to a later Specification Version is subject
to the patent rights, if any, applicable to that later Specification Version
under this policy.

## 15. Changes to This Policy

Scorched Earth Labs may publish additional patent rights under this policy and
may identify additional Specification versions covered by the pledge.

No amendment to this policy shall retroactively withdraw a patent license
already granted to a Conforming Implementation under an earlier version of the
Specification, except to the extent expressly permitted by the terms of the
applicable patent pledge.

## 16. Questions

Questions concerning patent coverage or conformance should be directed to:

Scorched Earth Labs, LLC
info@scorchedearthlabs.com
https://scorchedearthlabs.com
