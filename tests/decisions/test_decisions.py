"""Offline contract counterexamples; no model, network, or frozen benchmark."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from engine.decisions import Refusal, digest, evaluate, load_json, resolve
from engine.decisions.model import byte_digest, canonical, validate

ROOT = Path(__file__).resolve().parents[2]


def fixture(depth=3):
    """Synthetic identities, not deployment/adoption evidence."""
    source_bytes = b"Synthetic existing policy; this is a test fixture."
    source = {"repository": "fixture/authority", "revision": "test-r1",
              "path": "policy.txt", "digest": byte_digest(source_bytes),
              "kind": "existing_mandate"}
    scopes = [{"level": level, "id": name} for level, name in zip(
        ("universe", "space", "project", "role", "agent"),
        ("fixture-universe", "fixture-space", "purpose-project", "reviewer", "test-agent"))][:depth]
    registry = {"schema": "DecisionScopeBindings/v1", "status": "draft_offline_projection",
                "sources": [source], "scope_chains": [scopes]}
    registry_bytes = canonical(registry)
    registry_ref = dict(source, path="registry.json", digest=byte_digest(registry_bytes), kind="registry")
    root = load_json((ROOT / "tests/decisions/fixtures/policy-template.json").read_bytes())
    root.update(id="fixture-universe-policy", scope=scopes[0], sources=[source])
    root["decisions"][0]["source_digests"] = [source["digest"]]
    policies, chain, parent = {}, [], None
    for i, scope in enumerate(scopes):
        p = deepcopy(root) if i == 0 else dict(
            schema="DecisionPolicy/v1", id=f"fixture-policy-{i}", revision=1,
            status="draft", scope=scope, parent=parent, sources=[source],
            mandatory=[f"extra-obligation-{i}"], decisions=[])
        policies[p["id"]] = p
        pin = {"id": p["id"], "digest": digest(p)}
        chain.append(dict(pin, scope=scope))
        parent = pin
    snapshot = {"schema": "DecisionPolicySnapshot/v1", "purpose": "offline_fixture_not_admission",
                "valid_from": 100, "expires_at": 200, "registry_pin": registry_ref,
                "source_digests": [source["digest"], registry_ref["digest"]],
                "sources": [source, registry_ref],
                "revoked_digests": [], "policies": chain}
    sources = {source["digest"]: source_bytes, registry_ref["digest"]: registry_bytes}
    return policies, snapshot, sources


def reseal(policies, snapshot):
    """Model a changed externally pinned snapshot in negative controls."""
    parent = None
    for ref in snapshot["policies"]:
        policies[ref["id"]]["parent"] = parent
        ref["digest"] = digest(policies[ref["id"]])
        parent = {"id": ref["id"], "digest": ref["digest"]}


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.policies, self.snapshot, self.sources = fixture()
        self.pin = digest(self.snapshot)
        self.now = 150

    def resolve(self):
        return resolve(self.policies, self.snapshot, expected_snapshot_digest=self.pin,
                       target_scope=self.snapshot["policies"][-1]["scope"],
                       sources=self.sources, now=self.now)

    def prepare(self):
        self.resolved = self.resolve()
        state = {"task_goal": "fixture goal", "remaining_work": "fixture remaining work",
                 "risk_class": "low"}
        self.request = {"schema": "DecisionRequest/v1", "id": "fixture-request",
                        "decision_type": "model.tier", "projection_digest": self.resolved["digest"],
                        "scope": self.resolved["projection"]["scope"], "state": state,
                        "state_digest": digest(state), "candidates": ["economy", "balanced", "high_assurance"],
                        "baseline": "balanced"}
        self.evidence = {"schema": "DecisionEvidence/v1", "request_digest": digest(self.request),
                         "provider": "fixture", "model": "test-choice", "model_version": "test-r1",
                         "primitive": "choice", "score_semantics": "normalized_option_mass",
                         "values_ppm": {"economy": 800000, "balanced": 150000, "high_assurance": 50000},
                         "calibration": "not_measured", "abstain": False}

    def evaluate(self, verdict="allow"):
        result = evaluate(self.resolved, self.request, self.evidence,
                        expected_projection_digest=self.request["projection_digest"],
                        deterministic_verdict=verdict, snapshot=self.snapshot,
                        expected_snapshot_digest=self.pin, now=self.now)
        validate("trace", result)
        return result

    def test_shadow_trace_is_bound_and_not_permission(self):
        self.prepare()
        trace = self.evaluate()
        self.assertEqual(trace["recommended"], ["economy"])
        self.assertFalse(trace["applied"])
        self.assertFalse(trace["authorization_granted"])
        self.assertEqual(trace["evidence_digest"], digest(self.evidence))
        self.assertEqual(trace["request_digest"], digest(self.request))
        self.assertNotIn("fixture goal", json.dumps(trace))
        self.assertIn("extra-obligation-2", trace["mandatory"])
        self.assertEqual(trace["calibration"], "not_measured")

    def test_trace_is_not_a_mutable_alias_to_inputs(self):
        self.prepare(); trace = self.evaluate(); before = deepcopy(trace)
        self.evidence["values_ppm"]["economy"] = 1
        self.resolved["projection"]["mandatory"].clear()
        self.request["scope"]["id"] = "changed"
        self.assertEqual(trace, before)

    def test_all_five_levels(self):
        self.policies, self.snapshot, self.sources = fixture(5)
        self.pin = digest(self.snapshot)
        self.assertEqual(len(self.resolve()["projection"]["lineage"]), 5)

    def test_resolution_is_deterministic_and_does_not_mutate_sources(self):
        before = deepcopy(self.policies)
        self.assertEqual(self.resolve(), self.resolve())
        self.assertEqual(self.policies, before)

    def test_missing_policy(self):
        self.policies.pop(next(iter(self.policies)))
        with self.assertRaisesRegex(Refusal, "POLICY_SET_MISMATCH"):
            self.resolve()

    def test_changed_parent_bytes(self):
        next(iter(self.policies.values()))["revision"] = 2
        with self.assertRaisesRegex(Refusal, "POLICY_PIN_MISMATCH"):
            self.resolve()

    def test_wrong_parent_digest(self):
        child = list(self.policies.values())[1]
        child["parent"]["digest"] = "sha256:" + "0" * 64
        self.snapshot["policies"][1]["digest"] = digest(child)
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "PARENT_PIN_MISMATCH"):
            self.resolve()

    def test_lower_scope_cannot_weaken_threshold(self):
        child = list(self.policies.values())[1]
        child["decisions"] = deepcopy(next(iter(self.policies.values()))["decisions"])
        child["decisions"][0]["threshold_ppm"] = 1
        reseal(self.policies, self.snapshot)
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "INHERITED_DECISION_CONFLICT"):
            self.resolve()

    def test_lower_scope_cannot_remove_mandatory(self):
        root = next(iter(self.policies.values()))
        self.assertTrue(set(root["mandatory"]) <= set(self.resolve()["projection"]["mandatory"]))

    def test_no_duplicate_decision_override_in_one_policy(self):
        root = next(iter(self.policies.values()))
        other = deepcopy(root["decisions"][0]); other["threshold_ppm"] = 1
        root["decisions"].append(other)
        reseal(self.policies, self.snapshot); self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "DUPLICATE_DECISION"):
            self.resolve()

    def test_scope_chain_cannot_skip_space(self):
        self.snapshot["policies"][1]["scope"]["level"] = "project"
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "INVALID_SCOPE_CHAIN"):
            self.resolve()

    def test_project_is_not_repository(self):
        self.snapshot["policies"][-1]["scope"]["level"] = "repo"
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "INVALID_SNAPSHOT"):
            self.resolve()

    def test_same_name_in_foreign_space_does_not_match_registry(self):
        self.snapshot["policies"][1]["scope"] = {"level": "space", "id": "foreign"}
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "UNREGISTERED_SCOPE_CHAIN"):
            self.resolve()

    def test_stale_and_future_snapshot(self):
        for now in [99, 200, 201]:
            with self.subTest(now=now), self.assertRaisesRegex(Refusal, "STALE_SNAPSHOT"):
                self.now = now; self.resolve()

    def test_revoked_policy_and_source(self):
        pins = [self.snapshot["policies"][0]["digest"], self.snapshot["source_digests"][0]]
        for pin in pins:
            with self.subTest(pin=pin), self.assertRaisesRegex(Refusal, "REVOKED_PIN"):
                self.snapshot["revoked_digests"] = [pin]
                self.pin = digest(self.snapshot); self.resolve()

    def test_source_bytes_must_match_digest(self):
        self.sources[next(iter(self.sources))] = b"changed source"
        with self.assertRaisesRegex(Refusal, "SOURCE_DIGEST_MISMATCH"):
            self.resolve()

    def test_identical_bytes_do_not_allow_source_identity_forgery(self):
        next(iter(self.policies.values()))["sources"][0]["repository"] = "attacker/authority"
        # Policy and snapshot share a fixture source object; restore the
        # independent snapshot identities before testing the forged policy.
        self.snapshot["sources"] = fixture()[1]["sources"]
        reseal(self.policies, self.snapshot); self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "SOURCE_IDENTITY_MISMATCH"):
            self.resolve()

    def test_conflicting_source_identity_is_held(self):
        forged = dict(self.snapshot["sources"][0], digest="sha256:" + "0" * 64)
        self.snapshot["sources"].append(forged)
        self.snapshot["source_digests"].append(forged["digest"])
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "CONFLICTING_SOURCE_IDENTITY"):
            self.resolve()

    def test_candidate_cannot_supply_trust_root(self):
        next(iter(self.policies.values()))["admitted"] = True
        reseal(self.policies, self.snapshot); self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "INVALID_POLICY"):
            self.resolve()

    def test_snapshot_cannot_authorize_its_own_changed_digest(self):
        self.snapshot["expires_at"] = 999999
        with self.assertRaisesRegex(Refusal, "SNAPSHOT_PIN_MISMATCH"):
            self.resolve()

    def test_projection_mutation_is_detected(self):
        self.prepare(); self.resolved["projection"]["mandatory"] = []
        self.resolved["digest"] = digest(self.resolved["projection"])
        with self.assertRaisesRegex(Refusal, "PROJECTION_PIN_MISMATCH"):
            self.evaluate()

    def test_evaluation_rechecks_expiry(self):
        self.prepare(); self.now = 200
        with self.assertRaisesRegex(Refusal, "STALE_SNAPSHOT"):
            self.evaluate()

    def test_new_revocation_invalidates_old_projection(self):
        self.prepare()
        self.snapshot["revoked_digests"] = [self.snapshot["policies"][0]["digest"]]
        self.pin = digest(self.snapshot)
        with self.assertRaisesRegex(Refusal, "REVOKED_PIN"):
            self.evaluate()

    def test_allow_never_follows_model_probability(self):
        self.prepare()
        for verdict in ["deny", "unknown"]:
            with self.subTest(verdict=verdict):
                trace = self.evaluate(verdict)
                self.assertEqual(trace["policy_action"], "deny")
                self.assertEqual(trace["recommended"], [])

    def test_required_context_missing_abstains(self):
        self.prepare(); del self.request["state"]["risk_class"]
        self.request["state_digest"] = digest(self.request["state"])
        self.assertEqual(self.evaluate()["reason"], "INSUFFICIENT_STATE")

    def test_wrong_type_or_empty_context_abstains(self):
        for key, value in [("task_goal", "   "), ("risk_class", "unknown"),
                           ("risk_class", False), ("remaining_work", 42)]:
            with self.subTest(key=key, value=value):
                self.prepare(); self.request["state"][key] = value
                self.request["state_digest"] = digest(self.request["state"])
                self.assertEqual(self.evaluate()["reason"], "INSUFFICIENT_STATE")

    def test_missing_provider_retains_baseline(self):
        self.prepare(); self.evidence = None
        self.assertEqual(self.evaluate()["reason"], "PROVIDER_UNAVAILABLE")

    def test_choice_tie_abstains(self):
        self.prepare(); self.evidence["values_ppm"] = {"economy": 500000, "balanced": 500000, "high_assurance": 0}
        self.assertEqual(self.evaluate()["reason"], "AMBIGUOUS_WINNER")

    def test_exact_threshold_and_below(self):
        self.prepare()
        for mass, reason in [(699999, "BELOW_THRESHOLD"), (700000, "SHADOW_ONLY")]:
            self.evidence["values_ppm"] = {"economy": mass, "balanced": 1000000-mass, "high_assurance": 0}
            self.assertEqual(self.evaluate()["reason"], reason)

    def test_observation_domain_and_normalization(self):
        self.prepare()
        for value in [-1, 1000001, True, 0.8, float("nan"), float("inf"), "800000"]:
            with self.subTest(value=value), self.assertRaises(Refusal):
                self.evidence["values_ppm"]["economy"] = value; self.evaluate()
        self.evidence["values_ppm"]["economy"] = 800001
        with self.assertRaisesRegex(Refusal, "UNNORMALIZED_PROBABILITY"):
            self.evaluate()

    def test_independent_probability_is_not_normalized(self):
        root = next(iter(self.policies.values()))
        root["decisions"][0].update(primitive="independent_probability", score_semantics="independent_event_estimate")
        reseal(self.policies, self.snapshot); self.pin = digest(self.snapshot)
        self.prepare()
        self.evidence.update(primitive="independent_probability", score_semantics="independent_event_estimate")
        self.evidence["values_ppm"] = dict(economy=800000, balanced=900000, high_assurance=100000)
        self.assertEqual(self.evaluate()["recommended"], ["balanced", "economy"])

    def test_score_cannot_be_passed_as_probability(self):
        self.prepare(); self.evidence["score_semantics"] = "bounded_ordinal_utility"
        with self.assertRaisesRegex(Refusal, "SCORE_SEMANTICS_MISMATCH"):
            self.evaluate()

    def test_bounded_score_has_no_normalization_or_calibration_claim(self):
        root = next(iter(self.policies.values()))
        root["decisions"][0].update(primitive="score", score_semantics="bounded_ordinal_utility")
        reseal(self.policies, self.snapshot); self.pin = digest(self.snapshot)
        self.prepare()
        self.evidence.update(primitive="score", score_semantics="bounded_ordinal_utility")
        self.evidence["values_ppm"] = dict(economy=800000, balanced=900000, high_assurance=900000)
        trace = self.evaluate()
        self.assertEqual(trace["recommended"], ["balanced", "economy", "high_assurance"])
        self.assertEqual(trace["calibration"], "not_measured")

    def test_explicit_abstention_and_unpinned_model(self):
        self.prepare(); self.evidence["abstain"] = True
        self.assertEqual(self.evaluate()["reason"], "PROVIDER_ABSTAINED")
        for version in ["latest", "jev-latest", "auto", "default"]:
            self.evidence["model_version"] = version
            with self.subTest(version=version), self.assertRaisesRegex(Refusal, "UNPINNED_MODEL_VERSION"):
                self.evaluate()

    def test_calibration_cannot_be_self_declared(self):
        self.prepare(); self.evidence["calibration"] = "calibrated"
        with self.assertRaisesRegex(Refusal, "INVALID_EVIDENCE"):
            self.evaluate()

    def test_unknown_option_is_not_accepted(self):
        self.prepare(); self.evidence["values_ppm"]["unknown"] = 0
        with self.assertRaisesRegex(Refusal, "CANDIDATE_SET_MISMATCH"):
            self.evaluate()

    def test_wrong_request_and_wrong_scope(self):
        self.prepare(); self.evidence["request_digest"] = "sha256:" + "0"*64
        with self.assertRaisesRegex(Refusal, "EVIDENCE_REQUEST_MISMATCH"):
            self.evaluate()
        self.prepare(); self.request["scope"] = {"level": "project", "id": "foreign"}
        with self.assertRaisesRegex(Refusal, "WRONG_SCOPE"):
            self.evaluate()

    def test_duplicate_json_and_float_rejection(self):
        for raw in ['{"id":1,"id":2}', '{"x":NaN}', '{"x":0.4}', '{"x":' + '9'*5000 + '}', b'\xff']:
            with self.subTest(raw=raw), self.assertRaises(Refusal):
                load_json(raw)

    def test_synthetic_policy_schema_is_not_adoption(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(load_json((ROOT / "schemas/decision-policy.v1.json").read_bytes()))
        validate("policy", fixture()[0]["fixture-universe-policy"])
        self.assertIn("publication_enabled: false", (ROOT / "canon.source.yaml").read_text())


if __name__ == "__main__":
    unittest.main()
