from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "integrations" / "codex-external-agent-memory-import"
PIN = INTEGRATION / "PINNED_CODEX_COMMIT.txt"
PATCH = INTEGRATION / "codex-import-preflight.patch"
WORKFLOW = ROOT / ".github" / "workflows" / "upstream-codex-seam.yml"


class UpstreamReproductionTests(unittest.TestCase):
    def test_upstream_revision_is_an_exact_git_object_id(self) -> None:
        commit = PIN.read_text(encoding="utf-8").strip()
        self.assertRegex(commit, r"\A[0-9a-f]{40}\Z")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(workflow.count(commit), 2)
        self.assertNotIn("@main", workflow)

    def test_patch_touches_only_the_declared_import_boundary(self) -> None:
        text = PATCH.read_text(encoding="utf-8")
        paths = set(re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE))
        self.assertEqual(
            paths,
            {
                (
                    "codex-rs/external-agent-migration/src/memory_import.rs",
                    "codex-rs/external-agent-migration/src/memory_import.rs",
                ),
                (
                    "codex-rs/external-agent-migration/src/memory_import_tests.rs",
                    "codex-rs/external-agent-migration/src/memory_import_tests.rs",
                ),
            },
        )
        self.assertNotIn("/dev/null", text)

    def test_preflight_precedes_destructive_replacement(self) -> None:
        text = PATCH.read_text(encoding="utf-8")
        preflight = text.index("+    preflight(project_key, project_cwd, &source_files)?;")
        removal = text.index("     remove_project_resources(codex_home, project_key)?;")
        self.assertLess(preflight, removal)

    def test_rejection_test_checks_preserved_bytes(self) -> None:
        text = PATCH.read_text(encoding="utf-8")
        self.assertIn("preflight_failure_preserves_previous_imported_project", text)
        self.assertIn("CMV_SOURCE_HASH_MISMATCH", text)
        self.assertIn('b"previous verified memory"', text)
        self.assertIn("read preserved scope", text)


if __name__ == "__main__":
    unittest.main()
