# GAIN Agentic Investigation Challenge — Submission (ASU / Howard Center team)

A reusable **investigative assembly line** for records investigations — six composable
Agent Skills plus the newsworthy findings they produced on the GAIN federal lobbying
corpus (2022–2026 Q1).

**Site:** https://ewyloge-asu.github.io/gain-agent-challenge/ ·
**Submission map (required README):** [`submission/README.md`](submission/README.md)

## The four deliverables, at a glance

| Deliverable | Where |
|---|---|
| **1 · Agent Skills** | [`menu/skills/`](menu/skills/) (six skills, à la carte) · [`mega/investigative-desk/`](mega/investigative-desk/) (single-skill form) · [`dist/`](dist/) (zips) |
| **2 · Findings report** | [`submission/findings_report.md`](submission/findings_report.md) (+ [`submission/legal_checks/`](submission/legal_checks/)) |
| **3 · Interaction traces** | [`submission/traces/raw/`](submission/traces/raw/) (full session logs, JSONL) · [`submission/traces/sessions.html`](submission/traces/sessions.html) (rendered) · [`submission/traces/trace_index.md`](submission/traces/trace_index.md) (curated index) |
| **4 · README** | [`submission/README.md`](submission/README.md) — skills ↔ findings map, outside data, conflicts of interest, legal flags for the panel |

## The assembly line

```
S0 scope-framing (works on ANY dataset; selects/synthesizes a beat-pack)
  → gather & analyze   ingest + web-search-for-data · profile (robodoig) ·
                       discover leads · cross-check vs ground truth
  → organize           case-file: threads, status, cold-ledger, journal
  → harden claims      checking-the-law · howard-center-footnoter · QA
  → findings report + review dashboard
     (verifiability contract underneath: every number carries a provenance id)
```

Also in this repo, demonstrated end-to-end on real data:

- [`submission/generality_demo/`](submission/generality_demo/) — the same line on a
  **non-lobbying** beat (Medicare up-coding): S0 synthesized a healthcare beat-pack and
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

ASU / Howard Center for Investigative Journalism team. Contributors: Evan
(analysis engine, connectors, findings), Steve (RoboDoig profiler + QA), Mitul
(checking-the-law), Allie + Katie (case-file, amendment-aware de-dup), Shelby
(howard-center-footnoter, story framing). License: MIT.

> This repo previously hosted Evan's solo entry (the `lobbying-influence-mapper` alone);
> that work is superseded by — and included within — this combined submission. See git
> history for the original.
