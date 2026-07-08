# GAIN Agentic Investigation Challenge — Submission

**Skill:** `lobbying-influence-mapper` · **Author:** evan · **License:** MIT

A reusable Agent Skill for investigating lobbying and money in Congress, plus the
findings produced by running it on the GAIN corpus (2022–2026 Q1).

## What's here

```
evan_gain_agent_challenge_submission/
├── README.md                       # this map
├── validate_skill.py               # checks SKILL.md against the Agent Skills spec
├── lobbying-influence-mapper/      # THE SKILL — standalone, distributable unit
│   ├── SKILL.md                    # agent-facing instructions (spec frontmatter)
│   ├── README.md                   # human install/use guide (skills-dir install, demo, BYO)
│   ├── scripts/                    # ingest, resolve_entities, xref, detect_coordination,
│   │                               #   connector, state, review, common, make_demo_data, run_all.sh
│   ├── references/                 # schema, bridge_format, connectors, methodology
│   ├── assets/                     # offline snapshots (committees, FARA, Voteview, legislation, FEC)
│   └── demo_data/                  # bundled ~6 MB demo corpus — the skill runs out of the box
├── dist/                           # generated release archives (zip/tarball) — gitignored
├── docs/index.html                 # USER-FACING SITE (GitHub Pages-ready front door)
├── findings/findings_report.md     # the newsworthy discoveries, sourced
├── meeting/                        # shareable briefs (findings, tool pitch, team comparison)
├── traces/                         # invocation log keyed to each finding
└── build/                          # generated artifacts (db, cache, snapshots, state) — gitignored, regenerable
```

## User-facing site

`docs/index.html` is a self-contained webpage (no build step, no dependencies) that
serves as the front door for a non-technical reader: what the skill is, the
**pay → say → act** capability, the findings with sourced numbers, a plain-language
walkthrough, an operator quickstart, and the reproducibility ladder. Open it
directly in a browser, or enable **GitHub Pages → Deploy from branch → `/docs`** to
publish it.

## The skill (primary artifact)

`lobbying-influence-mapper` turns the three corpora into a provenance-stamped
SQLite store and gives the agent deterministic tools to cross-reference them:

- **ingest.py / common.py** — parse House XML + Senate JSON + press JSONL into a
  normalized store; every row carries a `prov` id.
- **resolve_entities.py** — cross-chamber entity resolution (the `senateID`
  bridge + name fallback) and honoree→member resolution.
- **xref.py** — query engine: `gatekeeper`, `member`, `client`, `lobbyist`,
  `anomaly`, `mismatch`, plus the **say** leg — `say` (press topic profile),
  `say-vs-do` (press topics vs. sponsored-bill policy areas), and `timeline`
  (dated money + press cadence vs. bills).
- **detect_coordination.py** — coordinated-messaging detector with party/timing
  /specificity signals.
- **connector.py** — config-driven, cached external-data connector (committees
  verified with no key; Congress.gov/FEC/FARA wired with offline fallback).
- **state.py** — investigation-state tracker across sessions.
- **review.py** — provenance → exact source record, for human verification.

Validate it: `python3 validate_skill.py lobbying-influence-mapper`
(or `skills-ref validate ./lobbying-influence-mapper`).

### Distribution (it's a portable skill, not a Cursor thing)

`lobbying-influence-mapper/` is a self-contained Agent Skill. A recipient installs
the folder into their agent's skills directory; a spec-compliant agent then
auto-discovers it from the `SKILL.md` `description` and invokes it in response to
plain-language questions. It **ships with `demo_data/`** (~6 MB) so it runs out of
the box, then points at the full corpus via `GAIN_DATA_DIR`. Build a versioned
release archive (the skill folder is the unit) with:

```bash
mkdir -p dist
zip -r dist/lobbying-influence-mapper-1.1.0.zip lobbying-influence-mapper \
  -x '*/__pycache__/*' '*.DS_Store'
```

Attach that archive to a GitHub Release for download. Full human install/use guide:
[lobbying-influence-mapper/README.md](lobbying-influence-mapper/README.md).

## Findings → which skill capability supports them → traces

