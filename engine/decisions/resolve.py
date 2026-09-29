"""Exact offline projection. Snapshot pins are inputs, never self-admission."""

from copy import deepcopy

from .model import byte_digest, digest, load_json, require, validate

LEVELS = ("universe", "space", "project", "role", "agent")


def check_snapshot(snapshot, expected_digest, now):
    validate("snapshot", snapshot)
    require(type(now) is int and now >= 0, "INVALID_CLOCK")
    require(digest(snapshot) == expected_digest, "SNAPSHOT_PIN_MISMATCH")
    require(snapshot["valid_from"] <= now < snapshot["expires_at"], "STALE_SNAPSHOT")
    require(set(snapshot["source_digests"]) == {s["digest"] for s in snapshot["sources"]},
            "SOURCE_MANIFEST_MISMATCH")
    identities = [(s["repository"], s["revision"], s["path"]) for s in snapshot["sources"]]
    require(len(identities) == len(set(identities)), "CONFLICTING_SOURCE_IDENTITY")
    pins = set(snapshot["source_digests"]) | {p["digest"] for p in snapshot["policies"]}
    require(not pins & set(snapshot["revoked_digests"]), "REVOKED_PIN")


def resolve(policies, snapshot, *, expected_snapshot_digest, target_scope,
            sources, now):
    """Build a shadow projection from an externally pinned scope snapshot.

    `snapshot` is an offline fixture, NOT authenticated admission evidence.
    No output grants authority or permits production publication. A future
    authenticated adapter must establish membership, source admission and
    revocation completeness before this function can have a runtime caller.
    """
    check_snapshot(snapshot, expected_snapshot_digest, now)
    chain = snapshot["policies"]
    require(1 <= len(chain) <= len(LEVELS), "INVALID_CHAIN")
    scopes = [ref["scope"] for ref in chain]
    require([s["level"] for s in scopes] == list(LEVELS[:len(chain)]),
            "INVALID_SCOPE_CHAIN")
    require(scopes[-1] == target_scope, "WRONG_SCOPE")
    ids = [ref["id"] for ref in chain]
    require(len(ids) == len(set(ids)), "DUPLICATE_POLICY")
    require(set(policies) == set(ids), "POLICY_SET_MISMATCH")
    require(snapshot["registry_pin"]["digest"] in snapshot["source_digests"],
            "REGISTRY_PIN_MISSING")
    require(snapshot["registry_pin"]["digest"] in sources, "REGISTRY_SOURCE_MISSING")
    # Verify every pinned source, including the registry, not only sources
    # that happened to be referenced by a selected decision.
    for pin in snapshot["source_digests"]:
        require(pin in sources and type(sources[pin]) is bytes
                and byte_digest(sources[pin]) == pin, "SOURCE_DIGEST_MISMATCH")
    require(snapshot["registry_pin"]["kind"] == "registry", "REGISTRY_KIND_MISMATCH")
    require(snapshot["registry_pin"] in snapshot["sources"], "SOURCE_IDENTITY_MISMATCH")
    bindings = load_json(sources[snapshot["registry_pin"]["digest"]])
    validate("bindings", bindings)
    require(scopes in bindings["scope_chains"], "UNREGISTERED_SCOPE_CHAIN")
    require(all(s in snapshot["sources"] for s in bindings["sources"]),
            "REGISTRY_PROVENANCE_MISSING")
    mandatory, decisions, lineage = set(), {}, []
    previous = None
    for ref in chain:
        policy = policies[ref["id"]]
        validate("policy", policy)
        require(policy["id"] == ref["id"] and digest(policy) == ref["digest"],
                "POLICY_PIN_MISMATCH")
        require(ref["digest"] not in snapshot["revoked_digests"], "REVOKED_POLICY")
        require(policy["scope"] == ref["scope"], "WRONG_SCOPE")
        require(policy["parent"] == previous, "PARENT_PIN_MISMATCH")
        for source in policy["sources"]:
            require(source in snapshot["sources"], "SOURCE_IDENTITY_MISMATCH")
            require(source["digest"] in snapshot["source_digests"], "SOURCE_NOT_PINNED")
            require(source["digest"] not in snapshot["revoked_digests"], "REVOKED_SOURCE")
        mandatory.update(policy["mandatory"])
        names = [d["id"] for d in policy["decisions"]]
        require(len(names) == len(set(names)), "DUPLICATE_DECISION")
        for decision in policy["decisions"]:
            name = decision["id"]
            require(set(decision["required_inputs"]) == set(decision["input_types"]),
                    "INPUT_CONTRACT_MISMATCH")
            require(set(decision["source_digests"]) <= {s["digest"] for s in policy["sources"]},
                    "DECISION_SOURCE_IDENTITY_MISSING")
            require(all(pin in snapshot["source_digests"] for pin in decision["source_digests"]),
                    "SOURCE_NOT_PINNED")
            require(not set(decision["source_digests"]) & set(snapshot["revoked_digests"]),
                    "REVOKED_SOURCE")
            require(len(decision["options"]) >= (2 if decision["primitive"] == "choice" else 1),
                    "INSUFFICIENT_OPTIONS")
            if name in decisions:
                # v1 deliberately refuses ALL semantic overrides. Scope
                # refinements may add decisions/obligations, never replace them.
                require(decision == decisions[name], "INHERITED_DECISION_CONFLICT")
            decisions[name] = deepcopy(decision)
        lineage.append(deepcopy(ref))
        previous = {"id": ref["id"], "digest": ref["digest"]}
    require(not set(snapshot["source_digests"]) & set(snapshot["revoked_digests"]),
            "REVOKED_SOURCE")
    require(bool(decisions), "EMPTY_DECISION_SET")
    projection = {
        "schema": "ResolvedDecisionPolicy/v1", "mode": "offline_shadow",
        "publication_enabled": False, "snapshot_digest": expected_snapshot_digest,
        "registry_pin": deepcopy(snapshot["registry_pin"]),
        "scope": deepcopy(target_scope), "lineage": lineage,
        "mandatory": sorted(mandatory),
        "decisions": [decisions[key] for key in sorted(decisions)],
    }
    return {"projection": projection, "digest": digest(projection)}
