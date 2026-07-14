# Agent of Record — GAIN Agentic Investigation Challenge submission (Arizona State University team)

A reusable **investigative assembly line** for records investigations — six composable
Agent Skills plus the newsworthy findings they produced on the GAIN federal lobbying
corpus (2022–2026 Q1).

**Site:** https://ewyloge-asu.github.io/gain-agent-challenge/ ·
**Submission map (required README):** [`submission/README.md`](submission/README.md) ·
**Plain-repo edition** (same submission, no website layer): [ewyloge-asu/case-agent](https://github.com/ewyloge-asu/case-agent)

## The four deliverables, at a glance

| Deliverable | Where |
|---|---|
| **1 · Agent Skills** | [`menu/skills/`](menu/skills/) (six skills, à la carte) · [`mega/investigative-desk/`](mega/investigative-desk/) (single-skill form) · [`dist/`](dist/) (zips) |
| **2 · Findings report** | [`submission/findings_report.md`](submission/findings_report.md) (+ [`submission/legal_checks/`](submission/legal_checks/)) |
| **3 · Interaction traces** | [`submission/traces/sessions.html`](submission/traces/sessions.html) (every skill invocation, full arguments) · [`submission/traces/outputs/`](submission/traces/outputs/) (verbatim outputs) · [`submission/traces/trace_index.md`](submission/traces/trace_index.md) (narrative index + scope note) |
| **4 · README** | [`submission/README.md`](submission/README.md) — skills ↔ findings map, outside data, conflicts of interest, legal flags for the panel |

## The assembly line

```
scope the question (works on ANY dataset; picks or builds the beat's plan)
  → gather & analyze   ingest + web-search-for-data · profile (robodoig) ·
                       discover leads · cross-check vs ground truth
  → organize           case-file: threads, status, cold-ledger, journal
  → harden claims      checking-the-law · howard-center-footnoter · QA
  → findings report + review dashboard
     (verifiability contract underneath: every number carries a provenance id)
```

Also in this repo, demonstrated end-to-end on real data:

- [`submission/generality_demo/`](submission/generality_demo/) — the same line on a
  **non-lobbying** beat (Medicare up-coding): the scoping step built a healthcare plan and
  web-search-for-data surfaced + snapshotted an HHS-OIG primary source.
- [`submission/footnoter_demo/`](submission/footnoter_demo/) — the findings draft
  footnoted to the engine's own outputs as Word tracked changes, with margin flags.
- [`submission/review_dashboard.html`](submission/review_dashboard.html) — generated from
  the real case file ([`casefile/`](casefile/)); every claim links to a source record.

## Reproduce (no API key, no network needed for the core findings)

Runs inside a code-executing agent (Claude Code, Cursor, Cowork) or any shell. Python
standard library only. Evaluators supply the corpus via `GAIN_DATA_DIR`
(see [`menu/data-setup.md`](menu/data-setup.md)).

```bash
export GAIN_DATA_DIR=/path/to/data GAIN_WORKDIR=$PWD/workdir
python3 menu/skills/lobbying-influence-mapper/scripts/ingest.py --years 2025 --datasets senate contributions press
python3 menu/skills/lobbying-influence-mapper/scripts/resolve_entities.py
python3 menu/skills/lobbying-influence-mapper/scripts/xref.py gatekeeper --filer lobbyist --year 2025 --top 12
python3 menu/skills/lobbying-influence-mapper/scripts/xref.py anomaly --year 2025 --factor 5
python3 validate_skills.py menu/skills      # all 6 skills validate against the spec
```

Optional free keys (Congress.gov, FEC) unlock live refreshes: `python3 menu/setup_keys.py`.
Shipped snapshots reproduce every keyed finding offline.

## Team

Walter Cronkite School of Journalism and Mass Communication, Arizona State University.
Evan Wyloge, Shelby Grossman & Katie Wilcox (Professors of Practice); Allie Seligman
(Clinical Assistant Professor); Stephen K. Doig (Professor); Brett Kurland (Assistant
Dean & Professor of Practice); DeAnna Soth (Learning Design Principal); Mitul
Balamurugan (ASU computer science student). License: MIT.

> This repo previously hosted Evan's solo entry (the `lobbying-influence-mapper` alone);
> that work is superseded by — and included within — this combined submission. See git
> history for the original.
