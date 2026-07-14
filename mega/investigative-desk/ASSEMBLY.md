---
name: investigative-method
description: >-
  Orchestrate a records-based investigation end to end on ANY dataset — not just
  lobbying. Start by scoping the question with the user (clarifying questions),
  open a durable case file, gather the given data plus relevant outside data
  (including web-search for datasets/APIs), profile it, surface and rank leads,
  verify them against ground truth, check the law, and footnote every claim —
  keeping the investigation organized across sessions with every number traceable
  to a source. Use whenever a user wants to investigate a dataset, "find stories
  in this data", triage leads, or run a reproducible public-records investigation.
license: MIT
metadata:
  author: Arizona State University team
  version: "0.1.0"
---

# Investigative Method (orchestrator)

This skill is the **spine of a full investigation**. It doesn't do the heavy lifting
itself — it *routes* between focused sub-skills in the right order, keeps the work
organized, and enforces one rule everywhere: **every claim traces to a source.**

It is built to work on **any dataset**, not only the bundled lobbying corpus. What makes
that possible is the first stage: you *scope the investigation with the user* and that
scope decides which **beat-pack** and which **outside data** the rest of the run uses.

## The three phases (and the sub-skills in each)

```
  ┌── STAYING ORGANIZED: case-file — created at scoping, updated throughout ──────────┐
  └────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────────────────────────────┐     ┌──────── HARDENING CLAIMS ────────────────┐
 │ GATHERING & ANALYZING                 │  →  │ checking-the-law · howard-center-        │
 │ scope the question · acquire data     │     │ footnoter · robodoig/verify_report       │
 │ (+web) · profile · discover leads ·   │     └──────────────────────────────────────────┘
 │ cross-check against ground truth      │
 └──────────────────────────────────────┘
  └── the rule underneath: provenance on every number; a human can round-trip it ───────┘
```

- **Gathering & analyzing:** `robodoig` (profile any table) +
  `lobbying-influence-mapper` (model/discover/verify for the lobbying beat) + this skill's
  acquisition tools (`tools/find_data.py`, `tools/fetch_source.py`).
- **Staying organized:** `case-file` (threads, status, entities, journal).
- **Hardening claims (quality control):** `checking-the-law` (legal), `howard-center-footnoter`
  (source every sentence), and `robodoig`'s `verify_report.py` (transcription check).

## The workflow

### Phase 1 — Scope the question  (INTERACTIVE, LOOPING — do this first, every investigation)

Do **not** jump into analysis. First, pin down what you're actually investigating, with the
user in the loop:

1. **Ask clarifying questions** until you can state: the *question*, the *scope* (entities,
   time range, jurisdiction/domain), and *what would count as a finding* (the finding bar).
   Run `python3 tools/scope.py --interactive` to be walked through the prompts, or gather
   the answers in conversation.
2. **Open the case file** with that scope — the scope IS the case file's `brief.md`:
   ```bash
   python3 ../case-file/scripts/casefile.py --dir casefile init
   # then write brief.md from the scope (question / scope / finding bar)
   ```
   `tools/scope.py` will scaffold `casefile/brief.md` and a `beatpack.json` for you.
3. **Pick the beat-pack.** The scope selects which domain pack + outside sources apply.
   This bundle ships a **lobbying** beat-pack (the mapper's connectors, ALI codes, FARA
   cross-walk; and `checking-the-law`'s US influence + campaign-finance law packs). For a
   new beat, synthesize a minimal pack (which datasets, which entity keys, which laws).
4. **Loop.** Scope is not one-shot. If acquisition or analysis later suggests the story is
   broader or narrower than framed, **ask the user whether to adjust scope**, then update
   `brief.md` and the threads. Record scope changes in the journal.

### L0 — Acquire & model the data (any source)

1. **The given data.** Point the analysis engine at it (`GAIN_DATA_DIR` for the lobbying
   corpus; for other tabular data, hand it to `robodoig` directly). See
   `../lobbying-influence-mapper/SKILL.md` and `../../data-setup.md`.
2. **Gather relevant OUTSIDE data (this is part of building the story, not just checking
   it).** For the gauged topic:
   - Known structured sources → the mapper's `connector.py` (Congress.gov, FEC, Voteview,
     FARA, committees).
   - **Web-search for datasets/APIs** → `tools/find_data.py "<topic>"` proposes candidate
     public datasets/APIs; then `tools/fetch_source.py <url>` retrieves and **snapshots**
     the chosen one so the finding re-runs offline. Use your web-search capability to fill
     the candidate list when the catalog is thin.
   - If a source needs a key, run `../../setup_keys.py` (it tells the user how to get each
     free key). Keys only unlock richer tiers; they never gate the core run.
3. **Model it** into the store (`ingest.py`, `resolve_entities.py`), provenance-stamped.

### L1 — Profile / orient

Run `robodoig` on the tabular slices to learn what's there and what's normal (types,
distributions, correlations, gaps). This is the cheap "what am I looking at?" pass before
spending reasoning budget. Read `../robodoig/SKILL.md`.

### L2 — Discover & rank leads

Use the mapper's query + anomaly + coordination commands (`xref.py`,
`detect_coordination.py`) to surface candidates. **Ingest each promising lead as a thread**
in the case file (`update-status --to chasing`), with its `next_action`.

### L3 — Cross-check against ground truth

For each lead, reconcile against the outside data gathered in L0 (`connector.py`,
snapshots). Record what the records show — and remember: **documented ≠ causation.**

### L4 — Legal check (per lead, as needed)

When a lead raises "is this illegal / was disclosure required?", run `checking-the-law` on
that one question. Carry its verdict verbatim into the thread; surface possible violations
as *questions for the panel/lawyer*, never as conclusions. Record in `case-file` under
`legal_flags`.

### L5 — Keep it organized (throughout)

Every session: `casefile.py brief` at start, `update-status` / `log` as things change,
`lint` at end. Threads move `open → chasing → confirmed` (needs a source) or `→ cold/killed`
(needs a reason). Never re-chase a cold thread — `brief` shows why it was parked.

### L6 — Assure (the verifiability contract)

- Every number in any output carries a provenance id; `../lobbying-influence-mapper/scripts/review.py "<prov>"`
  round-trips it to the raw record.
- Before delivering any generated report, run `../robodoig/scripts/verify_report.py` to catch
  transcription slips between the computed numbers and the written report.

### L7 — Source & publish

When drafting the findings, run `howard-center-footnoter` on the draft to tie every claim
to a primary source (tracked changes) and flag unsupported / out-of-context claims. Generate
the review dashboard (`tools/build_dashboard.py`) so an editor can verify by clicking.

## Guardrails
- **Scope first, always.** No analysis before the scoping step. The scope selects the beat-pack.
- **Human in the loop.** Ask clarifying questions up front and whenever the data suggests
  the scope should change.
- **Provenance or it didn't happen.** No claim graduates to a finding without a source id.
- **Legal:** the strongest thing you assert is *possible*, for a lawyer — never "X broke
  the law."
- **Comment is sought, never presumed.** No outreach has happened during analysis. Never
  write "did not respond to a request for comment" or any language implying parties were
  contacted. Instead instruct: *seek comment from every named party before publication;
  lawyer review before any quid-pro-quo implication.*
- **Works on any data:** if it's not lobbying, synthesize a minimal beat-pack at the scoping step and lean
  on `robodoig` + web-search-for-data; don't assume the lobbying schema.

## Related
- `lobbying-influence-mapper`, `robodoig` (the gathering & analyzing phase) · `case-file` (the staying-organized phase) ·
  `checking-the-law`, `howard-center-footnoter` (the claim-hardening phase).
