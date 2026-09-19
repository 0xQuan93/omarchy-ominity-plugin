import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "ominity.py"
spec = importlib.util.spec_from_file_location("ominity", MODULE_PATH)
ominity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ominity)


class DrawTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        patches = [patch.object(ominity, "STATE_ROOT", root), patch.object(ominity, "STATE_FILE", root / "reading.json")]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_daily_draw_is_stable_until_explicit_redraw(self):
        first = ominity.run("today")
        again = ominity.run("today")
        self.assertEqual(first["reading"], again["reading"])
        self.assertEqual(again["historyCount"], 1)
        redraw = ominity.run("redraw")
        self.assertNotEqual(first["reading"]["id"], redraw["reading"]["id"])
        self.assertEqual(redraw["historyCount"], 2)
        self.assertTrue(redraw["reading"]["redraw"])
        self.assertEqual(ominity.run("today")["reading"], redraw["reading"])

    def test_widget_toggle_does_not_draw(self):
        self.assertIsNone(ominity.run("state")["reading"])
        self.assertTrue(ominity.run("widget-toggle")["widget"])
        self.assertIsNone(ominity.run("state")["reading"])
        self.assertFalse(ominity.run("widget-toggle")["widget"])

    def test_corrupt_state_is_recovered_without_external_effects(self):
        ominity.STATE_FILE.write_text("broken", encoding="utf-8")
        result = ominity.run("today")
        self.assertTrue(result["ok"])
        self.assertEqual(ominity.STATE_FILE.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
