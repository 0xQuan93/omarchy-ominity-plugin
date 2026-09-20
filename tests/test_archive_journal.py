import hashlib
import json
import os
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

import archive
import journal
from experience import canonical_json, envelope
from living_store import artwork_status, load_daily


def witness_png() -> bytes:
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", 7, 12, 8, 6, 0, 0, 0)
    rows = (b"\0" + b"\0" * 28) * 12
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "ominity"

    def test_edit_is_private_and_does_not_touch_daily(self):
        first = journal.save_journal(self.root, "2026-09-20", "first thought", "later thought")
        self.assertEqual(journal.load_journal(self.root, "2026-09-20"), first)
        self.assertEqual(journal.journal_path(self.root, "2026-09-20").stat().st_mode & 0o777, 0o600)
        journal.save_journal(self.root, "2026-09-20", "changed", "")
        self.assertEqual(journal.load_journal(self.root, "2026-09-20")["firstImpression"], "changed")
        self.assertFalse((self.root / "history").exists())

    def test_rejects_tamper_invalid_date_and_oversized_text(self):
        with self.assertRaises(ValueError):
            journal.save_journal(self.root, "2026-02-30", "a", "b")
        with self.assertRaises(ValueError):
            journal.save_journal(self.root, "2026-09-20", "x" * 8193, "")
        journal.save_journal(self.root, "2026-09-20", "a", "b")
        path = journal.journal_path(self.root, "2026-09-20")
        document = json.loads(path.read_text())
        document["record"]["payload"]["firstImpression"] = "tampered"
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, "integrity"):
            journal.load_journal(self.root, "2026-09-20")


