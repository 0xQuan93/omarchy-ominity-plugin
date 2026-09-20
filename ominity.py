#!/usr/bin/env python3
"""Offline JSON boundary for Ominity's daily card and durable archive."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from experience import (canonical_json, capacity_signature, commit_machine_era,
                        envelope, experience_for, experience_seed,
                        installation_seed, load_era_state, prepare_machine_era,
                        valid_signature, valid_weather, verify_envelope,
                        weather_buckets, _unique_pairs)
from living_store import (artwork_status, commit_daily, commit_legacy,
                          commit_redraw_art, history_path, list_daily,
                          load_daily, recover, statistics, sync_era_records)

ROOT = Path(__file__).resolve().parent
STATE_ROOT = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "ominity"
STATE_FILE = STATE_ROOT / "reading.json"
REDRAW_LIMIT = 90


def deck() -> dict[str, dict]:
    raw = json.loads((ROOT / "deck/deck.json").read_text(encoding="utf-8"))
    cards = raw["cards"] if isinstance(raw, dict) else raw
    if len(cards) != 78 or len({card["id"] for card in cards}) != 78:
        raise ValueError("Ominity deck must contain 78 unique cards")
    return {card["id"]: card for card in cards}


def load_state() -> dict:
    if STATE_FILE.is_symlink():
        raise ValueError("Ominity state may not be a symlink")
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except FileNotFoundError:
        return {"widget": False, "history": []}
    except (OSError, ValueError):
        pass
    # Retain malformed bytes privately for manual recovery; never treat them
    # as a valid reading or leave an exposed state file behind.
    backup = STATE_FILE.with_name("reading-corrupt-" + secrets.token_hex(8) + ".json")
    os.replace(STATE_FILE, backup)
    os.chmod(backup, 0o600)
    fresh = {"widget": False, "history": []}
    save_state(fresh)
    return fresh


def _replace(path: Path, contents: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd, name = tempfile.mkstemp(prefix=path.stem + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_state(data: dict) -> None:
    _replace(STATE_FILE, json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")


def load_redraws() -> dict:
    path = STATE_ROOT / "redraws.json"
    if not path.exists():
        return {"totalCount": 0, "events": []}
    if path.is_symlink() or path.stat().st_mode & 0o777 != 0o600:
        raise ValueError("Ominity redraw log must have mode 0600")
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)
    result = verify_envelope(document, "redraw-log")
    if (type(result.get("totalCount")) is not int or result["totalCount"] < 0
            or not isinstance(result.get("events"), list)):
        raise ValueError("Invalid Ominity redraw log")
    return result


def save_redraws(data: dict) -> None:
    _replace(STATE_ROOT / "redraws.json", canonical_json(envelope("redraw-log", data)) + b"\n")


def migrate_legacy(data: dict, cards: dict[str, dict]) -> None:
    """Copy the old bounded history into permanent dates without changing it."""
    entries = list(data.get("history")) if isinstance(data.get("history"), list) else []
    current = data.get("reading")
    if isinstance(current, dict) and current not in entries:
        entries.append(current)
    if not entries:
        return
    redraws = load_redraws()
    seen = {hashlib.sha256(canonical_json(item)).hexdigest() for item in redraws["events"]}
    selected = {}
    changed = False
    for item in entries:
        if not isinstance(item, dict) or item.get("id") not in cards:
            continue
        try:
            history_path(STATE_ROOT, item.get("day"))
        except (TypeError, ValueError):
            continue
        if not item.get("redraw") and item["day"] not in selected:
            selected[item["day"]] = item
        if item.get("redraw"):
            key = hashlib.sha256(canonical_json(item)).hexdigest()
            if key not in seen:
                redraws["events"].append(item)
                redraws["totalCount"] += 1
                seen.add(key)
                changed = True
    for item in entries:
        if isinstance(item, dict) and item.get("id") in cards and item.get("day") not in selected:
            try:
                history_path(STATE_ROOT, item.get("day"))
            except (TypeError, ValueError):
                continue
            selected[item["day"]] = item
    for item in selected.values():
        commit_legacy(STATE_ROOT, item, cards[item["id"]])
    if changed:
        redraws["events"] = redraws["events"][-REDRAW_LIMIT:]
        save_redraws(redraws)


@contextmanager
def state_lock(name: str):
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
    """Compatibility lookup for the pre-archive state file."""
    current = data.get("reading")
    if isinstance(current, dict) and current.get("day") == day and current.get("id") in cards:
        return current
    history = data.get("history")
    if isinstance(history, list):
        for item in reversed(history):
            if isinstance(item, dict) and item.get("day") == day and item.get("id") in cards:
                return item
    return {}


def choose(cards: dict[str, dict], previous: str | None) -> str:
    ids = tuple(key for key in cards if key != previous)
    return ids[secrets.randbelow(len(ids))]


def _daypart(now: datetime) -> str:
    return "morning" if now.hour < 12 else "day" if now.hour < 18 else "evening"


def _time_snapshot(now: datetime) -> dict:
    key = getattr(now.tzinfo, "key", None)
    if key is None:
        tz_env = os.environ.get("TZ")
        if tz_env and re.fullmatch(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)+", tz_env):
            key = tz_env
    if key is None:
        try:
            key = Path("/etc/localtime").resolve(strict=True).relative_to("/usr/share/zoneinfo").as_posix()
        except (OSError, ValueError):
            pass
    offset = now.strftime("%z")
    return {"localDate": now.date().isoformat(),
            "localTimestamp": now.isoformat(timespec="seconds"),
            "utcTimestamp": now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "utcOffset": offset[:3] + ":" + offset[3:],
            "timezone": key, "timezoneSource": "system" if key else "unavailable",
            "timezoneDataVersion": None}


def _thread(records: list[dict], card_id: str, day: str) -> dict | None:
    previous = max((item["day"] for item in records if item["day"] < day and item["id"] == card_id), default=None)
    if previous is None:
        return None
    distance = (date.fromisoformat(day) - date.fromisoformat(previous)).days
    return {"type": "return", "text": f"This card returns after {distance} days.",
            "relationship": None,
            "evidence": {"previousDay": previous, "currentDay": day, "days": distance, "cardId": card_id}}


def _palette(colors: dict[str, str] | None):
    from deck.build_deck import DeckPalette
    if not colors:
        return DeckPalette()
    roles = ("background", "foreground", "accent", "muted")
    if set(colors) != set(roles) or any(not re.fullmatch(r"#[0-9a-fA-F]{6}", colors[role]) for role in roles):
        raise ValueError("Ominity theme colors must be four six-digit hex values")
    return DeckPalette.from_theme(*(colors[role] for role in roles))


def _new_reading(cards: dict[str, dict], now: datetime, card_id: str, reversed_card: bool,
                 seed: bytes, signature: dict, weather: dict, era_id: str,
                 records: list[dict], palette) -> tuple[dict, bytes, bytes]:
    from deck.experience_content import select_experience
    from deck.living_art import render_daily_art, motion_spec
    day = now.date().isoformat()
    card = cards[card_id]
    experience = experience_for(seed, day, card_id, reversed_card, signature, weather)
    experience.update(select_experience(card, experience_seed(seed, day, card_id, reversed_card, signature), _daypart(now)))
    experience["motion"] = motion_spec(card, experience)
    experience["thread"] = _thread(records, card_id, day)
    svg, png = render_daily_art(card, experience, palette)
    return ({"day": day, "id": card_id, "reversed": reversed_card,
             "drawnAt": now.isoformat(timespec="seconds"), "redraw": False,
             "time": _time_snapshot(now), "deckContentVersion": "1.1.0",
             "canonicalSnapshot": dict(card),
             "machine": {"eraId": era_id, "weather": dict(weather)},
             "experience": experience}, svg, png)


def _latest_reading(day: str, records: list[dict], redraws: dict) -> dict | None:
    for item in reversed(redraws["events"]):
        if item.get("day") == day:
            return item
    return next((item for item in records if item["day"] == day), None)


def _display(reading: dict | None, cards: dict[str, dict]) -> dict | None:
    if reading is None:
        return None
    result = dict(reading)
    result["card"] = reading.get("canonicalSnapshot") or cards.get(reading["id"])
    status = artwork_status(STATE_ROOT, reading)
    result["artworkStatus"] = status
    result["archiveStatus"] = "verified-original" if status["original"] else "legacy-or-damaged"
    result["artworkPath"] = (str(STATE_ROOT / reading["artwork"]["visualWitness"]["relativePath"])
                             if status["visualWitness"] == "verified" else None)
    return result


def _payload(data: dict, cards: dict[str, dict], day: str,
             records: list[dict], redraws: dict) -> dict:
    return {"ok": True, "day": day, "widget": data.get("widget") is True,
            "reading": _display(_latest_reading(day, records, redraws), cards),
            "historyCount": len(records) + redraws["totalCount"]}


def _storage_bytes() -> int:
    total = 0
    for folder in (STATE_ROOT / "history", STATE_ROOT / "artifacts", STATE_ROOT / "machine-eras"):
        if folder.exists():
            total += sum(path.stat().st_size for path in folder.rglob("*") if path.is_file() and not path.is_symlink())
    return total


def run(action: str, colors: dict[str, str] | None = None) -> dict:
    cards = deck()
    now = datetime.now().astimezone()
    day = now.date().isoformat()
    if action in ("today", "redraw"):
        # Lock order remains day -> state. Losers reload the committed day.
        with state_lock(day + ".lock"), state_lock("state.lock"):
            recover(STATE_ROOT)
            data = load_state()
            migrate_legacy(data, cards)
            records = list_daily(STATE_ROOT)
            redraws = load_redraws()
            canonical = load_daily(STATE_ROOT, day)
            if canonical is None:
                seed = installation_seed(STATE_ROOT)
                signature = capacity_signature()
                weather = weather_buckets()
                era_id, era_update = prepare_machine_era(STATE_ROOT, day, signature)
                previous = records[-1]["id"] if records else None
                card_id = choose(cards, previous)
                reading, svg, png = _new_reading(cards, now, card_id, bool(secrets.randbelow(2)),
                                                  seed, signature, weather, era_id, records, _palette(colors))
                # Artifact failure leaves the active era unchanged. The era
                # record is durable before the Daily Om commit marker.
                def prepare_reference() -> None:
                    current_era = era_update or load_era_state(STATE_ROOT)
                    sync_era_records(STATE_ROOT, current_era["eras"])
                    commit_machine_era(STATE_ROOT, era_update)

                canonical = commit_daily(STATE_ROOT, reading, svg, png,
                                         before_commit=prepare_reference)
                records.append(canonical)
            if action == "redraw":
                displayed = _latest_reading(day, records, redraws) or canonical
                previous_experience = canonical.get("experience") or {}
                signature = previous_experience.get("machineSignature")
                weather = previous_experience.get("weather")
                era_id = canonical.get("machine", {}).get("eraId")
                redraw_era_update = None
                if not valid_signature(signature) or not valid_weather(weather) or not isinstance(era_id, str):
                    signature = capacity_signature()
                    weather = weather_buckets()
                    era = load_era_state(STATE_ROOT)
                    if era:
                        era_id = era["activeId"]
                    else:
                        era_id, redraw_era_update = prepare_machine_era(STATE_ROOT, day, signature)
                seed = installation_seed(STATE_ROOT)
                card_id = choose(cards, displayed["id"])
                reading, svg, png = _new_reading(cards, now, card_id, bool(secrets.randbelow(2)),
                                                  seed, signature, weather, era_id, records, _palette(colors))
                reading["redraw"] = True
                reading = commit_redraw_art(STATE_ROOT, reading, svg, png)
                if redraw_era_update is not None:
                    sync_era_records(STATE_ROOT, redraw_era_update["eras"])
                    commit_machine_era(STATE_ROOT, redraw_era_update)
                redraws["events"] = (redraws["events"] + [reading])[-REDRAW_LIMIT:]
                redraws["totalCount"] += 1
                save_redraws(redraws)
            # Keep the old private adapter contract as a derived cache. The
            # dated canonical record and redraw log remain authoritative.
            latest = _latest_reading(day, records, redraws)
            if latest and latest.get("archiveOrigin") != "legacy-reading" and data.get("reading") != latest:
                data["reading"] = latest
                save_state(data)
            return _payload(data, cards, day, records, redraws)
    if action in ("state", "widget-toggle", "widget-show", "widget-hide", "stats", "history"):
        with state_lock("state.lock"):
            recover(STATE_ROOT)
            data = load_state()
            migrate_legacy(data, cards)
            if action.startswith("widget-"):
                data["widget"] = (not (data.get("widget") is True) if action == "widget-toggle"
                                  else action == "widget-show")
                save_state(data)
            records = list_daily(STATE_ROOT)
            redraws = load_redraws()
            if action == "stats":
                era_state = load_era_state(STATE_ROOT)
                return statistics(records, redraws["totalCount"], day, _storage_bytes(), cards,
                                  era_state["eras"] if era_state else [])
            if action == "history":
                days = []
                for item in reversed(records):
                    status = artwork_status(STATE_ROOT, item)
                    witness = item.get("artwork", {}).get("visualWitness", {})
                    days.append({
                        "day": item["day"], "id": item["id"],
                        "title": (item.get("canonicalSnapshot") or cards[item["id"]]).get("title"),
                        "reversed": item["reversed"],
                        "eraId": item.get("machine", {}).get("eraId"),
                        "artworkStatus": status,
                        "archiveStatus": "verified-original" if status["original"] else "legacy-or-damaged",
                        "artworkPath": str(STATE_ROOT / witness["relativePath"]) if status["visualWitness"] == "verified" else None,
                    })
                return {"ok": True, "days": days, "redrawCount": redraws["totalCount"]}
            return _payload(data, cards, day, records, redraws)
    raise ValueError(f"Unknown Ominity action: {action}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="state")
    for role in ("background", "foreground", "accent", "muted"):
        parser.add_argument("--" + role)
    args = parser.parse_args()
    colors = {role: getattr(args, role) for role in ("background", "foreground", "accent", "muted")
              if getattr(args, role) is not None}
    try:
        print(json.dumps(run(args.action, colors or None), ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
