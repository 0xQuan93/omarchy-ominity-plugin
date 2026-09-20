#!/usr/bin/env python3
"""Small local state boundary for the Ominity Quickshell plugin.

No network, model, or account is needed to draw a card. CLI output is one JSON
object per invocation so the QML surface never has to parse mutable files.
"""

from __future__ import annotations

import fcntl
import json
import os
import secrets
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from experience import (
    capacity_signature,
    experience_for,
    installation_seed,
    load_era_state,
    observe_machine_era,
    valid_signature,
    valid_weather,
    weather_buckets,
)

ROOT = Path(__file__).resolve().parent
STATE_ROOT = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "ominity"
STATE_FILE = STATE_ROOT / "reading.json"


def deck() -> dict[str, dict]:
    raw = json.loads((ROOT / "deck/deck.json").read_text(encoding="utf-8"))
    cards = raw["cards"] if isinstance(raw, dict) else raw
    if len(cards) != 78 or len({card["id"] for card in cards}) != 78:
        raise ValueError("Ominity deck must contain 78 unique cards")
    return {card["id"]: card for card in cards}


def load_state() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {"widget": False, "history": []}


def save_state(data: dict) -> None:
    STATE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE_ROOT, 0o700)
    fd, temp_name = tempfile.mkstemp(prefix="reading.", dir=STATE_ROOT, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, STATE_FILE)
        dir_fd = os.open(STATE_ROOT, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def payload(data: dict, cards: dict[str, dict], day: str) -> dict:
    current = data.get("reading") or {}
    if current.get("day") != day or current.get("id") not in cards:
        current = {}
    return {
        "ok": True,
        "day": day,
        "widget": data.get("widget") is True,
        "reading": current | {"card": cards[current["id"]]} if current else None,
        "historyCount": len(data.get("history", [])),
    }


def choose(cards: dict[str, dict], previous: str | None) -> str:
    ids = tuple(cards)
    if previous in cards:
        ids = tuple(card_id for card_id in ids if card_id != previous)
    return ids[secrets.randbelow(len(ids))]


@contextmanager
def state_lock(name: str):
    """Private advisory locks for a day and the shared mutable state files."""
    locks = STATE_ROOT / "locks"
    locks.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE_ROOT, 0o700)
    os.chmod(locks, 0o700)
    fd = os.open(locks / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_mode & 0o777 != 0o600:
            raise ValueError("Ominity lock must have mode 0600")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def reading_for_day(data: dict, day: str, cards: dict[str, dict]) -> dict:
    """Find the last recorded encounter for a day, including clock rollback."""
    current = data.get("reading")
    if isinstance(current, dict) and current.get("day") == day and current.get("id") in cards:
        return current
    history = data.get("history")
    if isinstance(history, list):
        for event in reversed(history):
            if isinstance(event, dict) and event.get("day") == day and event.get("id") in cards:
                return event
    return {}


def run(action: str) -> dict:
    cards = deck()
    now = datetime.now().astimezone()
    day = now.date().isoformat()

    if action in ("today", "redraw"):
        # Lock order is always day, then shared state. A second process must
        # reload after acquisition before it can sample or choose a card.
        with state_lock(day + ".lock"), state_lock("state.lock"):
            data = load_state()
            existing = reading_for_day(data, day, cards)
            if action == "today" and existing:
                data["reading"] = existing  # In-memory historical lookup only.
                return payload(data, cards, day)
            previous = data.get("reading") if isinstance(data.get("reading"), dict) else {}
            seed = installation_seed(STATE_ROOT)
            previous_experience = existing.get("experience") if existing else None
            previous_machine = existing.get("machine") if existing else None
            if (isinstance(previous_experience, dict)
                    and valid_signature(previous_experience.get("machineSignature"))
                    and valid_weather(previous_experience.get("weather"))
                    and isinstance(previous_machine, dict)
                    and isinstance(previous_machine.get("eraId"), str)):
                era_state = load_era_state(STATE_ROOT)
                if era_state is None or not any(
                    isinstance(era, dict) and era.get("id") == previous_machine["eraId"]
                    for era in era_state["eras"]
                ):
                    raise ValueError("Ominity reading references a missing Machine Era")
                signature = previous_experience["machineSignature"]
                weather = previous_experience["weather"]
                era_id = previous_machine["eraId"]
            else:
                signature = capacity_signature()
                era_id = observe_machine_era(STATE_ROOT, day, signature)
                weather = weather_buckets()
            card_id = choose(cards, existing.get("id") or previous.get("id"))
            reversed_card = bool(secrets.randbelow(2))
            experience = experience_for(seed, day, card_id, reversed_card, signature, weather)
            new = {
                "day": day,
                "id": card_id,
                "reversed": reversed_card,
                "drawnAt": now.isoformat(timespec="seconds"),
                "redraw": action == "redraw",
                "time": {
                    "localDate": day,
                    "localTimestamp": now.isoformat(timespec="seconds"),
                    "utcTimestamp": now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "utcOffset": now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:],
                    "timezone": getattr(now.tzinfo, "key", None),
                    "timezoneSource": "system" if getattr(now.tzinfo, "key", None) else "unavailable",
                },
                "machine": {"eraId": era_id, "weather": dict(weather)},
                "experience": experience,
            }
            history = data.get("history", [])
            if not isinstance(history, list):
                history = []
            data["history"] = (history + [new])[-90:]
            data["reading"] = new
            save_state(data)
            return payload(data, cards, day)
    if action in ("widget-toggle", "widget-show", "widget-hide"):
        with state_lock("state.lock"):
            data = load_state()
            if action == "widget-toggle":
                data["widget"] = data.get("widget") is not True
            else:
                data["widget"] = action == "widget-show"
            save_state(data)
            return payload(data, cards, day)
    if action != "state":
        raise ValueError(f"Unknown Ominity action: {action}")
    return payload(load_state(), cards, day)


if __name__ == "__main__":
    try:
        print(json.dumps(run(sys.argv[1] if len(sys.argv) == 2 else "state"), ensure_ascii=False))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
