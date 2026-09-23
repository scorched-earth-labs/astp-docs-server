# ASTP — Context Commitment Implementation Guide

**Version:** 1.0.0
**Status:** Stable for the reference package; the reference deployment's adoption is recorded in §7 and is not complete
**Authors:** Scorched Earth Labs
**Date:** 2026-09-22
**Applies To:** [`SPEC.md`](./SPEC.md) 6.0.0 — §4.8 ContextEntryNode, §4.9 Erasure, §5.7 Episode Root version 3, §5.7.3 Context Manifest, §5.8 `spine_algorithm_version` 3, §9.2–§9.3, §11, §12.4.1 `CONTEXT_COMMIT`, G-41 … G-43
**Companions:** [CONFORMANCE-CONTEXT.md](CONFORMANCE-CONTEXT.md) (CM-001 … CM-010), [`vectors/6.0.0/`](./vectors/6.0.0/), [IMPLEMENTATION-PHASE3.md](IMPLEMENTATION-PHASE3.md)

---

## 1. What this guide is for

6.0.0 lets a sealed Episode prove what its agents were *given*. This guide says what an implementer builds to make that true: which stored node to write, when, from where; what the store contract requires; how the seal reads it; how erasure is performed so that the seal survives it; and what the reference package provides for each step. It describes the reference package as it is (`astp` 2.1.0) and names, in §7, what the reference deployment has and has not yet done. Nothing here is normative; the normative text is `SPEC.md`.

The one sentence to carry: **the seal proves history, not retention.** The store holds hashes and pointers. Content lives behind the pointers, in a content plane the protocol never hashes, and can be destroyed without moving a sealed value.

## 2. The reference package surface

| Need | Where |
|---|---|
| The constructions — entry hash, content commitments, manifest, root version 3, tombstone; the node models | `astp.core.context_v1` |
| Sealing under version 3 from stored fields | `astp.core.context_v1.compute_episode_seal_v3` |
| Reproducing a version 3 root | `astp.core.seal_v2.reproduce_episode_root(spine_algorithm_version=3, capture_posture=…, context_entry_hashes=…)` |
| The store contract | `astp.adapters.base.StructuralStore` — `write_context_entry`, `context_entry`, `context_entries_of`, `set_capture_posture`, `capture_posture`, `tombstone_context_entry` |
| The reference store | `astp.adapters.memory.InMemoryStore` |
| The operations, with the governance rules applied where the write happens | `astp.core.context_operations` — `commit_context_entry`, `set_capture_posture`, `erase_context_entry`, `context_seal_inputs`, `episode_context_manifest_hash` |
| Inclusion proofs over the manifest | `astp.core.context_v1.generate_context_inclusion_proof_v1` / `verify_context_inclusion_proof_v1` |
| Proof of record with the sixth field | `astp.core.proof_of_record` (`spine_algorithm_version` 3 documents carry `context_manifest_hash`, `capture_posture`, `context_entry_count` and, in the full profile, the stored entries) |

## 3. Writing a context entry

An entry is written when content enters the context window of an agent whose reasoning is recorded as Segments in the Episode — not when a retriever returns, not when a file is attached, but when the content is *provided* (§2). One entry per provision to one agent. The write is `CONTEXT_COMMIT` (§12.4.1), Tier 1.

```python
from astp.core.context_v1 import ContextEntryNode, compute_context_content_hash_v1
from astp.core.context_operations import commit_context_entry

content_hash = compute_context_content_hash_v1(provided_bytes)            # plain
# or, for low-entropy personal data (G-42):
# salt = os.urandom(32); content_hash = compute_context_content_hash_v1(provided_bytes, salt)

entry = ContextEntryNode(
    entry_id=uuid4(), episode_id=episode_id, entry_type="retrieval",
    provided_to=agent_id, provided_at=now_utc,
    provided_before_sequence_index=None,                # set at seal or on the next Segment write — §4.8.2
    capture_state="captured", content_hash=content_hash, salted=False,
    verifiability_at_seal="verifiable",                 # a retained copy exists at content_ref
    media_type="text/markdown", source_version_hash=source_snapshot_hash,
    source_ref=f"kn:{node_id}", content_ref=blob_locator,
)
result = commit_context_entry(store, entry)             # writes, ledgers CONTEXT_COMMIT, returns entry_hash
```

