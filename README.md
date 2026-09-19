# Ominity

A quiet daily tarot ritual for the Omarchy bar and desktop. Click **✦** to draw today's card. The reading stays put for the local calendar day; **Draw again** is an intentional new reading. Right click the bar glyph, or use the reading's button, to toggle a compact desktop card.

[See all 78 original cards](docs/deck-sheet.png) and the [card back](docs/card-back.png).

The 78 original illustrated cards follow the Rider–Waite–Smith structure. Each includes an upright invitation, reversed angle, deeper interpretation, symbols to notice, and a reflection question. The guide in the reading explains the Major and Minor Arcana, suits, reversals, and a grounded way to use a daily draw. The card moves into the reading stage when drawn and the stage eases away when closed. Press **Esc** to put it away.

Ominity's art and prose are original. Research into Davide De Angelis's *Starman Tarot* informed its broad emphasis on transformation and creative possibility, while the visual language stays closer to classic tarot: ivory, etched ink, geometric detail, and spare Omarchy surfaces. This project is unaffiliated with De Angelis, David Bowie, or the Starman publishers. Publisher references: [Lo Scarabeo](https://www.loscarabeo.com/en/products/starman-tarot) and [Schiffer](https://schifferbooks.com/products/starman-tarot-remastered-tarot-deck-and-guidebook-box-set). The traditional deck structure follows Waite's [Pictorial Key](https://rider-waite.com/symbolism/pictorial-key-1-3/).

## Install

Run `python3 -B install_local.py` to check the 78 cards and preview the local target. Run `python3 -B install_local.py --install` to copy the plugin into `~/.config/omarchy/plugins/oxquan.ominity` and add it to the bar and persistent service list. The installer backs up the existing shell config and any prior Ominity copy under `~/.local/state/ominity/install-backups/`. Omarchy 4.0.4 is the current tested API target. Validate with `omarchy plugin validate ~/.config/omarchy/plugins/oxquan.ominity`; if the shell does not pick up a new service automatically, run `omarchy shell shell rescanPlugins` or restart the shell.

The card draw uses only Python's standard library and local files. Its state is `~/.local/state/ominity/reading.json` with user-only permissions. It has no network calls, analytics, or account. The app uses Omarchy `Color`, `Style`, `Button`, and `BorderSurface` tokens to follow the active theme. `omarchy shell ominity open`, `close`, `toggle`, `redraw`, `widget`, and `status` expose local IPC controls.

## Optional companion summary

The public plugin works without AI. An optional executable at `~/.config/ominity/summary` may read the current local card and print a single JSON object: `{"ok":true,"drawnAt":"<same reading stamp>","summary":"..."}`. Ominity shows **Ask Zephyr** only when that adapter exists. It calls the adapter only after a click; stale summaries from a prior draw are ignored. On Quan's machine, the private adapter is `~/Work/zephyr-local/ominity_summary.py`, using the existing local inference bus. To link it during installation, pass `--zephyr-adapter ~/Work/zephyr-local/ominity_summary.py` after marking that script executable.

Tarot here is a reflective practice. A reading is an invitation to notice patterns and choices, not a factual prediction.

## Development

`python3 -B deck/build_deck.py` regenerates the SVG deck from the authored card data. `python3 -B -m unittest discover -s tests` checks draw semantics, and `python3 -B -m unittest deck.test_deck` checks the 78-card catalog and artwork. `omarchy plugin validate .` checks the manifest and entry points. `/usr/lib/qt6/bin/qmlformat -n Desktop.qml` and the same command for `BarWidget.qml` parse the QML. The installed UI still needs a live visual pass after changes.

License: MIT. See [LICENSE](LICENSE).
