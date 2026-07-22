#!/usr/bin/env python3
"""Build or verify the exact clean-room public-file allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "PUBLIC_MANIFEST.json"
IGNORED_DIRECTORY_NAMES = {".git"}


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def classification(relative: str) -> str:
    if relative.startswith("fixtures/"):
        return "synthetic_generator"
    if relative.startswith("tests/data/"):
        return "synthetic_test_data"
    return "new_clean_room"


def is_reparse(path: Path) -> bool:
    info = path.lstat()
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & flag)


def build() -> dict:
    files = []
    candidates = sorted(
        ROOT.rglob("*"),
        key=lambda candidate: candidate.relative_to(ROOT).as_posix().encode("utf-8"),
    )
    for path in candidates:
        relative_parts = path.relative_to(ROOT).parts
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts):
            continue
        if is_reparse(path):
            raise RuntimeError("reparse points and symbolic links are not publishable")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeError("nonregular entries are not publishable")
        if path == OUTPUT:
            continue
        path.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
        relative = path.relative_to(ROOT).as_posix()
        if "__pycache__" in path.parts:
            raise RuntimeError("generated cache is not publishable")
        data = path.read_bytes()
        files.append(
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "origin": classification(relative),
            }
        )
    return {
        "format_version": "1.0",
        "self_excluded": "PUBLIC_MANIFEST.json",
        "release_status": "candidate_licensed_not_published",
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = canonical_bytes(build())
    if args.check:
        actual = OUTPUT.read_bytes() if OUTPUT.is_file() else b""
        status = "PASS" if actual == expected else "FAIL"
        print(
            json.dumps(
                {
                    "status": status,
                    "file_count": len(json.loads(expected)["files"]),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0 if status == "PASS" else 1
    OUTPUT.write_bytes(expected)
    print(
        json.dumps(
            {
                "status": "GENERATED",
                "file_count": len(json.loads(expected)["files"]),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
