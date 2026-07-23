from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "PUBLICATION_RECORD.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class PublicationRecordTests(unittest.TestCase):
    def test_published_version_is_bounded_to_exact_source_and_bundle(self) -> None:
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["format_version"], "1.0")
        self.assertEqual(record["portal_status"], "published")
        self.assertEqual(record["version"], "0.1.0")
        self.assertRegex(record["submitted_source_commit"], COMMIT_RE)
        self.assertEqual(
            record["submitted_source_commit"],
            "3c88e4623a5f18af6f5998e6189f13b733b6b704",
        )
        self.assertRegex(record["submitted_bundle"]["sha256"], SHA256_RE)
        self.assertEqual(
            record["submitted_bundle"]["sha256"],
            "c69e85c2487259d9aa6d8cfbfb4e8f43a50c0752fa444ca2bbefa08459c6c999",
        )
        self.assertEqual(record["submitted_bundle"]["bytes"], 116170)
        self.assertEqual(
            record["directory_url"],
            "https://chatgpt.com/plugins/plugins_6a616d0d67e88191844c7fe0bb2b2ac5",
        )
        self.assertIn("not OpenAI endorsement", record["scope_note"])


if __name__ == "__main__":
    unittest.main()
