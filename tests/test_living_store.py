import tempfile
import unittest
from pathlib import Path

from living_store import commit_legacy, list_daily, statistics


class StatisticsTest(unittest.TestCase):
    def test_streak_gaps_clock_rollback_and_lifetime_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            card = {"id": "major-17-the-star", "title": "The Star", "arcana": "major",
                    "suit": None, "element": None}
            for day in ("2026-09-16", "2026-09-18", "2026-09-19", "2026-09-22"):
                commit_legacy(root, {"day": day, "id": card["id"], "reversed": False}, card)
            records = list_daily(root)
            value = statistics(records, 3, "2026-09-20", deck_cards={card["id"]: card})
            self.assertEqual(value["days"], 4)
            self.assertEqual(value["streak"], {"current": 2, "longest": 2})
            self.assertEqual(value["windows"]["7"]["days"], 3)
            self.assertEqual(value["redrawCount"], 3)
            self.assertEqual(value["perCard"][0]["count"], 4)


if __name__ == "__main__":
    unittest.main()
