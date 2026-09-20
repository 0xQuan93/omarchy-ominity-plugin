"""Local, privacy-preserving inputs for Ominity's future living deck.

This module deliberately has no card-selection or interpretation authority. The
only persistent machine observations it returns are coarse capacity and weather
buckets. RFC 8785 input in this protocol is restricted to I-JSON's safe integer
range; floating-point values are rejected rather than approximately serialized.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import time
from pathlib import Path


PROTOCOL = "ominity-experience-v1"
SEED_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
GIB = 1024 ** 3


class UnsupportedEnvelope(ValueError):
    """The stored integrity protocol is unknown, rather than damaged."""


def canonical_json(value: object) -> bytes:
    """RFC 8785 JCS for the protocol's string/bool/null/safe-integer domain.

    UTF-16 code-unit key sorting matches ECMAScript property sorting. All
    persisted numeric values in this slice are integers, avoiding differences
    between Python and ECMAScript floating-point formatting.
    """

    def render(item: object) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, str):
            item.encode("utf-8")  # Reject unpaired surrogates.
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if type(item) is int:
            if abs(item) > 2**53 - 1:
                raise ValueError("Integer outside RFC 8785 I-JSON safe range")
            return str(item)
        if isinstance(item, list):
            return "[" + ",".join(render(member) for member in item) + "]"
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise TypeError("JSON object keys must be strings")
            ordered = sorted(item, key=lambda key: key.encode("utf-16-be"))
            return "{" + ",".join(render(key) + ":" + render(item[key]) for key in ordered) + "}"
        raise TypeError(f"Unsupported RFC 8785 value: {type(item).__name__}")

    return render(value).encode("utf-8")


def envelope(record_type: str, payload: dict) -> dict:
    record = {"schemaVersion": 1, "type": record_type, "payload": payload}
    return {
        "integrity": {
            "algorithm": "sha256",
            "canonicalization": "RFC8785",
            "digest": hashlib.sha256(canonical_json(record)).hexdigest(),
        },
        "record": record,
    }


def verify_envelope(document: dict, record_type: str) -> dict:
    if not isinstance(document, dict) or not isinstance(document.get("integrity"), dict):
        raise ValueError("Invalid Ominity integrity envelope")
    integrity = document["integrity"]
    if integrity.get("algorithm") != "sha256" or integrity.get("canonicalization") != "RFC8785":
        raise UnsupportedEnvelope("Unsupported Ominity integrity algorithm or canonicalization")
    record = document.get("record")
    if not isinstance(record, dict):
        raise ValueError("Invalid Ominity record")
    digest = integrity.get("digest")
    if not isinstance(digest, str) or not SEED_PATTERN.fullmatch(digest):
        raise ValueError("Invalid Ominity record digest")
    if not hmac.compare_digest(digest, hashlib.sha256(canonical_json(record)).hexdigest()):
        raise ValueError("Ominity record integrity check failed")
    if record.get("schemaVersion") != 1 or record.get("type") != record_type:
        raise UnsupportedEnvelope("Unsupported Ominity record schema or type")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Invalid Ominity record payload")
    return payload


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key in Ominity JSON record")
        result[key] = value
    return result


def installation_seed(state_root: Path) -> bytes:
    """Create once with atomic publication; refuse malformed or exposed seeds."""
    state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_root, 0o700)
    path = state_root / "identity.json"
    if not path.exists() and not path.is_symlink():
        seed_hex = secrets.token_hex(32)
        contents = canonical_json(envelope("identity", {"seed": seed_hex})) + b"\n"
        fd, temp_name = tempfile.mkstemp(prefix="identity.", dir=state_root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            # The link is the publication point; a concurrent creator wins
            # without either process ever exposing a partial identity file.
            try:
                os.link(temp_name, path)
                dir_fd = os.open(state_root, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except FileExistsError:
                pass
        finally:
            os.unlink(temp_name)
    if path.is_symlink():
        raise ValueError("Ominity identity may not be a symlink")
    if path.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Ominity identity must have mode 0600")
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    seed_hex = verify_envelope(document, "identity").get("seed")
    if not isinstance(seed_hex, str) or not SEED_PATTERN.fullmatch(seed_hex):
        raise ValueError("Ominity identity seed must be 64 lowercase hex characters")
    return bytes.fromhex(seed_hex)


def _bucket(value: int, limits: tuple[int, ...], prefix: str) -> str:
    if value <= 0:
        return prefix + "0"  # Explicit unknown; never invent a capacity.
    return prefix + str(next((index for index, limit in enumerate(limits, 1) if value <= limit), len(limits) + 1))


def _meminfo() -> dict[str, int]:
    values = {}
    with open("/proc/meminfo", encoding="ascii") as handle:
        for line in handle:
            key, _, rest = line.partition(":")
            if key in {"MemTotal", "MemAvailable"}:
                values[key] = int(rest.strip().split()[0]) * 1024
    return values


def capacity_signature() -> dict[str, str]:
    """Return only coarse classes, discarding raw values before persistence."""
    cpu = os.cpu_count() or 0
    try:
        memory = _meminfo().get("MemTotal", 0)
    except (OSError, ValueError):
        memory = 0
    try:
        stats = os.statvfs("/")
        disk = stats.f_frsize * stats.f_blocks
    except OSError:
        disk = 0
    return {
        "cpu": _bucket(cpu, (2, 4, 8, 16), "C"),
        "memory": _bucket(memory, tuple(limit * GIB for limit in (4, 8, 16, 32, 64)), "M"),
        "storage": _bucket(disk, tuple(limit * GIB for limit in (128, 256, 512, 1024)), "D"),
    }


def _cpu_counters() -> tuple[int, int]:
    with open("/proc/stat", encoding="ascii") as handle:
        fields = handle.readline().split()
    if fields[0] != "cpu" or len(fields) < 5:
        raise ValueError("Invalid /proc/stat CPU counters")
    counters = [int(value) for value in fields[1:]]
    # idle + iowait; all counters count toward elapsed CPU time.
    return sum(counters), counters[3] + (counters[4] if len(counters) > 4 else 0)


def _pressure_bucket(ratio: float) -> int:
    return min(4, max(0, int(ratio * 5)))


def weather_buckets() -> dict[str, int]:
    """Sample once at creation; no raw percentages escape this function."""
    try:
        total_a, idle_a = _cpu_counters()
        time.sleep(0.05)
        total_b, idle_b = _cpu_counters()
        elapsed = total_b - total_a
        cpu = _pressure_bucket(1 - (idle_b - idle_a) / elapsed) if elapsed > 0 else 2
    except (OSError, ValueError, IndexError, ZeroDivisionError):
        cpu = 2
    try:
        mem = _meminfo()
        memory = _pressure_bucket(1 - mem["MemAvailable"] / mem["MemTotal"])
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        memory = 2
    try:
        stats = os.statvfs("/")
        disk = _pressure_bucket(1 - stats.f_bavail / stats.f_blocks)
    except (OSError, ZeroDivisionError):
        disk = 2
    return {"cpu": cpu, "memory": memory, "disk": disk}


def experience_for(seed: bytes, day: str, card_id: str, reversed_card: bool,
                   signature: dict[str, str], weather: dict[str, int]) -> dict:
    """Derive visible metadata from byte-exact, versioned HMAC framing."""
    if len(seed) != 32:
        raise ValueError("Ominity installation seed must be 32 bytes")
    message = {
        "protocol": PROTOCOL,
        "localDate": day,
        "cardId": card_id,
        "orientation": "reversed" if reversed_card else "upright",
        "machineSignature": signature,
    }
    derived = hmac.new(seed, canonical_json(message), hashlib.sha256).digest()
    return {
        "version": 1,
        "machineSignature": dict(signature),
        "weather": dict(weather),
        "artVariant": int.from_bytes(derived[:4], "big") % 16,
    }
