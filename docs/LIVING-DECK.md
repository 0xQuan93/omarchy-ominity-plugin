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
{"integrity":{"algorithm":"sha256","canonicalization":"RFC8785","digest":"<sha256 of canonical record>"},"record":{"schemaVersion":1,"type":"identity","payload":{"seed":"<256-bit random value>"}}}
```

For a daily reading derive a deterministic seed with HMAC-SHA256 over a byte-exact framed message. The HMAC message is the UTF-8 RFC 8785 canonicalization of exactly this logical object:

```json
{
  "cardId":"major-17-the-star",
  "localDate":"2026-09-20",
  "machineSignature":{"cpu":"C3","memory":"M4","storage":"D4"},
  "orientation":"upright",
  "protocol":"ominity-experience-v1"
}
```

```text
message_bytes = UTF8(RFC8785(message_object))
experience_seed = HMAC-SHA256(installation_seed_bytes, message_bytes)
```

The installation seed is decoded from its specified stored representation to the original 32 bytes before use as the HMAC key. No ad-hoc concatenation, delimiter scheme, locale-dependent formatting, or implementation-specific JSON serialization participates in experience derivation.

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
    "facets": [
      {"id":"star-renewal","lens":"renewal","text":"..."},
      {"id":"star-attention","lens":"attention","text":"..."}
    ],
    "prompts": [
      {"id":"star-small-renewal","text":"What small source of renewal is already near?","dayparts":["morning","day"]},
      {"id":"star-evening-light","text":"What light remained visible today?","dayparts":["evening"]}
    ],
    "art_symbols": [
      {"id":"water-jars","label":"the water jars","variant":"shimmer","observation":"Water is offered both to the pool and to the earth."},
      {"id":"eight-stars","label":"the eight stars","variant":"constellation","observation":"One great light is surrounded by seven smaller lights."},
      {"id":"pool","label":"the pool","variant":"ripple","observation":"The poured water returns to a larger body."}
    ]
  }
}
```

The base `upright`, `reversed`, `interpretation`, `symbols`, `reflection`, and `art_note` remain canonical.

## Daily experience record

Extend the reading object without breaking existing consumers:

```json
{
  "integrity":{"algorithm":"sha256","canonicalization":"RFC8785","digest":"<sha256 of canonical record>"},
  "record":{
  "schemaVersion":1,
  "type":"daily-om",
  "payload":{
  "day":"2026-09-20",
  "id":"major-17-the-star",
  "reversed":false,
  "time":{
    "localDate":"2026-09-20",
    "localTimestamp":"2026-09-20T05:27:14-05:00",
    "utcTimestamp":"2026-09-20T10:27:14Z",
    "utcOffset":"-05:00",
    "timezone":"America/Chicago",
    "timezoneSource":"system",
    "timezoneDataVersion":"<when available>"
  },
  "redraw":false,
  "deckContentVersion":"1.1.0",
  "canonicalSnapshot":{
    "title":"The Star",
    "arcana":"major",
    "suit":null,
    "number":17,
    "numeral":"XVII",
    "element":null,
    "path":"The open night",
    "upright":"Restore hope through small, steady acts.",
    "reversed":"Exhaustion; losing sight of available support.",
    "interpretation":"After upheaval, the future may arrive as a trickle rather than a trumpet. Refill what is depleted and let simplicity count.",
    "symbols":["eight stars","water jars","pool"],
    "keywords":["hope","renewal","trust"],
    "reflection":"What small source of renewal is already near?",
    "artNote":"The largest star shines over a figure who pours water both into the pool and onto the earth."
  },
  "machine":{"eraId":"019a4d3e-7c91-7b2a-a901-2b61c67f1102","weather":{"cpu":2,"memory":1,"disk":3}},
  "artwork":{
    "rendererVersion":1,
    "master":{
      "sha256":"<64 hex chars>",
      "format":"image/svg+xml",
      "relativePath":"artifacts/sha256/9f/9f83...a21.svg"
    },
    "visualWitness":{
      "sha256":"<64 hex chars>",
      "format":"image/png",
      "width":1400,
      "height":2400,
      "aspectRatio":"7:12",
      "relativePath":"artifacts/sha256/ab/ab41...91c.png"
    }
  },
  "experience":{
    "version":1,
    "facet":{"id":"star-renewal","lens":"renewal","text":"..."},
    "prompt":{"id":"star-small-renewal","text":"What small source of renewal is already near?","period":"morning"},
    "symbol":{"id":"water-jars","label":"the water jars","variant":"shimmer","observation":"Water is offered both to the pool and to the earth."},
    "artVariant":7,
    "motion":{
      "schemaVersion":1,
      "canonicalPhaseMs":0,
      "durationMs":6000,
      "loop":true,
      "tracks":[
        {"target":"water-jars","property":"shimmer","curve":"sine","periodMs":2400,"amplitude":0.18,"phaseMs":0}
      ]
    },
    "thread":{
      "type":"return",
      "text":"The Star returns after 43 days.",
      "relationship":null,
      "evidence":{"previousDay":"2026-08-08","currentDay":"2026-09-20","days":43}
    }
  }
  }
  }
}
```

