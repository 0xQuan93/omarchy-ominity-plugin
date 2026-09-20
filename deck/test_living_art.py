"""Canonical Living Deck art and witness checks."""

import json
import struct
import unittest
import xml.etree.ElementTree as ET

from deck.build_deck import DECK_DIR, DeckPalette, card_svg
from deck.living_art import (VARIANTS, WITNESS_HEIGHT, WITNESS_WIDTH,
                             motion_spec, render_daily_art)


class LivingArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = json.loads((DECK_DIR / "deck.json").read_text(encoding="utf-8"))
        cls.star = next(card for card in cls.cards if card["title"] == "The Star")

    def test_same_encounter_has_identical_master_and_witness(self):
        encounter = {"weather": {"cpu": 2, "memory": 3, "disk": 1},
                     "machineSignature": {"cpu": "C3", "memory": "M4", "storage": "D2"},
                     "artVariant": 7,
                     "symbol": {"id": "eight-stars", "variant": "glimmer"}}
        first = render_daily_art(self.star, encounter)
        self.assertEqual(first, render_daily_art(self.star, encounter))
        self.assertIn(b'id="living-art-v1"', first[0])
        self.assertEqual(struct.unpack(">II", first[1][16:24]),
                         (WITNESS_WIDTH, WITNESS_HEIGHT))
        self.assertEqual(motion_spec(self.star, encounter),
                         {"schemaVersion": 1, "canonicalPhaseMs": 0,
                          "durationMs": 0, "loop": False, "tracks": []})
        self.assertNotIn(b"<animate", first[0])

    def test_coarse_weather_changes_detail_count_without_changing_card_meaning(self):
        base = {"artVariant": 3, "symbol": {"variant": "glimmer"}}
        images = []
        for key in ("cpu", "memory", "disk"):
            low = dict(base, weather={"cpu": 0, "memory": 0, "disk": 0})
            high = dict(base, weather={"cpu": 0, "memory": 0, "disk": 0})
            high["weather"][key] = 4
            low_svg, _ = render_daily_art(self.star, low)
            high_svg, _ = render_daily_art(self.star, high)
            self.assertNotEqual(low_svg, high_svg, key)
            self.assertIn(b"The Star", low_svg)
            self.assertIn(b"The Star", high_svg)
            images.append((low_svg, high_svg))
        self.assertEqual(len(images), 3)

    def test_all_authored_scenes_accept_variant_layer_and_render_png(self):
        self.assertEqual(len(self.cards), 78)
        namespace = "{http://www.w3.org/2000/svg}"
        for index, card in enumerate(self.cards):
            with self.subTest(card=card["id"]):
                encounter = {"weather": {"cpu": index % 5, "memory": (index + 1) % 5,
                                          "disk": (index + 2) % 5},
                             "artVariant": index % 16,
                             "symbol": {"variant": VARIANTS[index % len(VARIANTS)]}}
                svg, png = render_daily_art(card, encounter)
                root = ET.fromstring(svg)
                overlay = root.find(f".//{namespace}g[@id='living-art-v1']")
                self.assertIsNotNone(overlay)
                self.assertGreaterEqual(len(overlay), 3)
                self.assertEqual(root.attrib["viewBox"], "0 0 280 480")
                self.assertEqual(struct.unpack(">II", png[16:24]), (1400, 2400))
                self.assertTrue(png.endswith(b"\xaeB`\x82"))  # PNG IEND CRC
                self.assertIn(card_svg(card).split('<g clip-path="url(#window)">')[1]
                              .split('</g>\n<path d="M41 410H77')[0].encode("utf-8"), svg)

    def test_palette_recolors_scene_and_overlay_together(self):
        palette = DeckPalette.from_theme("#1a1b26", "#a9b1d6", "#7aa2f7", "#414868")
        encounter = {"weather": {"cpu": 2, "memory": 2, "disk": 2},
                     "symbol": {"variant": "halo"}}
        themed, _ = render_daily_art(self.star, encounter, palette)
        default, _ = render_daily_art(self.star, encounter)
        self.assertNotEqual(themed, default)
        self.assertIn(palette.paper.encode(), themed)
        self.assertIn(palette.gold.encode(), themed)
        self.assertIn(f'stroke="{palette.gold}"'.encode(), themed)

    def test_missing_symbol_metadata_and_invalid_weather(self):
        svg, png = render_daily_art(self.star, {"weather": {"cpu": 2, "memory": 2, "disk": 2}})
        self.assertIn(b'id="living-art-v1"', svg)
        self.assertTrue(png.startswith(b"\x89PNG"))
        with self.assertRaises(ValueError):
            render_daily_art(self.star, {"weather": {"cpu": True}})


if __name__ == "__main__":
    unittest.main()
