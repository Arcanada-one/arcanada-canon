"""Offline source-boundary adapter; delegates projection, never admits policy.

Caller-held pins/authority and synthetic access decisions are trust inputs.
This module is not an Auth adapter, Git fetcher or Canon L18 resolver.
"""

from contextlib import ExitStack
import os
from pathlib import Path
import stat

from .model import Refusal, byte_digest, digest, load_json, require, validate
from .resolve import check_snapshot, resolve

MAX_BYTES = 2_000_000


def _parts(value):
    require(type(value) is str and bool(value) and "\\" not in value
            and "\x00" not in value, "SOURCE_PATH_EXCLUDED")
    parts = value.split("/")
    require(all(p not in ("", ".", "..") for p in parts), "SOURCE_PATH_EXCLUDED")
    return parts


def _directory(path, stack):
    """Walk absolute roots by descriptor; reject symlinks in every ancestor."""
    path = Path(path)
    require(path.is_absolute(), "SOURCE_ROOT_EXCLUDED")
    parts = _parts(str(path)[1:])
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    stack.callback(os.close, fd)
    for part in parts:
        fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        stack.callback(os.close, fd)
    return fd


def _read(root_fd, relative, prefix):
    parts = _parts(relative)
    require(len(parts) > 1 and parts[0] == prefix, "SOURCE_ROOT_EXCLUDED")
    with ExitStack() as stack:
        fd = root_fd
        for part in parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            stack.callback(os.close, fd)
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        stack.callback(os.close, fd)
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_size <= MAX_BYTES, "SOURCE_FILE_EXCLUDED")
        # Descriptor traversal prevents a checked path being swapped for a link.
        # Bytes remain checked against the external immutable manifest pin.
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, MAX_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            require(size <= MAX_BYTES, "SOURCE_FILE_EXCLUDED")
        return b"".join(chunks)


def _preflight(bundle, expected_digest, actor, tenant, authorities, now):
    validate("source_bundle", bundle)
    require(digest(bundle) == expected_digest, "BUNDLE_PIN_MISMATCH")
    check_snapshot(bundle["snapshot"], bundle["snapshot_digest"], now)
    require(bundle["valid_from"] <= now < bundle["expires_at"], "STALE_BUNDLE")
    entries = bundle["entries"]
    ids = [e["id"] for e in entries]
    require(len(set(ids)) == len(ids) and set(ids) == set(bundle["required_sources"]),
            "REQUIRED_CLOSURE_MISMATCH")
    identities = [(e["id"], e["revision"]) for e in entries]
    require(len(identities) == len(set(identities)), "SOURCE_IDENTITY_CONFLICT")
    chain = bundle["snapshot"]["policies"]
    scopes = [p["scope"] for p in chain]
    policy_entries, source_entries = [], []
    for entry in entries:
        require(entry["authority"] in authorities, "UNKNOWN_AUTHORITY")
        require(entry["valid_from"] <= now < entry["expires_at"], "STALE_SOURCE")
        require(entry["digest"] not in bundle["revoked_digests"]
                and entry["digest"] not in bundle["snapshot"]["revoked_digests"],
                "REVOKED_SOURCE")
        require(entry["scope"] in scopes, "SOURCE_SCOPE_MISMATCH")
        index = scopes.index(entry["scope"])
        parent = None if index == 0 else {k: chain[index-1][k] for k in ("id", "digest")}
        require(entry["parent"] == parent, "SOURCE_PARENT_MISMATCH")
        access = entry["access"]
        require(access["decision"] == "allow" and access["purpose"] == "offline_fixture_not_grant",
                "BODY_READ_DENIED")
        if entry["classification"] == "private_overlay":
            require(access["actor"] == actor and access["tenant"] == tenant
                    and actor != "*" and tenant != "*", "BODY_READ_DENIED")
            prefix = "overlays"
        else:
            require(access["actor"] == "*" and access["tenant"] == "*", "PUBLIC_ACCESS_MISMATCH")
            prefix = "canon"
        parts = _parts(entry["path"])
        require(len(parts) > 1 and parts[0] == prefix, "SOURCE_ROOT_EXCLUDED")
        if entry["kind"] == "policy":
            require(entry["policy_pin"] == chain[index], "POLICY_BINDING_MISMATCH")
            policy_entries.append(entry["policy_pin"])
        else:
            require(entry["source_ref"]["digest"] == entry["digest"]
                    and entry["source_ref"]["revision"] == entry["revision"], "SOURCE_IDENTITY_MISMATCH")
            source_entries.append(entry["source_ref"])
    require(sorted(policy_entries, key=lambda x: x["id"]) == sorted(chain, key=lambda x: x["id"]),
            "POLICY_CLOSURE_MISMATCH")
    require(sorted(source_entries, key=digest) == sorted(bundle["snapshot"]["sources"], key=digest),
            "SOURCE_CLOSURE_MISMATCH")


def load_projection(bundle, *, expected_bundle_digest, public_repository,
                    private_repository, actor, tenant, trusted_authorities, now):
    """Only entrypoint for filesystem-backed offline projections.

    The entire required access closure is checked BEFORE opening any body.
    Both root paths, pins, identities and trusted authorities are caller-held,
    never taken from a candidate source. Return value is PRIVATE, including
    when only public source bodies happen to participate.
    """
    require(type(actor) is str and bool(actor) and type(tenant) is str and bool(tenant),
            "INVALID_CALLER_IDENTITY")
    require(type(trusted_authorities) in (set, frozenset) and bool(trusted_authorities)
            and all(type(a) is str and bool(a) for a in trusted_authorities),
            "INVALID_AUTHORITY_SET")
    _preflight(bundle, expected_bundle_digest, actor, tenant, trusted_authorities, now)
    public, private = Path(public_repository), Path(private_repository)
    require(not public.is_relative_to(private) and not private.is_relative_to(public),
            "MIXED_SOURCE_ROOTS")
    policies, sources = {}, {}
    try:
        with ExitStack() as stack:
            roots = {"public_base": _directory(public, stack),
                     "private_overlay": _directory(private, stack)}
            stats = [os.fstat(fd) for fd in roots.values()]
            require((stats[0].st_dev, stats[0].st_ino) != (stats[1].st_dev, stats[1].st_ino),
                    "MIXED_SOURCE_ROOTS")
            for entry in bundle["entries"]:
                prefix = "canon" if entry["classification"] == "public_base" else "overlays"
                data = _read(roots[entry["classification"]], entry["path"], prefix)
                require(byte_digest(data) == entry["digest"], "SOURCE_BYTES_MISMATCH")
                if entry["kind"] == "policy":
                    policy = load_json(data)
                    require(digest(policy) == entry["policy_pin"]["digest"], "POLICY_PIN_MISMATCH")
                    policies[entry["policy_pin"]["id"]] = policy
                else:
                    sources[entry["digest"]] = data
    except OSError:
        raise Refusal("SOURCE_UNAVAILABLE") from None
    return resolve(policies, bundle["snapshot"],
                   expected_snapshot_digest=bundle["snapshot_digest"],
                   target_scope=bundle["snapshot"]["policies"][-1]["scope"],
                   sources=sources, now=now)
