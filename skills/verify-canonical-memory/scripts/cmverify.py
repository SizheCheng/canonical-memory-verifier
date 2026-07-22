#!/usr/bin/env python3
"""Deterministic, read-only verifier for Canonical Memory bundles."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA_VERSION = "0.1.0"
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_RECORDS = 1000
MAX_DIRECTORY_ENTRIES = MAX_RECORDS + 2
MAX_SOURCE_BYTES = 256 * 1024
MAX_TOTAL_SOURCE_BYTES = 512 * 1024
MAX_VALUE_BYTES = 64 * 1024
MAX_DEPTH = 32

ROOT_FIELDS = {
    "schema_version",
    "bundle_kind",
    "bundle_id",
    "scope",
    "sources",
    "claims",
    "supersessions",
}
SOURCE_FIELDS = {"source_id", "path", "media_type", "bytes", "sha256"}
CLAIM_FIELDS = {
    "claim_id",
    "key",
    "claim_type",
    "value",
    "source_refs",
    "approval_eligible",
}
EDGE_FIELDS = {
    "edge_id",
    "superseded_claim_id",
    "superseding_claim_id",
    "reason",
}

ID_PATTERNS = {
    "bundle_id": re.compile(r"^bnd_[a-z0-9][a-z0-9._-]{0,63}$"),
    "source_id": re.compile(r"^src_[a-z0-9][a-z0-9._-]{0,63}$"),
    "claim_id": re.compile(r"^clm_[a-z0-9][a-z0-9._-]{0,63}$"),
    "edge_id": re.compile(r"^sup_[a-z0-9][a-z0-9._-]{0,63}$"),
    "scope": re.compile(r"^[a-z][a-z0-9._:/-]{0,127}$"),
    "key": re.compile(r"^[a-z][a-z0-9._-]{0,127}$"),
    "source_path": re.compile(r"^sources/[a-z0-9][a-z0-9._-]{0,127}$"),
    "sha256": re.compile(r"^[0-9a-f]{64}$"),
}


class DuplicateKeyError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        _emit(
            {
                "status": "INVALID",
                "errors": [
                    {
                        "code": "CMV_SCHEMA_INVALID",
                        "location": "$cli",
                        "detail": "invalid command-line arguments",
                    }
                ],
            }
        )
        raise SystemExit(64)


def _object_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_object(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _emit(value: Any) -> None:
    payload = _canonical_bytes(value) + b"\n"
    binary_stdout = getattr(sys.stdout, "buffer", None)
    if binary_stdout is not None:
        binary_stdout.write(payload)
        binary_stdout.flush()
    else:
        sys.stdout.write(payload.decode("utf-8"))
        sys.stdout.flush()


def _issue(code: str, location: str, detail: str) -> dict[str, str]:
    return {"code": code, "location": location, "detail": detail}


def _sort_issues(issues: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(issues, key=lambda item: (item["code"], item["location"], item["detail"]))


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    attrs = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(attrs & reparse_flag)


def _normal_name(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _bounded_string(value: Any, minimum: int, maximum: int) -> bool:
    return isinstance(value, str) and minimum <= len(value) <= maximum


def _bounded_directory_entries(
    path: Path, maximum: int
) -> tuple[list[Path], str | None]:
    entries: list[Path] = []
    try:
        with os.scandir(path) as iterator:
            for item in iterator:
                if len(entries) >= maximum:
                    return entries, "directory entry limit exceeded"
                entries.append(Path(item.path))
    except OSError:
        return [], "directory inventory unavailable"
    return entries, None


def _matches(value: Any, pattern_name: str) -> bool:
    return isinstance(value, str) and bool(ID_PATTERNS[pattern_name].fullmatch(value))


def _unknown_fields(
    record: dict[str, Any], allowed: set[str], location: str, issues: list[dict[str, str]]
) -> None:
    for name in sorted(set(record) - allowed):
        issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/{name}", "unknown field"))


def _check_depth(value: Any, depth: int = 0) -> bool:
    if depth > MAX_DEPTH:
        return False
    if isinstance(value, dict):
        return all(_check_depth(item, depth + 1) for item in value.values())
    if isinstance(value, list):
        return all(_check_depth(item, depth + 1) for item in value)
    return True


def _read_regular_bytes(path: Path, maximum: int) -> tuple[bytes | None, str | None]:
    try:
        if _is_reparse(path) or not path.is_file():
            return None, "not a regular non-reparse file"
        before = path.stat()
        if before.st_size > maximum:
            return None, "file exceeds byte limit"
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            data = handle.read(maximum + 1)
            closed = os.fstat(handle.fileno())
        if len(data) > maximum:
            return None, "file exceeds byte limit"
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_opened = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
        identity_closed = (closed.st_dev, closed.st_ino, closed.st_size, closed.st_mtime_ns)
        if identity_before != identity_opened or identity_opened != identity_closed:
            return None, "file changed during verification"
        return data, None
    except OSError:
        return None, "file could not be read"


def _load_manifest(bundle_dir: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    if not bundle_dir.exists():
        return None, [_issue("CMV_SOURCE_MISSING", "$bundle", "bundle directory is missing")]
    if _is_reparse(bundle_dir) or not bundle_dir.is_dir():
        return None, [_issue("CMV_NONREGULAR_PATH", "$bundle", "bundle must be a real directory")]

    manifest_path = bundle_dir / "bundle.json"
    data, error = _read_regular_bytes(manifest_path, MAX_MANIFEST_BYTES)
    if error is not None:
        return None, [_issue("CMV_NONREGULAR_PATH", "bundle.json", error)]
    assert data is not None
    try:
        text = data.decode("utf-8", errors="strict")
        manifest = json.loads(
            text,
            object_pairs_hook=_object_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError, RecursionError) as exc:
        return None, [_issue("CMV_INVALID_JSON", "bundle.json", str(exc))]
    if not isinstance(manifest, dict):
        return None, [_issue("CMV_SCHEMA_INVALID", "$", "root must be an object")]
    if not _check_depth(manifest):
        issues.append(_issue("CMV_SCHEMA_INVALID", "$", "maximum JSON depth exceeded"))
    return manifest, issues


def _validate_root_inventory(bundle_dir: Path, issues: list[dict[str, str]]) -> Path | None:
    entries, inventory_error = _bounded_directory_entries(bundle_dir, MAX_DIRECTORY_ENTRIES)
    if inventory_error is not None:
        issues.append(_issue("CMV_SCHEMA_INVALID", "$bundle", inventory_error))
        return None

    seen_names: dict[str, str] = {}
    for entry in entries:
        normalized = _normal_name(entry.name)
        prior = seen_names.get(normalized)
        if prior is not None and prior != entry.name:
            issues.append(_issue("CMV_PATH_COLLISION", "$bundle", "root name normalization collision"))
        seen_names[normalized] = entry.name
        if entry.name not in {"bundle.json", "sources"}:
            issues.append(_issue("CMV_UNDECLARED_FILE", entry.name, "undeclared root entry"))

    sources_dir = bundle_dir / "sources"
    if not sources_dir.exists():
        issues.append(_issue("CMV_SOURCE_MISSING", "sources", "sources directory is missing"))
        return None
    if _is_reparse(sources_dir) or not sources_dir.is_dir():
        issues.append(_issue("CMV_NONREGULAR_PATH", "sources", "sources must be a real directory"))
        return None
    return sources_dir


def _validate_manifest_shape(manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    _unknown_fields(manifest, ROOT_FIELDS, "$", issues)
    missing = ROOT_FIELDS - set(manifest)
    for name in sorted(missing):
        issues.append(_issue("CMV_SCHEMA_INVALID", f"$/{name}", "required field missing"))

    if manifest.get("schema_version") != SCHEMA_VERSION:
        issues.append(
            _issue(
                "CMV_UNSUPPORTED_SCHEMA_VERSION",
                "$/schema_version",
                f"expected {SCHEMA_VERSION}",
            )
        )
    if manifest.get("bundle_kind") != "imported_memory":
        issues.append(_issue("CMV_SCHEMA_INVALID", "$/bundle_kind", "expected imported_memory"))
    if not _matches(manifest.get("bundle_id"), "bundle_id"):
        issues.append(_issue("CMV_SCHEMA_INVALID", "$/bundle_id", "invalid bundle identifier"))
    if not _matches(manifest.get("scope"), "scope"):
        issues.append(_issue("CMV_SCHEMA_INVALID", "$/scope", "invalid scope"))

    for field in ("sources", "claims", "supersessions"):
        value = manifest.get(field)
        if not isinstance(value, list):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"$/{field}", "must be an array"))
        elif len(value) > MAX_RECORDS:
            issues.append(_issue("CMV_SCHEMA_INVALID", f"$/{field}", "record limit exceeded"))


def _validate_sources(
    bundle_dir: Path,
    sources_dir: Path | None,
    records: Any,
    issues: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    declared_paths: dict[str, str] = {}
    total_bytes = 0
    if not isinstance(records, list):
        return result

    for index, record in enumerate(records):
        location = f"$/sources/{index}"
        if not isinstance(record, dict):
            issues.append(_issue("CMV_SCHEMA_INVALID", location, "source must be an object"))
            continue
        _unknown_fields(record, SOURCE_FIELDS, location, issues)
        for name in sorted(SOURCE_FIELDS - set(record)):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/{name}", "required field missing"))

        source_id = record.get("source_id")
        if not _matches(source_id, "source_id"):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/source_id", "invalid source identifier"))
            continue
        if source_id in result:
            issues.append(_issue("CMV_DUPLICATE_ID", f"{location}/source_id", "duplicate source identifier"))
            continue

        source_path = record.get("path")
        if not _matches(source_path, "source_path"):
            issues.append(_issue("CMV_PATH_UNSAFE", f"{location}/path", "unsafe or non-flat source path"))
            continue
        path_parts = PurePosixPath(source_path).parts
        if len(path_parts) != 2 or path_parts[0] != "sources" or "\\" in source_path or ":" in source_path:
            issues.append(_issue("CMV_PATH_UNSAFE", f"{location}/path", "unsafe source path"))
            continue
        normalized = _normal_name(source_path)
        if normalized in declared_paths:
            issues.append(_issue("CMV_PATH_COLLISION", f"{location}/path", "duplicate normalized source path"))
            continue
        declared_paths[normalized] = source_path

        if not _bounded_string(record.get("media_type"), 1, 128):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/media_type", "invalid media type"))
        declared_size = record.get("bytes")
        if not _is_int(declared_size) or not 0 <= declared_size <= MAX_SOURCE_BYTES:
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/bytes", "invalid source byte count"))
        declared_hash = record.get("sha256")
        if not _matches(declared_hash, "sha256"):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/sha256", "invalid SHA-256"))

        result[source_id] = record
        if sources_dir is None:
            continue
        disk_path = bundle_dir / Path(*path_parts)
        data, error = _read_regular_bytes(disk_path, MAX_SOURCE_BYTES)
        if error is not None:
            code = "CMV_SOURCE_MISSING" if not disk_path.exists() else "CMV_NONREGULAR_PATH"
            issues.append(_issue(code, source_path, error))
            continue
        assert data is not None
        total_bytes += len(data)
        if _is_int(declared_size) and len(data) != declared_size:
            issues.append(_issue("CMV_SOURCE_SIZE_MISMATCH", source_path, "declared size does not match bytes"))
        if isinstance(declared_hash, str) and _sha256_bytes(data) != declared_hash:
            issues.append(_issue("CMV_SOURCE_HASH_MISMATCH", source_path, "declared SHA-256 does not match bytes"))

    if total_bytes > MAX_TOTAL_SOURCE_BYTES:
        issues.append(_issue("CMV_SCHEMA_INVALID", "sources", "total source byte limit exceeded"))

    if sources_dir is not None:
        actual_entries, inventory_error = _bounded_directory_entries(
            sources_dir, MAX_DIRECTORY_ENTRIES
        )
        if inventory_error is not None:
            issues.append(_issue("CMV_SCHEMA_INVALID", "sources", inventory_error))
        actual_normalized: dict[str, str] = {}
        for entry in actual_entries:
            relative = f"sources/{entry.name}"
            normalized = _normal_name(relative)
            prior = actual_normalized.get(normalized)
            if prior is not None and prior != relative:
                issues.append(_issue("CMV_PATH_COLLISION", "sources", "source name normalization collision"))
            actual_normalized[normalized] = relative
            if normalized not in declared_paths:
                issues.append(_issue("CMV_UNDECLARED_FILE", relative, "undeclared source entry"))
            if _is_reparse(entry) or not entry.is_file():
                issues.append(_issue("CMV_NONREGULAR_PATH", relative, "source entry must be a regular file"))
        for normalized, relative in declared_paths.items():
            if normalized not in actual_normalized:
                issues.append(_issue("CMV_SOURCE_MISSING", relative, "declared source file is missing"))

    return result


def _validate_claims(
    records: Any,
    sources_by_id: dict[str, dict[str, Any]],
    issues: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(records, list):
        return result
    for index, record in enumerate(records):
        location = f"$/claims/{index}"
        if not isinstance(record, dict):
            issues.append(_issue("CMV_SCHEMA_INVALID", location, "claim must be an object"))
            continue
        _unknown_fields(record, CLAIM_FIELDS, location, issues)
        for name in sorted(CLAIM_FIELDS - set(record)):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/{name}", "required field missing"))

        claim_id = record.get("claim_id")
        if not _matches(claim_id, "claim_id"):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/claim_id", "invalid claim identifier"))
            continue
        if claim_id in result:
            issues.append(_issue("CMV_DUPLICATE_ID", f"{location}/claim_id", "duplicate claim identifier"))
            continue

        if not _matches(record.get("key"), "key"):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/key", "invalid functional key"))
        if record.get("claim_type") not in {"fact", "historical_authority"}:
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/claim_type", "invalid claim type"))
        if not _bounded_string(record.get("value"), 1, MAX_VALUE_BYTES):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/value", "invalid claim value"))
        if record.get("approval_eligible") is not False:
            issues.append(
                _issue(
                    "CMV_APPROVAL_ELIGIBILITY_VIOLATION",
                    f"{location}/approval_eligible",
                    "imported memory can never satisfy live approval",
                )
            )

        refs = record.get("source_refs")
        if not isinstance(refs, list) or not 1 <= len(refs) <= 100:
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/source_refs", "must be a nonempty bounded array"))
        else:
            seen_refs: set[str] = set()
            for ref_index, source_id in enumerate(refs):
                ref_location = f"{location}/source_refs/{ref_index}"
                if not _matches(source_id, "source_id"):
                    issues.append(_issue("CMV_SCHEMA_INVALID", ref_location, "invalid source reference"))
                elif source_id in seen_refs:
                    issues.append(_issue("CMV_SCHEMA_INVALID", ref_location, "duplicate source reference"))
                elif source_id not in sources_by_id:
                    issues.append(_issue("CMV_DANGLING_REFERENCE", ref_location, "source reference does not resolve"))
                seen_refs.add(source_id)

        result[claim_id] = record
    return result


def _detect_cycle(edges: list[dict[str, Any]], claims_by_id: dict[str, dict[str, Any]]) -> bool:
    adjacency: dict[str, list[str]] = {claim_id: [] for claim_id in claims_by_id}
    indegree: dict[str, int] = {claim_id: 0 for claim_id in claims_by_id}
    for edge in edges:
        old_id = edge.get("superseded_claim_id")
        new_id = edge.get("superseding_claim_id")
        if old_id in adjacency and new_id in adjacency:
            adjacency[old_id].append(new_id)
            indegree[new_id] += 1
    ready = [claim_id for claim_id, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    visited = 0
    while ready:
        node = heapq.heappop(ready)
        visited += 1
        for neighbor in sorted(adjacency[node]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                heapq.heappush(ready, neighbor)
    return visited != len(adjacency)


def _validate_edges(
    records: Any,
    claims_by_id: dict[str, dict[str, Any]],
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    edge_ids: set[str] = set()
    edge_pairs: set[tuple[str, str]] = set()
    if not isinstance(records, list):
        return result
    for index, record in enumerate(records):
        location = f"$/supersessions/{index}"
        if not isinstance(record, dict):
            issues.append(_issue("CMV_SCHEMA_INVALID", location, "edge must be an object"))
            continue
        _unknown_fields(record, EDGE_FIELDS, location, issues)
        for name in sorted(EDGE_FIELDS - set(record)):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/{name}", "required field missing"))

        edge_id = record.get("edge_id")
        if not _matches(edge_id, "edge_id"):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/edge_id", "invalid edge identifier"))
        elif edge_id in edge_ids:
            issues.append(_issue("CMV_DUPLICATE_ID", f"{location}/edge_id", "duplicate edge identifier"))
        else:
            edge_ids.add(edge_id)

        old_id = record.get("superseded_claim_id")
        new_id = record.get("superseding_claim_id")
        if not _matches(old_id, "claim_id") or not _matches(new_id, "claim_id"):
            issues.append(_issue("CMV_SCHEMA_INVALID", location, "invalid edge endpoint identifier"))
            continue
        pair = (old_id, new_id)
        if pair in edge_pairs:
            issues.append(_issue("CMV_SCHEMA_INVALID", location, "duplicate logical edge"))
        edge_pairs.add(pair)
        if old_id == new_id:
            issues.append(_issue("CMV_SUPERSESSION_CYCLE", location, "self-supersession is forbidden"))
        old_claim = claims_by_id.get(old_id)
        new_claim = claims_by_id.get(new_id)
        if old_claim is None or new_claim is None:
            issues.append(_issue("CMV_DANGLING_REFERENCE", location, "edge endpoint does not resolve"))
        elif old_claim.get("key") != new_claim.get("key"):
            issues.append(_issue("CMV_SUPERSESSION_KEY_MISMATCH", location, "edge endpoints have different keys"))
        if not _bounded_string(record.get("reason"), 1, 512):
            issues.append(_issue("CMV_SCHEMA_INVALID", f"{location}/reason", "invalid edge reason"))
        result.append(record)

    if _detect_cycle(result, claims_by_id):
        issues.append(_issue("CMV_SUPERSESSION_CYCLE", "$/supersessions", "supersession graph contains a cycle"))
    return result


def _build_projection(
    claims_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    issues: list[dict[str, str]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for claim_id, claim in claims_by_id.items():
        key = claim.get("key")
        if isinstance(key, str):
            groups.setdefault(key, []).append(claim_id)
    superseded = {
        edge.get("superseded_claim_id")
        for edge in edges
        if edge.get("superseded_claim_id") in claims_by_id
    }
    projection: list[dict[str, Any]] = []
    for key in sorted(groups):
        heads = sorted(claim_id for claim_id in groups[key] if claim_id not in superseded)
        if len(heads) != 1:
            issues.append(
                _issue(
                    "CMV_CURRENT_HEAD_AMBIGUOUS",
                    f"$/claims[key={key}]",
                    f"expected one current head, found {len(heads)}",
                )
            )
            continue
        claim = claims_by_id[heads[0]]
        projection.append(
            {
                "key": key,
                "claim_id": heads[0],
                "claim_type": claim.get("claim_type"),
                "value": claim.get("value"),
                "source_refs": sorted(claim.get("source_refs", [])),
                "approval_eligible": False,
            }
        )
    return projection


def validate_bundle(bundle_dir: Path) -> dict[str, Any]:
    manifest, issues = _load_manifest(bundle_dir)
    if manifest is None:
        return {"status": "INVALID", "errors": _sort_issues(issues)}

    sources_dir = _validate_root_inventory(bundle_dir, issues)
    _validate_manifest_shape(manifest, issues)
    sources_by_id = _validate_sources(bundle_dir, sources_dir, manifest.get("sources"), issues)
    claims_by_id = _validate_claims(manifest.get("claims"), sources_by_id, issues)
    edges = _validate_edges(manifest.get("supersessions"), claims_by_id, issues)
    projection = _build_projection(claims_by_id, edges, issues)

    if issues:
        return {
            "schema_version": manifest.get("schema_version"),
            "status": "INVALID",
            "errors": _sort_issues(issues),
        }

    source_set = [
        {
            "source_id": item["source_id"],
            "path": item["path"],
            "media_type": item["media_type"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        }
        for item in sorted(sources_by_id.values(), key=lambda item: item["source_id"])
    ]
    graph = sorted(edges, key=lambda item: item["edge_id"])
    digests = {
        "manifest_sha256": _sha256_object(manifest),
        "source_set_sha256": _sha256_object(source_set),
        "graph_sha256": _sha256_object(graph),
        "projection_sha256": _sha256_object(projection),
    }
    conformance_core = {"schema_version": SCHEMA_VERSION, **digests}
    conformance_digests = {
        **digests,
        "conformance_sha256": _sha256_object(conformance_core),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": manifest["bundle_id"],
        "scope": manifest["scope"],
        "status": "VERIFIED",
        "counts": {
            "sources": len(sources_by_id),
            "claims": len(claims_by_id),
            "supersessions": len(edges),
            "current_heads": len(projection),
        },
        "digests": conformance_digests,
        "projection": projection,
        "manifest": manifest,
        "sources_by_id": sources_by_id,
        "claims_by_id": claims_by_id,
        "edges": graph,
    }


def _public_base(result: dict[str, Any], command: str) -> dict[str, Any]:
    if result["status"] != "VERIFIED":
        return {
            "command": command,
            "schema_version": result.get("schema_version"),
            "status": "INVALID",
            "errors": result["errors"],
        }
    return {
        "command": command,
        "schema_version": result["schema_version"],
        "bundle_id": result["bundle_id"],
        "scope": result["scope"],
        "status": "VERIFIED",
        "counts": result["counts"],
        "digests": result["digests"],
    }


def command_verify(bundle_dir: Path) -> tuple[dict[str, Any], int]:
    result = validate_bundle(bundle_dir)
    public = _public_base(result, "verify")
    return public, 0 if result["status"] == "VERIFIED" else 2


def command_project(bundle_dir: Path) -> tuple[dict[str, Any], int]:
    result = validate_bundle(bundle_dir)
    public = _public_base(result, "project")
    if result["status"] != "VERIFIED":
        return public, 2
    public["projection"] = result["projection"]
    return public, 0


def command_trace(bundle_dir: Path, claim_id: str) -> tuple[dict[str, Any], int]:
    result = validate_bundle(bundle_dir)
    public = _public_base(result, "trace")
    if result["status"] != "VERIFIED":
        return public, 2
    claims_by_id = result["claims_by_id"]
    claim = claims_by_id.get(claim_id)
    if claim is None:
        return (
            {
                "command": "trace",
                "schema_version": SCHEMA_VERSION,
                "status": "INVALID",
                "errors": [
                    _issue("CMV_CLAIM_NOT_FOUND", "$/claim_id", "claim identifier not found")
                ],
            },
            2,
        )

    key = claim["key"]
    group_ids = sorted(
        candidate_id
        for candidate_id, candidate in claims_by_id.items()
        if candidate["key"] == key
    )
    group_claims = []
    source_ids: set[str] = set()
    for candidate_id in group_ids:
        candidate = claims_by_id[candidate_id]
        refs = sorted(candidate["source_refs"])
        source_ids.update(refs)
        group_claims.append(
            {
                "claim_id": candidate_id,
                "claim_type": candidate["claim_type"],
                "value": candidate["value"],
                "source_refs": refs,
                "approval_eligible": False,
            }
        )
    group_edges = [
        edge
        for edge in result["edges"]
        if edge["superseded_claim_id"] in group_ids
        and edge["superseding_claim_id"] in group_ids
    ]
    source_metadata = [
        {
            "source_id": source_id,
            "path": result["sources_by_id"][source_id]["path"],
            "media_type": result["sources_by_id"][source_id]["media_type"],
            "bytes": result["sources_by_id"][source_id]["bytes"],
            "sha256": result["sources_by_id"][source_id]["sha256"],
        }
        for source_id in sorted(source_ids)
    ]
    final_head = next(item for item in result["projection"] if item["key"] == key)
    public["trace"] = {
        "requested_claim_id": claim_id,
        "key": key,
        "claims": group_claims,
        "supersession_edges": group_edges,
        "sources": source_metadata,
        "final_head_claim_id": final_head["claim_id"],
    }
    return public, 0


def command_demo() -> tuple[dict[str, Any], int]:
    root = Path(__file__).resolve().parents[3]
    bundle_dir = root / "fixtures" / "valid" / "historical-authority"
    result = validate_bundle(bundle_dir)
    public = _public_base(result, "demo")
    if result["status"] != "VERIFIED":
        return public, 2
    authority = [
        item for item in result["projection"] if item["claim_type"] == "historical_authority"
    ]
    public["demo"] = {
        "scenario": "authority-replay",
        "remembered_authority": authority,
        "live_approval": "REQUIRED_FROM_HOST_CONTROL_PLANE",
        "invariant": "REMEMBERED_AUTHORITY_IS_NEVER_LIVE_APPROVAL",
    }
    return public, 0


def _build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="cmverify", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "project"):
        child = subparsers.add_parser(name)
        child.add_argument("bundle_dir")
    trace = subparsers.add_parser("trace")
    trace.add_argument("bundle_dir")
    trace.add_argument("claim_id")
    demo = subparsers.add_parser("demo")
    demo.add_argument("scenario", choices=["authority-replay"])
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _build_parser().parse_args(argv)
        if args.command == "verify":
            output, code = command_verify(Path(args.bundle_dir))
        elif args.command == "project":
            output, code = command_project(Path(args.bundle_dir))
        elif args.command == "trace":
            output, code = command_trace(Path(args.bundle_dir), args.claim_id)
        else:
            output, code = command_demo()
        _emit(output)
        return code
    except SystemExit:
        raise
    except Exception:
        _emit(
            {
                "status": "INVALID",
                "errors": [
                    _issue("CMV_SCHEMA_INVALID", "$internal", "internal failure masked")
                ],
            }
        )
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
