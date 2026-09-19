#!/usr/bin/env python3
"""Install the workspace source into the user-owned Omarchy plugin directory."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
TARGET = CONFIG / "omarchy/plugins/oxquan.ominity"
SHELL = CONFIG / "omarchy/shell.json"
ADAPTER = CONFIG / "ominity/summary"


def planned_shell() -> tuple[dict, bool]:
    data = json.loads(SHELL.read_text(encoding="utf-8"))
    left = data["bar"]["layout"]["left"]
    plugins = data.setdefault("plugins", [])
    changed = False
    if not any(row.get("id") == "oxquan.ominity" for row in left):
        after = next((i for i, row in enumerate(left) if row.get("id") == "oxquan.division-resurgence"), len(left) - 1)
        left.insert(after + 1, {"id": "oxquan.ominity"})
        changed = True
    if not any(row.get("id") == "oxquan.ominity" for row in plugins):
        plugins.append({"id": "oxquan.ominity"})
        changed = True
    return data, changed


def check_source() -> int:
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    deck = json.loads((SOURCE / "deck/deck.json").read_text(encoding="utf-8"))
    cards = deck["cards"] if isinstance(deck, dict) else deck
    if manifest["id"] != "oxquan.ominity" or len(cards) != 78:
        raise ValueError("Invalid manifest or incomplete deck")
    if len({card["id"] for card in cards}) != 78:
        raise ValueError("Duplicate card ID")
    missing = [card["art"] for card in cards if not (SOURCE / card["art"]).is_file()]
    if missing:
        raise ValueError(f"Missing {len(missing)} card illustrations")
    for file in ("Desktop.qml", "BarWidget.qml", "ominity.py"):
        if not (SOURCE / file).is_file():
            raise ValueError(f"Missing {file}")
    return len(cards)


def install(adapter: Path | None) -> dict:
    count = check_source()
    shell, changed = planned_shell()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = STATE / "ominity/install-backups" / stamp
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(SHELL, backup / "shell.json")
    if ADAPTER.exists() or ADAPTER.is_symlink():
        shutil.copy2(ADAPTER, backup / "summary", follow_symlinks=False)
    stage = backup / "new-plugin"
    shutil.copytree(SOURCE, stage, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "test_*.py", ".install-backups"))
    prior = backup / "plugin"
    try:
        if TARGET.exists():
            TARGET.rename(prior)
        stage.rename(TARGET)
        if changed:
            SHELL.write_text(json.dumps(shell, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if adapter:
            if not adapter.is_file() or not os.access(adapter, os.X_OK):
                raise ValueError("Zephyr adapter must be an executable file")
            ADAPTER.parent.mkdir(parents=True, exist_ok=True)
            ADAPTER.unlink(missing_ok=True)
            ADAPTER.symlink_to(adapter.resolve())
    except Exception:
        if TARGET.exists():
            shutil.rmtree(TARGET)
        if prior.exists():
            prior.rename(TARGET)
        shutil.copy2(backup / "shell.json", SHELL)
        raise
    return {"installed": str(TARGET), "cards": count, "shellChanged": changed, "zephyr": bool(adapter), "backup": str(backup)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="write the plugin and shell config")
    parser.add_argument("--zephyr-adapter", type=Path, help="optional local summary executable")
    args = parser.parse_args()
    count = check_source()
    _, changed = planned_shell()
    if not args.install:
        print(json.dumps({"ready": True, "cards": count, "target": str(TARGET), "wouldChangeShell": changed}, indent=2))
        return
    print(json.dumps(install(args.zephyr_adapter), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Ominity install: {exc}", file=sys.stderr)
        raise SystemExit(1)
