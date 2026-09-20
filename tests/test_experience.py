import hashlib
import hmac
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import experience


class CanonicalizationTest(unittest.TestCase):
    def test_jcs_framing_and_utf16_key_order(self):
        self.assertEqual(
            experience.canonical_json({"😀": 2, "\ue000": 1, "a": "line\nend"}),
            b'{"a":"line\\nend","\xf0\x9f\x98\x80":2,"\xee\x80\x80":1}',
        )
        for invalid in (1.5, 2**53, "\ud800"):
            with self.assertRaises((TypeError, ValueError, UnicodeError)):
                experience.canonical_json(invalid)

    def test_versioned_hmac_message_is_byte_exact(self):
        signature = {"cpu": "C3", "memory": "M4", "storage": "D4"}
        result = experience.experience_for(bytes.fromhex("00" * 32), "2026-09-20", "major-17-the-star", False, signature, {"cpu": 2, "memory": 1, "disk": 3})
        message = b'{"cardId":"major-17-the-star","localDate":"2026-09-20","machineSignature":{"cpu":"C3","memory":"M4","storage":"D4"},"orientation":"upright","protocol":"ominity-experience-v1"}'
        expected = hmac.new(bytes(32), message, hashlib.sha256).digest()
        self.assertEqual(result["artVariant"], int.from_bytes(expected[:4], "big") % 16)
        self.assertNotIn(expected.hex(), json.dumps(result))
        self.assertEqual(result["machineSignature"], signature)


class IdentityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "ominity"

    def test_private_identity_is_stable_and_complete(self):
        first = experience.installation_seed(self.root)
        second = experience.installation_seed(self.root)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 32)
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        path = self.root / "identity.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        document = json.loads(path.read_text())
        self.assertEqual(document["record"]["payload"]["seed"], first.hex())
        self.assertEqual(experience.verify_envelope(document, "identity"), {"seed": first.hex()})

    def test_concurrent_first_use_publishes_one_identity(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            seeds = list(pool.map(lambda _: experience.installation_seed(self.root), range(24)))
        self.assertEqual(len(set(seeds)), 1)
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["identity.json"])

    def test_rejects_corruption_unsupported_protocol_and_bad_seed(self):
        experience.installation_seed(self.root)
        path = self.root / "identity.json"
        original = json.loads(path.read_text())
        cases = []
        corrupt = json.loads(json.dumps(original))
        corrupt["record"]["schemaVersion"] = 2
        cases.append((corrupt, ValueError))
        unsupported = json.loads(json.dumps(original))
        unsupported["integrity"]["canonicalization"] = "future-JCS"
        cases.append((unsupported, experience.UnsupportedEnvelope))
        for bad in ("A" * 64, "a" * 63, "z" * 64):
            cases.append((experience.envelope("identity", {"seed": bad}), ValueError))
        for document, error in cases:
            path.write_text(json.dumps(document))
            with self.assertRaises(error):
                experience.installation_seed(self.root)

    def test_rejects_duplicate_keys_and_public_mode(self):
        experience.installation_seed(self.root)
        path = self.root / "identity.json"
        path.write_text('{"record":{},"record":{}}')
        with self.assertRaisesRegex(ValueError, "Duplicate key"):
            experience.installation_seed(self.root)
        os.chmod(path, 0o644)
        with self.assertRaisesRegex(ValueError, "0600"):
            experience.installation_seed(self.root)


class BucketTest(unittest.TestCase):
    def test_capacity_boundaries_and_unknown(self):
        self.assertEqual(experience._bucket(2, (2, 4, 8, 16), "C"), "C1")
        self.assertEqual(experience._bucket(3, (2, 4, 8, 16), "C"), "C2")
        self.assertEqual(experience._bucket(17, (2, 4, 8, 16), "C"), "C5")
        self.assertEqual(experience._bucket(0, (2, 4, 8, 16), "C"), "C0")
        with patch.object(experience.os, "cpu_count", return_value=8), patch.object(experience, "_meminfo", return_value={"MemTotal": 16 * experience.GIB}), patch.object(experience.os, "statvfs", return_value=SimpleNamespace(f_frsize=experience.GIB, f_blocks=256)):
            self.assertEqual(experience.capacity_signature(), {"cpu": "C3", "memory": "M3", "storage": "D2"})

    def test_weather_only_returns_buckets(self):
        with patch.object(experience, "_cpu_counters", side_effect=[(100, 60), (200, 90)]), patch.object(experience.time, "sleep"), patch.object(experience, "_meminfo", return_value={"MemAvailable": 40, "MemTotal": 100}), patch.object(experience.os, "statvfs", return_value=SimpleNamespace(f_bavail=20, f_blocks=100)):
            self.assertEqual(experience.weather_buckets(), {"cpu": 3, "memory": 3, "disk": 4})


if __name__ == "__main__":
    unittest.main()
