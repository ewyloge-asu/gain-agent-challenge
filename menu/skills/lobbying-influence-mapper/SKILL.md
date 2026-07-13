---
name: lobbying-influence-mapper
description: >-
  Investigate congressional lobbying and money in politics: who funds which
  lawmakers, revolving door, foreign influence, say-vs-do, and disclosure
  anomalies; every claim traceable to a source filing.
license: MIT
compatibility: Requires Python 3.9+ (standard library only at runtime). Optional refresh of external data needs PyYAML and internet access.
metadata:
  author: evan
  version: "1.1.0"
---

# Lobbying Influence Mapper

A toolkit for agent-driven investigations of lobbying and money in Congress.
It is built around one idea: **push the heavy lifting (parsing, normalizing,
indexing, joining) onto cheap deterministic scripts, and spend the agent's
reasoning budget on leads and judgment.** Every record keeps a provenance id,
so any number you report can be traced back to its exact source filing.

## Install & try it (bundled demo)

This skill is portable: install the folder into your agent's skills directory,
then point it at data. It ships with `demo_data/` (a ~6 MB self-consistent slice)
so it runs out of the box before you supply the full corpus. Human install/use
guide: [README.md](README.md). To build and query the bundled demo:

```bash
export GAIN_DATA_DIR="$PWD/demo_data" GAIN_WORKDIR="$PWD/build"
python scripts/ingest.py --years 2025 2026 --datasets senate contributions press
python scripts/resolve_entities.py
python scripts/xref.py gatekeeper --filer lobbyist --year 2025
python scripts/xref.py say-vs-do "Mark Warner"
```

For real work, point `GAIN_DATA_DIR` at the full corpus instead (same layout) and
run `scripts/run_all.sh`. The demo features Warner, Guthrie, Scalise, Smith, and
Tillis plus the Nippon Steel / Tencent / Loc Nation clients.

## When to use this skill

Activate it for investigations like:

