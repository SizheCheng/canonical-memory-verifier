from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "verify-canonical-memory" / "scripts" / "cmverify.py"
SCHEMA = ROOT / "skills" / "verify-canonical-memory" / "references" / "bundle.schema.json"
INDEX = ROOT / "fixtures" / "fixture-index.json"
DATA = ROOT / "tests" / "data"

SPEC = importlib.util.spec_from_file_location("cmverify_candidate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CMV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CMV)


class CanonicalMemoryVerifierTests(unittest.TestCase):
    def cli(self, *args: str) -> tuple[int, dict]:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(completed.stderr, "")
        return completed.returncode, json.loads(completed.stdout)

    def test_schema_document_is_strict_json(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$defs"]["claim"]["properties"]["approval_eligible"]["const"], False)

    def test_every_declared_fixture_has_expected_result(self) -> None:
        rows = json.loads(INDEX.read_text(encoding="utf-8"))["fixtures"]
        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            with self.subTest(row=row["fixture"]):
                code, output = self.cli("verify", f"fixtures/{row['fixture']}")
                self.assertEqual(output["status"], row["expected_status"])
                self.assertEqual(code, 0 if row["expected_status"] == "VERIFIED" else 2)
                actual_codes = {item["code"] for item in output.get("errors", [])}
                self.assertTrue(set(row["required_error_codes"]).issubset(actual_codes))

    def test_projection_uses_only_the_superseding_head(self) -> None:
        code, output = self.cli("project", "fixtures/valid/supersession-chain")
        self.assertEqual(code, 0)
        self.assertEqual([item["claim_id"] for item in output["projection"]], ["clm_target_new"])
        self.assertIs(output["projection"][0]["approval_eligible"], False)

    def test_trace_reaches_final_head_and_source_level_evidence(self) -> None:
        code, output = self.cli(
            "trace",
            "fixtures/valid/supersession-chain",
            "clm_target_old",
        )
        self.assertEqual(code, 0)
        trace = output["trace"]
        self.assertEqual(trace["final_head_claim_id"], "clm_target_new")
        self.assertEqual(len(trace["sources"]), 2)
        self.assertTrue(all(item["approval_eligible"] is False for item in trace["claims"]))

    def test_trace_missing_claim_fails_closed(self) -> None:
        code, output = self.cli("trace", "fixtures/valid/basic", "clm_missing")
        self.assertEqual(code, 2)
        self.assertEqual(output["errors"][0]["code"], "CMV_CLAIM_NOT_FOUND")

    def test_authority_demo_requires_live_host_approval(self) -> None:
        code, output = self.cli("demo", "authority-replay")
        self.assertEqual(code, 0)
        self.assertEqual(output["demo"]["live_approval"], "REQUIRED_FROM_HOST_CONTROL_PLANE")
        remembered = output["demo"]["remembered_authority"]
        self.assertEqual(len(remembered), 1)
        self.assertIs(remembered[0]["approval_eligible"], False)

    def test_output_is_byte_deterministic_and_path_free(self) -> None:
        first = subprocess.check_output(
            [sys.executable, str(SCRIPT), "verify", "fixtures/valid/basic"],
            cwd=ROOT,
        )
        second = subprocess.check_output(
            [sys.executable, str(SCRIPT), "verify", "fixtures/valid/basic"],
            cwd=ROOT,
        )
        self.assertEqual(first, second)
        self.assertNotIn(str(ROOT).encode("utf-8"), first)
        self.assertNotIn(b"fixtures/valid/basic", first)

    def test_manifest_whitespace_does_not_change_semantic_digest(self) -> None:
        original = CMV.validate_bundle(ROOT / "fixtures" / "valid" / "basic")
        reformatted = CMV.validate_bundle(DATA / "basic-pretty")
        self.assertEqual(original["digests"], reformatted["digests"])

    def test_duplicate_json_key_is_rejected(self) -> None:
        result = CMV.validate_bundle(DATA / "duplicate-json-key")
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["errors"][0]["code"], "CMV_INVALID_JSON")

    def test_undeclared_source_file_is_rejected(self) -> None:
        result = CMV.validate_bundle(DATA / "undeclared-file")
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("CMV_UNDECLARED_FILE", codes)

    def test_cli_usage_error_is_json(self) -> None:
        code, output = self.cli("verify")
        self.assertEqual(code, 64)
        self.assertEqual(output["status"], "INVALID")

    def test_cli_usage_error_does_not_echo_arguments(self) -> None:
        sensitive_argument = str(ROOT / "private" / "secret.txt")
        code, output = self.cli(
            "verify",
            "fixtures/valid/basic",
            sensitive_argument,
        )
        self.assertEqual(code, 64)
        self.assertEqual(output["errors"][0]["detail"], "invalid command-line arguments")
        serialized = json.dumps(output, ensure_ascii=False)
        self.assertNotIn(sensitive_argument, serialized)
        self.assertNotIn(str(ROOT), serialized)

    def test_maximum_acyclic_graph_does_not_recurse(self) -> None:
        claims = {
            f"clm_node_{index:04d}": {"key": "long.chain"}
            for index in range(CMV.MAX_RECORDS)
        }
        edges = [
            {
                "superseded_claim_id": f"clm_node_{index:04d}",
                "superseding_claim_id": f"clm_node_{index + 1:04d}",
            }
            for index in range(CMV.MAX_RECORDS - 1)
        ]
        self.assertFalse(CMV._detect_cycle(edges, claims))
        edges.append(
            {
                "superseded_claim_id": f"clm_node_{CMV.MAX_RECORDS - 1:04d}",
                "superseding_claim_id": "clm_node_0000",
            }
        )
        self.assertTrue(CMV._detect_cycle(edges, claims))

    def test_cli_writes_utf8_independently_of_console_encoding(self) -> None:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "latin-1"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "project",
                "tests/data/unicode",
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        self.assertIn(b"caf\xc3\xa9", completed.stdout)
        self.assertEqual(json.loads(completed.stdout.decode("utf-8"))["status"], "VERIFIED")

    def test_string_limits_use_json_schema_code_points(self) -> None:
        self.assertTrue(CMV._bounded_string("é" * CMV.MAX_VALUE_BYTES, 1, CMV.MAX_VALUE_BYTES))
        self.assertFalse(
            CMV._bounded_string("é" * (CMV.MAX_VALUE_BYTES + 1), 1, CMV.MAX_VALUE_BYTES)
        )

    def test_directory_inventory_stops_at_bound(self) -> None:
        class FakeEntry:
            def __init__(self, index: int) -> None:
                self.path = str(ROOT / f"synthetic-{index}")

        class FakeScandir:
            def __enter__(self):
                return iter(
                    FakeEntry(index)
                    for index in range(CMV.MAX_DIRECTORY_ENTRIES + 1)
                )

            def __exit__(self, exc_type, exc_value, traceback):
                return False

        with mock.patch.object(CMV.os, "scandir", return_value=FakeScandir()):
            entries, error = CMV._bounded_directory_entries(
                ROOT, CMV.MAX_DIRECTORY_ENTRIES
            )
        self.assertEqual(len(entries), CMV.MAX_DIRECTORY_ENTRIES)
        self.assertEqual(error, "directory entry limit exceeded")

    def test_unsafe_source_path_forms_are_rejected(self) -> None:
        for value in (
            "../outside.txt",
            "sources/../outside.txt",
            "sources\\outside.txt",
            "C:/outside.txt",
            "sources/nested/outside.txt",
            "sources/file.txt:stream",
        ):
            with self.subTest(value=value):
                self.assertFalse(CMV._matches(value, "source_path"))

    def test_name_normalization_is_casefolded_nfc(self) -> None:
        self.assertEqual(
            CMV._normal_name("sources/Évidence.txt"),
            CMV._normal_name("SOURCES/E\u0301VIDENCE.TXT"),
        )

    def test_reparse_sources_directory_fails_closed(self) -> None:
        original = CMV._is_reparse

        def fake_is_reparse(path: Path) -> bool:
            return path.name == "sources" or original(path)

        with mock.patch.object(CMV, "_is_reparse", side_effect=fake_is_reparse):
            result = CMV.validate_bundle(ROOT / "fixtures" / "valid" / "basic")
        self.assertEqual(result["status"], "INVALID")
        self.assertIn(
            "CMV_NONREGULAR_PATH",
            {item["code"] for item in result["errors"]},
        )


if __name__ == "__main__":
    unittest.main()