What the operation enforces: the Episode exists and still admits provisions; the entry is new; a captured entry has a content hash and a verifiability state, a declared-incomplete entry has neither; `resolves` names a declared-incomplete entry of the same Episode; and **G-42** — an entry the implementation classified `low_entropy_personal` (`pii_classification`) and committed plain is refused before anything is written.

**Hash the bytes as provided** (§4.8.3): what entered context after chunking, extraction or formatting — not the source artifact. For an attachment that is the provided form of the `AttachmentNode`'s bytes; `source_ref` carries the `attachment_id`.

**When capture fails**, write the entry anyway with `capture_state="declared_incomplete"` and whatever provenance you hold (§4.8.5). A silent hole is not permitted; a declared one is a manifest member. If the content is recovered later, write a *new* entry with `resolves=<the incomplete entry's id>`; never mutate the old one.

**The spine position** (`provided_before_sequence_index`, §4.8.2) is the `sequence_index` of the first non-ephemeral Segment the recipient wrote after `provided_at`, or NULL if none had been written at seal. A deployment either sets it when that Segment is written or fills it at seal from stored Segments; it is in the entry preimage, so it must be fixed before the entry is hashed for the seal.

## 4. Posture and the seal

Before sealing under version 3 the Episode declares what it undertook to capture (§5.7.3, G-41):

```python
from astp.core.context_operations import set_capture_posture, context_seal_inputs
from astp.core.context_v1 import compute_episode_seal_v3

set_capture_posture(store, episode_id, "declared_only")       # or "all_external" / "none"
posture, entries = context_seal_inputs(store, episode_id)      # G-41: posture present, every entry captured or declared_incomplete
seal = compute_episode_seal_v3(episode_id, segment_seal_inputs, capture_posture=posture, context_entries=entries,
                               signal_content_hashes=…, excluded_content_hashes=…, structural_member_hashes=…)
```

`seal` carries the five version 2 roots unchanged plus `context_manifest_hash`, `episode_root_hash` under `EPISODE_ROOT:v3:`, and the identifiers (`spine_algorithm_version` 3, `ordering_version` 2, `hash_version` 2). Stamp the crystallization record from the seal result, never from a module constant.

**Choosing the posture.** `all_external` claims every provision has an entry, so absence means nothing was provided — claim it only once every seam writes entries. `declared_only` is honest while seams are partial. `none` is for an Episode that committed no context at all; it still seals under version 3 with an empty manifest (CM-001).

**What a version 2 seal of the same Episode does:** reproduces exactly as before (CM-010). Adopting version 3 is a cutover at the crystallize handler, not a migration.

## 5. Erasure

The content plane is the deployment's. The sequence of §4.9.2 is:

1. Destroy the content at `content_ref`.
2. Destroy the salt at `salt_ref` — **atomically with 1**. A salt that survives its content, or the reverse, is an erasure that did not happen. Keep salts in a namespace separate from content (§4.8.3) and delete the pair in one transaction.
3. Record it:

```python
from astp.core.context_operations import erase_context_entry

r = erase_context_entry(store, entry_id, erasure_authority="GDPR-Art17", erasure_request_id=request_id,
                        erased_by=principal, content_and_salt_destroyed=True)
```

The operation builds the `ErasureTombstone` over the entry's unchanged hash, stores it as a `CodicilNode` (`CODICIL_APPEND`), nulls `content_ref` and `salt_ref`, sets `erasure_state="tombstoned"`, and touches nothing else. `content_and_salt_destroyed` is the caller's assertion that steps 1–2 happened; the store cannot do them and refuses to record an erasure nobody claims to have done. After it, the Episode root verifies identically (CM-006), and a verifier reports the entry as erased and witnessed, never as a failure (G-43).

A plain-hashed entry's `content_hash` remains exactly as reversible as it always was after erasure. That is why G-42 exists, and why the classification at write time (§4.9.1) is the implementation's residual risk to own.

## 6. Verifying and exporting

- `astp.core.seal_v2.reproduce_episode_root(spine_algorithm_version=3, …)` rebuilds a version 3 root from the spine root, the component hash lists, the posture and the entry hashes — nothing else (§9.3).
- `generate_context_inclusion_proof_v1(entry_hashes, entry_hash)` proves one entry without the others; `verify_context_inclusion_proof_v1(proof, posture, count, context_manifest_hash)` reproduces the manifest hash from it (§9.2, CM-004).
- `build_proof_of_record(spine_algorithm_version=3, context_manifest_hash=…, capture_posture=…, context_entry_count=…, context_entries=store.context_entries_of(episode_id), …)` exports a document a third party verifies with `python -m astp.core.proof_of_record verify <file>`. The attested profile withholds the entry list and says so.

