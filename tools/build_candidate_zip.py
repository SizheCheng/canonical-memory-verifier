#!/usr/bin/env python3
"""Build a deterministic local-review ZIP from PUBLIC_MANIFEST.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_MANIFEST = ROOT / "PUBLIC_MANIFEST.json"
IGNORED_DIRECTORY_NAMES = {".git"}
MANIFEST_FIELDS = {"format_version", "self_excluded", "release_status", "files"}
FILE_FIELDS = {"path", "bytes", "sha256", "origin"}
ALLOWED_ORIGINS = {"new_clean_room", "synthetic_generator", "synthetic_test_data"}
ALLOWED_RELEASE_STATUSES = {"candidate_licensed_not_published"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKeyError(ValueError):
    pass


def object_pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key: {key}")
        result[key] = value
    return result


def fail(message: str) -> int:
    print(
        json.dumps(
            {"status": "FAIL", "error": message},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 1


def is_reparse(path: Path) -> bool:
    info = path.lstat()
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & flag)


def safe_relative(value: str) -> bool:
    pure = PurePosixPath(value)
    return (
        isinstance(value, str)
        and value != ""
        and not pure.is_absolute()
        and len(pure.parts) > 0
        and all(part not in {"", ".", ".."} for part in pure.parts)
        and "\\" not in value
        and ":" not in value
    )


def load_and_validate_manifest(data: bytes) -> dict:
    try:
        manifest = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=object_pairs_no_duplicates,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError("public manifest is not strict JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_FIELDS:
        raise ValueError("public manifest fields are invalid")
    if manifest.get("format_version") != "1.0":
        raise ValueError("unsupported public manifest format")
    if manifest.get("self_excluded") != "PUBLIC_MANIFEST.json":
        raise ValueError("public manifest self exclusion is invalid")
    if manifest.get("release_status") not in ALLOWED_RELEASE_STATUSES:
        raise ValueError("public manifest release status is invalid")
    declared = manifest.get("files")
    if not isinstance(declared, list) or not declared or len(declared) > 10000:
        raise ValueError("public manifest file inventory is invalid")
    seen: set[str] = set()
    seen_normalized: set[str] = set()
    for item in declared:
        if not isinstance(item, dict) or set(item) != FILE_FIELDS:
            raise ValueError("public manifest file record is invalid")
        relative = item.get("path")
        if not isinstance(relative, str) or not safe_relative(relative):
            raise ValueError("unsafe public manifest member")
        if relative == "PUBLIC_MANIFEST.json" or relative in seen:
            raise ValueError("duplicate public manifest member")
        normalized = unicodedata.normalize("NFC", relative).casefold()
        if normalized in seen_normalized:
            raise ValueError("normalized public manifest member collision")
        size = item.get("bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ValueError("public manifest byte count is invalid")
        digest = item.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError("public manifest SHA-256 is invalid")
        if item.get("origin") not in ALLOWED_ORIGINS:
            raise ValueError("public manifest origin is invalid")
        seen.add(relative)
        seen_normalized.add(normalized)
    return manifest


def path_chain_is_regular(path: Path) -> bool:
    current = ROOT
    if is_reparse(current):
        return False
    for part in path.relative_to(ROOT).parts:
        current = current / part
        if is_reparse(current):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        pass
    else:
        return fail("output must be outside the plugin root")

    if is_reparse(PUBLIC_MANIFEST) or not PUBLIC_MANIFEST.is_file():
        return fail("public manifest is missing or nonregular")
    manifest_bytes = PUBLIC_MANIFEST.read_bytes()
    try:
        manifest = load_and_validate_manifest(manifest_bytes)
    except ValueError as exc:
        return fail(str(exc))
    declared = manifest["files"]
    members = ["PUBLIC_MANIFEST.json"] + [item["path"] for item in declared]

    actual_members: set[str] = set()
    for path in sorted(ROOT.rglob("*")):
        relative_parts = path.relative_to(ROOT).parts
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts):
            continue
        if is_reparse(path):
            return fail("reparse point or symbolic link in plugin tree")
        if path.is_dir():
            continue
        if not path.is_file():
            return fail("nonregular entry in plugin tree")
        path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
        actual_members.add(path.relative_to(ROOT).as_posix())
    if actual_members != set(members):
        return fail("plugin tree differs from public manifest inventory")

    for item in declared:
        path = ROOT / Path(item["path"])
        if not path.is_file() or not path_chain_is_regular(path):
            return fail("declared member is missing or nonregular")
        data = path.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            return fail("public manifest byte binding mismatch")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for relative in sorted(members):
                data = (
                    manifest_bytes
                    if relative == "PUBLIC_MANIFEST.json"
                    else (ROOT / Path(relative)).read_bytes()
                )
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                info.flag_bits |= 0x800
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()

    with zipfile.ZipFile(output, "r") as archive:
        actual = archive.namelist()
        if actual != sorted(members) or len(actual) != len(set(actual)):
            return fail("ZIP member inventory mismatch")
        if archive.testzip() is not None:
            return fail("ZIP CRC verification failed")

    data = output.read_bytes()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "member_count": len(members),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "submission_authorized": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
