# Disposition proposal: two historical Canon manifest mismatches

Prepared 2026-09-29; remeasured on merged `main` 2026-09-30. **Recommendation for review; not an
adopted exception, replacement manifest or runtime admission.** This change adds
only this document. It changes neither imported bytes nor historical evidence.

## Decision requested

Preserve `governance/adoption/source-manifest.json` as the byte manifest of the
original bootstrap import. Preserve the present `INDEX.md` and
`OPEN-QUESTIONS.md` without editing them. Record their later annotations as
**derived historical metadata with explicit original-to-current lineage**, in
an additive successor disposition reviewed by the source owner. Do not make the
original manifest's current-tree comparison pass by substituting hashes,
ignoring these paths or treating semantic usefulness as byte equality.

This document supplies the diagnosis, exact identities and proposed treatment.
It does not implement a new verifier, register an exception or allocate an AUP
DEC number.

## Evidence and limits

The comparison uses Git objects in a complete clone; PR author/merger/review
counts come from the GitHub API:

| Evidence | Exact revision / meaning |
| --- | --- |
| Original workspace source | `bb8b9a6bbc2443605bdc6bca47a28c97134a73f7`, `documentation/source-specifications/canon-arcana/` |
| Original Canon bootstrap | `22c97439a66fd01d3e23e878bf5b4cdb2cd7ea1e`, commit timestamp 2026-09-09T22:31:02Z |
| Previously reviewed Canon base | `b879f0cb40828055e4034d820da37075283f2bc7` |
| Merged Canon head remeasured for this change | `4e2e55a` (Canon #8, the offline public-base / private-overlay boundary) |
| Related decision | DEC-AUP-0063 (AUP #226, merged at `ebe1c76`); workspace #1353 at `a6e0fa2` |

This document was drafted against a local pre-merge head and then remeasured
against merged `main` at `4e2e55a` in a complete clone: the two files, their blobs
and the manifest are unchanged, and the same two entries fail.

The manifest contains 39 entries. All 39 hashes reproduce at the bootstrap
commit; 37 reproduce at merged `main` `4e2e55a`. Exactly the two entries below
fail its current-tree comparison. Both current files already have identical
bytes at `b879f0c`; they were not changed by Canon #7 or #8.

The manifest itself is byte-identical at bootstrap and at `4e2e55a` (last changed
by the bootstrap commit):
SHA-256 `79a015f0b6ff770e1228900ce0277bb89f1813db732b7d7111659896fd2833e7`.
The historical bootstrap receipt and disabled runtime manifest are preserved.
This finding is separate from the twelve charter-evidence mismatches, the original
ZIP checksum question and the unavailable submitted version-diff artifact.

### Exact file identities

Paths below are relative to `docs/specifications/canon-arcana/` in Canon. The
original workspace counterparts live under the source prefix in the table above.
SHA-256 values cover raw bytes, with no newline or encoding normalization.

| File | Version | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `INDEX.md` | Original workspace = bootstrap = manifest expectation | 5642 | `623dab65ac7385e54f4fd41d8954925d6dca86d6ef1bc8e12478467f30196e03` |
| `INDEX.md` | Present at `b879f0c` and `4e2e55a` | 6922 | `0441bf577ffdfe4969317d8c3eee86ea20d522403bf1b222b6e50207b48ae093` |
| `OPEN-QUESTIONS.md` | Original workspace = bootstrap = manifest expectation | 8395 | `ff217c17c357892488944b7beef5b250bd2b8c7d0bdb40f2a20c3ad6a622171d` |
| `OPEN-QUESTIONS.md` | Present at `b879f0c` and `4e2e55a` | 11069 | `399e932632310fafcf2c85b72b75a3fb8b342d0c5b9f6ef88e4bf5ab84762fd6` |

Git blob identities provide a second, independently addressable link:

| File | Bootstrap blob | Present blob |
| --- | --- | --- |
| `INDEX.md` | `6a5fb3cca2393a6ab4807f8ee3970012c6307cae` | `7f3e016b8f34ea9583e4f0dec9a6e772669c230d` |
| `OPEN-QUESTIONS.md` | `ff7bcc6d3b6ecdff929be093f72add55874d9bec` | `e4aa07fb53a7f8a0ee490ed85b15204ab119dc8d` |

## Cause

**Measured byte-level cause:** later editorial annotations changed the two
metadata files while the original import manifest retained the original hashes.
The original hashes are reproducible; this is neither unexplained hash corruption
nor a line-ending-only discrepancy. Both original and later bytes are available.

- `INDEX.md`: eleven lines were inserted after the missing version-diff note.
  The insertion is labelled 2026-09-14 and describes reconstructing a comparison
  of specification versions, the new `05-RECONSTRUCTED-v0.2-to-v0.3.diff` file,
  and the continuing lack of the author's original diff checksum evidence.
- `OPEN-QUESTIONS.md`: the original entries 8, 9 and 10 were replaced by five
  lines of updated discussion. These cover the existing charter-migration
  mandate and remaining implementation, a dated Muneral index-access observation,
  and the reconstructed version-diff. Other questions are unchanged.

The referenced reconstructed diff is on Canon `main`: 115741 bytes, 2639 lines,
SHA-256 `71e2cd914480662ffcc1622d284c0bcc4ca976e5eef2ecc9c007ec74df0f1886`.
It is a separate derived artifact, not proof of the missing author's original
file, its creation procedure or its checksum. It is not one of the 39 entries.
The historical API/rights/count assertions in the annotations are not fresh
Muneral observations or present-day grants. This review does not renew them.

**Process-level diagnosis (inference from those facts):** mutable follow-up
commentary was written into paths still treated as immutable import members,
without an accompanying lineage/disposition layer. Keeping the original manifest
was correct for historical provenance; continuing to describe the current versions
as byte-exact originals is incorrect. The dated annotations explain their content
purpose, but do not themselves establish authorization for editing imported paths.

**Measured on complete history (2026-09-30):** the edits entered through three
merged Canon PRs, all on 2026-09-14 — #4 (`c45411d`) and #5 (`c84b9e9`) changed
`OPEN-QUESTIONS.md`; #6 (`983fc3b`) changed both files and added the reconstructed
diff. Each PR was authored and merged by the `Arcanada` service account with zero
recorded reviews. No later commit touches either file.

**Still not measured:** an authorization or admission record for editing these
imported paths. The zero-review merges show that none was recorded on the PRs;
they do not show that the edits were unauthorized. No credential incident is
inferred.

## Options

| Option | Effect | Assessment |
| --- | --- | --- |
| Replace the two hashes in the historical manifest | Current-tree comparison becomes green | Reject: rewrites the identity of the original import and conceals the divergence |
| Restore the two current files to bootstrap bytes | Original comparison passes; later context disappears from current paths | Do not execute: violates this task's no-byte-change boundary and is unnecessary while both versions remain addressable |
| Add a wildcard exclusion or ignore these two mismatches | Suppresses the failing check | Reject: converts missing provenance into an implicit integrity waiver |
| Preserve both versions and add narrowly pinned successor lineage | Keeps raw mismatch visible; distinguishes original import from later commentary | **Recommend**, conditional on source-owner review and exact-head remeasurement |
| Leave the mismatch wholly unexplained until full history is recovered | Retains a safe hold | Fallback if the proposed classification or exact identities cannot be independently confirmed |

## Recommended treatment and evidence gates

1. Accept the narrow diagnosis as an explained historical metadata divergence,
   not a new declaration that the import is intact. The original source and
   bootstrap hash checks are `verified`; comparison of the two current paths to
   the original manifest remains `failed`. Preservation of current bytes relative
   to the inspected base is separately `verified`.
2. Attribution is measured (Canon #4, #5, #6 above); authorization remains
   `not_measured`. That gap does not block publishing this qualified diagnosis;
   it does block claiming that the edits were authorized or retroactively admitted.
3. If independently approved, publish an additive successor lineage record under
   governance/adoption, with a newly allocated identity and explicit scope of only
   these two files. Bind original repository/commit/path/blob/SHA-256, original
   manifest digest, observed Canon commit/path/blob/SHA-256, the exact delta, event
   attribution or its `not_measured` status, reviewer identity, disposition and
   these reversal conditions. This is proposed follow-up, not created by this PR.
4. Classify the present versions as non-runtime derived historical commentary.
   Do not promote their dated operational observations into current facts,
   normative policy, source admission or access grants. Future annotations belong
   in new derived documents, preserving existing imported paths and manifests.
5. A future verifier may report separately: original-import evidence, current-tree
   equality, successor-lineage validity, and admission. It must not relabel a failed
   original comparison as pass. Any acceptance of a derived successor requires
   explicit prior-policy authority and independently reviewed exact identities;
   a new file listing hashes cannot self-authorize the exception. Existing checks
   that require literal equality remain failing until their owners approve a
   separately scoped change; this document does not weaken them.
6. On this PR: only `MANIFEST-DISPOSITION.md` changes; all 39 entries and the
   manifest were rehashed at `4e2e55a` with the two-file failed result preserved.
   PR-head and resulting-main checks are recorded separately. DEC-AUP-0063's preservation rule and all existing authority,
   independent-review, federation and runtime gates remain in force.

## reverse_if

Withdraw or narrow only the successor classification/pointer in an additive
corrective decision; keep original files, manifest, annotations and evidence.
Reopen the affected source-integrity hold if any of the following occurs:

- Recovered history contradicts the proposed editorial explanation or shows
  different source identities. Record the exact conflict rather than picking a
  preferred version; attribution remains held until resolved.
- A recorded SHA-256, Git blob, source revision or manifest digest does not
  reproduce, either of the two files changes again, or any additional entry fails.
  Do not widen the two-path disposition automatically.
- Review finds a substantive rule/authority change, sensitive disclosure or other
  content beyond the stated non-runtime historical annotations. Route it to a
  separately bounded semantic, disclosure or incident disposition; do not infer
  that a clean secret scan clears its content.
- A consumer treats the current annotations as immutable originals, fresh grants
  or active policy; a verifier skips the mismatch; or this record is used as a
  blanket exception. Withdraw that use and require explicit consumer correction.
- A successor record is promoted without the required independent review or is
  used to claim the missing original ZIP/diff was verified, all charter-evidence
  mismatches were closed, or Canon was runtime-admitted.

Reversal never means deleting source history, silently restoring bytes, replacing
historical hashes, changing repository visibility, or touching runtime/adapters.

## Reproduction

Use a complete or object-sufficient local Canon clone and a workspace clone that
contains the original source commit. Read Git blobs, not the mutable working tree:

```bash
# In the Canon clone, for each of INDEX.md and OPEN-QUESTIONS.md:
git show 22c97439a66fd01d3e23e878bf5b4cdb2cd7ea1e:docs/specifications/canon-arcana/INDEX.md | sha256sum
git show 4e2e55a:docs/specifications/canon-arcana/INDEX.md | sha256sum
git show 4e2e55a:governance/adoption/source-manifest.json | sha256sum
# In the workspace clone:
git show bb8b9a6bbc2443605bdc6bca47a28c97134a73f7:documentation/source-specifications/canon-arcana/INDEX.md | sha256sum
```

All 39 comparisons reproduce with a loop over `files[]` in the manifest at
`4e2e55a`. No model calls, Auth grants, Muneral writes, code changes or
source-byte repairs were performed by this change.
