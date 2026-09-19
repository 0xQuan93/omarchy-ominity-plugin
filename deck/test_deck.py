"""Asset contract checks for the complete Ominity deck."""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from deck.build_deck import CARD_DIR, DECK_DIR, RANKS, ROOT, card_back_svg, card_svg, make_deck, numbered_scene


MAJOR_TITLES = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower",
    "The Star", "The Moon", "The Sun", "Judgement", "The World",
]
SUITS = ["Wands", "Cups", "Swords", "Pentacles"]


class DeckContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = json.loads((DECK_DIR / "deck.json").read_text())

    def test_complete_traditional_structure(self):
        cards = self.cards
        self.assertEqual(len(cards), 78)
        self.assertEqual([card["title"] for card in cards[:22]], MAJOR_TITLES)
        self.assertEqual([card["number"] for card in cards[:22]], list(range(22)))
        for suit in SUITS:
            found = [card for card in cards if card["suit"] == suit]
            self.assertEqual([card["title"] for card in found], [f"{rank} of {suit}" for rank in RANKS])
            self.assertEqual([card["number"] for card in found], list(range(1, 15)))

    def test_each_reading_and_art_is_distinct_and_complete(self):
        cards = self.cards
        self.assertEqual(len({card["id"] for card in cards}), 78)
        self.assertEqual(len({card["art"] for card in cards}), 78)
        self.assertEqual(len({card["interpretation"] for card in cards}), 78)
        self.assertEqual(len({card["reflection"] for card in cards}), 78)
        for card in cards:
            with self.subTest(card=card["id"]):
                self.assertIn(card["arcana"], ("major", "minor"))
                self.assertGreaterEqual(len(card["title"]), 5)
                for field in ("upright", "reversed", "interpretation", "reflection"):
                    self.assertGreater(len(card[field]), 8)
                self.assertEqual(len(card["keywords"]), 3)
                self.assertEqual(len(card["symbols"]), 3)
                self.assertEqual(card["art"], f"assets/cards/{card['id']}.svg")
                asset = ROOT / card["art"]
                self.assertTrue(asset.is_file())
                root = ET.parse(asset).getroot()
                self.assertEqual(root.attrib["viewBox"], "0 0 280 480")
                self.assertIn(card["title"], asset.read_text())
                self.assertEqual(asset.read_text().strip(), card_svg(card))

    def test_generated_files_match_source(self):
        self.assertEqual(self.cards, make_deck())
        self.assertEqual(len(list(CARD_DIR.glob("*.svg"))), 78)
        guide = json.loads((DECK_DIR / "guide.json").read_text())
        self.assertEqual(set(guide["suits"]), set(SUITS))
        self.assertIn("reversals", guide)
        self.assertIn("daily_reflection", guide)
        back = ROOT / "assets" / "card-back.svg"
        self.assertEqual(back.read_text().strip(), card_back_svg())
        self.assertEqual(ET.parse(back).getroot().attrib["viewBox"], "0 0 280 480")

    def test_original_illustrations_stay_vector_and_numbered_scenes_are_distinct(self):
        namespace = "{http://www.w3.org/2000/svg}"
        scenes = {numbered_scene(suit, number) for suit in SUITS for number in range(1, 11)}
        self.assertEqual(len(scenes), 40)
        for asset in [*(CARD_DIR.glob("*.svg")), ROOT / "assets" / "card-back.svg"]:
            with self.subTest(asset=asset.name):
                svg = ET.parse(asset).getroot()
                self.assertIsNone(svg.find(f".//{namespace}image"))
                self.assertIsNone(svg.find(f".//{namespace}filter"))
                self.assertEqual(svg.attrib["viewBox"], "0 0 280 480")

    def test_svg_text_uses_qtsvg_compatible_font_attributes(self):
        namespace = "{http://www.w3.org/2000/svg}"
        expected = {"number": "Noto Serif", "title": "Noto Serif",
                    "small": "Noto Sans", "label": "Noto Sans"}
        for asset in CARD_DIR.glob("*.svg"):
            with self.subTest(asset=asset.name):
                texts = ET.parse(asset).getroot().findall(f".//{namespace}text")
                self.assertEqual({node.attrib.get("class") for node in texts}, set(expected))
                for node in texts:
                    self.assertEqual(node.attrib["font-family"], expected[node.attrib["class"]])
                    self.assertTrue(node.attrib["font-size"].isdigit())
                    self.assertIn(node.attrib["font-weight"], ("400", "600"))


if __name__ == "__main__":
    unittest.main()
