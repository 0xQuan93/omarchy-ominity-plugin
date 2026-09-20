# Ominity Living Deck — implementation RFC

## Goal

Make every daily pull feel personal without changing the canonical card or claiming that machine telemetry changes the reading.

Ominity keeps the existing daily card + orientation stable. A new deterministic **experience layer** controls visual micro-variation, a symbolic lens, highlighted artwork details, reflection prompts, history echoes, and statistics.

The result should remain local-first, offline, reproducible for the day, theme-aware, and explicitly reflective rather than predictive.

## Design principles

1. **The card is sacred; presentation is generative.** Machine state never changes the card, orientation, or canonical meaning.
2. **Stable for the day.** Reopening Ominity recreates the same visual treatment and reading facet.
3. **Private by default.** Raw hardware identifiers, serials, MAC addresses, hostnames, usernames, process names, and file names are never stored or exposed.
4. **No telemetry.** Machine information is sampled locally and reduced to coarse buckets before use.
5. **Meaningful variation, not noise.** Every visual parameter maps to an authored detail already present in the card.
6. **History creates continuity.** Statistics and echoes describe the user's actual draw history without pretending patterns predict future events.

## Experience seed

Create a private random installation secret on first run:

`~/.local/state/ominity/identity.json`

Mode 0600:

```json
{"version":1,"seed":"<256-bit random value>"}
```

For a daily reading derive a deterministic seed with HMAC-SHA256:

```text
experience_seed = HMAC(
  installation_seed,
  "ominity-experience-v1" ||
  local_date ||
  card_id ||
  orientation ||
  machine_signature
)
```

The installation seed prevents two otherwise identical computers from producing identical experiences. The version string lets future releases evolve the algorithm without silently changing old records.

### Stable machine signature

Use **capacity/configuration facts** for the daily seed, not volatile load:

- logical CPU count, bucketed: 1–2 / 3–4 / 5–8 / 9–16 / 17+
- physical RAM total, bucketed: <=4 / <=8 / <=16 / <=32 / <=64 / >64 GiB
- root filesystem total size, bucketed: <=128 / <=256 / <=512 / <=1024 / >1024 GiB
- optional display scale bucket if Quickshell already exposes it

Do not use CPU model strings, disk UUIDs, serial numbers, MAC addresses, hostname, username, IP address, or other fingerprint-grade identifiers.

## Machine aura: live state affects art, never meaning

The user's idea of letting the *machine itself* leave fingerprints on the card is strongest when split into two channels:

### Stable machine DNA

Capacity/configuration facts feed the deterministic daily seed. This gives each installation a recognizable visual lineage.

### Ephemeral machine weather

At the instant the card is first revealed, sample coarse local state:

- memory pressure from `/proc/meminfo` using `MemAvailable / MemTotal`
- CPU activity from two short samples of `/proc/stat`
- root disk utilization from `os.statvfs("/")`

Linux exposes memory statistics through `/proc/meminfo` and CPU counters through `/proc/stat`. These should be converted immediately into coarse 0–4 buckets.

Example:

```json
{
  "cpu": 2,
  "memory": 1,
  "disk": 3
}
```

Persist those buckets with the daily reading so reopening the card does not visually mutate. Never persist raw percentages.

### Visual mappings

Machine weather must remain semantically neutral:

| Signal | Visual expression |
| --- | --- |
| RAM pressure | atmospheric density: mist, stars, particles, background texture |
| CPU activity | motion energy: shimmer cadence, orbit spacing, line pulse |
| Disk utilization | grounding density: border marks, lower-field geometry, constellation fullness |
| CPU-count bucket | number/complexity of secondary geometric marks |
| RAM-capacity bucket | depth layers / number of distant details |
| Disk-capacity bucket | frame ornament family |

High utilization must **not** imply danger, bad fortune, negative orientation, or a darker reading. It is aesthetic state only.

Example: two users both draw The Star upright. One machine may render sparse, slow-moving stars with a thin geometric frame; another may render a denser constellation and slightly more energetic water shimmer. The card and reading remain The Star upright.

## Authored card variation schema

Extend each card with optional experience metadata:

