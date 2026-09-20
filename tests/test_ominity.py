import importlib.util
import json
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
        with patch.object(ominity, "capacity_signature", return_value={"cpu": "C3", "memory": "M4", "storage": "D4"}) as signature, patch.object(ominity, "weather_buckets", return_value={"cpu": 2, "memory": 1, "disk": 3}) as weather:
            first = ominity.run("today")
            again = ominity.run("today")
            redraw = ominity.run("redraw")
        self.assertEqual(signature.call_count, 1)
        self.assertEqual(weather.call_count, 1)
        self.assertEqual(first["reading"], again["reading"])
        self.assertEqual(again["historyCount"], 1)
        self.assertNotEqual(first["reading"]["id"], redraw["reading"]["id"])
        self.assertEqual(redraw["historyCount"], 2)
        self.assertTrue(redraw["reading"]["redraw"])
        self.assertEqual(ominity.run("today")["reading"], redraw["reading"])
        self.assertEqual(first["reading"]["experience"]["weather"], redraw["reading"]["experience"]["weather"])
        self.assertEqual(first["reading"]["experience"]["machineSignature"], redraw["reading"]["experience"]["machineSignature"])
        stored = ominity.STATE_FILE.read_text()
        self.assertNotIn("MemTotal", stored)
        self.assertNotIn(json.loads((ominity.STATE_ROOT / "identity.json").read_text())["record"]["payload"]["seed"], stored)
        self.assertEqual(first["reading"]["time"]["localDate"], first["day"])

    def test_widget_toggle_does_not_draw(self):
        self.assertIsNone(ominity.run("state")["reading"])
        self.assertTrue(ominity.run("widget-toggle")["widget"])
        self.assertIsNone(ominity.run("state")["reading"])
        self.assertFalse(ominity.run("widget-toggle")["widget"])
        self.assertFalse((ominity.STATE_ROOT / "identity.json").exists())

    def test_legacy_current_reading_is_not_rewritten(self):
        ominity.run("widget-show")
        day = ominity.run("state")["day"]
        legacy = {"day": day, "id": "major-17-the-star", "reversed": False, "drawnAt": "old", "redraw": False}
        ominity.save_state({"widget": True, "reading": legacy, "history": [legacy]})
        result = ominity.run("today")
        self.assertEqual(result["reading"]["id"], legacy["id"])
        self.assertNotIn("experience", result["reading"])
        self.assertFalse((ominity.STATE_ROOT / "identity.json").exists())

    def test_corrupt_state_is_recovered_without_external_effects(self):
        ominity.STATE_FILE.write_text("broken", encoding="utf-8")
        result = ominity.run("today")
        self.assertTrue(result["ok"])
        self.assertEqual(ominity.STATE_FILE.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
