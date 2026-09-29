"""Strict wire values and byte identity. This is not KC2 canonicalization."""

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


class Refusal(ValueError):
    """A stable refusal code; never include input bodies or secrets in errors."""


def require(condition, code):
    if not condition:
        raise Refusal(code)


def _json_values(value):
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for item in value:
            _json_values(item)
        return
    if type(value) is dict:
        require(all(type(k) is str for k in value), "INVALID_JSON_KEY")
        for item in value.values():
            _json_values(item)
        return
    raise Refusal("NON_CANONICAL_VALUE")


def canonical(value):
    _json_values(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def byte_digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_KEY")
        result[key] = value
    return result


def load_json(data):
    require(type(data) in (str, bytes) and len(data) <= 2_000_000,
            "INVALID_DOCUMENT_SIZE")
    try:
        value = json.loads(data, object_pairs_hook=_pairs)
        _json_values(value)
        return value
    except (ValueError, RecursionError):
        # ValueError covers JSONDecodeError, UnicodeError and the int-digit limit.
        raise Refusal("INVALID_JSON") from None


def validate(kind, value):
    _json_values(value)
    path = Path(__file__).resolve().parents[2] / "schemas/decision-policy.v1.json"
    schema = load_json(path.read_bytes())
    schema["$ref"] = "#/$defs/" + kind
    if next(Draft202012Validator(schema).iter_errors(value), None) is not None:
        raise Refusal("INVALID_" + kind.upper())
