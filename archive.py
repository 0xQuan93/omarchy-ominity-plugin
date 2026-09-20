"""Portable, verify-first, self-contained Ominity archives.

The ZIP format contains ``manifest.json`` and only the paths enumerated by its
versioned integrity-checked manifest. An ordinary export never includes the
installation identity or mutable active Machine Era state.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from experience import (_unique_pairs, _valid_date, _valid_era_id,
                        canonical_json, envelope, valid_signature, verify_envelope)
from journal import _journal_lock, _validate_payload as validate_journal_payload

MAX_MEMBERS = 100_000
MAX_TOTAL_BYTES = 64 * 1024**3
MAX_ARTIFACT_BYTES = 128 * 1024**2
MAX_JSON_BYTES = 16 * 1024**2
MAX_MANIFEST_BYTES = 32 * 1024**2
CHUNK = 1024**2
HEX = re.compile(r"[0-9a-f]{64}\Z")
DAY_PATH = re.compile(r"(history|journal)/([0-9]{4})/([0-9]{4}-[0-9]{2}-[0-9]{2})\.json\Z")
ART_PATH = re.compile(r"artifacts/sha256/([0-9a-f]{2})/([0-9a-f]{64})\.(svg|png)\Z")
ERA_PATH = re.compile(r"machine-eras/([0-9a-f-]{36})\.json\Z")


class ArchiveConflict(ValueError):
    """Import would replace a canonical or content-addressed local file."""

    def __init__(self, paths: list[str]):
        self.paths = paths
        super().__init__("Archive conflicts with local immutable records: " + ", ".join(paths[:10]))


def _kind(path: str) -> tuple[str, str | None]:
    if not isinstance(path, str) or not path.isascii() or "\\" in path or "\0" in path:
        raise ValueError("Invalid archive member path")
    if (not path or path.startswith("/") or any(segment in ("", ".", "..") for segment in path.split("/"))):
        raise ValueError("Unsafe archive member path")
    match = DAY_PATH.fullmatch(path)
    if match:
        kind, year, day = match.groups()
        if not _valid_date(day) or day[:4] != year:
            raise ValueError("Invalid archive day path")
        return kind, day
    match = ART_PATH.fullmatch(path)
    if match:
        prefix, digest, suffix = match.groups()
        if prefix != digest[:2]:
            raise ValueError("Invalid content-addressed artifact path")
        return "artifact-" + suffix, digest
    match = ERA_PATH.fullmatch(path)
    if match and _valid_era_id(match.group(1)):
        return "machine-era", match.group(1)
    raise ValueError(f"Unexpected Ominity archive path: {path}")


def _media_type(path: str) -> str:
    kind, _ = _kind(path)
    return {"artifact-svg": "image/svg+xml", "artifact-png": "image/png"}.get(kind, "application/json")


def _limit(path: str) -> int:
    return MAX_ARTIFACT_BYTES if _kind(path)[0].startswith("artifact-") else MAX_JSON_BYTES


def _read_json(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_pairs)


def _validate_record(path: str, data: bytes) -> dict | None:
    kind, key = _kind(path)
    if len(data) > _limit(path):
        raise ValueError(f"Archive member too large: {path}")
    if kind.startswith("artifact-"):
        if hashlib.sha256(data).hexdigest() != key:
            raise ValueError(f"Artifact path digest mismatch: {path}")
        if kind == "artifact-png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid PNG witness: {path}")
        if kind == "artifact-svg" and b"<svg" not in data[:4096]:
            raise ValueError(f"Invalid SVG master: {path}")
        return None
    record_type = {"history": "daily-om", "journal": "journal", "machine-era": "machine-era"}[kind]
    payload = verify_envelope(_read_json(data), record_type)
    if kind == "history":
        if payload.get("day") != key or not isinstance(payload.get("id"), str) or type(payload.get("reversed")) is not bool:
            raise ValueError(f"Invalid Daily Om payload: {path}")
    elif kind == "journal":
        validate_journal_payload(payload, key)
    else:
        if (payload.get("id") != key or not _valid_date(payload.get("started"))
                or (payload.get("ended") is not None and not _valid_date(payload["ended"]))
                or not valid_signature(payload.get("classes"))):
            raise ValueError(f"Invalid Machine Era payload: {path}")
    return payload


def _reference_map(records: dict[str, dict], members: dict[str, dict]) -> dict[str, int]:
    """Prove that every witnessed Daily Om resolves to two assets and an era."""
    counts = {"days": 0, "legacyDays": 0, "journals": 0, "eras": 0}
    for path, payload in records.items():
        kind, _ = _kind(path)
        if kind == "journal":
            counts["journals"] += 1
        elif kind == "machine-era":
            counts["eras"] += 1
        elif kind == "history":
            counts["days"] += 1
            if payload.get("archiveOrigin") == "legacy-reading":
                legacy_machine = payload.get("machine")
                if payload.get("artwork") or (isinstance(legacy_machine, dict) and legacy_machine.get("eraId")):
                    raise ValueError("Legacy reading claims partial artwork or Machine Era provenance")
                counts["legacyDays"] += 1
                continue
            machine = payload.get("machine")
            artwork = payload.get("artwork")
            if not isinstance(machine, dict) or not isinstance(artwork, dict):
                raise ValueError(f"Daily Om lacks artwork or Machine Era: {path}")
            era_id = machine.get("eraId")
            era_path = f"machine-eras/{era_id}.json"
            if not _valid_era_id(era_id) or era_path not in records:
                raise ValueError(f"Daily Om references unavailable Machine Era: {path}")
            for field, media in (("master", "image/svg+xml"), ("visualWitness", "image/png")):
                ref = artwork.get(field)
                if not isinstance(ref, dict):
                    raise ValueError(f"Daily Om lacks {field}: {path}")
                target, digest = ref.get("relativePath"), ref.get("sha256")
                if not isinstance(target, str) or not isinstance(digest, str):
                    raise ValueError(f"Malformed artwork reference: {path}")
                target_kind, target_digest = _kind(target)
                if (target_kind != ("artifact-svg" if field == "master" else "artifact-png")
                        or target_digest != digest or ref.get("format") != media
                        or target not in members or members[target]["sha256"] != digest
                        or ref.get("bytes") != members[target]["bytes"]):
                    raise ValueError(f"Daily Om references unavailable artwork: {path}")
    return counts


def _manifest(members: list[dict]) -> dict:
    return envelope("archive-manifest", {
        "archiveId": str(uuid.uuid7()) if hasattr(uuid, "uuid7") else _uuid7(),
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "full",
        "base": None,
        "removedPaths": [],
        "members": members,
    })


def _uuid7() -> str:
    # Reuse the protocol's UUIDv7 generator without depending on Python 3.14.
    from experience import _era_id
    return _era_id()


def _validate_manifest(document: dict) -> tuple[dict, dict[str, dict]]:
    payload = verify_envelope(document, "archive-manifest")
    if (set(payload) != {"archiveId", "createdAt", "mode", "base", "removedPaths", "members"}
            or not _valid_era_id(payload["archiveId"])
            or not isinstance(payload["createdAt"], str)
            or not payload["createdAt"].endswith("Z")):
        raise ValueError("Invalid Ominity archive manifest")
    try:
        datetime.fromisoformat(payload["createdAt"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid archive creation time") from error
    if payload["mode"] != "full" or payload["base"] is not None or payload["removedPaths"] != []:
        raise ValueError("Only self-contained full Ominity archives are supported")
    entries = payload["members"]
    if not isinstance(entries, list) or len(entries) > MAX_MEMBERS:
        raise ValueError("Archive member count exceeds limit")
    paths = []
    members = {}
    total = 0
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "mediaType", "bytes", "sha256"}:
            raise ValueError("Invalid archive manifest member")
        path = entry["path"]
        _kind(path)
        digest = entry["sha256"]
        size = entry["bytes"]
        if (entry["mediaType"] != _media_type(path) or not isinstance(digest, str) or not HEX.fullmatch(digest)
                or type(size) is not int or size < 0 or size > _limit(path)):
            raise ValueError(f"Invalid archive member metadata: {path}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Archive total size exceeds limit")
        paths.append(path)
        members[path] = entry
    if paths != sorted(set(paths)):
        raise ValueError("Archive member paths must be unique and sorted")
    return payload, members


def _safe_source(root: Path, path: str) -> Path:
    _kind(path)
    target = root
    for segment in path.split("/"):
        target = target / segment
        if target.is_symlink():
            raise ValueError(f"Symlink in Ominity archive source or destination: {path}")
    return target


def _source_metadata(root: Path, path: str) -> tuple[dict, dict | None]:
    target = _safe_source(root, path)
    if not target.is_file():
        raise ValueError(f"Missing archive source: {path}")
    if target.stat().st_size > _limit(path):
        raise ValueError(f"Archive member too large: {path}")
    digest = hashlib.sha256()
    size = 0
    header = b""
    with target.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            size += len(chunk)
            if size > _limit(path):
                raise ValueError(f"Archive member too large: {path}")
            if len(header) < 4096:
                header += chunk[:4096 - len(header)]
            digest.update(chunk)
    kind, key = _kind(path)
    if kind.startswith("artifact-"):
        if digest.hexdigest() != key:
            raise ValueError(f"Artifact path digest mismatch: {path}")
        if kind == "artifact-png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid PNG witness: {path}")
        if kind == "artifact-svg" and b"<svg" not in header:
            raise ValueError(f"Invalid SVG master: {path}")
        payload = None
    else:
        payload = _validate_record(path, target.read_bytes())
    return {"path": path, "mediaType": _media_type(path), "bytes": size,
            "sha256": digest.hexdigest()}, payload


def _collect_source(state_root: Path) -> tuple[dict[str, dict], dict[str, int]]:
    root = Path(state_root)
    members = {}
    records = {}
    for subdir, pattern in (("history", "*/*.json"), ("journal", "*/*.json"),
                            ("machine-eras", "*.json")):
        folder = root / subdir
        if folder.is_symlink():
            raise ValueError("Symlink in Ominity archive source")
        if folder.exists():
            for target in folder.glob(pattern):
                path = target.relative_to(root).as_posix()
                members[path], records[path] = _source_metadata(root, path)
    for path, payload in list(records.items()):
        if _kind(path)[0] != "history" or payload.get("archiveOrigin") == "legacy-reading":
            continue
        artwork = payload.get("artwork", {})
        for ref in (artwork.get("master"), artwork.get("visualWitness")):
            if not isinstance(ref, dict) or not isinstance(ref.get("relativePath"), str):
                raise ValueError(f"Incomplete artwork reference: {path}")
            target = ref["relativePath"]
            if target not in members:
                members[target], _ = _source_metadata(root, target)
    if len(members) > MAX_MEMBERS or sum(member["bytes"] for member in members.values()) > MAX_TOTAL_BYTES:
        raise ValueError("Ominity archive exceeds resource limits")
    counts = _reference_map(records, members)
    return members, counts


def export_archive(state_root: Path, output_path: Path, *, overwrite: bool = False) -> dict:
    """Write a complete portable ZIP without replacing an existing backup by default."""
    root = Path(state_root)
    output = Path(output_path)
    if output.is_symlink() or (output.exists() and not overwrite):
        raise FileExistsError(f"Ominity archive output already exists: {output}")
    source_members, counts = _collect_source(root)
    if not counts["days"]:
        raise ValueError("No Daily Oms are available to export")
    members = [source_members[path] for path in sorted(source_members)]
    document = _manifest(members)
    _validate_manifest(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ominity-archive-", suffix=".zip", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                                 allowZip64=True) as archive:
                archive.writestr("manifest.json", canonical_json(document) + b"\n")
                for member in members:
                    digest = hashlib.sha256()
                    count = 0
                    with _safe_source(root, member["path"]).open("rb") as source, archive.open(member["path"], "w") as dest:
                        while chunk := source.read(CHUNK):
                            count += len(chunk)
                            if count > member["bytes"]:
                                raise ValueError(f"Source changed during export: {member['path']}")
                            digest.update(chunk)
                            dest.write(chunk)
                    if count != member["bytes"] or digest.hexdigest() != member["sha256"]:
                        raise ValueError(f"Source changed during export: {member['path']}")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        if overwrite:
            os.replace(temporary, output)
        else:
            os.link(temporary, output)
            os.unlink(temporary)
        directory_fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"archiveId": document["record"]["payload"]["archiveId"], "path": str(output),
            "members": len(members), **counts}


def _zip_members(archive: zipfile.ZipFile) -> tuple[dict, dict[str, dict]]:
    infos = archive.infolist()
    if len(infos) > MAX_MEMBERS + 1 or len({info.filename for info in infos}) != len(infos):
        raise ValueError("Archive has too many or duplicate ZIP entries")
    if not infos or sum(info.filename == "manifest.json" for info in infos) != 1:
        raise ValueError("Archive manifest is missing")
    for info in infos:
        if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("Archive contains a directory or symlink")
        if info.filename != "manifest.json":
            _kind(info.filename)
    manifest_info = archive.getinfo("manifest.json")
    if manifest_info.file_size > MAX_MANIFEST_BYTES:
        raise ValueError("Archive manifest exceeds size limit")
    document = _read_json(archive.read(manifest_info))
    payload, members = _validate_manifest(document)
    if set(info.filename for info in infos) != set(members) | {"manifest.json"}:
        raise ValueError("ZIP entries differ from the verified manifest")
    for info in infos:
        if info.filename in members and info.file_size != members[info.filename]["bytes"]:
            raise ValueError(f"ZIP size differs from manifest: {info.filename}")
    return payload, members


def _extract_verified(archive_path: Path, staged: Path) -> tuple[dict, dict[str, dict], dict[str, int]]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        payload, members = _zip_members(archive)
        records = {}
        for path, entry in members.items():
            target = staged / path
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            digest = hashlib.sha256()
            count = 0
            with archive.open(path) as source, target.open("xb") as output:
                os.chmod(target, 0o600)
                while chunk := source.read(CHUNK):
                    count += len(chunk)
                    if count > entry["bytes"]:
                        raise ValueError(f"Expanded archive member exceeds declared size: {path}")
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            if count != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                raise ValueError(f"Archive member digest or size mismatch: {path}")
            if _kind(path)[0].startswith("artifact-"):
                _validate_record(path, target.read_bytes())
            else:
                records[path] = _validate_record(path, target.read_bytes())
        counts = _reference_map(records, members)
        return payload, members, counts


def verify_archive(archive_path: Path) -> dict:
    """Verify every member and all historical references without importing."""
    with tempfile.TemporaryDirectory(prefix="ominity-verify-") as directory:
        payload, members, counts = _extract_verified(Path(archive_path), Path(directory))
    return {"archiveId": payload["archiveId"], "members": len(members), **counts}


@contextmanager
def _import_lock(root: Path):
    locks = root / "locks"
    locks.mkdir(mode=0o700, parents=True, exist_ok=True)
    if locks.is_symlink():
        raise ValueError("Invalid Ominity lock directory")
    fd = os.open(locks / "archive.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_mode & 0o777 != 0o600:
            raise ValueError("Ominity archive lock must have mode 0600")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _digest_file(path: Path, limit: int) -> str:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            size += len(chunk)
            if size > limit:
                raise ValueError("Existing Ominity file exceeds archive limit")
            digest.update(chunk)
    return digest.hexdigest()


def _publish_new(source: Path, target: Path) -> bool:
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.parent.is_symlink() or target.is_symlink():
        raise ValueError("Invalid Ominity import destination")
    os.chmod(target.parent, 0o700)
    try:
        os.link(source, target)
    except FileExistsError:
        return False
    _fsync_dir(target.parent)
    return True


def import_archive(archive_path: Path, state_root: Path, *, journal_policy: str = "keep") -> dict:
    """Verify all bytes first, then publish without replacing immutable history.

    ``journal_policy='keep'`` preserves edited local reflections. ``'replace'``
    first backs them up under archive-conflicts/<archiveId>/local/.
    """
    if journal_policy not in {"keep", "replace"}:
        raise ValueError("journal_policy must be 'keep' or 'replace'")
    root = Path(state_root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("Invalid Ominity state directory")
    os.chmod(root, 0o700)
    staging_root = root / "staging"
    staging_root.mkdir(mode=0o700, exist_ok=True)
    if staging_root.is_symlink():
        raise ValueError("Invalid Ominity staging directory")
    os.chmod(staging_root, 0o700)
    with tempfile.TemporaryDirectory(prefix="archive-", dir=staging_root) as directory:
        staged = Path(directory)
        payload, members, counts = _extract_verified(Path(archive_path), staged)
        conflicts = []
        journal_conflicts = []
        with _import_lock(root):
            for path in members:
                target = _safe_source(root, path)
                if not target.exists():
                    continue
                if _kind(path)[0] != "journal" and (
                        not target.is_file() or _digest_file(target, _limit(path)) != members[path]["sha256"]):
                    conflicts.append(path)
            if conflicts:
                raise ArchiveConflict(conflicts)
            imported = 0
            # Assets and eras are published before JSON history commit markers.
            order = {"artifact-svg": 0, "artifact-png": 0, "machine-era": 1,
                     "journal": 2, "history": 3}
            for path in sorted(members, key=lambda item: (order[_kind(item)[0]], item)):
                kind, _ = _kind(path)
                target = _safe_source(root, path)
                source = staged / path
                if kind == "journal":
                    with _journal_lock(root, _kind(path)[1]):
                        local_digest = _digest_file(target, _limit(path)) if target.exists() else None
                        if local_digest is not None and local_digest != members[path]["sha256"]:
                            if journal_policy == "keep":
                                journal_conflicts.append(path)
                                continue
                            backup = root / "archive-conflicts" / payload["archiveId"] / "local" / local_digest / path
                            cursor = root
                            for segment in backup.relative_to(root).parts:
                                cursor = cursor / segment
                                if cursor.is_symlink():
                                    raise ValueError("Symlink in archive conflict backup path")
                            backup.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                            os.chmod(target, 0o600)
                            if not backup.exists() and not _publish_new(target, backup):
                                raise ValueError("Could not preserve local journal before replacement")
                            os.replace(source, target)
                            _fsync_dir(target.parent)
                            imported += 1
                        elif _publish_new(source, target):
                            imported += 1
                elif _publish_new(source, target):
                    imported += 1
                elif _digest_file(target, _limit(path)) != members[path]["sha256"]:
                    raise ArchiveConflict([path])
        return {"archiveId": payload["archiveId"], "imported": imported,
                "journalConflicts": journal_conflicts if journal_policy == "keep" else [], **counts}
