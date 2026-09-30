# Verify the offline decision-policy slice

Use Python 3.12 on Linux and install `requirements-decision-dev.txt` in an isolated
virtual environment. Dependency installation/auditing needs network access; the
following checks use synthetic local data and make no network or model calls:

```bash
python3 -B -m unittest discover -s tests/decisions -v
python3 -B tests/decisions/check_architecture.py
python3 -m compileall -q engine tests/decisions
```

`test_source_boundary.py` builds a public base plus private overlay in temporary
fixture directories, pins the complete manifest outside the source bodies, then
calls the actual loader and shadow facade. Tests cover actor/tenant denial before
body reads, missing/denied required closure, unknown classes, overlapping roots,
candidate/traversal/symlink/hardlink/FIFO paths, changed bytes/parent, stale/revoked
base or overlay, lower-scope weakening and deterministic denial at full confidence.
Public output is compared with a constant oracle across private success, denial
and different bodies; internal traces remain private.

`test_decisions.py` retains the pure projection and evaluator counterexamples:
exact scope/source identity, inherited obligations, changed snapshot/projection,
invalid probabilities, ties, insufficient state and calibration distinctions.
The policy template and all identities are synthetic. They do not measure
production tenants, model quality, frozen benchmarks or canonical scope mappings.

The dedicated Python CI uses read-only permissions, pinned actions and disposable
GitHub-hosted runners. It runs tests/fitness, compilation and a dependency audit;
it has no deployment, write token, private overlay artifact or self-hosted PR job.
Hosted-runner availability/billing must be measured by CI, never silently routed
to a privileged runner. A prepared workflow is not a passing remote check.

Before integration, verify current owner/source mappings, actual Auth verdicts,
source admission and revocation completeness. Refresh measurements while keeping
unchanged historical pins; do not rescue a stale projection by replacing hashes.
Keep local test, independent review, PR-head CI, resulting-main and runtime
receipts separate. L01/L05/L18 and real consumer completion are not established
by this offline suite.

For the bounded hierarchy consistency regression, run:

```bash
python3 -B -m unittest discover -s tests/decisions -p test_hierarchy.py -v
python3 -B tests/decisions/hierarchy_canary.py
```

Run the canary as a separate Python process over the real filesystem loader and
private/public shadow facades, using only synthetic pinned files. It checks
preserved mandatory obligations, rejection of a fully resealed matrix project,
and constant public output. No socket, provider or model call is required. Any
future loopback probe must run inside a private network namespace.