Do not store the derived HMAC or installation secret in reading history.

### Immutable Daily Om artifacts

A completed daily encounter is a historical artifact, not a view that should be reconstructed from the latest deck. Persist both stable authored IDs **and the exact user-visible authored content selected that day**.

**Snapshot by boundary, not by convenience.** When a Daily Om is finalized, copy every deck-authored or experience-authored value required to reproduce the encounter into the artifact. Historical rendering must never consult the current `deck.json` to fill missing user-facing information.

The canonical snapshot therefore contains the complete user-facing card definition used by the UI at that time: title, arcana, suit, number/numeral, element, path, upright, reversed, interpretation, symbols, keywords, reflection, and art note. The experience snapshot preserves complete selected objects, including facet ID/lens/text, prompt ID/text/daypart, symbol ID/label/observation/variant hook, plus experience-engine version and art variant. The artifact also preserves deck-content version, Machine Era ID, machine-weather buckets, and card/orientation.

Future wording edits may change new Daily Oms but must never rewrite an old one. Historical rendering should prefer the snapshot. Versioned deck content may remain useful for migrations and provenance, but it is not a substitute for preserving the content the user actually encountered.

### Archived artwork and provenance

The visual card face is part of the encounter boundary. Reproduction parameters alone are insufficient because a future SVG generator, theme renderer, font stack, or variation algorithm could change. When a Daily Om is finalized, preserve **two complementary artifacts** in the content-addressed local store:

1. the exact generated SVG as the **structural master**, and
2. a lossless PNG of the finalized rendered card as the **visual witness**.

The SVG proves what Ominity generated. The PNG preserves what the finalized card looked like at a documented **canonical animation phase** independent of future fonts, SVG engines, layout metrics, or renderer behavior.

If the Living Deck uses motion, the immutable experience snapshot must also contain a versioned deterministic motion specification: duration, loop behavior, canonical phase, target/property identifiers, curves, periods, amplitudes, and phase offsets needed to reproduce temporal behavior. The PNG is the exact still witness at the canonical phase; the motion snapshot is the temporal provenance. Do not archive daily video merely to preserve deterministic motion.

Suggested layout:

```text
~/.local/state/ominity/
├── history/
│   └── 2026/
│       └── 2026-09-20.json
└── artifacts/
    └── sha256/
        ├── 9f/
        │   └── 9f83...a21.svg
        └── ab/
            └── ab41...91c.png
```

Compute SHA-256 independently over the final SVG bytes and lossless PNG bytes. The visual witness must preserve the card's canonical 7:12 geometry; the reference archival size is 1400×2400 (5× the current 280×480 logical card) with no implicit crop or padding. If another witness resolution is introduced later, it must retain 7:12 or explicitly version and snapshot the capture canvas/padding semantics.

The Daily Om stores both digests, media types, witness dimensions/aspect ratio, renderer/experience version, and relative artifact paths.

Historical display defaults to the verified PNG visual witness when exact visual reproduction matters. The SVG remains available as the inspectable/vector structural master. This distinction prevents an unchanged SVG from rendering differently decades later because an external font, SVG engine, or glyph-layout implementation changed.

Content addressing provides natural deduplication: identical rendered bytes need only be stored once. It also permits local provenance status without a network, blockchain, account, or external authority:

- **Structural master verified** — archived SVG bytes match their stored digest.
- **Visual witness verified** — archived PNG bytes match their stored digest and can reproduce the finalized pixels without external fonts.
- **Artifact modified** — one or more archived assets exist but no longer match their digest.
- **Artwork unavailable** — a legacy or damaged record lacks its original assets; Ominity may offer a clearly labeled reconstruction but must not present it as the original.

