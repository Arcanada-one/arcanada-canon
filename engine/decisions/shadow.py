"""Body-loading/evaluation facade. Internal result is always private."""

from .evaluate import evaluate
from .load import load_projection
from .model import Refusal


def run_private_shadow(bundle, request, evidence, *, deterministic_verdict, **load_args):
    projection = load_projection(bundle, **load_args)
    return evaluate(projection, request, evidence,
                    expected_projection_digest=projection["digest"],
                    deterministic_verdict=deterministic_verdict,
                    snapshot=bundle["snapshot"], expected_snapshot_digest=bundle["snapshot_digest"],
                    now=load_args["now"])


def public_receipt():
    """No argument is accepted: no content-dependent field can be declassified.

    Even success/refusal is withheld to avoid a private-existence oracle.
    This constant describes the interface, not whether a private run passed.
    """
    return {"schema": "PublicDecisionBoundary/v1", "mode": "offline_shadow",
            "applied": False, "authorization_granted": False,
            "publication_enabled": False, "result": "withheld"}


def run_public_shadow(*args, **kwargs):
    try:
        run_private_shadow(*args, **kwargs)
    except Refusal:
        pass
    return public_receipt()
