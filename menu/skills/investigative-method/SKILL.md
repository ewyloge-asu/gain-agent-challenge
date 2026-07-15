---
name: investigative-method
description: >-
  Run a records-based investigation end to end on ANY dataset — scope the question with
  the user, open a durable case file, gather the given data plus relevant outside data
  (including web-search for datasets/APIs), profile it, surface and rank leads, verify
  them against ground truth, check the law, and footnote every claim — keeping the
  investigation organized across sessions with every number traceable to a source. Use
  whenever a user wants to investigate a dataset, "find stories in this data", triage
  leads, or run a reproducible public-records investigation.
license: MIT
metadata:
  author: Arizona State University team
  version: "0.2.0"
---

# Investigative Method

A self-contained playbook + toolset for turning a dataset into sourced, defensible
findings. It doesn't hand off to other skills — it walks the whole path itself: scope,
acquire, profile, find leads, cross-check, check the law, stay organized, and footnote —
enforcing one rule throughout: **every claim traces to a source.**

It works on **any dataset**. The first stage — scoping with the user — is what decides
which beat-pack (domain knowledge: entity keys, outside sources, relevant law) and which
outside data the rest of the run uses.

## What's in this skill

```
investigative-method/
  SKILL.md
  tools/
    scope.py           S0 — clarifying questions → casefile/brief.md + beatpack.json
    casefile.py         durable state: threads, findings, legal flags, entities, journal
    find_data.py        propose public datasets/APIs for a topic (curated + live CKAN)
    fetch_source.py      fetch + snapshot (sha256, content-type) any URL for reproducibility
    build_dashboard.py   render a single-file HTML review dashboard from the case file
```

All tools are Python standard-library only (no installs required). Data profiling,
lead-discovery, legal research, and footnoting are done directly — write short pandas/
duckdb snippets and reason about the results — rather than through a packaged tool,
since those steps depend on whatever the dataset and domain actually are.

## The workflow

### Phase 1 — Scope the question (INTERACTIVE, LOOPING — do this first, every time)

Do **not** jump into analysis. Pin down what's actually being investigated, with the
user in the loop:

1. **Ask clarifying questions** until you can state the *question*, the *scope*
   (entities, time range, jurisdiction/domain), and *what would count as a finding* (the
   finding bar). Run `python3 tools/scope.py --dir casefile --interactive` to be walked
   through the prompts, or gather the answers in conversation and pass them as flags
   (see `--help`).
2. **Open the case file** with that scope:
   ```bash
   python3 tools/scope.py --dir casefile --question "..." --entities "..." \
       --from 2025-01-01 --to 2025-12-31 --jurisdiction "..." --domain "..." \
       --finding-bar "..."
   python3 tools/casefile.py --dir casefile init
   ```
   `scope.py` writes `casefile/brief.md` (the case brief — human-owned from here on)
   and `casefile/beatpack.json` (the selected domain pack). `casefile.py init` scaffolds
   the rest of the state (threads/, findings.json, entities.json, journal.jsonl).
3. **Pick or synthesize the beat-pack.** `scope.py` ships a **lobbying** beat-pack (US
   federal LDA/LD-203 filings, relevant entity keys, campaign-finance/lobbying-law
   pointers, and outside sources like Congress.gov/FEC/FARA/Voteview). For any other
   beat, it emits a generic pack — read `casefile/beatpack.json` and fill in: which
   datasets, which entity keys (the join columns), and which laws are plausibly
   relevant. This is a map, never the answer.
4. **Loop.** Scope is not one-shot. If acquisition or analysis later suggests the story
   is broader or narrower than framed, **ask the user whether to adjust scope**, edit
   `brief.md`, and log the change (`tools/casefile.py --dir casefile log "..."`).

### L0 — Acquire the data (any source)

1. **The given data.** Load it directly (pandas for tabular, or read text/PDF/etc. as
   appropriate) from wherever the user pointed you. Note the path/location in
   `brief.md` if not already there.