The user owns these files and may edit, copy, or delete them. Verification describes provenance; it does not enforce immutability.

### Transactional finalization

A Daily Om is committed as a unit. Atomic writes for individual files are not sufficient because a crash could otherwise publish canonical history before both visual artifacts exist.

Use a JSON-last commit protocol. Canonical creation is additionally serialized by a per-local-day advisory lock (for example `locks/2026-09-20.lock` using `fcntl.flock`). After acquiring the lock, re-check canonical history before sampling weather or generating artifacts. If another process already committed that date, return the committed Daily Om. Redraw operations must use compatible serialization so they cannot race canonical creation.

Use the following commit protocol:

1. create a private staging transaction under the Ominity state directory;
2. write the finalized SVG, PNG witness, and Daily Om JSON candidate into staging with mode 0600;
3. compute and verify both artifact digests against the candidate record;
4. flush and `fsync` the staged SVG, PNG, **and Daily Om JSON candidate** before any rename;
5. atomically publish the SVG and PNG into their content-addressed locations (reusing an already-present object only after verifying its digest);
6. `fsync` the artifact directories so those renames are durable;
7. only then atomically publish the canonical Daily Om history JSON;
8. `fsync` the history directory; the JSON publication is the **commit marker**;
9. remove the staging transaction.

Canonical history must never reference an artifact that has not already been durably published and verified.

On startup, recovery scans abandoned staging transactions. If no history commit marker exists, it may safely remove the staging files; already-published content-addressed objects may be retained for deduplication or garbage-collected when unreferenced. If the history JSON exists, both referenced artifacts must already verify by construction. Recovery operations must be idempotent so repeated crashes do not create duplicate canonical Daily Oms.

This ordering gives Ominity a simple crash-consistency invariant: **no committed Daily Om without both original artifacts**. Installation identity and Machine Era state mutations must likewise be serialized and use durable atomic replacement.

The archived SVG is the structural source artifact; the lossless PNG is the visual source of truth for a historical Daily Om. Renderer inputs (theme palette, machine buckets, art variant, symbol variant, renderer version, display scale) remain useful provenance metadata and may be stored as well, but must not replace either archived artifact.


### Record integrity and schema evolution

Artwork hashes are not enough: the historical record itself needs provenance. Every persistent structure carries an explicit `schemaVersion` and `type` inside a **hashed record object** (Daily Om, identity, Machine Era state, journal, archive manifest). Integrity metadata lives outside that record so the digest does not recursively include itself.

Use **RFC 8785 JSON Canonicalization Scheme (JCS)** as the byte-exact canonicalization contract. Compute SHA-256 over the UTF-8 RFC 8785 canonical representation of the entire `record` object, including `schemaVersion`, `type`, and `payload`. The outer `integrity` object stores `algorithm: "sha256"`, `canonicalization: "RFC8785"`, and the digest. Verification therefore binds interpretation/version metadata as well as artifact digests, canonical prose, experience snapshot, machine-era association, timestamps, and all other historical fields.

Do not substitute an ad-hoc “sorted JSON” serializer. Implementations/importers must either support the named canonicalization algorithm exactly or report the record as unsupported rather than corrupt. Non-finite JSON numbers are forbidden; persistent numeric values must be representable under RFC 8785 semantics.

The identity, Daily Om, Machine Era, journal, and archive-manifest examples in this RFC are normative persisted shapes and use the same envelope. Archive manifests additionally hash every member they enumerate.

Migrations must be additive/non-destructive. Never silently rewrite a verified historical payload in place. If a future schema needs a transformed representation, preserve the original payload and create a versioned derived/migrated view with provenance linking it to the source.

### Time identity

“One per local day” requires explicit time provenance. Snapshot:

- local calendar date used as the canonical day key;
- offset-aware local timestamp;
- UTC timestamp;
- UTC offset;
- IANA timezone name when reliably available;
- timezone-source/version metadata when available.

The per-day lock and canonical path are keyed by the snapshotted local date. Re-check after lock acquisition prevents two records for the same date. Clock rollback, DST changes, or reopening later must not create a second canonical Daily Om for a date that already exists. A genuine travel/timezone change may affect the next not-yet-committed local date, but never rewrites an existing artifact.

