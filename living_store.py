"""Durable, verified local archive for Ominity Daily Oms.

The dated JSON is the commit marker. Artwork is flushed, published, and
verified before that marker can appear. All callers serialize a day with the
same advisory lock used by the drawing boundary.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from experience import (canonical_json, commit_machine_era, envelope,
                        load_era_state, verify_envelope, _unique_pairs)


DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _day(day: str) -> None:
    if not isinstance(day, str) or not DAY.fullmatch(day):
        raise ValueError("Invalid Ominity day")
    date.fromisoformat(day)


def history_path(root: Path, day: str) -> Path:
    _day(day)
    return root / "history" / day[:4] / f"{day}.json"


def _fsync_dir(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _private_directory(path: Path) -> None:
    missing = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        _fsync_dir(directory.parent)
    if path.is_symlink():
        raise ValueError("Ominity archive directory may not be a symlink")
    if not path.is_dir():
        raise ValueError("Ominity archive path is not a directory")
    os.chmod(path, 0o700)


def _write_fsynced(path: Path, contents: bytes) -> None:
    with path.open("xb") as handle:
        os.chmod(path, 0o600)
        handle.write(contents)
        handle.flush()
        os.fsync(handle.fileno())


def _parse(path: Path, record_type: str) -> dict:
    if path.is_symlink():
        raise ValueError("Ominity archive record may not be a symlink")
    if path.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Ominity archive record must have mode 0600")
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    return verify_envelope(document, record_type)


def _art_path(root: Path, digest: str, extension: str) -> Path:
    if not isinstance(digest, str) or not SHA.fullmatch(digest) or extension not in {"svg", "png"}:
        raise ValueError("Invalid Ominity artwork reference")
    return root / "artifacts" / "sha256" / digest[:2] / f"{digest}.{extension}"


def _reference(root: Path, contents: bytes, extension: str) -> dict:
    digest = hashlib.sha256(contents).hexdigest()
    path = _art_path(root, digest, extension)
    return {
        "sha256": digest,
        "format": "image/svg+xml" if extension == "svg" else "image/png",
        "relativePath": path.relative_to(root).as_posix(),
        "bytes": len(contents),
    }


def _png_dimensions(contents: bytes) -> tuple[int, int]:
    if len(contents) < 24 or contents[:8] != PNG_SIGNATURE or contents[12:16] != b"IHDR":
        raise ValueError("Ominity visual witness is not a PNG")
    width, height = struct.unpack(">II", contents[16:24])
    if width < 1 or height < 1 or width * 12 != height * 7:
        raise ValueError("Ominity visual witness must retain 7:12 geometry")
    return width, height


def _verify_artifact(root: Path, item: dict, extension: str) -> str:
    if not isinstance(item, dict):
        return "missing"
    digest = item.get("sha256")
    try:
        path = _art_path(root, digest, extension)
    except ValueError:
        return "modified"
    if item.get("relativePath") != path.relative_to(root).as_posix():
        return "modified"
    if path.is_symlink():
        return "modified"
    try:
        contents = path.read_bytes()
    except FileNotFoundError:
        return "missing"
    if hashlib.sha256(contents).hexdigest() != digest or item.get("bytes") != len(contents):
        return "modified"
    if extension == "png":
        try:
            if _png_dimensions(contents) != (item.get("width"), item.get("height")):
                return "modified"
        except ValueError:
            return "modified"
    return "verified"


def artwork_status(root: Path, payload: dict) -> dict:
    artwork = payload.get("artwork")
    if not isinstance(artwork, dict):
        return {"master": "legacy-unwitnessed", "visualWitness": "legacy-unwitnessed", "original": False}
    master = _verify_artifact(root, artwork.get("master"), "svg")
    witness = _verify_artifact(root, artwork.get("visualWitness"), "png")
    return {"master": master, "visualWitness": witness, "original": master == witness == "verified"}


def load_daily(root: Path, day: str) -> dict | None:
    path = history_path(root, day)
    try:
        payload = _parse(path, "daily-om")
    except FileNotFoundError:
        return None
    if payload.get("day") != day or payload.get("id") is None or type(payload.get("reversed")) is not bool:
        raise ValueError("Invalid Ominity Daily Om payload")
    return payload


def _publish_object(root: Path, staged: Path, reference: dict, extension: str) -> None:
    target = _art_path(root, reference["sha256"], extension)
    _private_directory(target.parent)
    if target.exists() or target.is_symlink():
        if _verify_artifact(root, reference, extension) != "verified":
            raise ValueError("Existing Ominity artwork object has conflicting bytes")
        return
    # Hard link is an atomic no-overwrite publication on the same filesystem.
    try:
        os.link(staged, target, follow_symlinks=False)
    except FileExistsError:
        if _verify_artifact(root, reference, extension) != "verified":
            raise ValueError("Existing Ominity artwork object has conflicting bytes")
    _fsync_dir(target.parent)
    if _verify_artifact(root, reference, extension) != "verified":
        raise ValueError("Published Ominity artwork failed verification")


def commit_daily(root: Path, reading: dict, svg_bytes: bytes, png_bytes: bytes,
                 renderer_version: int = 1,
                 before_commit: Callable[[], None] | None = None) -> dict:
    """Commit one canonical Daily Om; never replace a committed day."""
    day = reading.get("day")
    destination = history_path(root, day)
    prior = load_daily(root, day)
    if prior is not None:
        return prior
    if not isinstance(svg_bytes, bytes) or not svg_bytes.lstrip().startswith(b"<svg"):
        raise ValueError("Ominity structural master must be SVG bytes")
    if not isinstance(png_bytes, bytes):
        raise ValueError("Ominity visual witness must be PNG bytes")
    width, height = _png_dimensions(png_bytes)
    master = _reference(root, svg_bytes, "svg")
    witness = _reference(root, png_bytes, "png")
    witness.update({"width": width, "height": height, "aspectRatio": "7:12"})
    persisted = dict(reading)
    persisted["artwork"] = {"rendererVersion": renderer_version, "master": master, "visualWitness": witness}
    document = envelope("daily-om", persisted)
    candidate = canonical_json(document) + b"\n"
    _private_directory(root)
    staging_root = root / "staging"
    _private_directory(staging_root)
    stage = Path(tempfile.mkdtemp(prefix="daily-", dir=staging_root))
    os.chmod(stage, 0o700)
    try:
        _write_fsynced(stage / "card.svg", svg_bytes)
        _write_fsynced(stage / "card.png", png_bytes)
        _write_fsynced(stage / "daily.json", candidate)
        _fsync_dir(stage)
        for name, content in (("master", svg_bytes), ("visualWitness", png_bytes)):
            if hashlib.sha256(content).hexdigest() != persisted["artwork"][name]["sha256"]:
                raise ValueError("Staged Ominity artwork digest mismatch")
        verify_envelope(json.loads(candidate, object_pairs_hook=_unique_pairs), "daily-om")
        _publish_object(root, stage / "card.svg", master, "svg")
        _publish_object(root, stage / "card.png", witness, "png")
        if artwork_status(root, persisted)["original"] is not True:
            raise ValueError("Ominity artwork is not verified")
        if before_commit is not None:
            before_commit()
        _private_directory(destination.parent)
        _fsync_dir(destination.parent.parent)
        # Caller holds the day lock. A hard link also protects against an
        # accidental second writer that bypasses it.
        try:
            os.link(stage / "daily.json", destination, follow_symlinks=False)
        except FileExistsError:
            existing = load_daily(root, day)
            if existing is None:
                raise
            return existing
        _fsync_dir(destination.parent)
        return persisted
    finally:
        shutil.rmtree(stage)


def commit_legacy(root: Path, event: dict, card: dict | None = None) -> dict:
    """Preserve a pre-archive daily draw without claiming original artwork."""
    day = event.get("day")
    destination = history_path(root, day)
    prior = load_daily(root, day)
    if prior is not None:
        return prior
    payload = dict(event)
    payload["redraw"] = False
    payload["archiveOrigin"] = "legacy-reading"
    if card is not None:
        payload["canonicalSnapshot"] = dict(card)
    _private_directory(root)
    _private_directory(destination.parent)
    candidate = canonical_json(envelope("daily-om", payload)) + b"\n"
    fd, name = tempfile.mkstemp(prefix="legacy-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(candidate)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(name, destination)
        except FileExistsError:
            return load_daily(root, day)
        _fsync_dir(destination.parent)
        return payload
    finally:
        os.unlink(name)


def list_daily(root: Path) -> list[dict]:
    history = root / "history"
    if not history.exists():
        return []
    records = []
    for path in sorted(history.glob("[0-9][0-9][0-9][0-9]/*.json")):
        _day(path.stem)
        if path.parent.name != path.stem[:4]:
            raise ValueError("Misplaced Ominity Daily Om")
        item = _parse(path, "daily-om")
        if item.get("day") != path.stem:
            raise ValueError("Ominity Daily Om filename and date disagree")
        records.append(item)
    return records


def commit_redraw_art(root: Path, reading: dict, svg_bytes: bytes, png_bytes: bytes) -> dict:
    """Publish artwork for a redraw before its bounded log entry is saved."""
    width, height = _png_dimensions(png_bytes)
    if not svg_bytes.lstrip().startswith(b"<svg"):
        raise ValueError("Ominity redraw master must be SVG")
    master = _reference(root, svg_bytes, "svg")
    witness = _reference(root, png_bytes, "png")
    witness.update({"width": width, "height": height, "aspectRatio": "7:12"})
    _private_directory(root)
    staging_root = root / "staging"
    _private_directory(staging_root)
    stage = Path(tempfile.mkdtemp(prefix="daily-", dir=staging_root))
    try:
        _write_fsynced(stage / "card.svg", svg_bytes)
        _write_fsynced(stage / "card.png", png_bytes)
        _fsync_dir(stage)
        _publish_object(root, stage / "card.svg", master, "svg")
        _publish_object(root, stage / "card.png", witness, "png")
    finally:
        shutil.rmtree(stage)
    result = dict(reading)
    result["artwork"] = {"rendererVersion": 1, "master": master, "visualWitness": witness}
    if not artwork_status(root, result)["original"]:
        raise ValueError("Ominity redraw artwork failed verification")
    return result


def sync_era_records(root: Path, eras: list[dict]) -> None:
    """Publish portable per-era records before a Daily Om references them.

    An era's end date may change when a transition is confirmed. The local
    active state remains authoritative for new draws; these records are the
    archive's verified historical descriptions.
    """
    directory = root / "machine-eras"
    _private_directory(directory)
    for era in eras:
        identifier = era.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[0-9a-f-]{36}", identifier):
            raise ValueError("Invalid Ominity Machine Era ID")
        path = directory / f"{identifier}.json"
        contents = canonical_json(envelope("machine-era", era)) + b"\n"
        if path.exists() and path.read_bytes() == contents:
            continue
        fd, name = tempfile.mkstemp(prefix="era-", dir=directory)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, path)
            _fsync_dir(directory)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def list_era_records(root: Path) -> list[dict]:
    directory = root / "machine-eras"
    if not directory.exists():
        return []
    eras = []
    for path in sorted(directory.glob("*.json")):
        era = _parse(path, "machine-era")
        if era.get("id") != path.stem:
            raise ValueError("Ominity Machine Era filename and ID disagree")
        eras.append(era)
    return eras


def stage_era_update(root: Path, day: str, state: dict) -> None:
    """Durably record an era change that is conditional on a Daily Om commit."""
    _day(day)
    pending = root / "pending-eras"
    _private_directory(pending)
    path = pending / f"{day}.json"
    if path.exists():
        raise ValueError("Ominity era update is already pending")
    document = envelope("pending-era", {"day": day, "state": state})
    _write_fsynced(path, canonical_json(document) + b"\n")
    _fsync_dir(pending)


def _remove_pending(path: Path) -> None:
    path.unlink()
    _fsync_dir(path.parent)


def finalize_era_update(root: Path, day: str) -> None:
    """Apply an era change only after its Daily Om commit marker exists."""
    path = root / "pending-eras" / f"{day}.json"
    if not path.exists():
        return
    update = _parse(path, "pending-era")
    if update.get("day") != day or not isinstance(update.get("state"), dict):
        raise ValueError("Invalid Ominity pending era update")
    daily = load_daily(root, day)
    if daily is None:
        raise ValueError("Ominity Daily Om is not committed")
    if daily.get("machine", {}).get("eraId") != update["state"].get("activeId"):
        raise ValueError("Ominity Daily Om and pending era disagree")
    commit_machine_era(root, update["state"])
    _remove_pending(path)


def recover_era_updates(root: Path) -> int:
    """Idempotently finish committed changes and discard uncommitted ones."""
    pending = root / "pending-eras"
    if not pending.exists():
        return 0
    count = 0
    for path in sorted(pending.glob("*.json")):
        _day(path.stem)
        update = _parse(path, "pending-era")
        if update.get("day") != path.stem or not isinstance(update.get("state"), dict):
            raise ValueError("Invalid Ominity pending era update")
        if load_daily(root, path.stem) is not None:
            finalize_era_update(root, path.stem)
        else:
            # The JSON marker never landed. Local active state is unchanged;
            # restore any old era's end date and remove a newly staged era.
            current = load_era_state(root)
            live = {era["id"] for era in current["eras"]} if current else set()
            referenced = {item.get("machine", {}).get("eraId") for item in list_daily(root)}
            for era in update["state"].get("eras", []):
                identifier = era.get("id")
                if identifier not in live and identifier not in referenced:
                    orphan = root / "machine-eras" / f"{identifier}.json"
                    if orphan.exists():
                        orphan.unlink()
                        _fsync_dir(orphan.parent)
            if current:
                sync_era_records(root, current["eras"])
            _remove_pending(path)
        count += 1
    return count


def recover(root: Path) -> int:
    """Remove abandoned private staging directories, keeping published objects."""
    staging = root / "staging"
    if not staging.exists():
        return 0
    removed = 0
    for path in staging.iterdir():
        if path.name.startswith("daily-") and path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
            removed += 1
    if removed:
        _fsync_dir(staging)
    return removed


def statistics(records: list[dict], redraw_count: int, today: str, storage_bytes: int = 0,
               deck_cards: dict[str, dict] | None = None, eras: list[dict] | None = None) -> dict:
    _day(today)
    cards = {}
    last_seen = {}
    arcana = {"major": 0, "minor": 0}
    orientations = {"upright": 0, "reversed": 0}
    suits = {}
    elements = {}
    days = sorted({entry["day"] for entry in records})
    for entry in records:
        card_id = entry["id"]
        cards[card_id] = cards.get(card_id, 0) + 1
        last_seen[card_id] = max(last_seen.get(card_id, ""), entry["day"])
        card = entry.get("canonicalSnapshot") or {}
        kind = card.get("arcana") or ("major" if card_id.startswith("major-") else "minor")
        arcana[kind] = arcana.get(kind, 0) + 1
        orientations["reversed" if entry["reversed"] else "upright"] += 1
        for target, value in ((suits, card.get("suit")), (elements, card.get("element"))):
            if value:
                target[value] = target.get(value, 0) + 1
    count = len(records)
    ratio = lambda value: round(value / count, 4) if count else 0.0
    suit_total = sum(suits.values())
    element_total = sum(elements.values())
    longest = current = 0
    previous = None
    for value in days:
        current = current + 1 if previous and (date.fromisoformat(value) - date.fromisoformat(previous)).days == 1 else 1
        longest = max(longest, current)
        previous = value
    eligible = [value for value in days if value <= today]
    current = 0
    if eligible and (date.fromisoformat(today) - date.fromisoformat(eligible[-1])).days <= 1:
        cursor = date.fromisoformat(eligible[-1])
        day_set = set(eligible)
        while cursor.isoformat() in day_set:
            current += 1
            cursor -= timedelta(days=1)
    top = sorted(cards.items(), key=lambda item: (-item[1], item[0]))[:10]
    deck_cards = deck_cards or {}
    per_card = [{
        "id": key, "title": card.get("title", key), "suit": card.get("suit"),
        "arcana": card.get("arcana"), "count": cards.get(key, 0),
        "percent": ratio(cards.get(key, 0)), "lastDay": last_seen.get(key),
        "daysSince": ((date.fromisoformat(today) - date.fromisoformat(last_seen[key])).days
                      if key in last_seen and last_seen[key] <= today else None),
    } for key, card in deck_cards.items()]
    windows = {}
    for span in (7, 30, 90):
        selected = [entry for entry in records if 0 <= (date.fromisoformat(today) - date.fromisoformat(entry["day"])).days < span]
        n = len(selected)
        window_cards = {}
        window_arcana = {"major": 0, "minor": 0}
        window_orientation = {"upright": 0, "reversed": 0}
        window_suits = {}
        for entry in selected:
            key = entry["id"]
            window_cards[key] = window_cards.get(key, 0) + 1
            card = entry.get("canonicalSnapshot") or deck_cards.get(key, {})
            kind = card.get("arcana") or ("major" if key.startswith("major-") else "minor")
            window_arcana[kind] = window_arcana.get(kind, 0) + 1
            window_orientation["reversed" if entry["reversed"] else "upright"] += 1
            suit = card.get("suit")
            if suit:
                window_suits[suit] = window_suits.get(suit, 0) + 1
        wratio = lambda value: round(value / n, 4) if n else 0.0
        windows[str(span)] = {
            "days": n,
            "perCard": {key: window_cards.get(key, 0) for key in deck_cards},
            "arcana": {key: wratio(value) for key, value in window_arcana.items()},
            "orientation": {key: wratio(value) for key, value in window_orientation.items()},
            "suits": {key: round(value / sum(window_suits.values()), 4) for key, value in sorted(window_suits.items())},
        }
    era_days = {}
    for entry in records:
        era_id = entry.get("machine", {}).get("eraId")
        if era_id:
            era_days[era_id] = era_days.get(era_id, 0) + 1
    era_summary = [{"id": era["id"], "displayLabel": era["displayLabel"],
                    "started": era["started"], "ended": era["ended"],
                    "days": era_days.get(era["id"], 0)} for era in (eras or [])]
    return {
        "ok": True, "days": count, "uniqueCards": len(cards),
        "arcana": {key: ratio(value) for key, value in arcana.items()},
        "orientation": {key: ratio(value) for key, value in orientations.items()},
        "suits": {key: round(value / suit_total, 4) if suit_total else 0.0 for key, value in sorted(suits.items())},
        "elements": {key: round(value / element_total, 4) if element_total else 0.0 for key, value in sorted(elements.items())},
        "topCards": [{"id": key, "count": value, "percent": ratio(value)} for key, value in top],
        "streak": {"current": current, "longest": longest},
        "windows": windows, "perCard": per_card, "eras": era_summary,
        "redrawCount": redraw_count, "storageBytes": storage_bytes,
    }
