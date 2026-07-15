---
name: investigative-method
description: >-
  The front door of a records investigation: scope the question with the user, find and
  snapshot the outside data it needs (including web-search for datasets/APIs), and
  render a case file into a single-file review dashboard. It composes with — but does
  not duplicate — the other five skills: hand off to case-file for durable thread/entity
  tracking, robodoig or lobbying-influence-mapper for profiling and modeling, checking-
  the-law for legal questions, and howard-center-footnoter for sourcing a draft. Use
  whenever a user wants to start a new investigation, scope a question, find outside
  data/datasets/APIs for a topic, or turn a case file into a shareable dashboard.
license: MIT
metadata:
  author: Arizona State University team
  version: "0.3.0"
---

# Investigative Method

Three unique jobs, done well, rather than one skill trying to do everything: **scope**
the question with the user, **find and snapshot** the outside data an investigation
needs, and **render** a case file into a dashboard a human can review by clicking. It
works on **any dataset** — the scoping step is what decides which beat-pack (domain
knowledge: entity keys, outside sources, relevant law) applies.

Everything else — profiling data, discovering and ranking leads, cross-checking, legal
review, footnoting a draft — is the job of a more specialized skill (robodoig,
lobbying-influence-mapper, checking-the-law, howard-center-footnoter) or of case-file for
staying organized across sessions. This skill points you to the right one rather than
reimplementing what it already does well.

## What's in this skill

```
investigative-method/
  SKILL.md
  tools/
    scope.py           clarifying questions → casefile/brief.md + beatpack.json
    find_data.py        propose public datasets/APIs for a topic (curated + live CKAN)
    fetch_source.py      fetch + snapshot (sha256, content-type) any URL for reproducibility
    build_dashboard.py   render a single-file HTML review dashboard from a case file
```

All four tools are Python standard-library only (no installs required).
`build_dashboard.py` is the one exception to "no dependency": it reads a case file
produced by the **case-file** skill, and imports that skill's parser directly rather
than shipping a second copy of it — so it needs case-file installed alongside this
skill (e.g. `~/.claude/skills/case-file/`) to run.

## The workflow

### 1 — Scope the question (INTERACTIVE, LOOPING — do this first, every time)

Do **not** jump into analysis. Pin down what's actually being investigated, with the
user in the loop:

1. **Ask clarifying questions** until you can state the *question*, the *scope*
   (entities, time range, jurisdiction/domain), and *what would count as a finding* (the
   finding bar). Run `python3 tools/scope.py --dir casefile --interactive` to be walked
   through the prompts, or gather the answers in conversation and pass them as flags
   (see `--help`).
2. **Write the brief:**
   ```bash
   python3 tools/scope.py --dir casefile --question "..." --entities "..." \
       --from 2025-01-01 --to 2025-12-31 --jurisdiction "..." --domain "..." \
       --finding-bar "..."
   ```
   This writes `casefile/brief.md` (the case brief — human-owned from here on) and
   `casefile/beatpack.json` (the selected domain pack).
3. **Pick or synthesize the beat-pack.** `scope.py` ships a **lobbying** beat-pack (US
   federal LDA/LD-203 filings, relevant entity keys, campaign-finance/lobbying-law
   pointers, and outside sources like Congress.gov/FEC/FARA/Voteview). For any other
   beat, it emits a generic pack — read `casefile/beatpack.json` and fill in: which
   datasets, which entity keys (the join columns), and which laws are plausibly
   relevant. This is a map, never the answer.
4. **Loop.** Scope is not one-shot. If acquisition or analysis later suggests the story
   is broader or narrower than framed, ask the user whether to adjust scope and edit
   `brief.md` (or log the change via case-file, if installed).

### 2 — Find & snapshot outside data

Gathering outside data is part of *building* the story, not just checking it. For the
scoped topic:

- `python3 tools/find_data.py "<topic>"` proposes candidate public datasets/APIs — a
  curated catalog of high-value investigative sources (FEC, Congress.gov, FARA,
  USAspending, SEC EDGAR, CourtListener, Federal Register, CMS, GAO, Voteview, data.gov)
  ranked by topic match, plus a live data.gov catalog query and ready-to-run web-search
  queries to widen the net with your own web-search capability.
- `python3 tools/fetch_source.py "<url>" --out-dir casefile/snapshots` retrieves and
  **snapshots** the chosen source (raw bytes + sha256 + fetch timestamp), so the finding
  re-runs offline and the source id can be cited later.
- If a source needs a key, tell the user which free key to get and why (the pack's
  `external_sources` in `beatpack.json` marks `needs_key`). Keys unlock richer tiers;
  they never gate the core run.

Give every source record a stable id (e.g. the snapshot's `slug` from its `.meta.json`,
or a row/line reference into the given data) — this is what every later claim cites.

### 3 — Hand off to the specialized skill for the job at hand

- **Profile the data / find leads:** robodoig (any table) or lobbying-influence-mapper
  (the lobbying beat).
- **Stay organized across sessions:** case-file — threads, findings, legal flags,
  entities, journal.
- **Legal questions:** checking-the-law — reads the actual statute, applies it
  element-by-element, never asserts more than "possible, ask a lawyer."
- **Source a draft:** howard-center-footnoter — ties every claim to a primary source as
  tracked changes.

This skill doesn't reimplement any of that work; it hands you to the tool built for it.

### 4 — Render the review dashboard

Once a case file exists (via case-file), turn it into something an editor can review by
clicking rather than re-running the analysis:
```bash
python3 tools/build_dashboard.py --dir casefile --out review_dashboard.html
```
This single HTML file (no server, no deps) shows the brief, the thread board by status,
findings, legal flags, and key entities.

## Guardrails

- **Scope first, always.** No analysis before the scoping step. The scope selects the
  beat-pack.
- **Human in the loop.** Ask clarifying questions up front and whenever the data
  suggests the scope should change.
- **Snapshot what you cite.** Any outside source pulled in via `fetch_source.py` is
  hashed and dated, so a finding built on it re-runs and re-verifies offline.
- **Works on any data:** if it's not lobbying, read the generic beat-pack in
  `beatpack.json` and use `tools/find_data.py` for outside sources — don't assume any
  particular schema.
