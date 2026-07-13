#!/usr/bin/env python3
"""Contract tests for the production generate pipeline (no theater).

Runs against the real scripts/generate.py module and regenerated artifacts.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# Load generate.py as module without requiring package layout
_spec = importlib.util.spec_from_file_location("generate", ROOT / "scripts" / "generate.py")
gen = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(gen)


class TestUISober(unittest.TestCase):
    def test_dark_ui_is_greyscale(self):
        self.assertTrue(gen.ui_colors_are_sober(gen.UI_DARK))

    def test_light_ui_is_greyscale(self):
        self.assertTrue(gen.ui_colors_are_sober(gen.UI_LIGHT))

    def test_rainbow_would_fail(self):
        bad = dict(gen.UI_DARK)
        bad["key"] = (227, 179, 65)  # yellow — not sober
        self.assertFalse(gen.ui_colors_are_sober(bad))


class TestPureAscii(unittest.TestCase):
    def test_rejects_block_chars(self):
        with self.assertRaises(ValueError):
            gen.assert_pure_ascii("hello ▀ world")

    def test_rejects_braille(self):
        with self.assertRaises(ValueError):
            gen.assert_pure_ascii("hello ⣿ world")

    def test_accepts_printable_ascii(self):
        gen.assert_pure_ascii("XYZ $$@# MW&8%B\n.:-=+*")


class TestArtifacts(unittest.TestCase):
    """Artifacts must exist after generate; verify real file properties."""

    def test_cards_exist_and_nonempty(self):
        for name in ("card-dark.png", "card-light.png", "ascii-art.txt"):
            p = ROOT / name
            self.assertTrue(p.exists(), f"missing {name}")
            self.assertGreater(p.stat().st_size, 100, f"empty {name}")

    def test_ascii_art_file_is_pure(self):
        text = (ROOT / "ascii-art.txt").read_text(encoding="utf-8")
        gen.assert_pure_ascii(text)
        self.assertTrue(any(c in text for c in "@#$%&*MW"))

    def test_readme_is_card_only(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("card-dark.png", readme)
        self.assertNotIn("Now shipping", readme)
        self.assertNotIn("### Stack", readme)
        self.assertNotIn("Off-hours", readme)
        # no long bio tables
        self.assertLess(len(readme.splitlines()), 20)

    def test_card_ui_region_low_saturation(self):
        from PIL import Image

        im = Image.open(ROOT / "card-dark.png").convert("RGB")
        w, h = im.size
        # right half = text panel
        sat = n = 0
        for y in range(20, h - 20, 3):
            for x in range(w // 2, w - 10, 3):
                r, g, b = im.getpixel((x, y))
                if r + g + b < 35:
                    continue
                n += 1
                if max(r, g, b) - min(r, g, b) > 40:
                    sat += 1
        ratio = sat / max(1, n)
        self.assertLess(ratio, 0.05, f"text region too colorful: {ratio:.3f}")

    def test_no_palette_strip_bright_primaries(self):
        """Palette dots were high-chroma squares; ensure absent near art bottom."""
        from PIL import Image

        im = Image.open(ROOT / "card-dark.png").convert("RGB")
        w, h = im.size
        # bottom band left half
        primary = 0
        for y in range(h - 40, h - 5):
            for x in range(20, w // 2, 2):
                r, g, b = im.getpixel((x, y))
                # classic palette primaries: pure-ish red/orange/green/blue
                if max(r, g, b) > 200 and min(r, g, b) < 80 and max(r, g, b) - min(r, g, b) > 120:
                    primary += 1
        self.assertLess(primary, 15, f"palette-like pixels under art: {primary}")


class TestLinkedInFull(unittest.TestCase):
    def test_linkedin_includes_slug_id(self):
        rows = gen.info_rows()
        linked = [r for r in rows if r[0] == "field" and r[1] == "LinkedIn"][0]
        self.assertIn("a10013345", linked[2])


if __name__ == "__main__":
    unittest.main()
