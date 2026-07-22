from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_candidate_zip.py"
PUBLIC_MANIFEST = ROOT / "PUBLIC_MANIFEST.json"

SPEC = importlib.util.spec_from_file_location("cmv_package_builder", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


class PublicPackageTests(unittest.TestCase):
    def current_manifest(self) -> dict:
        return json.loads(PUBLIC_MANIFEST.read_text(encoding="utf-8"))

    def test_current_manifest_is_strict_and_publishable(self) -> None:
        parsed = PACKAGE.load_and_validate_manifest(PUBLIC_MANIFEST.read_bytes())
        self.assertEqual(parsed["release_status"], "candidate_licensed_not_published")
        ordered_paths = [item["path"] for item in parsed["files"]]
        self.assertEqual(
            ordered_paths,
            sorted(ordered_paths, key=lambda path: path.encode("utf-8")),
        )
        paths = set(ordered_paths)
        self.assertIn("LICENSE", paths)
        self.assertIn(".github/workflows/ci.yml", paths)

    def test_duplicate_manifest_key_is_rejected(self) -> None:
        data = b'{"format_version":"1.0","format_version":"1.0"}'
        with self.assertRaisesRegex(ValueError, "strict JSON"):
            PACKAGE.load_and_validate_manifest(data)

    def test_unknown_origin_is_rejected(self) -> None:
        manifest = self.current_manifest()
        manifest["files"][0]["origin"] = "unreviewed_private_source"
        data = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "origin"):
            PACKAGE.load_and_validate_manifest(data)

    def test_boolean_byte_count_is_rejected(self) -> None:
        manifest = self.current_manifest()
        manifest["files"][0]["bytes"] = True
        data = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "byte count"):
            PACKAGE.load_and_validate_manifest(data)

    def test_unsafe_manifest_path_is_rejected(self) -> None:
        manifest = self.current_manifest()
        manifest["files"][0]["path"] = "../private.txt"
        data = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "unsafe"):
            PACKAGE.load_and_validate_manifest(data)

    def test_review_zip_is_byte_deterministic(self) -> None:
        first = ROOT.parent / ".cmv-package-test-first.zip"
        second = ROOT.parent / ".cmv-package-test-second.zip"
        try:
            for output in (first, second):
                captured = io.StringIO()
                with mock.patch.object(
                    sys, "argv", [str(SCRIPT), "--output", str(output)]
                ), redirect_stdout(captured):
                    code = PACKAGE.main()
                self.assertEqual(code, 0, captured.getvalue())
                self.assertEqual(json.loads(captured.getvalue())["status"], "BUILT")
            self.assertEqual(first.read_bytes(), second.read_bytes())
        finally:
            first.unlink(missing_ok=True)
            second.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