### Machine Era transition state machine

Machine Era changes must be conservative and deterministic rather than “multiple launches” by implication. Keep an active era plus an optional candidate signature. A materially different coarse signature becomes a candidate; confirm it only after observations on at least **3 distinct local days**. Matching the active signature clears the candidate. Repeated observations within one day count once. Until confirmation, new Daily Oms remain associated with the active era while recording no raw hardware identifiers.

When confirmed, close the previous era immediately before the first Daily Om assigned to the new era and retain an explicit transition/milestone record. Implementations may classify a documented subset of upgrades as milestones within an era, but the rule must be versioned and deterministic.

### Failure semantics

A Daily Om is canonical only after the history JSON commit marker is durably published. Disk-full, permission, renderer, hash, or fsync failures before that point must not return an uncommitted encounter as canonical. If a canonical record already exists, return it. Otherwise report a local finalization error and allow a later retry. Temporary artifacts are recoverable staging data, not history.

### Portable Ominity Archive

Longevity requires surviving machine loss and migration. Define a versioned, offline export format containing verified Daily Om envelopes, referenced SVG/PNG artifacts, Machine Era history, journal/reflection records, and a manifest enumerating every file with SHA-256 and byte size. Export itself must not include the private installation seed unless the user explicitly chooses a separate identity backup; normal archive portability should not clone the secret identity of the old installation.

Import is verify-first: validate manifest paths against traversal, enforce size/count limits before extraction, verify every digest and record envelope, reject/segregate conflicts rather than overwriting canonical history, and only then commit imported records transactionally. Imported Machine Eras remain historical; importing onto a new computer does not relabel old Daily Oms or make the new hardware part of an old era. The receiving installation begins/continues its own current Machine Era.

Archive manifests should support incremental export so decades of unchanged content-addressed artifacts need not be recopied unnecessarily. A future backup UI can show last verified export date without requiring cloud services.

Normative archive-manifest shape (the manifest **does not list or hash itself**, avoiding recursive integrity):

```json
{
  "integrity":{
    "algorithm":"sha256",
    "canonicalization":"RFC8785",
    "digest":"<sha256 of canonical record>"
  },
  "record":{
    "schemaVersion":1,
    "type":"archive-manifest",
    "payload":{
      "archiveId":"019a5c72-10f2-7d30-8e42-30ec4ec57d51",
      "createdAt":"2026-09-20T10:45:00Z",
      "members":[
        {
          "path":"history/2026/2026-09-20.json",
          "mediaType":"application/json",
          "bytes":4821,
          "sha256":"<64 hex chars>"
        },
        {
          "path":"artifacts/sha256/ab/ab41...91c.png",
          "mediaType":"image/png",
          "bytes":412881,
          "sha256":"<64 hex chars>"
        }
      ]
    }
  }
}
```

Member paths are normalized relative POSIX paths: no absolute paths, empty segments, `.`, `..`, backslashes, NULs, or symlink traversal. Member byte counts are checked before allocation/extraction and digests are verified before transactional import. Members are sorted lexicographically by `path` for deterministic export presentation; manifest integrity itself is defined by RFC 8785, not array reordering.

### Storage budget

Longevity matters more than minimizing a few megabytes. At one Daily Om per day, even a conservative 500 KiB average visual witness is about 178 MiB/year, 1.74 GiB/decade, and roughly 7 GiB over 40 years before filesystem compression or image optimization. The SVG and JSON metadata are comparatively small.

Ominity should still record artifact byte sizes and expose archive storage usage in Constellation. Future optional lossless optimization may reduce storage, but it must preserve the verified bytes or create a new explicitly versioned artifact rather than silently rewriting historical witnesses.

This gives a decades-old Daily Om archival integrity: opening a 2026 encounter in 2043 shows what Ominity presented in 2026, not a modern reinterpretation.

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

## Machine Eras

Ominity should recognize long-lived relationships with hardware without storing identifying hardware data.

Derive a coarse **Machine Era signature** from the same privacy-preserving capacity buckets used by Machine DNA. When that coarse signature materially changes and remains changed, begin a new local Machine Era with a random opaque ID such as `019a4d3e-7c91-7b2a-a901-2b61c67f1102`. Never store manufacturer/model, hostname, serials, MAC addresses, disk UUIDs, CPU model strings, or other fingerprint-grade identifiers.

