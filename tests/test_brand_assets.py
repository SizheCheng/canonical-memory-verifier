from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MIN_DIMENSION = 48
MAX_DIMENSION = 4096
FORBIDDEN_ELEMENTS = {"script", "image", "foreignObject"}


def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


class BrandAssetTests(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    def asset_path(self, value: str) -> Path:
        self.assertTrue(value.startswith("./assets/"))
        pure = PurePosixPath(value)
        self.assertFalse(pure.is_absolute())
        self.assertNotIn("..", pure.parts)
        return ROOT.joinpath(*pure.parts)

    def assert_safe_square_svg(self, path: Path) -> None:
        data = path.read_bytes()
        self.assertLessEqual(len(data), MAX_IMAGE_BYTES)
        text = data.decode("utf-8", errors="strict")
        root = ET.fromstring(text)
        self.assertEqual(local_name(root.tag), "svg")

        width = float(root.attrib["width"])
        height = float(root.attrib["height"])
        self.assertEqual(width, height)
        self.assertGreaterEqual(width, MIN_DIMENSION)
        self.assertLessEqual(width, MAX_DIMENSION)

        view_box = [float(item) for item in root.attrib["viewBox"].split()]
        self.assertEqual(len(view_box), 4)
        self.assertEqual(view_box[2], view_box[3])
        self.assertGreaterEqual(view_box[2], MIN_DIMENSION)

        for element in root.iter():
            self.assertNotIn(local_name(element.tag), FORBIDDEN_ELEMENTS)
            for name, value in element.attrib.items():
                self.assertFalse(local_name(name).lower().endswith("href"))
                self.assertNotIn("url(", value.lower())
                self.assertNotIn("data:", value.lower())

    def test_required_brand_assets_are_safe_square_svgs(self) -> None:
        interface = self.manifest()["interface"]
        for field in ("logo", "logoDark", "composerIcon"):
            path = self.asset_path(interface[field])
            self.assertEqual(path.suffix, ".svg")
            self.assertTrue(path.is_file())
            self.assert_safe_square_svg(path)

    def test_brand_color_matches_canonical_ink(self) -> None:
        self.assertEqual(self.manifest()["interface"]["brandColor"], "#17233E")


if __name__ == "__main__":
    unittest.main()
