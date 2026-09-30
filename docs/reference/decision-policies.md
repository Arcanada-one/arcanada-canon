# Decision policies: offline source-contract reference

Status: draft, `offline_shadow`; no admitted policy, running consumer or release.
Public baseCanon/private overlays are the operator-approved architecture as of
2026-09-29. Public readability does not imply source admission, private body
access or compiled-policy activation. See [adoption](../../governance/adoption/README.md).
`canon.source.yaml` remains publication-disabled with no active release.

## Ownership and planned work

KC2 owns semantic assertions, composition and `Resolve(G_s,T)`. Canon owns source,
scope and binding proposals. Existing workspace registry writers and Auth retain
membership and executable permission authority. Shared access-contract vocabulary
and its fail-closed authorization composition are separate from recommendations.

This Python experiment contributes bounded contract examples toward L01 schema
and L05 source-boundary work. It is not planned Rust `canon-source-git`, Canon L18
mandatory applicability, L19 ContextSnapshot or L24 action guard. It delegates to
one existing offline inheritance projection; it introduces no production resolver.
Mandatory string union is not clause applicability or KC closure. The exact
universe/space/project/role/agent prefix is a synthetic test profile, not adoption
of a new hierarchy. Project identity is never inferred from a repository name.
L01/L05/L18 completion, federation AC007 and real consumers remain NOT_MEASURED.

## Versioned source boundary

`DecisionSourceBundle/v1` in `schemas/decision-policy.v1.json` binds:

- a caller-held bundle digest, validity window and exact offline snapshot;
- every required source ID, revision, byte digest, authority and source class;
- exact scope and immediate parent pin, policy or provenance-source identity;
- explicit public/private classification and actor/tenant body-read decision;
- complete mandatory source and policy closure, with revocation inputs.

`engine.decisions.load.load_projection()` is the filesystem entrypoint. It checks
all required access decisions before opening any source body. Public files must be
under `canon/` in the caller-supplied public repository; private files under
`overlays/` in a separate caller-supplied private repository. These are synthetic
fixture roots, not allocation of an actual overlay repository. Overlapping roots,
unknown classes, candidate roots, traversal, symlinks (including root ancestors),
hardlinks and non-regular files refuse. Descriptor-relative `O_NOFOLLOW` traversal
prevents path/symlink check-then-read races; bounded bytes are hashed after reading.
Concurrent writes that change pinned bytes refuse. Root directories and external
pins must be trusted caller inputs. Same-user hostile processes, mount changes,
resource side channels and real tenant isolation are outside this offline model.

Every entry is required in v1. Absent or denied overlays refuse the affected
closure; there is no fallback to a base-only projection. Private reads require
exact actor AND tenant equality and explicit `allow`; unknown is denied. Access
records say `offline_fixture_not_grant`: they model decisions from a future Auth
adapter, not authentication or cryptographic admission. An untrusted caller that
chooses every pin, identity and grant can fabricate an internally consistent
fixture. Byte consistency proves neither authority nor registry truth.

After loading, `resolve()` checks exact source bytes/identities, registered scope
chain, parent digests, expiry/revocation and policy closure. Lower scopes may add
obligations/decisions but may not replace inherited decision semantics. Snapshot
revocation lists are inputs, not proof of live revocation completeness. The
lower-level dictionary API remains for pure unit tests; runtime consumers must
not treat it as a filesystem, disclosure or authorization gate.

## Evidence and actions

Evidence binds the exact request, state, scope, projection, candidate set and
provider/model revision. Required state types test structure, not truth. The
synthetic capability-tier example uses an uncalibrated 700000 ppm threshold.
No operational policies, real source inventories or private topology are added
by this slice. Scientific prose is not automatically a normative obligation.

| Primitive | Meaning | Validation |
| --- | --- | --- |
| `choice` | Mass over mutually exclusive options | Integer millionths; total 1000000; ties abstain |
| `independent_probability` | Possibly overlapping event estimates | Each integer 0..1000000; no sum constraint |
| `score` | Bounded ordinal utility, not correctness probability | Each integer 0..1000000; distinct semantics |

Floats, booleans as quantities, NaN, duplicate JSON keys, unknown options and
self-declared calibration are refused. `digest()` is this wire format's byte
identity helper, not KC2 canonicalization or a signature verifier.

`shadow.run_private_shadow()` freshly loads then evaluates. Deterministic `deny`
or `unknown` prevents recommendations even at maximum model confidence. Missing
context/evidence, abstention, ties and low scores retain baseline. Qualifying
observations only recommend. All traces say `offline_shadow`, `applied:false`,
`authorization_granted:false`. A caller-supplied `allow` never grants authority;
production needs a real, freshly bound authorized verdict.

## Disclosure

Internal projections, snapshots, bundle metadata and DecisionTrace/v1 are private:
request IDs, scope/lineage, labels, thresholds, model metadata and digests can
identify private material even when raw state is absent. Do not serialize them
into public logs, CI artifacts, issue comments or frontend responses.

`run_public_shadow()` discards both internal traces and stable refusals and returns
only `PublicDecisionBoundary/v1`, identical for success and refusal. It contains
no identifiers, names, counts, hashes, recommendations or outcome-dependent
fields. `public_receipt()` accepts no data to declassify. Its constant `withheld`
means no private outcome is disclosed, not successful execution. This is a local
serialization boundary, not a timing-safe network service. Private diagnostic
transport and selective declassification need separate owner review.

## Delivery gates

No Auth integration, provider/model call, Git fetch, task mutation, production
consumer or active-release publisher exists here. Existing provider-neutral
adapter and Arcanada/Talomnia/agent consumer tasks remain open work. Control owns
the next exact consumer slice. Per-class disclosure, independent prior-policy
review, exact PR-head CI and resulting-main evidence precede publication of new
content; runtime adds fidelity, signatures/revocation, actual tenant body reads,
action guards, federation, restore and rollback gates.

## Scope registry consistency

The offline `DecisionScopeBindings/v1` consumer validates every registered chain,
including those outside the selected policy path. A binding document describes
one universe and at most 1024 chains, each with one to five entries in the
existing experimental universe/space/project/role/agent order. Missing or repeated
rungs refuse; a valid selected chain cannot hide an invalid sibling chain.

Typed space and project IDs have one immediate parent across the document. A
project registered beneath two different spaces refuses with
`AMBIGUOUS_SCOPE_PARENT`, even if both chains and every source digest are pinned.
Distinct projects may share a space; prefixes may recur across chains. Identity
is exact and typed: equal text at different levels is not a collision. This
check does not normalize aliases or infer project identity from repository names.
The existing role/agent labels remain contextual test-profile labels; equal role
names in different projects do not establish shared ownership or a new canonical
scope rung. Galaxy and Module are not added.

`MULTIPLE_SCOPE_UNIVERSES` and `INVALID_REGISTERED_SCOPE_CHAIN` are private stable
refusal codes without IDs or source bodies. The actual filesystem loader invokes
this validation through the existing resolver before shadow evaluation. A
conflict never reaches probability evaluation; the public facade still emits the
same constant for success and refusal. No fallback selects whichever parent was
listed first, and no valid selected prefix sanitizes a contradictory registry.

These checks establish internal consistency of caller-pinned offline inputs,
not registration truth, issuer authority, owner assignment, KC2 semantics or
Canon L18 completion. Production hierarchy mapping and admission remain separate
work. Existing snapshot/source/parent/revocation checks and mandatory obligations
continue to apply. To roll back, revert this source correction; do not silently
rewrite registry history or repin a conflicting live source.