class ArchiveTest(unittest.TestCase):
    DAY = "2026-09-20"
    ERA = "019a4d3e-7c91-7b2a-a901-2b61c67f1102"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "source"
        self.dest = self.base / "dest"
        self.zip = self.base / "backup.zip"
        self._fixture()

    def _put(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        os.chmod(path, 0o600)
        return path

    def _fixture(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        png = witness_png()
        svg_hash = hashlib.sha256(svg).hexdigest()
        png_hash = hashlib.sha256(png).hexdigest()
        svg_path = f"artifacts/sha256/{svg_hash[:2]}/{svg_hash}.svg"
        png_path = f"artifacts/sha256/{png_hash[:2]}/{png_hash}.png"
        self._put(svg_path, svg)
        self._put(png_path, png)
        era = {"id": self.ERA, "ordinal": 1, "displayLabel": "Machine Era 01",
               "started": self.DAY, "ended": None,
               "classes": {"cpu": "C3", "memory": "M4", "storage": "D4"}}
        self._put(f"machine-eras/{self.ERA}.json", canonical_json(envelope("machine-era", era)))
        daily = {"day": self.DAY, "id": "major-17-the-star", "reversed": False,
                 "machine": {"eraId": self.ERA},
                 "artwork": {"master": {"sha256": svg_hash, "format": "image/svg+xml", "relativePath": svg_path, "bytes": len(svg)},
                             "visualWitness": {"sha256": png_hash, "format": "image/png", "relativePath": png_path, "bytes": len(png),
                                               "width": 7, "height": 12, "aspectRatio": "7:12"}}}
        self._put(f"history/2026/{self.DAY}.json", canonical_json(envelope("daily-om", daily)))
        self._put("identity.json", b"secret-identity-must-not-leak")
        journal.save_journal(self.root, self.DAY, "A real reflection", "")

    def test_full_export_verify_import_and_no_identity(self):
        result = archive.export_archive(self.root, self.zip)
        self.assertEqual(result["days"], 1)
        with zipfile.ZipFile(self.zip) as file:
            self.assertNotIn("identity.json", file.namelist())
            self.assertEqual(file.namelist()[1:], sorted(file.namelist()[1:]))
            self.assertEqual(file.read("manifest.json").count(b"secret-identity"), 0)
        self.assertEqual(archive.verify_archive(self.zip)["members"], 5)
        imported = archive.import_archive(self.zip, self.dest)
        self.assertEqual(imported["imported"], 5)
        self.assertFalse((self.dest / "identity.json").exists())
        self.assertEqual(journal.load_journal(self.dest, self.DAY)["firstImpression"], "A real reflection")
        self.assertTrue(artwork_status(self.dest, load_daily(self.dest, self.DAY))["original"])
        self.assertEqual(archive.import_archive(self.zip, self.dest)["imported"], 0)
        with self.assertRaises(FileExistsError):
            archive.export_archive(self.root, self.zip)

    def test_immutable_conflict_rejected_without_partial_import(self):
        archive.export_archive(self.root, self.zip)
        conflicting = self.dest / f"history/2026/{self.DAY}.json"
        conflicting.parent.mkdir(parents=True)
        conflicting.write_text("different local daily")
        with self.assertRaises(archive.ArchiveConflict):
            archive.import_archive(self.zip, self.dest)
        self.assertFalse((self.dest / "artifacts").exists())
        self.assertEqual(conflicting.read_text(), "different local daily")

    def test_journal_overlay_preserves_old_edit(self):
        archive.export_archive(self.root, self.zip)
        journal.save_journal(self.dest, self.DAY, "local edit", "evening")
        kept = archive.import_archive(self.zip, self.dest)
        self.assertEqual(kept["journalConflicts"], [f"journal/2026/{self.DAY}.json"])
        self.assertEqual(journal.load_journal(self.dest, self.DAY)["firstImpression"], "local edit")
        replaced = archive.import_archive(self.zip, self.dest, journal_policy="replace")
        self.assertEqual(replaced["journalConflicts"], [])
        self.assertEqual(journal.load_journal(self.dest, self.DAY)["firstImpression"], "A real reflection")
        backups = list((self.dest / "archive-conflicts" / replaced["archiveId"] / "local").glob(f"*/journal/2026/{self.DAY}.json"))
        self.assertEqual(len(backups), 1)
        self.assertIn("local edit", backups[0].read_text())

    def test_rejects_path_traversal_extra_zip_entry_and_corruption(self):
        archive.export_archive(self.root, self.zip)
        with zipfile.ZipFile(self.zip, "a") as file:
            file.writestr("../identity.json", b"bad")
        with self.assertRaises(ValueError):
            archive.verify_archive(self.zip)
        self.assertFalse(self.dest.exists())

    def test_rejects_member_digest_mismatch_before_import(self):
        archive.export_archive(self.root, self.zip)
        with zipfile.ZipFile(self.zip) as old:
            data = {name: old.read(name) for name in old.namelist()}
        data[f"history/2026/{self.DAY}.json"] += b" "
        with zipfile.ZipFile(self.zip, "w") as changed:
            for name, blob in data.items():
                changed.writestr(name, blob)
        with self.assertRaisesRegex(ValueError, "ZIP size differs"):
            archive.import_archive(self.zip, self.dest)
        self.assertFalse(self.dest.joinpath("history").exists())

    def test_legacy_day_is_labeled_unwitnessed(self):
        legacy = {"day": "2026-09-19", "id": "major-18-the-moon", "reversed": True,
                  "archiveOrigin": "legacy-reading"}
        self._put("history/2026/2026-09-19.json", canonical_json(envelope("daily-om", legacy)))
        result = archive.export_archive(self.root, self.zip)
        self.assertEqual(result["legacyDays"], 1)
        self.assertEqual(archive.verify_archive(self.zip)["legacyDays"], 1)

    def test_rejects_unknown_card_before_export_or_import(self):
        path = self.root / f"history/2026/{self.DAY}.json"
        document = json.loads(path.read_text())
        document["record"]["payload"]["id"] = "unknown-card"
        path.write_bytes(canonical_json(envelope("daily-om", document["record"]["payload"])))
        with self.assertRaisesRegex(ValueError, "Invalid Daily Om payload"):
            archive.export_archive(self.root, self.zip)
        self.assertFalse(self.zip.exists())

        legacy = {"day": self.DAY, "id": "unknown-card", "reversed": False,
                  "archiveOrigin": "legacy-reading"}
        bad_history = canonical_json(envelope("daily-om", legacy))
        self._write_forged_archive(f"history/2026/{self.DAY}.json", bad_history)
        with self.assertRaisesRegex(ValueError, "Invalid Daily Om payload"):
            archive.verify_archive(self.zip)
        with self.assertRaisesRegex(ValueError, "Invalid Daily Om payload"):
            archive.import_archive(self.zip, self.dest)
        self.assertFalse(self.dest.joinpath("history").exists())

    def test_rejects_invalid_or_mismatched_png_before_import(self):
        archive.export_archive(self.root, self.zip)
        with zipfile.ZipFile(self.zip) as source:
            original = {name: source.read(name) for name in source.namelist()}
        png_path = next(name for name in original if name.endswith(".png"))
        self._write_forged_archive(png_path, b"\x89PNG\r\n\x1a\n", original)
        with self.assertRaisesRegex(ValueError, "PNG"):
            archive.verify_archive(self.zip)
        with self.assertRaisesRegex(ValueError, "PNG"):
            archive.import_archive(self.zip, self.dest)
        self.assertFalse(self.dest.joinpath("history").exists())

        damaged = bytearray(witness_png())
        damaged[-17] ^= 1  # Corrupt the IDAT CRC while keeping its PNG signature.
        self._write_forged_archive(png_path, bytes(damaged), original)
        with self.assertRaisesRegex(ValueError, "PNG"):
            archive.verify_archive(self.zip)

        history_path = f"history/2026/{self.DAY}.json"
        history = json.loads(original[history_path])
        history["record"]["payload"]["artwork"]["visualWitness"]["width"] = 14
        mismatch = canonical_json(envelope("daily-om", history["record"]["payload"]))
        self._write_forged_archive(history_path, mismatch, original)
        with self.assertRaisesRegex(ValueError, "mismatched PNG witness"):
            archive.verify_archive(self.zip)

    def test_rejects_invalid_png_before_export(self):
        bad_png = b"\x89PNG\r\n\x1a\n"
        digest = hashlib.sha256(bad_png).hexdigest()
        png_path = f"artifacts/sha256/{digest[:2]}/{digest}.png"
        self._put(png_path, bad_png)
        history_path = self.root / f"history/2026/{self.DAY}.json"
        history = json.loads(history_path.read_text())
        witness = history["record"]["payload"]["artwork"]["visualWitness"]
        witness.update({"relativePath": png_path, "sha256": digest, "bytes": len(bad_png)})
        history_path.write_bytes(canonical_json(envelope("daily-om", history["record"]["payload"])))
        with self.assertRaisesRegex(ValueError, "PNG"):
            archive.export_archive(self.root, self.zip)
        self.assertFalse(self.zip.exists())

    def _write_forged_archive(self, path, contents, original=None):
        if original is None:
            # Build a valid starting archive with the ordinary fixture.
            self._fixture()
            archive.export_archive(self.root, self.zip)
            with zipfile.ZipFile(self.zip) as source:
                original = {name: source.read(name) for name in source.namelist()}
        updated = dict(original)
        replacement_path = path
        if path.endswith(".png"):
            digest = hashlib.sha256(contents).hexdigest()
            replacement_path = f"artifacts/sha256/{digest[:2]}/{digest}.png"
            del updated[path]
            history_path = f"history/2026/{self.DAY}.json"
            history = json.loads(updated[history_path])
            witness = history["record"]["payload"]["artwork"]["visualWitness"]
            witness.update({"relativePath": replacement_path, "sha256": digest, "bytes": len(contents)})
            updated[history_path] = canonical_json(envelope("daily-om", history["record"]["payload"]))
        updated[replacement_path] = contents
        manifest = json.loads(updated["manifest.json"])
        for entry in manifest["record"]["payload"]["members"]:
            if entry["path"] == path:
                entry["path"] = replacement_path
                entry["bytes"] = len(contents)
                entry["sha256"] = hashlib.sha256(contents).hexdigest()
            elif path.endswith(".png") and entry["path"] == f"history/2026/{self.DAY}.json":
                entry["bytes"] = len(updated[entry["path"]])
                entry["sha256"] = hashlib.sha256(updated[entry["path"]]).hexdigest()
        manifest["record"]["payload"]["members"].sort(key=lambda entry: entry["path"])
        updated["manifest.json"] = canonical_json(envelope("archive-manifest", manifest["record"]["payload"]))
        with zipfile.ZipFile(self.zip, "w") as destination:
            for name, blob in updated.items():
                destination.writestr(name, blob)


if __name__ == "__main__":
    unittest.main()