2. **Gather relevant OUTSIDE data.** This is part of *building* the story, not just
   checking it. For the scoped topic:
   - `python3 tools/find_data.py "<topic>"` proposes candidate public datasets/APIs —
     a curated catalog of high-value investigative sources (FEC, Congress.gov, FARA,
     USAspending, SEC EDGAR, CourtListener, Federal Register, CMS, GAO, Voteview,
     data.gov) ranked by topic match, plus a live data.gov catalog query and
     ready-to-run web-search queries to widen the net with your own web-search
     capability.
   - `python3 tools/fetch_source.py "<url>" --out-dir casefile/snapshots` retrieves and
     **snapshots** the chosen source (raw bytes + sha256 + fetch timestamp), so the
     finding re-runs offline and the source id can be cited later.
   - If a source needs a key, tell the user which free key to get and why (the pack's
     `external_sources` in `beatpack.json` marks `needs_key`). Keys unlock richer
     tiers; they never gate the core run.
3. **Give every source record a stable id** (e.g. the snapshot's `slug` from its
   `.meta.json`, or a row/line reference into the given data) — this id is what every
   later claim will cite.

### L1 — Profile / orient

Before spending reasoning budget hunting for a story, learn what's actually in the
data: write a short pandas/duckdb pass over each table — column types, ranges and
distributions, null/gap rates, obvious duplicates, and correlations between the columns
that matter for the scoped question. This cheap "what am I looking at?" pass tells you
what counts as *normal*, which is the baseline every anomaly gets compared against.

### L2 — Discover & rank leads

Query the profiled data for the patterns that make a story: concentration (one entity
receiving/giving disproportionately), timing clusters (activity bunched around a vote
or decision), self-dealing (related parties on both sides of a transaction), and
outliers against the L1 baseline. Rank candidates by how surprising they are relative to
the finding bar in `brief.md` — a dataset summary is not a finding.

**Ingest each promising lead as a thread** in the case file:
```bash
python3 tools/casefile.py --dir casefile new-thread --title "..." --priority 1 \
    --next-action "..." --source-records <ids>
```

### L3 — Cross-check against ground truth

For each lead, reconcile it against the outside data gathered in L0 (the snapshots and
any live sources). Record what the records actually show — and remember:
**documented ≠ causation.** A pattern in the data is a lead to chase, not a conclusion.

### L4 — Legal check (per lead, as needed)

When a lead raises "is this illegal / was disclosure required?", research the actual
statute or regulation that applies (use your web-search capability for the current text
and any relevant enforcement guidance; the pack's `law_packs` in `beatpack.json` names
likely areas to start from, e.g. lobbying-disclosure or campaign-finance law). State
findings as *possible* issues for a lawyer or editor to assess — never as "X broke the
law." Record the verdict:
```bash
python3 tools/casefile.py --dir casefile legal-flag --issue "..." --status open \
    --source-records <ids>
```

### L5 — Keep it organized (throughout)

Every session: `python3 tools/casefile.py --dir casefile brief` at the start (shows the
brief, all threads, and the last journal entry); `update-status` / `log` as things
change; `lint` at the end. Threads move `open → chasing → confirmed` (needs a source) or
`→ cold/killed` (needs a reason). Never re-chase a cold thread — `brief` shows why it
was parked.

```bash
python3 tools/casefile.py --dir casefile update-status T003 --to confirmed \
    --source-records <ids>
python3 tools/casefile.py --dir casefile update-status T007 --to cold \
    --reason "outside sources contradict the pattern"
python3 tools/casefile.py --dir casefile lint
```

### L6 — Assure (the verifiability contract)

- Every number in any output carries a source id from L0/L3; a human should be able to
  open the cited snapshot or source row and see the number for themselves.
- Before delivering any generated report, **re-derive every number in the draft
  directly from the data/snapshots and diff it against what's written** — don't trust
  memory for a figure that was computed earlier in the session. Fix any mismatch before
  it goes out.

### L7 — Source & publish

When drafting the findings: cite a source id for every factual claim and every quote,
and make sure it is one a human can round-trip (a snapshot, a specific row/page, a URL).
Generate the review dashboard so an editor can verify by clicking rather than
re-running the analysis:
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
- **Provenance or it didn't happen.** No claim graduates to a finding without a source
  id (`lint` enforces this for findings, legal flags, and confirmed threads).
- **Legal:** the strongest thing you assert is *possible*, for a lawyer — never "X broke
  the law."
- **Comment is sought, never presumed.** No outreach has happened during analysis. Never
  write "did not respond to a request for comment" or any language implying parties were
  contacted. Instead instruct: *seek comment from every named party before publication;
  legal review before any quid-pro-quo implication.*
- **Works on any data:** if it's not lobbying, read the generic beat-pack in
  `beatpack.json`, profile the data yourself (L1), and use `tools/find_data.py` for
  outside sources — don't assume any particular schema.