| Finding | Supported by | Trace |
|---|---|---|
| **1. Pay-the-gavel** (lobbyist money pools on chairs/leadership; Guthrie case) | `xref.py gatekeeper/member` + `connector.py annotate-gatekeeper` (committee verify) | traces/invocation_log.md §Finding 1 |
| **2. Foreign revolving door** (Tencent→McEntee; Nippon Steel→Akin Gump/Ballard) | `xref.py client/lobbyist` | §Finding 2 |
| **Say vs. do** (press topics vs. sponsored bills; e.g. Warner talks Defense/Foreign-affairs more than he sponsors) | `xref.py say` / `say-vs-do` | traces §Say leg |
| **3. Disclosure abuse FLAG** (Loc Nation $180M fictional) | `xref.py anomaly` + `review.py` | §Finding 3 |
| Supporting: coordinated messaging (DHS/Noem thread) | `detect_coordination.py` | §Supporting |
| Cold thread: Senate↔House income consistency | `xref.py mismatch` | §Cold thread |

Full detail: [findings/findings_report.md](findings/findings_report.md).

## Outside data used (tiered so keys never gate the core findings)

Reproducibility ladder: **Tier 0** (no key) reproduces all core findings from the
corpus + committed snapshots; **Tier 1** (free Congress.gov key) adds the "act"
leg; **Tier 2** (FEC key) adds campaign-finance ground-truthing. Every keyed
fetch is snapshotted so keyed findings still re-run offline.

- **`unitedstates/congress-legislators`** (public GitHub, no key) — committee
  membership + the authoritative bioguide→FEC candidate-id crosswalk; verifies
  Finding 1 and powers reliable FEC lookups. Snapshot: `…/assets/committees.json`.
- **FARA active foreign-agent registry** (no key) — corroborates Finding 2
  (firms are FARA-registered; lobbyist John McEntee is not). Snapshot:
  `…/assets/fara_active.json`. Command: `connector.py fara`.
- **Voteview roll-call votes** (public bulk CSV, no key) — the vote dimension of
  "act": participation, party-unity, and ideology for the top recipients (they're
  ~97–99% party-line votes). Snapshot: `…/assets/votes.json`. Commands:
  `connector.py enrich-votes`, `vote-align`. Honest caveat: floor votes track
  *party*, not donors — so sponsorship (Tier 1) stays the cleaner "act" signal.
- **Congress.gov** (free key, Tier 1) — `connector.py enrich-act` pulls the top
  recipients' sponsored bills + policy areas (the "act" leg): the money-committee
  chairs' bills track their committee jurisdictions. Snapshot:
  `…/assets/legislation.json`.
- **FEC** (`DEMO_KEY`/real key, Tier 2) — `connector.py enrich-finance` gives a
  real denominator: registered lobbyists are ~13–17% of the money-committee
  chairs' *total* campaign receipts. Snapshot: `…/assets/fec_totals.json`.
- Real-world context in the findings report (DOD Tencent listing, Nippon/U.S.
  Steel CFIUS timeline, McEntee's prior role) is labeled *[context]* and should
  be independently confirmed before publication.

## Reproducibility
Runtime is Python standard library only. `GAIN_DATA_DIR=/path/to/data bash
lobbying-influence-mapper/scripts/run_all.sh` rebuilds the store and regenerates
every headline number. Ingest timings on a laptop: cheap datasets ~2 min total,
House 2025 ~40s.

**On the data:** the ~8 GB challenge corpus is *not* committed to this repo (size
limits; it is the challenge's dataset to distribute). Point `GAIN_DATA_DIR` at the
decompressed `data/` directory (containing `congress_press/ senate/ house/`). The
small external snapshots in `…/assets/` *are* committed, so every keyed finding
still re-runs offline. The regenerable `build/` store (~2 GB) is gitignored.

## Conflicts of interest
None known.

## Possible legal violations flagged to the panel
- **Finding 3 (Loc Nation):** apparent misuse of the federal LDA filing system
  (pseudo-legal/financial claims filed as lobbying disclosures). Recommended for
  referral/review.
- Finding 2's revolving-door relationships are disclosed and presumptively lawful;
  flagged as newsworthy, not as violations.