## 7. The reference deployment (Ignis OS) — status

| Seam / step | Status (2026-09-22) |
|---|---|
| **Attachment injection** — a document's text placed in an agent's prompt | **Writing entries.** `ignis.ariadne.context_provision` records one `attachment` entry per provided form per agent (elective under `declared_only`: the same form re-injected on later turns is not committed again); hashed over the text as provided; `verifiable` with `content_ref` naming the document node when the whole document was provided, `attested` when it was cut to the prompt budget — the cut is now visible in the record. Stored as `(:AstpContextEntry)` off the Episode, `PROVIDED_FROM` the document; `CONTEXT_COMMIT` ledgered. `Neo4jStructuralStore` implements the six contract methods; new Episodes carry `capture_posture = declared_only`. |
| **Retrieval** | **Writing entries** for two paths. Segments read through the Ariadne retrieval tools: one `retrieval` entry per Segment placed in the result, over its `content_text` verbatim, `source_ref` `segment:<id>`, `source_version_hash` the stored `content_hash`, verifiable — in the Episode the reader is reasoning in, which the snapshot control captured for the turn; the §11.1 audit is unchanged beside it. Knowledge nodes recalled into the grounding block: one entry per node over its rendering, `source_ref` `knowledge:<node_id>`, `source_version_hash` the node's `content_hash`, attested. Clotho's corpus-chunk tool: one entry per chunk, the commit in `source_ref`, attested. Chat-memory recall does not run inside Episodes and provides nothing there. |
| **Tool results (generic)** | **Writing entries.** The tool execution node records every successful tool result that entered the agent's context: `external` for a capability (MCP-backed) read, `retrieval` for an in-process read; a write's acknowledgement is not content and is not recorded; tools that record their own provisions are skipped. `source_ref` is the tool and its arguments; attested. |
| **Web fetch** | **Writing entries.** `fetch_webpage_tool` records each successful fetch as an `external` entry: the extracted text as it entered context, `source_ref` the URI with status, fetch time, ETag and Last-Modified, `source_version_hash` NULL, attested — in the Episode the agent is reasoning in. |
| **Layer 3 `tool_output`** | **Writing entries.** The Ignis MCP's `ignis_record_skill_invocation` records, after the invocation commits, its `output_result` as stored as a `tool_output` entry of the step's Episode, provided to `invoked_by`; `source_ref` the invocation, `source_version_hash` its `content_hash` (the §21 relation), verifiable. |
| Spine position (§4.8.2) | Filled at seal time, before the read, from the recipient's first later Segment (`backfill_provided_before_positions`); the seal-input reader (`fetch_seal_inputs_v2`) returns the posture and the entries, hashes them, and says whether a version 3 seal is possible (`sealable_under_v3`). |
| **Sealing under version 3** | **Live (2026-09-23).** The crystallize handler fills entry positions (§4.8.2), reads posture and entries through the same reader the verifier uses, and seals under version 3 when the reader says it can — otherwise version 2, with the refusals logged. The verifier reproduces version 3 seals (`seal_v3`); the exporter carries the sixth field. Unsealed Episodes that predate the seam were given `declared_only`. First sealed context manifest: Episode `29c9ec3b-f020-49e4-830c-991bdf2d0217`, one attachment entry, proof reproduced by the package alone. |
| **Salt namespace, erasure** | **Live.** A conservative deterministic classifier marks low-entropy personal data at write time; such content commits salted, the salt on its own node (`AstpContextSalt`, own constraint, reachable only by `salt_ref`), and is declared incomplete rather than committed plain when no namespace is at hand. `erase_context_entry_content` destroys the retained copy and the salt in one transaction, then the protocol's operation appends the tombstone codicil; the root does not move (verified live). **Known limitation:** an entry whose retained copy is a Layer 3 `SkillInvocation` cannot be erased — Layer 3 nodes are immutable — and the deployment refuses rather than tombstone a copy that still exists; erasable content must not be committed as a plain `tool_output` entry. No HITL gate on the erasure endpoint yet. |

Every way the reference deployment provides content to an agent inside an Episode has a writing seam, and the erasure path is live. Remaining: `all_external` for new Episodes once the entry stream has been observed for a while; an approval gate on the erasure endpoint; a tighter classifier.