```json
{
  "experience": {
    "facets": {
      "attention": ["..."],
      "creation": ["..."],
      "connection": ["..."],
      "inner_world": ["..."],
      "work": ["..."],
      "change": ["..."]
    },
    "prompts": {
      "morning": ["..."],
      "day": ["..."],
      "evening": ["..."]
    },
    "art_symbols": [
      {"id":"lantern","label":"the lantern","variant":"glow"},
      {"id":"path","label":"the mountain path","variant":"trace"},
      {"id":"stars","label":"the distant stars","variant":"constellation"}
    ]
  }
}
```

The base `upright`, `reversed`, `interpretation`, `symbols`, `reflection`, and `art_note` remain canonical.

## Daily experience record

Extend the reading object without breaking existing consumers:

```json
{
  "day":"2026-09-20",
  "id":"major-17-the-star",
  "reversed":false,
  "drawnAt":"...",
  "redraw":false,
  "experience":{
    "version":1,
    "facet":"renewal",
    "prompt":"star-small-renewal",
    "promptPeriod":"morning",
    "symbol":"water-jars",
    "artVariant":7,
    "machineWeather":{"cpu":2,"memory":1,"disk":3}
  }
}
```

Do not store the derived HMAC or installation secret in reading history.

## History and statistics

The current 90-entry combined history is **not** sufficient for Constellation. Canonical daily history must be retained independently from redraw events so lifetime statistics remain truthful. One canonical record per local day is small enough to retain permanently; redraw events may be stored separately and bounded. Cumulative statistics may be cached for speed, but canonical history remains the source of truth.

Expose:

- total ritual days
- current streak and longest streak
- unique cards seen / 78
- Major vs Minor Arcana percentage
- upright vs reversed percentage
- suit distribution
- element distribution
- per-card appearance count and percentage
- days since a card last appeared
- most frequently seen cards, displayed without assigning supernatural significance
- recent 7 / 30 / 90 day windows
- redraw count, separately from canonical daily draws

For frequency percentages, default to one canonical draw per local day. A redraw should be visible in a separate redraw log but should not silently count as an additional "day" in the main distribution. The existing `[-90:]` combined retention must be replaced before lifetime metrics ship.

### Immutable daily artifacts

Once created, a daily encounter is a versioned historical artifact. Persist stable IDs for authored selections (`facet`, `symbol`, `prompt`, and future relationship metadata) rather than array positions. A prompt should have its own ID and may declare valid periods; the selected prompt ID and period are persisted with the reading. Reopening later in another daypart must not select a different prompt.

Deck edits, reordered JSON arrays, or later experience-engine versions must not silently reinterpret an old encounter. Permanent canonical history enables true lifetime streaks, discovery counts, return intervals, and per-card frequencies.

### Suggested CLI actions

```text
ominity.py stats
ominity.py history
ominity.py today
ominity.py redraw
```

`stats` should return JSON only, matching the current QML boundary.

Suggested shape:

```json
{
  "ok":true,
  "days":42,
  "uniqueCards":31,
  "arcana":{"major":0.2381,"minor":0.7619},
  "orientation":{"upright":0.6190,"reversed":0.3810},
  "suits":{"Wands":0.25,"Cups":0.21875,"Swords":0.28125,"Pentacles":0.25},
  "topCards":[{"id":"major-09-the-hermit","count":3,"percent":0.0714}],
  "streak":{"current":8,"longest":17}
}
```

## The Thread

Use history to generate factual symbolic continuity.

Examples:

- "The Hermit returns after 43 days."
- "This is the fourth Sword in your last seven daily cards."
- "Three of your last five cards have been Major Arcana."

A later authored relationship graph can add optional labels such as `echo`, `tension`, `complement`, and `continuation`. Those relationships should be editorial deck metadata, not generated claims.

## Reflection and journaling

Pattern tracking is useful because a daily practice becomes more meaningful when users can compare readings over time. Ominity should add an optional one- or two-sentence local reflection per day and a weekly/monthly review surface.

Recommended fields:

```json
{
  "firstImpression":"...",
  "eveningReflection":"..."
}
```

Keep this separate from the draw object so editing a journal entry never changes the historical draw.

## UI proposal

### Card face

Keep the current card-first experience. Add only subtle machine-derived variation.

### Reading side

Add compact sections:

1. canonical orientation meaning
2. **Lens** — today's authored facet
3. **Notice** — today's highlighted visual symbol
4. **The Thread** — one history-based observation when available
5. **Carry this** — today's deterministic reflection prompt

### Archive / Constellation

A new statistics surface should feel like part of Ominity rather than an analytics dashboard:

- 78-card matrix showing seen/unseen cards
- suit/arcana percentages
- upright/reversed balance
- card frequency
- 7/30/90-day filters
- streak
- recent thread
- tap a card to see dates it appeared

Call this surface **Constellation**: the user's history becomes a map of encounters with the deck.

## Optional Zephyr contract

Zephyr should synthesize already-selected context, never choose the card or invent machine meaning.

Input:

```json
{
  "card":"The Hermit",
  "orientation":"reversed",
  "facet":"creation",
  "symbol":"lantern",
  "timeOfDay":"night",
  "thread":"Eight of Pentacles → The Hermit",
  "question":"What idea needs privacy before it needs an audience?"
}
```

Do not send machine telemetry to Zephyr. It has no interpretive role.

## Implementation plan

### Phase 1 — state + deterministic engine

- add installation identity helper
- add safe machine-capacity bucketing
- add one-time machine-weather sampling
- derive experience seed with HMAC-SHA256
- persist experience metadata on the reading
- preserve current daily stability and explicit redraw behavior
- add tests proving stable reproduction and secret/state permissions

### Phase 2 — statistics

- add `stats` and `history` actions
- migrate from the combined 90-event buffer to permanent canonical daily history plus a separate bounded redraw log
- canonicalize one daily draw per date for main percentages
- optionally cache cumulative aggregates while keeping canonical history as source of truth
- calculate streaks, frequency, suit, arcana, orientation, and last-seen
- add unit tests for redraw handling and date gaps

### Phase 3 — authored experience metadata

- add facets, prompts, and addressable art symbols to all 78 cards
- assign stable IDs to facets, prompts, symbols, and future relationship metadata
- allow prompts to declare valid dayparts and persist the selected prompt ID + period
- validate schema in deck tests
- select facet/prompt/symbol deterministically from the experience seed

### Phase 4 — living artwork

- extend `card_svg()` with a backwards-compatible optional variant object
- make SVG generators expose safe variation hooks per scene
- map machine weather to neutral visual parameters
- include experience version + variant in themed cache keys
- preserve the bundled static deck as fallback

### Phase 5 — Constellation UI

- add stats/history process boundary
- build 78-card history matrix
- add 7/30/90-day views
- add Thread and Return callouts
- keep stats descriptive rather than predictive

### Phase 6 — journal + Zephyr

- local reflection file with atomic writes and mode 0600
- morning/evening prompts
- optional Zephyr synthesis using card context only

## Tests / acceptance criteria

- same installation + same daily reading + same persisted weather => identical experience
- two installation seeds => different experience variants with overwhelming probability
- machine data never changes card id, orientation, or canonical meaning
- no raw machine metrics are written to disk
- no hardware identifiers are collected
- daily `today` remains stable
- explicit redraw remains explicit
- stats count canonical ritual days separately from redraws
- canonical daily history is not truncated by redraw activity or a 90-event cap
- lifetime totals remain derivable from canonical history
- selected prompt ID + period survive reopening in a different daypart
- reordering authored prompt arrays cannot change an existing daily artifact
- corrupt identity/weather/history state recovers safely
- all state files are mode 0600
- theme rendering remains atomic
- static art remains a valid fallback
- no network access is introduced

## Research notes

Linux documents `/proc/meminfo` as the kernel interface for memory statistics and `/proc/stat` as the source of CPU state counters used by user-space monitoring tools. Ominity should use these only locally and coarsen them immediately.

Daily tarot/journaling guidance consistently emphasizes reflection, retaining dated entries, and reviewing recurring cards/themes over time. This supports Constellation as a reflection/history feature rather than a predictive scoring system.

External references:

- Linux CPU load documentation: https://docs.kernel.org/admin-guide/cpu-load.html
- proc_meminfo(5): https://man7.org/linux/man-pages/man5/proc_meminfo.5.html
- Serpents Way daily practice: https://serpentsway.com/practice/
- Kerykeion tarot journal guide: https://kerykeion.net/content/learn-tarots/guides/tarot-journal
- Tarot by Hand daily practice (2026): https://tarotbyhand.com/blog/daily-tarot-reading

## Product language

Ominity should continue to frame tarot as reflection:

> The card supplies a symbolic lens. Your history supplies context. Your machine leaves a visual fingerprint. None of those things determine your future.

That sentence captures the boundary of the Living Deck.