An era record uses the same integrity envelope:

```json
{
  "integrity":{"algorithm":"sha256","canonicalization":"RFC8785","digest":"<sha256 of canonical record>"},
  "record":{
    "schemaVersion":1,
    "type":"machine-era",
    "payload":{
    "id":"019a4d3e-7c91-7b2a-a901-2b61c67f1102",
    "ordinal":2,
    "displayLabel":"Machine Era 02",
    "started":"2031-08-15",
    "ended":null,
    "classes":{"cpu":"C4","memory":"M5","storage":"D5"}
    }
  }
}
```

Machine Era durable IDs must be collision-resistant across independent installations/imports (UUIDv7 is the reference format). Sequential ordinals such as “01” and “02” are presentation metadata only and must never be used as references or uniqueness keys. Each Daily Om stores the collision-resistant Machine Era ID. Constellation can then show the user's history in chapters such as **Machine Era 01** without claiming to identify a physical device.

Do not store canonical Daily Om counts in the Machine Era record. Counts, percentages, first/last encounter dates, and similar aggregates are derived from verified canonical Daily Oms. Performance caches are allowed only when explicitly marked rebuildable/non-authoritative and must be safe to delete and regenerate.

To avoid creating a new era for transient configuration changes, require confirmation across multiple launches/days before closing the current era. Upgrades are part of the story: a RAM or storage upgrade may either remain within the era with a milestone event or begin a new era according to a documented material-change threshold.

Machine Eras are **sentimental computing**, not device tracking: they let a user see how different periods of hardware participation shaped the visual language of their archive while the tarot meaning remained unchanged.

## The Thread

Use history to generate factual symbolic continuity.

Examples:

- "The Hermit returns after 43 days."
- "This is the fourth Sword in your last seven daily cards."
- "Three of your last five cards have been Major Arcana."

A later authored relationship graph can add optional labels such as `echo`, `tension`, `complement`, and `continuation`. Those relationships should be editorial deck metadata, not generated claims.

**The Thread is part of the immutable encounter boundary.** Persist the exact Thread text shown that day plus the factual evidence used to derive it (for example prior/current dates, card IDs, counts/window) and, when applicable, a complete snapshot of the selected authored relationship object. Historical display never recomputes an old Thread from newly imported or subsequently expanded history.

## Reflection and journaling

Pattern tracking is useful because a daily practice becomes more meaningful when users can compare readings over time. Ominity should add an optional one- or two-sentence local reflection per day and a weekly/monthly review surface.

Recommended persisted shape:

