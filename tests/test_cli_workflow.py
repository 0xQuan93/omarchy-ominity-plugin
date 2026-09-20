"""Exercise the public JSON boundary through a complete local archive journey."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("rsvg-convert"), "librsvg is needed for witnessed artwork")
class CliWorkflowTest(unittest.TestCase):
    def test_draw_journal_export_import_and_historical_lookup(self):
        with tempfile.TemporaryDirectory(prefix="ominity-cli-test-") as directory:
            source = Path(directory) / "source"
            destination = Path(directory) / "destination"
            archive = Path(directory) / "backup.zip"

            def call(state, *args, body=None):
                env = dict(os.environ, XDG_STATE_HOME=str(state))
                result = subprocess.run([sys.executable, "-B", str(PLUGIN / "ominity.py"), *args],
                                        input=body, text=True, capture_output=True, env=env, check=False)
                self.assertTrue(result.stdout, result.stderr)
                response = json.loads(result.stdout)
                self.assertEqual(result.returncode, 0, response)
                self.assertTrue(response["ok"], response)
                return response

            today = call(source, "today")
            day = today["day"]
            self.assertEqual(today["reading"]["archiveStatus"], "verified-original")
            self.assertTrue(Path(today["reading"]["artworkPath"]).is_file())
            journal = {"firstImpression": "A quiet start.", "eveningReflection": "Returned to the image."}
            call(source, "journal-save", "--day", day, body=json.dumps(journal) + "\n")
            self.assertEqual(call(source, "day", "--day", day)["journal"]["eveningReflection"],
                             journal["eveningReflection"])

            exported = call(source, "archive-export", "--path", str(archive))
            self.assertEqual(exported["days"], 1)
            self.assertEqual(call(source, "archive-verify", "--path", str(archive))["archiveId"],
                             exported["archiveId"])
            imported = call(destination, "archive-import", "--path", str(archive))
            self.assertEqual(imported["importedDays"], 1)
            self.assertEqual(call(destination, "stats")["days"], 1)
            restored = call(destination, "day", "--day", day)
            self.assertEqual(restored["reading"]["id"], today["reading"]["id"])
            self.assertEqual(restored["reading"]["archiveStatus"], "verified-original")
            self.assertEqual(restored["journal"]["firstImpression"], journal["firstImpression"])


if __name__ == "__main__":
    unittest.main()
