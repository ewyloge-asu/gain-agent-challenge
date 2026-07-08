# Agent Skill — Lobbying Influence Mapper

This document explains the *tool* — what it is, why it was necessary, and how it works —
written to be followed without a technical background. The companion document,
[`findings_brief.md`](./findings_brief.md), covers the journalism the tool produced. The
precise technical spec is in
[`lobbying-influence-mapper/SKILL.md`](../lobbying-influence-mapper/SKILL.md).

---

## What is an "Agent Skill," and why does the challenge want one?

The challenge asks for two things: a newsworthy finding, **and** a reusable tool that lets
an AI agent reproduce that kind of investigation on its own.

An **"Agent Skill"** is a packaged set of instructions and scripts that teaches an AI
assistant how to do a specific job — here, "investigate lobbying influence." Think of it as
a playbook plus a toolbox: the AI reads the playbook, runs the included scripts, and can
then answer real investigative questions about the data. The format is an open standard
(agentskills.io), so another newsroom could drop this skill into their own AI assistant and
use it on a different dataset.

The skill is called **`lobbying-influence-mapper`**.

**One-sentence version:** it turns ~8GB of messy, disconnected federal lobbying and press
records into a clean, searchable "influence map" that an AI can reason over — with every
single number traceable back to its source, and the whole thing reproducible offline.

---

## Why a tool was needed at all

The raw data is genuinely hard to use:

- It is **three disconnected formats** — Senate filings in JSON, House filings in XML, press
  releases in another format — spread across roughly **410,000 files**.
- The same person or company is **named inconsistently** across those files, with no shared
  ID linking them. "Brett Guthrie," "Guthrie, Brett (R-KY)," and a press-release byline may
  all be the same person, and nothing in the data says so.

An AI agent cannot simply "read" 410,000 files and keep it all straight — it would be slow,
expensive, and error-prone. So the skill does the heavy, mechanical work *once*, with
ordinary deterministic code, and produces a tidy database the AI can query in seconds. The
AI then spends its effort on judgment, not on grinding through files.

---

## The headline numbers about the tool

- **8 / 4 / 6** — it ships 8 scripts, 4 reference documents, and 6 saved data "snapshots."
- **No dependencies** — the scripts use only Python's built-in library, so there is nothing
  to install and little to break.
- **Works offline** — the core findings reproduce with no internet and no API keys.
- **Passes the spec** — it validates against the official agentskills.io format.

---

## What the tool can actually answer: pay → gatekeep → act

The skill is built to answer the three-part question behind the main finding:

- **PAY — "who funds whom?"** It reads the lobbyist contribution reports and resolves the
  messy honoree names down to a specific, official member-of-Congress ID, with dollars and
  dates attached.
- **GATEKEEP — "does that recipient actually control the agenda?"** It checks each member's
  committee role against an official public roster of Congress.
- **ACT — "what do they then do?"** It pulls their sponsored bills and policy areas
  (Congress.gov) and their voting behavior (Voteview), and grounds the money against their
  total fundraising (FEC).

---

## How it is built — a small assembly line of scripts

The tool is a pipeline: each script does one job and hands off to the next.

```
ingest → resolve_entities → xref (ask questions) → connector (pull outside data) → review / state
```

| Stage | Script | What it does, in plain terms |
|---|---|---|
| **Ingest** | `ingest.py` | Reads the Senate JSON, House XML, and press files and loads them into one tidy database (SQLite). Tags every record with a "where did this come from" stamp. |
| **Resolve** | `resolve_entities.py` | Figures out which differently-spelled names are the same entity, and links the Senate and House versions of the same filing together. |
| **Ask questions** | `xref.py` | The query engine. Commands like `gatekeeper`, `member`, `client`, and `timeline` answer investigative questions and always show their sources. |
| **Detect** | `detect_coordination.py` | Finds coordinated messaging campaigns (the "method" finding). |
| **Pull outside data** | `connector.py` | Safely fetches and caches data from outside sources — the congressional roster, FARA, Voteview, Congress.gov, and the FEC. |
| **Verify** | `review.py` / `state.py` | Takes any "where did this come from" stamp and shows the exact original record; remembers progress between sessions. |

---

## The "reproducibility ladder" — why API keys never block the core findings

Some outside data (like the FEC) needs a free API key. To keep the findings checkable by
anyone without a key, the data is structured in tiers — and a copy ("snapshot") of every
piece of outside data fetched is saved, so the findings re-run later with no internet and no
keys at all.

| Tier | What it needs | What it adds | Re-runnable with no key? |
|---|---|---|---|
| **Tier 0** | Nothing — fully offline | The core pay-the-gavel finding, committee verification, FARA, Voteview votes | Yes (corpus + saved snapshots) |
| **Tier 1** | A free Congress.gov key | The "act" leg: sponsored bills + policy areas | Yes — saved as a snapshot |
| **Tier 2** | A free FEC key | The fundraising "denominator" (lobbyist share of total receipts) | Yes — saved as a snapshot |

The practical upshot: a reviewer with **no keys at all** can still reproduce every headline,
because the saved snapshots are in the package. (Keys, when present, load automatically from
a private `credentials.env` file that is never committed.)

---

## Why this scores well as a *tool* (the four things the challenge rewards)

- **Reusable.** Pointing it at a new outside dataset is a one-line change; caching, offline
  fallback, and source-tracking come for free. It works for any member, committee, or client
  — not just the ones in this investigation.
- **Reproducible.** Deterministic, nothing to install, rebuilds with one command
  (`run_all.sh`). The saved snapshots mean it runs with no network and no secrets.
- **Human-verifiable.** Every number carries a source stamp, and `review.py "<stamp>"` hands
  back the original raw record. Nothing is a black box.
- **Honest by design.** A `methodology.md` spells out the data's limits, where entity-matching
  can go wrong, the "votes track party, not donors" caveat, and that correlation is not
  causation.

---

## What is built now, and what is next

- **Voteview voting records — BUILT** (needs no key). Adds participation, party-loyalty, and
  ideology scores for the top recipients. This is what made it possible to *avoid
  overclaiming*: it revealed the 97–99% party-line voting, so the analysis leans on bill
  sponsorship instead of votes.
- **FARA foreign-principals — QUEUED** (public, no key). Would add the full
  firm → foreign-client → activity → payment chain, to confirm whether Tencent and Nippon
  Steel are the precise FARA principals and to surface agent fees and disclosed official
  contacts.