```json
{
  "integrity":{"algorithm":"sha256","canonicalization":"RFC8785","digest":"<sha256 of canonical record>"},
  "record":{
    "schemaVersion":1,
    "type":"journal",
    "payload":{
    "day":"2026-09-20",
    "firstImpression":"...",
    "eveningReflection":"..."
    }
  }
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
- browse Daily Oms by Machine Era and see era boundaries/milestones
- preserve the visual lineage of retired hardware without retaining identifying hardware data

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
- add Machine Era state and conservative material-change detection
- add safe machine-capacity bucketing
- add one-time machine-weather sampling
- derive experience seed with HMAC-SHA256
- persist experience metadata on the reading
- preserve current daily stability and explicit redraw behavior
- add per-day locking, post-lock canonical recheck, and serialized identity/Machine Era mutation
- add explicit timestamp/timezone provenance
- add schema versions and canonical Daily Om payload hashing
- add tests proving stable reproduction, concurrency safety, durability, and secret/state permissions

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
- archive the finalized rendered SVG structural master and lossless PNG visual witness into a content-addressed SHA-256 artifact store
- finalize Daily Oms transactionally with staged writes, artifact-first durable publication, and history-JSON-last commit semantics
- fsync artifact files/directories before publishing canonical history
- recover abandoned staging transactions idempotently on startup
- write both archived artifacts atomically and verify each digest before historical display
- historical exact-view mode uses the PNG witness so external font/SVG changes cannot alter the recorded appearance
- preserve renderer/theme/machine inputs as provenance metadata while treating the SVG as the structural master and the lossless PNG witness as the visual source of truth
- support clearly labeled reconstruction only when a legacy/damaged artifact lacks original artwork
- preserve the bundled static deck as fallback

### Phase 5 — Constellation UI

- add stats/history process boundary
- build 78-card history matrix
- add Machine Era timeline and era-scoped archive browsing
- expose record/artifact verification state and archive storage usage
- add verified portable archive export/import surface
- add 7/30/90-day views
- add Thread and Return callouts
- keep stats descriptive rather than predictive

### Phase 6 — journal + Zephyr

- local reflection file with atomic writes and mode 0600
- morning/evening prompts
- optional Zephyr synthesis using card context only

## Normative-example rule

Every normative persisted-schema example in this RFC must satisfy every invariant defined elsewhere in the RFC. When an invariant changes, examples must be updated in the same change. Tests should deserialize the normative fixture shapes where practical so documentation cannot silently drift from implementation.

## Tests / acceptance criteria

- same installation + same daily reading + same persisted weather => identical experience
- experience derivation is deterministic for identical inputs
- different installation seeds are tested for healthy distribution across many samples; finite visible variants may legitimately collide
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
- authored schema gives every selectable facet, prompt, symbol, and relationship an explicit stable ID
- historical Daily Oms preserve exact selected authored content, not only IDs
- the complete user-facing canonical card definition, including path and keywords, is snapshotted with every Daily Om
- every selected facet snapshots ID, lens, and text
- every selected prompt snapshots ID, text, and selected daypart
- every selected art symbol snapshots ID, label, variant hook, and Notice observation
- every displayed Thread snapshots exact text, derivation evidence, and any selected authored relationship object
- importing/backfilling history cannot change a historical Thread
- animated experiences snapshot a versioned deterministic motion timeline; PNG witness corresponds to the documented canonical phase
- historical rendering never consults the current deck to complete missing user-facing fields
- finalized Daily Oms preserve both the exact generated SVG structural master and a lossless PNG visual witness
- structural master and visual witness are independently SHA-256 verified before being labeled original
- verified visual reproduction does not depend on the current system font stack
- PNG witnesses preserve the canonical 7:12 card geometry (reference size 1400×2400)
- canonical history JSON is never published before both referenced artifacts are durably present and verified
- crash recovery cannot create duplicate canonical Daily Oms and safely handles abandoned staging data
- staged Daily Om JSON is flushed and fsynced before its atomic commit rename
- concurrent `today` calls serialize per local day; losers reload the committed artifact rather than generating a second canonical encounter
- redraw cannot race canonical creation
- every persistent record hashes its complete RFC 8785-canonicalized `record` object, including schemaVersion and type, under an explicit integrity envelope
- changing schemaVersion/type invalidates the stored digest
- implementations use byte-exact RFC 8785 JCS rather than implementation-specific JSON serialization
- experience HMAC framing is UTF-8 RFC 8785 canonical JSON with an explicit protocol field; no ambiguous concatenation is allowed
- unsupported canonicalization/integrity algorithms are reported as unsupported, not corrupt
- Machine Era durable IDs are collision-resistant across independent archives; ordinals are display-only
- normative examples remain consistent with all RFC invariants
- Daily Om payloads have deterministic canonical serialization and an independently stored SHA-256 integrity envelope
- verified historical payloads are never silently rewritten by schema migrations
- local date, offset-aware timestamp, UTC timestamp/offset, and timezone identity (when available) are snapshotted
- clock rollback/DST cannot create a second canonical Daily Om for an already committed local date
- Machine Era candidates require observations on at least 3 distinct local days before transition
- disk-full/permission/render/hash/fsync failure before the commit marker never returns an uncommitted Daily Om as canonical
- portable archive export enumerates files with hashes/sizes and import verifies before transactional commit
- archive import prevents path traversal, enforces resource limits, and never overwrites conflicting canonical history
- Machine Era encounter counts/aggregates are derived from canonical Daily Oms or rebuildable caches, never authoritative era fields
- imported Machine Eras remain historical and are not reassigned to the receiving machine
- archive manifest is a normative shared-envelope record, enumerates member path/media type/byte size/SHA-256, and explicitly excludes itself
- importing independent archives with identical era ordinals cannot collide because references use durable collision-resistant IDs
- missing/modified artwork is surfaced honestly and never silently replaced with a modern render
- every Daily Om persists its Machine Era ID directly
- deck wording changes cannot silently reinterpret historical Daily Oms
- Machine Era changes use only coarse non-identifying classes and resist transient configuration churn
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
