# GAIN Agentic Investigation Challenge — Submission (Arizona State University team)

A reusable **investigative assembly line** for records investigations, plus the newsworthy
findings it produced on the GAIN federal lobbying corpus.

## What's included

### The skill(s)
Delivered in two forms from **one shared source** (`../menu/` is canonical; `../mega/` is
assembled from it):

- **Menu (bundle)** — six composable skills you can install together or à la carte.
  The `Skill` column is the install identifier; **`What it does` is the real name**:
  | Skill (identifier) | Role | What it does |
  |---|---|---|
  | `investigative-method` | the conductor | scopes the question with the user (works on any data), opens the case file, drives the workflow; includes web-search-for-data |
  | `lobbying-influence-mapper` | find the leads | ingest → resolve entities → cross-reference → verify vs. outside data, with provenance on every number |
  | `robodoig` | understand any table | profile any tabular dataset + transcription-error QA *(named for Steve Doig, the Pulitzer-winning ASU data-journalism pioneer whose method it automates)* |
  | `case-file` | never lose the thread | durable thread/entity/journal state across sessions |
  | `checking-the-law` | is it actually illegal? | read the actual statute, apply it element-by-element |
  | `howard-center-footnoter` | source every claim | footnote a draft to primary sources (tracked changes) |
- **Mega (single skill)** — `investigative-desk`: the whole line behind one `SKILL.md`.

All skills **validate against the Agent Skills spec** (`python3 ../validate_skills.py menu/skills`).
Downloads: `../dist/` (menu bundle, mega, and per-skill zips).

### Findings report
`findings_report.md` — the newsworthy discoveries (below). Legal assessments in
`legal_checks/`.

### Interaction traces
`traces/sessions.html` — **every skill invocation across the four working sessions**,
with full arguments, in order, plus the verbatim output of each key invocation in
`traces/outputs/`. `traces/trace_index.md` is the narrative index: each invocation keyed
to its command, output, and the human-judgment moments. Scope: we read the traces
deliverable as the full record of the model sessions *using* the tool stack — every
invocation, input, and output is here; the sessions' interleaved tool-development
activity is development history, not an interaction trace, and is out of scope.

### Review surface
`review_dashboard.html` — generated from the case file; thread board + findings + legal
flags, every claim linked to a source record.

### Footnoter demo (claim hardening, end-to-end)
`footnoter_demo/` — a `.docx` excerpt of the findings report footnoted to the actual
pipeline outputs as Word tracked changes: 10 footnotes (9 sourced + 1 ⟨NEEDS SOURCE⟩) and
2 margin comments (`no_source`, `context_concern`). See `footnoter_demo/README.md`.

### Generality test (the FULL pipeline on a second beat)
`generality_demo/` — the whole assembly line run end-to-end on a non-lobbying beat
(Medicare hospital up-coding), zero lobbying-specific code: scoped question → synthesized
healthcare beat-pack → live acquisition (CMS API + HHS-OIG report, sha256 snapshots) →
robodoig profile of 4,079 billing rows → peer-baseline anomaly pass (25 ranked leads;
median highest-severity share 74.4%, outliers 90–92%) → case-file thread + dashboard.
Includes a caught-and-recorded data-suppression artifact — the tool's honesty features
working on foreign data. See `generality_demo/README.md`.

## Findings and the skills that support them

| Finding | Status | Skills used |
|---|---|---|
| Pay-the-gavel — lobbyist money pools on committee gatekeepers (Guthrie #1, $694K) | Confirmed | mapper (gatekeeper/resolve), connector (roster/FEC), case-file |
| Foreign revolving door — Tencent $4.04M; McEntee not FARA-registered | Confirmed | mapper (client/lobbyist/FARA), checking-the-law |
| Loc Nation — $80M of pseudo-legal claims filed as lobbying (integrity) | Flag | mapper (anomaly, amendment-aware), checking-the-law |
| Coordinated messaging is detectable (9-member Dream & Promise cluster) | Method | mapper (detect_coordination) |
| Senate↔House consistency (36,643 comparable periods, 0 gaps >$100K — re-verified this session, amendment-aware) | Cold | mapper (mismatch), case-file |

## Outside data used
`unitedstates/congress-legislators` (committee roles, member roster — shipped snapshot),
Congress.gov (sponsored bills, Tier 1), FEC (receipts denominator, Tier 2), Voteview
(votes), FARA (foreign-agent registry). All snapshotted so findings re-run offline.

## Possible legal violations flagged to the panel
- **Loc Nation** — possible misuse of the federal LDA filing system. `legal_checks/loc_nation.md`
  (verdict: genuinely-unclear → for the panel).
- **McEntee / FARA** — LDA-vs-FARA election for foreign-client work. `legal_checks/mcentee_fara.md`
  (verdict: genuinely-unclear → for the panel).
Both are framed as questions for a lawyer, not assertions of illegality.

## Conflicts of interest
None known. No team member has a relationship with any entity named.

## Reproduce
```
export GAIN_DATA_DIR=/path/to/data GAIN_WORKDIR=$PWD/build/workdir
python3 ../menu/skills/lobbying-influence-mapper/scripts/ingest.py --years 2025 --datasets senate contributions press
python3 ../menu/skills/lobbying-influence-mapper/scripts/resolve_entities.py
python3 ../menu/skills/lobbying-influence-mapper/scripts/xref.py gatekeeper --filer lobbyist --year 2025 --top 12
python3 ../menu/skills/lobbying-influence-mapper/scripts/xref.py anomaly --year 2025 --factor 5
```
No API key or network required for the core findings (shipped snapshots). Optional keys via
`../menu/setup_keys.py`.
