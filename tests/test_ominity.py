import importlib.util
import json
import tempfile
import threading
import time
import unittest
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import living_store
import experience


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
        self.assertEqual(first["reading"]["machine"]["eraId"], redraw["reading"]["machine"]["eraId"])
        stored = ominity.history_path(ominity.STATE_ROOT, first["day"]).read_text()
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

    def test_redraw_of_legacy_day_keeps_canonical_and_creates_own_era(self):
        day = ominity.run("state")["day"]
        old = {"day": day, "id": "major-17-the-star", "reversed": False,
               "drawnAt": "old", "redraw": False}
        ominity.save_state({"widget": True, "reading": old, "history": [old]})
        redraw = ominity.run("redraw")["reading"]
        canonical = ominity.load_daily(ominity.STATE_ROOT, day)
        self.assertEqual(canonical["id"], old["id"])
        self.assertEqual(canonical["archiveOrigin"], "legacy-reading")
        self.assertTrue(redraw["redraw"])
        self.assertTrue(redraw["artworkPath"])
        self.assertEqual(redraw["machine"]["eraId"], ominity.load_era_state(ominity.STATE_ROOT)["activeId"])

    def test_concurrent_today_rechecks_after_day_lock(self):
        workers = 8
        start = threading.Barrier(workers)

        def weather():
            time.sleep(0.06)  # Make the pre-lock read race observable.
            return {"cpu": 2, "memory": 1, "disk": 3}

        def call_today(_):
            start.wait()
            return ominity.run("today")

        with patch.object(ominity, "capacity_signature", return_value={"cpu": "C3", "memory": "M4", "storage": "D4"}), patch.object(ominity, "weather_buckets", side_effect=weather) as sampled:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(call_today, range(workers)))
        self.assertEqual(sampled.call_count, 1)
        self.assertEqual(len({json.dumps(result["reading"], sort_keys=True) for result in results}), 1)
        self.assertEqual({result["historyCount"] for result in results}, {1})
        self.assertEqual(len(ominity.list_daily(ominity.STATE_ROOT)), 1)
        lock_file = ominity.STATE_ROOT / "locks" / (results[0]["day"] + ".lock")
        self.assertEqual(lock_file.stat().st_mode & 0o777, 0o600)

    def test_prior_day_in_history_is_found_after_clock_rollback(self):
        cards = ominity.deck()
        older = {"day": "2026-09-20", "id": "major-17-the-star"}
        newer = {"day": "2026-09-21", "id": "major-18-the-moon"}
        self.assertEqual(ominity.reading_for_day({"reading": newer, "history": [older, newer]}, older["day"], cards), older)

    def test_corrupt_state_is_recovered_without_external_effects(self):
        ominity.STATE_FILE.write_text("broken", encoding="utf-8")
        result = ominity.run("today")
        self.assertTrue(result["ok"])
        self.assertEqual(ominity.STATE_FILE.stat().st_mode & 0o777, 0o600)

    def test_daily_record_is_immutable_and_visual_witness_is_verified(self):
        first = ominity.run("today")
        day = first["day"]
        reading = first["reading"]
        self.assertEqual(reading["archiveStatus"], "verified-original")
        self.assertTrue(Path(reading["artworkPath"]).is_file())
        self.assertEqual((ominity.STATE_ROOT / "machine-eras" / (reading["machine"]["eraId"] + ".json")).is_file(), True)
        original = ominity.history_path(ominity.STATE_ROOT, day).read_bytes()
        with patch.object(ominity, "_daypart", return_value="evening"):
            again = ominity.run("today")
        self.assertEqual(first["reading"]["experience"]["prompt"], again["reading"]["experience"]["prompt"])
        self.assertEqual(original, ominity.history_path(ominity.STATE_ROOT, day).read_bytes())
        witness = Path(reading["artworkPath"])
        witness.write_bytes(witness.read_bytes() + b"tamper")
        damaged = ominity.run("state")["reading"]
        self.assertIsNone(damaged["artworkPath"])
        self.assertEqual(damaged["artworkStatus"]["visualWitness"], "modified")
        self.assertEqual(ominity.run("stats")["days"], 1)

    def test_artifact_failure_never_publishes_daily_or_advances_era(self):
        with patch.object(living_store, "_publish_object", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                ominity.run("today")
        day = ominity.run("state")["day"]
        self.assertIsNone(ominity.load_daily(ominity.STATE_ROOT, day))
        self.assertIsNone(ominity.load_era_state(ominity.STATE_ROOT))
        self.assertEqual(list((ominity.STATE_ROOT / "staging").iterdir()), [])
        self.assertEqual(ominity.run("today")["historyCount"], 1)

    def test_failed_daily_json_commit_discards_pending_era(self):
        real_link = living_store.os.link

        def fail_history(source, target, *args, **kwargs):
            if "/history/" in str(target) and str(target).endswith(".json"):
                raise OSError("history unavailable")
            return real_link(source, target, *args, **kwargs)

        with patch.object(living_store.os, "link", side_effect=fail_history):
            with self.assertRaisesRegex(OSError, "history unavailable"):
                ominity.run("today")
        self.assertIsNone(ominity.load_era_state(ominity.STATE_ROOT))
        self.assertEqual(ominity.run("state")["historyCount"], 0)
        self.assertEqual(list((ominity.STATE_ROOT / "pending-eras").iterdir()), [])
        self.assertEqual(ominity.list_era_records(ominity.STATE_ROOT), [])

    def test_recovery_finishes_era_after_daily_json_commit(self):
        with patch.object(living_store, "commit_machine_era", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                ominity.run("today")
        self.assertIsNone(ominity.load_era_state(ominity.STATE_ROOT))
        self.assertEqual(len(ominity.list_daily(ominity.STATE_ROOT)), 1)
        day = ominity.run("state")["day"]
        self.assertIsNotNone(ominity.load_daily(ominity.STATE_ROOT, day))
        self.assertEqual(ominity.run("stats")["eras"][0]["days"], 1)
        self.assertEqual(list((ominity.STATE_ROOT / "pending-eras").iterdir()), [])
        self.assertIsNotNone(ominity.load_era_state(ominity.STATE_ROOT))

    def test_stats_count_canonical_days_separately_from_redraws(self):
        first = ominity.run("today")
        ominity.run("redraw")
        stats = ominity.run("stats")
        history = ominity.run("history")
        self.assertEqual(stats["days"], 1)
        self.assertEqual(stats["redrawCount"], 1)
        self.assertEqual(stats["windows"]["7"]["days"], 1)
        self.assertEqual(len(stats["perCard"]), 78)
        self.assertEqual(sum(item["count"] for item in stats["perCard"]), 1)
        self.assertEqual(stats["eras"][0]["days"], 1)
        self.assertEqual(len(history["days"]), 1)
        self.assertEqual(history["days"][0]["id"], first["reading"]["id"])
        self.assertTrue(history["days"][0]["artworkPath"])

    def test_stats_include_imported_eras_without_reassigning_local_history(self):
        ominity.run("today")
        imported = {"id": experience._era_id(), "ordinal": 1,
                    "displayLabel": "Machine Era 01", "started": "2020-01-01",
                    "ended": "2021-01-01",
                    "classes": {"cpu": "C2", "memory": "M2", "storage": "D2"}}
        living_store.sync_era_records(ominity.STATE_ROOT, [imported])
        eras = ominity.run("stats")["eras"]
        self.assertEqual(len(eras), 2)
        self.assertEqual(eras[0]["id"], imported["id"])
        self.assertEqual(eras[0]["days"], 0)
        self.assertEqual(eras[1]["days"], 1)

    def test_legacy_history_migrates_without_a_ninety_day_cap(self):
        start = date(2025, 1, 1)
        events = [{"day": (start + timedelta(days=index)).isoformat(),
                   "id": "major-17-the-star", "reversed": False,
                   "drawnAt": "old", "redraw": False} for index in range(95)]
        ominity.save_state({"widget": True, "reading": events[-1], "history": events})
        stats = ominity.run("stats")
        self.assertEqual(stats["days"], 95)
        self.assertEqual(stats["topCards"][0]["count"], 95)
        self.assertEqual(len(ominity.run("history")["days"]), 95)
        self.assertEqual(ominity.run("stats")["days"], 95)


if __name__ == "__main__":
    unittest.main()
