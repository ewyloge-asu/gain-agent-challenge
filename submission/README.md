# GAIN Agentic Investigation Challenge — Submission (Arizona State University team)

Six standalone Agent Skills for records investigations — each works on its own, with no
required pipeline — plus the newsworthy findings they produced on the GAIN federal
lobbying corpus.

## What's included

### The skill(s)
Six standalone Agent Skills, from **one shared source** (`../menu/`). Each installs and
runs independently — download only the one you need. The `Skill` column is the install
identifier; **`What it does` is the real name**:

| Skill (identifier) | Role | What it does |
|---|---|---|
| `investigative-method` | scope, find data, snapshot it | scopes the question with the user (works on any data), checks via a quick web search whether it's already been reported on recently, finds and snapshots outside data, and renders a case file into a review dashboard; hands off to case-file, robodoig/lobbying-influence-mapper, checking-the-law, and howard-center-footnoter for everything else rather than duplicating them |
| `lobbying-influence-mapper` | find the leads | ingest → resolve entities → cross-reference → verify vs. outside data, with provenance on every number |
| `robodoig` | understand any table | profile any tabular dataset + transcription-error QA *(named for Steve Doig, the Pulitzer-winning ASU data-journalism pioneer whose method it automates)* |
| `case-file` | never lose the thread | durable thread/entity/journal state across sessions |
| `checking-the-law` | is it actually illegal? | read the actual statute, apply it element-by-element |
| `howard-center-footnoter` | source every claim | footnote a draft to primary sources (tracked changes) |

All skills **validate against the Agent Skills spec** (`python3 ../validate_skills.py menu/skills`).
Downloads: `../dist/` (per-skill zips).

### Findings
The newsworthy discoveries are published as summary bullets on the
[site](https://ewyloge-asu.github.io/gain-agent-challenge/#findings) and in the table
below. Legal assessments are in `legal_checks/`. Public language about any finding is
limited to that summary bullet, the linked logs, and (for the Kentucky
GOP-headquarters finding) the linked verification spreadsheet — nothing beyond what
those support is asserted.

### Interaction traces (logs)
`traces/outputs/` — verbatim logs of the key invocations backing each published finding.

### Review surface
`review_dashboard.html` — generated from the case file; thread board + findings + legal
flags, every claim linked to a source record.

### Footnoter demo (claim hardening, end-to-end)
`footnoter_demo/` — a `.docx` excerpt of the findings report footnoted to the other
skills' own outputs as Word tracked changes: 10 footnotes (9 sourced + 1 ⟨NEEDS SOURCE⟩) and
2 margin comments (`no_source`, `context_concern`). See `footnoter_demo/README.md`.

### Generality test (all six skills, on a second beat)
We ran all six skills together, end-to-end, on a non-lobbying beat (Medicare hospital
up-coding), zero lobbying-specific code: scoped question → synthesized healthcare
beat-pack → live acquisition (CMS API + HHS-OIG report, sha256 snapshots) → robodoig
profile of 4,079 billing rows → peer-baseline anomaly pass (25 ranked leads; median
highest-severity share 74.4%, outliers 90–92%) → case-file thread + dashboard. Includes a
caught-and-recorded data-suppression artifact — the tool's honesty features working on
foreign data.

## Findings and the skills that support them

| Finding | Status | Skills used |
|---|---|---|
| Kentucky GOP headquarters — 16 corporations with business before Congress gave $4.4M to a building-fund named for Sen. Mitch McConnell; only 4 of 16 disclosed it in federal filings | Confirmed (disclosure question, not an alleged violation) | mapper (ingest/resolve, honoree + building-fund queries) |
| Foreign revolving door — Tencent $4.04M; McEntee not FARA-registered | Confirmed | mapper (client/lobbyist/FARA), checking-the-law |
| Senate↔House consistency (36,643 comparable periods, 0 gaps >$100K — re-verified this session, amendment-aware) | Cold | mapper (mismatch), case-file |

Also demonstrated, as a capability rather than a finding: a **coordinated-messaging
detector** (`mapper/detect_coordination.py`) that surfaces near-identical language pushed
by many offices in a tight window — e.g. a 9-member bipartisan cluster reusing one
think-tank statistic within 2 days of the Dream & Promise Act reintroduction.

## Outside data used
`unitedstates/congress-legislators` (committee roles, member roster — shipped snapshot),
Congress.gov (sponsored bills, Tier 1), FEC (receipts denominator, Tier 2), Voteview
(votes), FARA (foreign-agent registry). All snapshotted so findings re-run offline.

## Possible legal violations flagged to the panel
- **McEntee / FARA** — LDA-vs-FARA election for foreign-client work. `legal_checks/mcentee_fara.md`
  (verdict: genuinely-unclear → for the panel).
This is framed as a question for a lawyer, not an assertion of illegality.

## Conflicts of interest
None known. No team member has a relationship with any entity named.

## Reproduce
```
export GAIN_DATA_DIR=/path/to/data GAIN_WORKDIR=$PWD/build/workdir
python3 ../menu/skills/lobbying-influence-mapper/scripts/ingest.py --years 2025 --datasets senate contributions press
python3 ../menu/skills/lobbying-influence-mapper/scripts/resolve_entities.py
```
No API key or network required for the core findings (shipped snapshots). Optional keys via
`../menu/setup_keys.py`.
