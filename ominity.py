#!/usr/bin/env python3
"""Small local state boundary for the Ominity Quickshell plugin.

No network, model, or account is needed to draw a card. CLI output is one JSON
object per invocation so the QML surface never has to parse mutable files.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from experience import capacity_signature, experience_for, installation_seed, weather_buckets

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


def run(action: str) -> dict:
    cards = deck()
    data = load_state()
    now = datetime.now().astimezone()
    day = now.date().isoformat()
    existing = data.get("reading") or {}

    if action in ("today", "redraw"):
        if action == "redraw" or existing.get("day") != day or existing.get("id") not in cards:
            card_id = choose(cards, existing.get("id"))
            reversed_card = bool(secrets.randbelow(2))
            previous_experience = existing.get("experience") if existing.get("day") == day else None
            if isinstance(previous_experience, dict) and isinstance(previous_experience.get("machineSignature"), dict) and isinstance(previous_experience.get("weather"), dict):
                signature = previous_experience["machineSignature"]
                weather = previous_experience["weather"]
            else:
                signature = capacity_signature()
                weather = weather_buckets()
            experience = experience_for(
                installation_seed(STATE_ROOT), day, card_id, reversed_card, signature, weather
            )
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
                "experience": experience,
            }
            history = data.get("history", [])
            if not isinstance(history, list):
                history = []
            data["history"] = (history + [new])[-90:]
            data["reading"] = new
            save_state(data)
    elif action == "widget-toggle":
        data["widget"] = data.get("widget") is not True
        save_state(data)
    elif action == "widget-show":
        data["widget"] = True
        save_state(data)
    elif action == "widget-hide":
        data["widget"] = False
        save_state(data)
    elif action != "state":
        raise ValueError(f"Unknown Ominity action: {action}")
    return payload(data, cards, day)


if __name__ == "__main__":
    try:
        print(json.dumps(run(sys.argv[1] if len(sys.argv) == 2 else "state"), ensure_ascii=False))
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
