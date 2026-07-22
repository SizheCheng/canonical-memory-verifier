#!/usr/bin/env python3
"""Fail closed on obvious private identifiers, secrets, and binary payloads."""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".patch", ".py", ".svg", ".txt", ".yml", ".yaml"}
TEXT_FILENAMES = {".gitattributes", ".gitignore", "LICENSE", "NOTICE"}
IGNORED_DIRECTORY_NAMES = {".git"}
PATTERNS = [
    ("absolute_windows_user_path", re.compile(r"C:" + r"\\Users\\", re.IGNORECASE)),
    ("chat_share_url", re.compile(r"chatgpt\.com/" + r"share/", re.IGNORECASE)),
    ("codex_task_uri", re.compile(r"codex:" + r"//threads/", re.IGNORECASE)),
    ("conversation_uri", re.compile(r"chatgpt-" + r"conversation://", re.IGNORECASE)),
    ("uuid", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)),
    ("openai_secret", re.compile(r"\bs" + r"k-[A-Za-z0-9_-]{16,}\b")),
    ("github_token", re.compile(r"\bgh" + r"[pousr]_[A-Za-z0-9]{20,}\b")),
]


def is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & flag)


def main() -> int:
    violations: list[dict[str, str]] = []
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT).as_posix()
        if any(part in IGNORED_DIRECTORY_NAMES for part in path.relative_to(ROOT).parts):
            continue
        if is_reparse(path):
            violations.append({"path": relative, "kind": "reparse_or_symlink"})
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            violations.append({"path": relative, "kind": "nonregular_entry"})
            continue
        if "__pycache__" in path.parts:
            violations.append({"path": relative, "kind": "generated_cache"})
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_FILENAMES:
            violations.append({"path": relative, "kind": "undeclared_binary_or_extension"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            violations.append({"path": relative, "kind": "non_utf8_text"})
            continue
        for kind, pattern in PATTERNS:
            if pattern.search(text):
                violations.append({"path": relative, "kind": kind})
    status = "PASS" if not violations else "FAIL"
    print(json.dumps({"status": status, "violations": violations}, sort_keys=True, separators=(",", ":")))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
