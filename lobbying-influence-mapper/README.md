# Lobbying Influence Mapper

A portable **Agent Skill** for investigating lobbying and money in Congress. You
install it once into an AI agent that supports the [Agent Skills](https://agentskills.io)
spec; from then on the agent can answer reporting questions — *who funds a
lawmaker, what they say in public, and what they actually legislate* — by running
the skill's bundled scripts and handing you a source for every number.

You don't write code. You ask; the agent runs the skill; you check the receipts.

It ships with a **tiny demo corpus**, so it runs out of the box before you point
it at the full dataset.

---

## Install

The skill is a self-contained folder. Drop it into your agent's skills directory
(the exact path depends on your runtime — anything that implements the Agent
Skills spec):

```bash
# from a release archive
unzip lobbying-influence-mapper-1.1.0.zip -d ~/.agent/skills/

# or from source
git clone <repo-url>
cp -r repo/lobbying-influence-mapper ~/.agent/skills/
```

Requirements: **Python 3.9+ (standard library only)** at runtime. No pip install,
no data-science stack. (Refreshing external snapshots optionally uses PyYAML +
internet; the core never needs a key.)

Verify it's well-formed against the spec:

```bash
python3 validate_skill.py lobbying-influence-mapper    # included one level up in the repo
```

## Try it in 60 seconds (bundled demo)

The skill includes `demo_data/` — a ~6 MB self-consistent slice of the federal
corpus (five featured members, the Nippon Steel / Tencent / Loc Nation clients).
Build the store from it and run a few commands:

```bash
cd lobbying-influence-mapper
export GAIN_DATA_DIR="$PWD/demo_data"
export GAIN_WORKDIR="$PWD/build"

python3 scripts/ingest.py --years 2025 2026 --datasets senate contributions press
python3 scripts/resolve_entities.py

python3 scripts/xref.py gatekeeper --filer lobbyist --year 2025   # who's funded
python3 scripts/xref.py say-vs-do "Mark Warner"                   # say vs. do
python3 scripts/xref.py anomaly --year 2025 --factor 5            # integrity flag
python3 scripts/xref.py client "NIPPON STEEL"                     # client footprint
python3 scripts/review.py "demo_data/congress_press/2026-01.jsonl#L17"  # a receipt
```

On the demo you'll see all five members on the gatekeeper board, Warner's
say-vs-do reads, and Loc Nation + Nippon Steel flagged as income outliers — the
same findings as the full corpus, in miniature.

## Use it for real (bring your own data)

The skill expects the federal disclosure layout (all public records):

```
data/
  congress_press/<year>/<year>-MM.jsonl     # congressional press releases (2026 at the root)
  senate/<year>/filings/filings_<year>.json        # Senate LDA filings
  senate/<year>/contributions/contributions_<year>.json   # LD-203 contributions
  house/<year>_<quarter>_XML/*.xml           # House LDA filings
```

Point `GAIN_DATA_DIR` at your decompressed `data/` and rebuild:

```bash
GAIN_DATA_DIR=/path/to/data GAIN_WORKDIR="$PWD/build" bash scripts/run_all.sh
```

(`make_demo_data.py` is the build-time tool that produced `demo_data/` from the
full corpus — included for transparency; recipients don't need it.)

## How an agent actually uses it

Once installed, a spec-compliant agent **auto-discovers** the skill from the
`description` in `SKILL.md` — you don't attach or paste anything. You ask in plain
language, e.g.:

> "Who got the most lobbyist money in 2025, and for the top senator, does their
> public messaging line up with what they actually sponsor? Show me the source
> for the headline number."

The agent loads the skill, runs `gatekeeper` → `say-vs-do` → `review`, and returns
numbers with provenance you can verify before publishing.

## What's inside

```
lobbying-influence-mapper/
├── SKILL.md            # agent-facing instructions (spec frontmatter + workflow)
├── README.md           # this file (human install/use guide)
├── scripts/            # ingest, resolve_entities, xref, detect_coordination,
│                       #   connector, state, review, common, run_all.sh, make_demo_data
├── references/         # schema, bridge_format, connectors, methodology
├── assets/             # offline snapshots (committees, FARA, Voteview, legislation, FEC)
└── demo_data/          # the bundled ~6 MB demo corpus
```

See `SKILL.md` for the full command surface and the Tier 0–2 reproducibility
ladder, and `references/methodology.md` for limits and caveats. MIT licensed.
