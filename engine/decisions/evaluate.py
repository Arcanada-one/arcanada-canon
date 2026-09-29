"""Provider-neutral observations to shadow advice; no tools or model calls."""

from copy import deepcopy

from .model import digest, require, validate
from .resolve import check_snapshot
PPM = 1_000_000


def adequate(kind, value):
    if kind == "text":
        return type(value) is str and 0 < len(value.strip()) <= 18000
    if kind == "risk_class":
        return value in ("low", "medium", "high", "critical")
    if kind == "identifier_list":
        return (type(value) is list and 0 < len(value) <= 100
                and all(type(v) is str and 0 < len(v) <= 200 for v in value)
                and len(value) == len(set(value)))
    return False


def evaluate(resolved, request, evidence, *, expected_projection_digest,
             deterministic_verdict, snapshot, expected_snapshot_digest, now):
    """The caller must freshly resolve the snapshot before every evaluation.

    The externally held projection digest prevents a provider response or a
    mutated local projection from replacing policy. It is content identity,
    not a signature or an ACL grant. Output is permanently shadow-only.
    """
    validate("request", request)
    check_snapshot(snapshot, expected_snapshot_digest, now)
    validate("projection", resolved["projection"])
    projection = resolved["projection"]
    require(projection["snapshot_digest"] == expected_snapshot_digest,
            "STALE_PROJECTION")
    require(projection["lineage"] == snapshot["policies"], "PROJECTION_LINEAGE_MISMATCH")
    require(resolved["digest"] == expected_projection_digest == digest(projection),
            "PROJECTION_PIN_MISMATCH")
    require(request["projection_digest"] == expected_projection_digest,
            "REQUEST_POLICY_MISMATCH")
    require(request["scope"] == projection["scope"], "WRONG_SCOPE")
    require(digest(request["state"]) == request["state_digest"], "STATE_PIN_MISMATCH")
    found = [d for d in projection["decisions"] if d["id"] == request["decision_type"]]
    require(len(found) == 1, "DECISION_MISSING_OR_AMBIGUOUS")
    decision = found[0]
    require(set(request["candidates"]) == set(decision["options"]), "CANDIDATE_SET_MISMATCH")
    require(request["baseline"] in request["candidates"], "INVALID_BASELINE")
    require(deterministic_verdict in ("allow", "deny", "unknown"), "INVALID_AUTH_VERDICT")
    receipt = {
        "schema": "DecisionTrace/v1", "mode": "offline_shadow", "applied": False,
        "authorization_granted": False, "decision_type": decision["id"],
        "request_id": request["id"], "request_digest": digest(request),
        "projection_digest": expected_projection_digest,
        "snapshot_digest": projection["snapshot_digest"],
        "state_digest": request["state_digest"],
        "candidate_digest": digest(request["candidates"]),
        "scope": deepcopy(request["scope"]), "lineage": deepcopy(projection["lineage"]),
        "mandatory": deepcopy(projection["mandatory"]), "baseline": request["baseline"],
        "threshold_ppm": decision["threshold_ppm"],
        "threshold_basis": decision["threshold_basis"],
        "evidence_digest": None, "provider": None, "model": None,
        "model_version": None, "observations": None,
        "calibration": "not_measured", "recommended": [],
        "policy_action": "retain_baseline", "reason": "unknown",
    }
    if deterministic_verdict != "allow":
        receipt.update(policy_action="deny", reason="DETERMINISTIC_" + deterministic_verdict.upper())
        return receipt
    missing = [k for k in decision["required_inputs"]
               if not adequate(decision["input_types"][k], request["state"].get(k))]
    if missing:
        receipt["reason"] = "INSUFFICIENT_STATE"
        return receipt
    if evidence is None:
        receipt["reason"] = "PROVIDER_UNAVAILABLE"
        return receipt
    validate("evidence", evidence)
    require(evidence["request_digest"] == digest(request), "EVIDENCE_REQUEST_MISMATCH")
    require(evidence["primitive"] == decision["primitive"], "SCORE_SEMANTICS_MISMATCH")
    require(evidence["score_semantics"] == decision["score_semantics"],
            "SCORE_SEMANTICS_MISMATCH")
    require(set(evidence["values_ppm"]) == set(request["candidates"]), "CANDIDATE_SET_MISMATCH")
    version = evidence["model_version"].lower()
    require(version not in ("latest", "auto", "default") and not version.endswith("-latest"),
            "UNPINNED_MODEL_VERSION")
    values = evidence["values_ppm"]
    if decision["primitive"] == "choice":
        require(sum(values.values()) == PPM, "UNNORMALIZED_PROBABILITY")
    receipt.update(evidence_digest=digest(evidence), provider=evidence["provider"],
                   model=evidence["model"], model_version=evidence["model_version"],
                   observations=deepcopy(values))
    if evidence["abstain"]:
        receipt["reason"] = "PROVIDER_ABSTAINED"
        return receipt
    if decision["primitive"] == "choice":
        best = max(values.values())
        selected = [k for k, v in values.items() if v == best]
        if len(selected) != 1:
            receipt["reason"] = "AMBIGUOUS_WINNER"
            return receipt
        selected = selected if best >= decision["threshold_ppm"] else []
    else:
        selected = sorted(k for k, v in values.items() if v >= decision["threshold_ppm"])
    if not selected:
        receipt["reason"] = "BELOW_THRESHOLD"
        return receipt
    receipt.update(recommended=selected, policy_action="recommend_optional", reason="SHADOW_ONLY")
    return receipt