- "Who funds committee chairs / leadership?" (lobbyist & PAC contributions → members)
- "Trace one client's full influence footprint" (registrants, lobbyists, issues, agencies)
- "Find the revolving door" (former officials now lobbying, via `covered_position`)
- "Foreign influence" (foreign clients, who they hired, what they lobbied on)
- "Senate vs. House disclosure discrepancies" (same engagement, two filings)
- "Say vs. do" (does a member's public messaging match what they sponsor / who funds them?)
- "Coordinated messaging / astroturf" (verbatim talking points across members)
- "Disclosure-data integrity" (null/abusive/outlier filings)
- Any of the above **joined to outside data** (votes, committees, campaign finance).

## Data model assumptions

The skill expects the GAIN corpus layout described in `data_manual.md`:
`data/congress_press/**/*.jsonl`, `data/senate/<year>/{filings,contributions}/*.json`,
`data/house/<year>_*_XML/*.xml`. Point the skill at it with `GAIN_DATA_DIR`.
See [references/schema.md](references/schema.md) for the normalized tables and
[references/bridge_format.md](references/bridge_format.md) for how the Senate↔House
join key works.

## Workflow

Run from the skill root. Generated artifacts go to `GAIN_WORKDIR` (default `build/`).

### 1. Build the store (deterministic, one time per corpus)

```bash
export GAIN_DATA_DIR=/path/to/data
export GAIN_WORKDIR=/path/to/build
# Cheap datasets across all years; House XML is heavier, scope by year as needed.
python scripts/ingest.py --years 2022 2023 2024 2025 2026 --datasets senate contributions press
python scripts/ingest.py --years 2025 --datasets house
python scripts/resolve_entities.py
```

`ingest.py` parses everything into a SQLite db with a `prov` column on every row.
`resolve_entities.py` builds two resolver tables: `honoree_resolution`
(contribution honoree → member `bioguide`) and `xref_engagements`
(House filing ↔ Senate filing via the `senateID` bridge, name-match fallback).

### 2. Query and pressure-test leads

Each subcommand prints aggregates + provenance, and accepts `--json`.

```bash
python scripts/xref.py gatekeeper --filer lobbyist --year 2025 --top 25   # pay leaderboard
python scripts/xref.py member "Brett Guthrie"                              # pay + say for a member
python scripts/xref.py client "NIPPON STEEL"                               # one client's footprint
python scripts/xref.py lobbyist "John McEntee"                             # revolving-door view
python scripts/xref.py say "Mark Warner"                                   # the 'say' leg: press topic profile
python scripts/xref.py --json say-vs-do "Mark Warner"                      # press topics vs. sponsored-bill areas
python scripts/xref.py anomaly --year 2025 --factor 5                      # outlier / integrity scan
python scripts/xref.py mismatch --year 2025 --min-gap 100000               # Senate vs House gaps
python scripts/xref.py --json timeline "Mark Warner" --year 2025           # dated money + press vs. sponsored bills
python scripts/detect_coordination.py clusters --year 2025 --min-members 6 # copy-paste messaging
python scripts/detect_coordination.py keyword "strategy group"             # chase one thread
```

The press corpus is **Senate-heavy** (top senators have ~1,000+ releases; many
House members have only a handful), so `say` / `say-vs-do` are most robust for
senators and prolific House members. Press topics are keyword-tagged on the
title + lede into a coarse shared domain taxonomy (`common.POLICY_DOMAINS`) so
they line up with Congress.gov bill `policy_area`s; treat the alignment as
directional, not exact. See [references/methodology.md](references/methodology.md).

Interpreting `detect_coordination` signals: high `n_members` + bipartisan
`parties` + tight `span_days` + `specificity` ≥ 2 usually means a *targeted*
campaign; single-party low-specificity reuse is usually ordinary boilerplate.

### 3. Enrich with outside data (optional, keeps reproducibility)

`connector.py` is a config-driven external connector with on-disk caching and an
offline fallback, so the skill never *requires* a secret to run.

Reproducibility ladder (keys unlock richer tiers; they never gate Tier 0):
- **Tier 0 (no key, offline):** core findings reproduce from corpus + shipped
  snapshots. Includes committee roles, FARA, and **Voteview roll-call votes**.
- **Tier 1 (free Congress.gov key):** the "act" leg (sponsored legislation; bill
  policy areas for vote-alignment).
- **Tier 2 (FEC key):** campaign-finance ground-truthing.

```bash
# Tier 0 -- no key. Committee roles + FARA foreign-agent cross-check (snapshots shipped)
python scripts/connector.py annotate-gatekeeper --year 2025 --filer lobbyist --top 20
python scripts/connector.py committee G000558
python scripts/connector.py fara                          # firms/lobbyists vs FARA registry
python scripts/connector.py votes G000558                 # Voteview roll-call profile (no key)
python scripts/connector.py enrich-votes --year 2025 --filer lobbyist --top 12
#   -> participation / party-unity / ideology for top recipients; snapshots assets/votes.json
python scripts/connector.py refresh-committees            # one-off live refresh; PyYAML + net

# Tier 1 -- free Congress.gov key: completes pay -> say -> act
python scripts/connector.py legislation G000558                     # one member's bills
python scripts/connector.py enrich-act --year 2025 --filer lobbyist --top 12
#   -> top recipients' sponsored bills + policy areas; snapshots assets/legislation.json
python scripts/connector.py vote-align G000558                      # votes x bill policy areas
#   -> policy-area mix of a member's floor votes; snapshots assets/vote_align_<bioguide>.json
# Tier 2 -- FEC (DEMO_KEY works rate-limited; set FEC_API_KEY for real use)
python scripts/connector.py fec "Brett Guthrie"                     # one candidate
python scripts/connector.py enrich-finance --year 2025 --filer lobbyist --top 12
#   -> lobbyist $ as a share of each recipient's FEC receipts; snapshots assets/fec_totals.json
# Keys are auto-loaded from a gitignored credentials.env (see credentials.env.example).
```

Snapshots ship in `assets/` (`committees.json` incl. the bioguide->FEC crosswalk,
`fara_active.json`, plus `legislation.json` / `fec_totals.json` once you run the
keyed tiers), so the Tier 0 commands work offline out of the box. Any
keyed fetch should be snapshotted the same way so keyed findings still re-run
offline. Retarget the connector to a new dataset by adding one entry to its
`SOURCES` registry. See [references/connectors.md](references/connectors.md).

### 4. Stay oriented + verify

```bash
python scripts/state.py thread add "pay-the-gavel" --note "money vs chairs"
python scripts/state.py thread set "pay-the-gavel" --status confirmed
python scripts/state.py show                       # what's open / cold / confirmed
python scripts/review.py "<prov string>"           # claim → exact source record
```

`review.py` takes any `prov` value the store emits and prints the raw source
filing, so a human editor can verify a claim in seconds.

## How this maps to investigation quality

- **Organized across sessions** — `state.py` tracks threads, entities, and leads.
- **Efficient with the corpus** — all extraction/indexing/joining is deterministic
  SQLite; the agent reads small aggregates, never 8GB of raw files.
- **Human-verifiable** — every row carries `prov`; `review.py` round-trips it.
- **Extends the agent** — a cross-chamber entity resolver, an honoree→member
  resolver, a coordinated-messaging detector, and a pluggable external connector.

## Reproducibility

Runtime is Python standard library only. `scripts/run_all.sh` rebuilds the store
and regenerates every headline number end to end. External enrichment is cached
and falls back to the shipped snapshot, so an evaluator with no API key and no
network can still re-run the core findings. See
[references/methodology.md](references/methodology.md) for caveats (self-reported
data, ~35% null income, name-match limits).
