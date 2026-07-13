---
name: case-file
description: Keep a multi-day, multi-session investigation oriented across sessions with a durable, git-diffable case file on disk — thread board with a state machine, entity registry, source-bound findings, a cold-thread reasoning ledger, and an append-only journal. Use when running a long-lived investigation (lobbying disclosures, campaign finance, procurement, court records, or similar), when leads must be tracked as open/chasing/cold/confirmed without re-briefing the agent each session, when findings must stay bound to source record IDs an editor can audit, or to hydrate at session start and write investigation state back throughout.
---

# Case File

## Overview

Use this skill to keep a long-running investigation organized, reproducible, and
auditable across many sessions. The case file is a durable, human-readable,
version-controlled record on disk that is the single source of truth for
investigation state. Hydrate from it at the start of every session (`brief`) and
write back to it throughout (`update-status`, `log`).

Design principle: **the machine owns the invariants; the agent owns the narrative.**
Structured fields (thread status, source links, required next actions) go through a
deterministic, LLM-free CLI that enforces a state machine. Reasoning, hypotheses, and
notes are free prose. That split is what keeps the investigation both reproducible
(the tooling replays identically) and rich (the agent writes in its own words).

Built for the GAIN Agent Challenge lobbying corpus, but the machinery is
corpus-agnostic — it composes with any anomaly/lead source and any entity resolver.

## Runtime Requirements

- Python 3 with the standard library only. No third-party packages, no network — so
  every command replays identically (the reproducibility gate).
- Run commands from anywhere; pass the case-file directory with `--dir`. The default
  directory name is `casefile`.
- Keep the case file under version control (git). Every command produces a clean
  diff an editor can audit; `.state.json` is a regenerable cache and can be
  git-ignored.

## File Layout

```
casefile/
  brief.md            # the question, scope, what counts as a finding (stable, human-owned)
  workflow.md         # the reproducible analysis procedure (optional but recommended)
  entities.yaml       # entity registry: canonical_id, display, status, why-it-matters
  threads/
    T-0042.md         # one file per thread: YAML front-matter + free-text body
  findings.yaml       # findings that graduated from a thread, each with >=1 source record
  journal.md          # append-only, timestamped session log
  .state.json         # derived rollup cache (regenerable; never hand-edited)
```

A complete worked example lives in `assets/example-casefile/` (an education-lobbying
investigation with one deep near-confirmed thread and six open leads). Read it to see
the field conventions in practice, or copy it as a starting point. Field-by-field
reference: `references/file_formats.md`.

## The Mandatory Session Ritual

Follow this every session. It is what makes the investigation survive across sessions
instead of being re-briefed from scratch.

**At session start — hydrate, don't re-read the whole case file:**

```bash
python3 scripts/casefile.py --dir casefile brief
```

`brief` is a deterministic digest (no model reasoning): open/chasing threads by
priority with their next actions, recent journal activity, **cold threads with the
reasons they were parked** (so you never re-chase a dead end), and the key entities.
It re-orients you in a few hundred tokens. Start from its "OPEN / CHASING" list.

**During the session — record state as it changes:**

- Move a thread only through the CLI (never hand-edit `status`):

  ```bash
  python3 scripts/casefile.py --dir casefile update-status --thread T-0042 --to chasing
  python3 scripts/casefile.py --dir casefile update-status --thread T-0042 --to cold \
      --reason "checked — the contribution dates don't line up with the votes"
  python3 scripts/casefile.py --dir casefile update-status --thread T-0042 --to confirmed \
      --source "Senate LD-203 2025 filing #abc123"
  ```

- Log narrative progress in your own words:

  ```bash
  python3 scripts/casefile.py --dir casefile log --session S3 \
      "Pulled priority firm filings; drafted comment requests; FEC cross-ref still open."
  ```

**At session end — check for rot and leave a clean state:**

```bash
python3 scripts/casefile.py --dir casefile lint
```

