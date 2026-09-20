"""Private, editable reflections kept apart from immutable Daily Oms."""

from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from experience import _unique_pairs, canonical_json, envelope, verify_envelope

MAX_REFLECTION_CHARS = 8192


def _day(day: str) -> str:
    if not isinstance(day, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise ValueError("Invalid journal day")
    try:
        date.fromisoformat(day)
    except ValueError as error:
        raise ValueError("Invalid journal day") from error
    return day


def journal_path(state_root: Path, day: str) -> Path:
    day = _day(day)
    return Path(state_root) / "journal" / day[:4] / f"{day}.json"


def _validate_payload(payload: dict, day: str) -> dict:
    if set(payload) != {"day", "firstImpression", "eveningReflection"} or payload["day"] != day:
        raise ValueError("Invalid Ominity journal payload")
    for key in ("firstImpression", "eveningReflection"):
        value = payload[key]
        if not isinstance(value, str) or len(value) > MAX_REFLECTION_CHARS:
            raise ValueError(f"Invalid journal {key}")
        value.encode("utf-8")
    return payload


def load_journal(state_root: Path, day: str) -> dict:
    path = journal_path(state_root, day)
    if not path.exists() and not path.is_symlink():
        return {"day": day, "firstImpression": "", "eveningReflection": ""}
    if path.is_symlink() or not path.is_file():
        raise ValueError("Invalid Ominity journal path")
    if path.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Ominity journal must have mode 0600")
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle, object_pairs_hook=_unique_pairs)
    return _validate_payload(verify_envelope(document, "journal"), _day(day))


@contextmanager
def _journal_lock(state_root: Path, day: str):
    locks = Path(state_root) / "locks"
    locks.mkdir(mode=0o700, parents=True, exist_ok=True)
    if locks.is_symlink():
        raise ValueError("Invalid Ominity lock directory")
    os.chmod(locks, 0o700)
    fd = os.open(locks / f"journal-{day}.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_mode & 0o777 != 0o600:
            raise ValueError("Ominity journal lock must have mode 0600")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def save_journal(state_root: Path, day: str, first_impression: str,
                 evening_reflection: str) -> dict:
    """Replace a reflection atomically; edits never touch canonical history."""
    day = _day(day)
    payload = _validate_payload({
        "day": day,
        "firstImpression": first_impression,
        "eveningReflection": evening_reflection,
    }, day)
    root = Path(state_root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("Invalid Ominity state directory")
    os.chmod(root, 0o700)
    path = journal_path(root, day)
    with _journal_lock(root, day):
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.parent.is_symlink() or path.is_symlink():
            raise ValueError("Invalid Ominity journal path")
        os.chmod(path.parent, 0o700)
        contents = canonical_json(envelope("journal", payload)) + b"\n"
        fd, temporary = tempfile.mkstemp(prefix=".journal-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return payload
