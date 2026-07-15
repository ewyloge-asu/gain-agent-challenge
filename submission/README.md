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

### "No gatekeeper" finding (fully worked example)
`loc-nation-no-gatekeeper/` — the complete record behind the first site finding: a single
filer registered a fictitious "sovereign nation" and reported $80M in 2025 lobbying fees,
which posted straight into the public record unchecked. Organized per the submission
instructions so each piece is easy to connect to the finding it supports:
- `README.md` — what's in the folder and how it maps to the finding.
- `FINDINGS_SUMMARY.md` — the findings report for this lead: the story, then every claim
  with its corrected figure, counting method, source, and caveats.
- `interaction-trace/interaction-trace.html` (also published at
  [`docs/traces/loc-nation-no-gatekeeper.html`](../docs/traces/loc-nation-no-gatekeeper.html),
  linked from the site finding as "interaction trace") and `interaction-trace.jsonl` — the
  full session log, human turns and skill invocations highlighted.
- `working-papers/` — the four intermediate memos (verification, system-and-law,
  enforcement record, and an adversarial fact-check pass that corrected two figures
  before publication).
- `casefile/` — the auditable case file (brief, threads, `findings.yaml`, entities,
  journal) written by the `case-file` skill.

Skills invoked, keyed to the trace: `investigative-method`, `lobbying-influence-mapper`,
`checking-the-law` (plus `case-file` via its CLI).

### Findings
The newsworthy discoveries are published as summary bullets on the
[site](https://ewyloge-asu.github.io/gain-agent-challenge/#findings) and in the table
below. Legal assessments are in `legal_checks/`. Public language about any finding is
limited to that summary bullet plus its linked evidence — the interaction trace and the
live public filing for the "no gatekeeper" finding, the verification spreadsheet for the
Kentucky GOP-headquarters finding — nothing beyond what those support is asserted.

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
| No gatekeeper — a fictitious "sovereign nation" reported $80M in 2025 lobbying fees (~21x the next-largest real client by income), posted to the public record unchecked; GAO shows enforcement is aimed almost entirely at non-filers, with no documented case of anyone penalized for a false figure | Confirmed, verified and fact-checked (see `loc-nation-no-gatekeeper/`) | investigative-method (scope, find/snapshot data), lobbying-influence-mapper (ingest, anomaly scan, rankings), checking-the-law (statute + GAO read), case-file |
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
(votes), FARA (foreign-agent registry), GAO-25-107523 (LDA enforcement audit, for the
"no gatekeeper" finding), law.cornell.edu (2 U.S.C. §§ 1605–1606, 18 U.S.C. § 1001, read
2026-07-15). All snapshotted or dated so findings re-run/re-verify offline.

## Possible legal violations flagged to the panel
- **Loc Nation false filing** — a knowingly false LDA filing may implicate 2 U.S.C. § 1606
  (civil/criminal) and possibly 18 U.S.C. § 1001; every hook requires a culpable mental
  state ("knowingly," "corruptly," "willfully"), and a filer who sincerely believes the
  figure may fall outside these statutes entirely. See
  `loc-nation-no-gatekeeper/casefile/findings.yaml` (legal_flags, status: to_verify) and
  `loc-nation-no-gatekeeper/working-papers/LEAD1_system_and_law.md`.
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
```
No API key or network required for the core findings (shipped snapshots). Optional keys via
`../menu/setup_keys.py`.
