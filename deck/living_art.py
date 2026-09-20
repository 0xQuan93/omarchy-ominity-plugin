"""Deterministic still artwork for a canonical Daily Om.

The authored tableau from ``card_svg`` remains the card.  A small, palette-aware
layer inside its illustration window makes the selected art symbol and coarse
machine weather visible.  Version 1 is intentionally static: the witness is
always captured at phase zero, and ``motion_spec`` records that no motion is
being promised by the renderer.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess

from .build_deck import DeckPalette, card_svg

WITNESS_WIDTH = 1400
WITNESS_HEIGHT = 2400
RENDERER_VERSION = 1
VARIANTS = ("glimmer", "trace", "ripple", "halo", "ember", "grain")
_PLATE_END = '</g>\n<path d="M41 410H77'


def _bucket(weather: dict, key: str) -> int:
    value = weather.get(key, 2)
    if type(value) is not int or not 0 <= value <= 4:
        raise ValueError(f"Machine weather {key!r} must be an integer from 0 to 4")
    return value


def _capacity(signature: dict, key: str, prefix: str) -> int:
    value = signature.get(key, prefix + "0")
    if not isinstance(value, str) or not re.fullmatch(prefix + r"[0-6]", value):
        return 0
    return int(value[-1])


def _variant(card: dict, experience: dict) -> str:
    symbol = experience.get("symbol")
    if isinstance(symbol, dict) and symbol.get("variant") in VARIANTS:
        return symbol["variant"]
    # Older records without a selected art symbol still get a stable motif.
    suit = card.get("suit")
    if suit == "Wands":
        return "ember"
    if suit == "Cups":
        return "ripple"
    if suit == "Swords":
        return "trace"
    if suit == "Pentacles":
        return "grain"
    return VARIANTS[int(hashlib.sha256(card["id"].encode("utf-8")).hexdigest()[:2], 16) % len(VARIANTS)]


def _coordinates(card_id: str, variant: int, index: int) -> tuple[int, int]:
    key = f"living-art-v1:{card_id}:{variant}:{index}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    # Marks sit in the edges of the authored scene so its main gesture survives.
    x = (39 + digest[0] % 29) if index % 2 == 0 else (213 + digest[0] % 29)
    y = 106 + digest[1] % 245
    return x, y


def _motif(kind: str, x: int, y: int, scale: float, color: str) -> str:
    size = 2.5 * scale
    if kind == "glimmer":
        return (f'<path d="M{x} {y-size:.2f}V{y+size:.2f}M{x-size:.2f} {y}H{x+size:.2f}" '
                f'fill="none" stroke="{color}" stroke-width=".75"/>')
    if kind == "trace":
        return (f'<path d="M{x-4*scale:.2f} {y+size:.2f}Q{x} {y-2*size:.2f} '
                f'{x+4*scale:.2f} {y-size:.2f}" fill="none" stroke="{color}" '
                f'stroke-width=".9" stroke-linecap="round"/>')
    if kind == "ripple":
        return (f'<path d="M{x-5*scale:.2f} {y}q{5*scale:.2f} {-2.5*scale:.2f} '
                f'{10*scale:.2f} 0M{x-3*scale:.2f} {y+2*scale:.2f}'
                f'q{3*scale:.2f} {-1.5*scale:.2f} {6*scale:.2f} 0" '
                f'fill="none" stroke="{color}" stroke-width=".8" stroke-linecap="round"/>')
    if kind == "halo":
        return (f'<circle cx="{x}" cy="{y}" r="{3.2*scale:.2f}" '
                f'fill="none" stroke="{color}" stroke-width=".75"/>')
    if kind == "ember":
        return (f'<path d="M{x} {y-3*scale:.2f}Q{x+3*scale:.2f} {y} {x} '
                f'{y+3*scale:.2f}Q{x-3*scale:.2f} {y} {x} {y-3*scale:.2f}Z" '
                f'fill="{color}"/>')
    return (f'<circle cx="{x}" cy="{y}" r="{1.1*scale:.2f}" fill="{color}"/>')


def _overlay(card: dict, experience: dict, palette: DeckPalette) -> str:
    weather = experience.get("weather") or {}
    if not isinstance(weather, dict):
        raise ValueError("Machine weather must be an object")
    cpu = _bucket(weather, "cpu")
    memory = _bucket(weather, "memory")
    disk = _bucket(weather, "disk")
    signature = experience.get("machineSignature") or {}
    if not isinstance(signature, dict):
        signature = {}
    cpu_size = _capacity(signature, "cpu", "C")
    ram_size = _capacity(signature, "memory", "M")
    disk_size = _capacity(signature, "storage", "D")
    art_variant = experience.get("artVariant", 0)
    if type(art_variant) is not int or not 0 <= art_variant <= 15:
        raise ValueError("Art variant must be an integer from 0 to 15")
    kind = _variant(card, experience)
    color = palette.accents.get(card.get("suit"), palette.gold)

    # Memory/CPU pressure adds faint atmosphere. Capacity adds at most two
    # secondary details; no weather value selects a different hue or meaning.
    count = 2 + memory + (cpu // 2) + min(2, ram_size // 3) + min(1, cpu_size // 4)
    details = []
    for index in range(count):
        x, y = _coordinates(card["id"], art_variant, index)
        details.append(_motif(kind, x, y, 1 + (index % 3) * .22, color))

    # Storage affects grounding marks in the frame, not the scene's subject.
    grounding = 1 + disk + min(2, disk_size // 3)
    for index in range(grounding):
        x = 35 + index * 9
        details.append(f'<path d="M{x} 403v{2 + index % 2}" fill="none" '
                       f'stroke="{palette.gold}" stroke-width=".75"/>')
    return '<g id="living-art-v1" opacity=".62">' + "".join(details) + '</g>'


def motion_spec(card: dict, experience: dict) -> dict:
    """Versioned provenance for the static phase-zero artwork in renderer v1."""
    return {"schemaVersion": 1, "canonicalPhaseMs": 0, "durationMs": 0,
            "loop": False, "tracks": []}


def render_daily_art(card: dict, experience: dict,
                     palette: DeckPalette | None = None) -> tuple[bytes, bytes]:
    """Return exact generated SVG and a lossless 1400×2400 PNG witness.

    Requires the system's ``rsvg-convert``.  It rasterizes the finalized SVG,
    including the current font stack, once; the archived PNG then preserves
    those pixels independently of future SVG/font changes.
    """
    palette = palette or DeckPalette()
    svg = card_svg(card, palette)
    if svg.count(_PLATE_END) != 1:
        raise ValueError("Unrecognized Ominity card SVG structure")
    svg = svg.replace(_PLATE_END, _overlay(card, experience, palette) + _PLATE_END)
    svg_bytes = (svg + "\n").encode("utf-8")
    renderer = shutil.which("rsvg-convert")
    if renderer is None:
        raise RuntimeError("rsvg-convert is required to preserve the Daily Om visual witness")
    result = subprocess.run([renderer, "--format", "png", "--width", str(WITNESS_WIDTH),
                             "--height", str(WITNESS_HEIGHT)], input=svg_bytes,
                            capture_output=True, check=False)
    if result.returncode != 0 or not result.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Could not render Daily Om PNG witness: "
                           + result.stderr.decode("utf-8", errors="replace").strip())
    return svg_bytes, result.stdout
