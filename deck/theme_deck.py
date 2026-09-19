#!/usr/bin/env python3
"""Render the original Ominity SVG deck in the live Omarchy theme palette.

The published plates remain untouched. A complete themed deck is written
atomically under the user's cache and reused for the same palette/source.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

if __package__:
    from .build_deck import DECK_DIR, DeckPalette, card_back_svg, card_svg
else:
    from build_deck import DECK_DIR, DeckPalette, card_back_svg, card_svg


def render_theme(background: str, foreground: str, accent: str, muted: str,
                 cache_home: Path | None = None) -> Path:
    colors = tuple(value.lower() for value in (background, foreground, accent, muted))
    if any(not re.fullmatch(r"#[0-9a-f]{6}", value) for value in colors):
        raise ValueError("Theme colors must be six-digit #RRGGBB values")
    palette = DeckPalette.from_theme(*colors)
    deck_file = DECK_DIR / "deck.json"
    source_file = Path(__file__).with_name("build_deck.py")
    deck_bytes = deck_file.read_bytes()
    source_bytes = source_file.read_bytes()
    digest = hashlib.sha256(b"ominity-theme-v1\0" + json.dumps(colors).encode()
                            + b"\0" + source_bytes + b"\0" + deck_bytes).hexdigest()[:20]
    if cache_home is None:
        cache_home = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    base = cache_home / "ominity" / "decks"
    base.mkdir(parents=True, exist_ok=True)
    target = base / digest

    # Theme changes can queue multiple shell processes; serialize completion
    # so a caller never sees a partially written collection of card faces.
    with (base / ".render.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (target / ".complete").is_file():
            return target
        if target.exists():
            shutil.rmtree(target)

        cards = json.loads(deck_bytes)
        if not isinstance(cards, list) or len(cards) != 78 or len({card["id"] for card in cards}) != 78:
            raise ValueError("Ominity deck must contain 78 unique cards")
        staging = Path(tempfile.mkdtemp(prefix=".render-", dir=base))
        try:
            for card in cards:
                art = card["art"]
                if not re.fullmatch(r"assets/cards/[a-z0-9-]+\.svg", art):
                    raise ValueError(f"Invalid card art path: {art!r}")
                destination = staging / art
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(card_svg(card, palette) + "\n", encoding="utf-8")
            (staging / "assets" / "card-back.svg").write_text(
                card_back_svg(palette) + "\n", encoding="utf-8")
            (staging / ".complete").write_text(digest + "\n", encoding="ascii")
            staging.rename(target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ("background", "foreground", "accent", "muted"):
        parser.add_argument(f"--{role}", required=True)
    args = parser.parse_args()
    try:
        directory = render_theme(args.background, args.foreground, args.accent, args.muted)
        print(json.dumps({"ok": True, "directory": str(directory)}))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
