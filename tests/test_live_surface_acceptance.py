from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "LIVE_SURFACE_ACCEPTANCE.json"


class LiveSurfaceAcceptanceTests(unittest.TestCase):
    def test_published_listing_is_separate_from_runtime_acceptance(self) -> None:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["format_version"], "1.0")
        self.assertEqual(record["version"], "0.1.0")
        self.assertEqual(record["directory_listing"]["status"], "pass")
        self.assertTrue(record["directory_listing"]["installed"])
        self.assertTrue(record["directory_listing"]["published_instructions_visible"])
        self.assertEqual(record["runtime_invocation"]["status"], "fail")
        self.assertEqual(
            record["runtime_invocation"]["error_code"],
            "CMV_PUBLISHED_SKILL_RUNTIME_UNAVAILABLE",
        )
        self.assertEqual(
            record["runtime_invocation"]["root_cause_status"],
            "not_established",
        )
        self.assertEqual(len(record["runtime_invocation"]["cases"]), 3)
        self.assertEqual(
            record["codex_cli_marketplace_snapshot"]["matching_entries"], 0
        )

    def test_record_excludes_private_account_and_chat_identifiers(self) -> None:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertFalse(record["privacy"]["conversation_ids_recorded"])
        self.assertFalse(record["privacy"]["account_email_recorded"])
        self.assertFalse(record["privacy"]["organization_id_recorded"])


if __name__ == "__main__":
    unittest.main()
