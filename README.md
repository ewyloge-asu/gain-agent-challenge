# Agent of Record — GAIN Agentic Investigation Challenge submission (Arizona State University team)

Six standalone Agent Skills for records investigations. Each works on its own — there's
no required pipeline — and they can be combined for a fuller investigation. Plus the
newsworthy findings they produced on the GAIN federal lobbying corpus (2022–2026 Q1).

**Site:** https://ewyloge-asu.github.io/gain-agent-challenge/ ·
**Submission map (required README):** [`submission/README.md`](submission/README.md) ·
**Plain-repo edition** (same submission, no website layer): [ewyloge-asu/case-agent](https://github.com/ewyloge-asu/case-agent)

## The four deliverables, at a glance

| Deliverable | Where |
|---|---|
| **1 · Agent Skills** | [`menu/skills/`](menu/skills/) — six standalone skills, install only what you need · [`dist/`](dist/) (per-skill zips) |
| **2 · Findings** | published as summary bullets on the [site](https://ewyloge-asu.github.io/gain-agent-challenge/#findings) (+ [`submission/legal_checks/`](submission/legal_checks/)) |
| **3 · Interaction traces (logs)** | [`submission/traces/outputs/`](submission/traces/outputs/) — verbatim logs backing each published finding |
| **4 · README** | [`submission/README.md`](submission/README.md) — skills ↔ findings map, outside data, conflicts of interest, legal flags for the panel |

## How the skills can be combined

There's no formal pipeline — each skill validates and runs on its own. This is simply
one way we combined them for the lobbying corpus:

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

- We also ran all six skills together on a **non-lobbying** beat (Medicare up-coding):
  the scoping step built a healthcare plan and web-search-for-data surfaced + snapshotted
  an HHS-OIG primary source.
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
python3 validate_skills.py menu/skills      # all 6 skills validate against the spec
```

Optional free keys (Congress.gov, FEC) unlock live refreshes: `python3 menu/setup_keys.py`.
Shipped snapshots reproduce every keyed finding offline.

## Team

A group of faculty at the Walter Cronkite School of Journalism and Mass Communication,
Arizona State University. Mitul Balamurugan (masters student, Fulton Schools of
Engineering, ASU); Stephen K. Doig (Professor); Shelby Grossman (Professor of Practice);
Brett Kurland (Assistant Dean & Professor of Practice); Allie Seligman (Clinical
Assistant Professor); Katie Wilcox (Professor of Practice); Evan Wyloge (Professor of
Practice). License: MIT.

> This repo previously hosted Evan's solo entry (the `lobbying-influence-mapper` alone);
> that work is superseded by — and included within — this combined submission. See git
> history for the original.
