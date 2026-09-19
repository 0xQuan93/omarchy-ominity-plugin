"""Behavior checks for Ominity's live theme art cache."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from deck.build_deck import DeckPalette, _contrast
from deck.theme_deck import render_theme


TOKYO = ("#1a1b26", "#a9b1d6", "#7aa2f7", "#414868")
LIGHT = ("#f8f3e8", "#242a31", "#af582e", "#948c82")


class ThemedDeckTests(unittest.TestCase):
    def test_palette_keeps_text_legible_and_suits_distinct(self):
        for colors in (TOKYO, LIGHT, ("#ffffff", "#ffffff", "#ffffff", "#ffffff")):
            with self.subTest(colors=colors):
                palette = DeckPalette.from_theme(*colors)
                self.assertGreaterEqual(_contrast(palette.ink, palette.paper), 7)
                self.assertGreaterEqual(_contrast(palette.gold, palette.paper), 4.5)
                self.assertEqual(len(set(palette.accents.values())), 4)
                for tone in palette.accents.values():
                    self.assertGreaterEqual(_contrast(tone, palette.paper), 3)

    def test_complete_decks_are_cached_per_palette(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = render_theme(*TOKYO, cache_home=home)
            self.assertTrue((first / ".complete").is_file())
            self.assertEqual(len(list((first / "assets/cards").glob("*.svg"))), 78)
            face = first / "assets/cards/major-00-the-fool.svg"
            back = first / "assets/card-back.svg"
            self.assertEqual(ET.parse(face).getroot().attrib["viewBox"], "0 0 280 480")
            self.assertEqual(ET.parse(back).getroot().attrib["viewBox"], "0 0 280 480")
            self.assertEqual(render_theme(*TOKYO, cache_home=home), first)
            second = render_theme(*LIGHT, cache_home=home)
            self.assertNotEqual(first, second)
            self.assertNotEqual(face.read_text(), (second / "assets/cards/major-00-the-fool.svg").read_text())
            self.assertNotEqual(back.read_text(), (second / "assets/card-back.svg").read_text())

    def test_rejects_invalid_color_without_writing_deck(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            with self.assertRaises(ValueError):
                render_theme("red", *TOKYO[1:], cache_home=home)
            self.assertFalse((home / "ominity").exists())


if __name__ == "__main__":
    unittest.main()