Fix anything `lint` flags before you stop. Then write a "next session — start here"
note with `log`. `update-status` auto-logs transitions and regenerates `.state.json`,
so the next `brief` is already accurate.

## Thread State Machine

```
        open ──▶ chasing ──▶ confirmed
          │         │
          │         ├──▶ cold   (reason required; revivable to chasing)
          └─────────┴──▶ killed (reason required; terminal)
```

The CLI enforces these rules — it will refuse an illegal move:

- `confirmed` requires **≥1 source record ID** (pass `--source`, or the thread must
  already carry `source_records`). `confirmed` is terminal here.
- `cold` and `killed` require a **free-text `--reason`**. `cold` can be revived to
  `chasing`; `killed` is terminal.
- `open`/`chasing` threads must carry a non-empty `next_action` (lint enforces this).

The **cold-thread reasoning ledger** — a recorded reason on every park/kill — is the
distinctive feature. It stops the agent re-chasing dead ends across sessions, the most
common failure mode of long-running agentic investigations. `brief` always surfaces
cold reasons so you decide with the earlier reasoning in front of you.

## What Lint Checks

`lint` enforces the skeleton regardless of how notes were written:

- `open`/`chasing` thread with an empty `next_action`.
- `cold`/`killed` thread with no `reason`.
- Thread claiming `confirmed` with no `source_records`.
- Finding in `findings.yaml` with no `source_records`.
- Entity referenced by a thread but missing from `entities.yaml` (the registry).
- With `--corpus-index PATH` (a file of valid source IDs, one per line): any
  `source_records` ID not present in the corpus index.

```bash
python3 scripts/casefile.py --dir casefile lint --corpus-index corpus_ids.txt
```

## Starting a New Investigation

```bash
# copy the worked example as a template, then edit brief.md / workflow.md:
python3 scripts/casefile.py --dir casefile init --template assets/example-casefile

# or scaffold an empty skeleton:
python3 scripts/casefile.py --dir casefile init
```

Then: write `brief.md` (question, scope, finding bar), register canonical entities in
`entities.yaml`, and open one thread file per lead under `threads/` (front-matter +
hypothesis body). Ingest leads from an upstream anomaly/lead source as threads;
reference an entity resolver's canonical IDs in the registry.

## Evidence Rules

- Every thread and finding names its **source records** and the **workflow step /
  script** that produced it. No source, no `confirmed`.
- "documented" (present in public filings) is not "confirmed causation." Record what
  the records show; keep influence/causation as an open reporting question in the
  thread body, not a finding claim.
- Put possible legal/ethics issues in `findings.yaml` under `legal_flags` with a
  `status: to_verify` so they surface for review rather than getting buried.
- The journal is append-only. Never rewrite past entries; add a new one.

## How It Composes

- **Anomaly / lead source** → leads become thread files under `threads/`.
- **Entity resolver** → `entities.yaml` references its canonical IDs (the join key).
- **Findings report** (deliverable) → generated from `findings.yaml`.
- **Interaction traces** (deliverable) → the append-only `journal.md` is most of the
  spine; keep sessions keyed to it.

## Command Reference

| Command | What it does |
|---|---|
| `init [--template DIR]` | Scaffold a new case file (empty, or copied from a template). |
| `brief` | Deterministic session-start digest. Run first, every session. |
| `update-status --thread ID --to STATUS [--reason ...] [--source ...]` | Move a thread through the state machine (enforces the rules; auto-logs; refreshes `.state.json`). |
| `log --session ID "message"` | Append a timestamped journal entry. |
| `lint [--corpus-index PATH]` | Enforce the invariants. Run at session end. |
| `rollup` | Regenerate the `.state.json` rollup cache. |

Attribution: created for the GAIN Agent Challenge package. It does not incorporate
external Agent Skill source code. All scripts are LLM-free standard-library Python.
