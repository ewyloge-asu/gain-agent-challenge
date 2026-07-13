# Interaction Traces

**Skill-invocation traces (the published record):** **`sessions.html`** — every actual
skill invocation across the four working sessions, with full arguments, in order
(regenerate via `python3 render_traces.py`).

**Scope note.** We read the traces deliverable — "full logs of the model sessions …
keyed to the skill invocations they came from" — as covering the sessions *using* the
tool stack: every invocation, its inputs, and its outputs. Our working sessions
interleaved that use with building the tools themselves (and ordinary team
conversation), which is development history, not an interaction trace of the skills.
This record therefore includes the complete log of tool use — nothing that ran is
omitted — while development activity is out of scope and counted where it was removed.

**Invocation outputs:** the actual *outputs* of every key invocation are captured
verbatim in **`outputs/`** — one file per numbered step below (e.g.
`04_gatekeeper_top12.json`, `06_review_locnation_roundtrip.json`), plus
`00_cold_rerun_transcript.txt`, the full log of the clean-workdir re-run that reconfirms
the headline numbers. Every output regenerates from the commands shown.

**This file is the curated index** into those logs: the investigation session that
produced `findings_report.md`, keyed to the skill invocations. Each step lists the
**skill / command**, the **key output**, and any **human-judgment moment** (where a
person intervened — the thing the challenge asks us to surface). All numbers are from
the full 2025 corpus. Steps 1–10 map to Session 3; step 3's third pass and step 11 map
to Session 4.

Environment: `GAIN_DATA_DIR=data` (full corpus), `GAIN_WORKDIR=build/workdir`. Runtime:
Python standard library only.

---

### 1 · S0 scope-framing → case file  (`investigative-method` / `scope.py`, `case-file`)
```
casefile.py --dir casefile init
scope.py --dir casefile --force --question "Where does lobbyist money concentrate, and does
   the disclosure system contain integrity anomalies worth flagging?" --domain lobbying ...
```
Output: `brief.md` (question/scope/finding bar) + `beatpack.json` (auto-selected the
**lobbying** beat-pack). **Human judgment:** framed the question and the finding bar;
chose the inclusive-but-ranked scope (Option A).

### 2 · Model the corpus  (`lobbying-influence-mapper` / `ingest.py`)
```
ingest.py --years 2025 --datasets senate contributions press
```
Output: `108,225` senate filings · `203,427` activities · `543,990` lobbyist-rows ·
`39,438` contribution reports (`149,182` items) · `48,318` press releases. ~14s.

### 3 · Resolve entities  (`lobbying-influence-mapper` / `resolve_entities.py`)
First run: honoree→member coverage **60.6%**. **Human judgment:** noticed the headline
micro-example (Guthrie) was missing from the resolved leaderboard, diagnosed that the
`members` table was built only from the press corpus (Senate-heavy), and fixed the resolver
to **seed members from the congress-legislators roster** + harden the name key.
Second run: coverage **80.5%**; every headline recipient now resolves.
Third pass (follow-up session): resolved **campaign-committee honorees** ("Guthrie for
Congress", "Friends of Glenn Thompson") to their member with a conservative,
unique-match-only extractor, and enriched roster-seeded members with party/state + canonical
names. Coverage **81.8%** (+~$4.9M correctly attributed); the remaining unresolved tail is
dominated by non-member entities (party committees, inaugural committees, caucus
foundations) that should not attribute to a member.

### 4 · PAY leaderboard  (`lobbying-influence-mapper` / `xref.py gatekeeper`)
```
xref.py gatekeeper --filer lobbyist --year 2025 --top 12
```
Output (top 3): Brett Guthrie $694,295 (177 registrants) · Jason Smith $674,775 · Mark
Warner $632,009. **Human judgment:** confirmed thread T-0001 (pay-the-gavel) with a source
record; scoped the claim to bill *sponsorship*, not votes.

### 5 · Anomaly / integrity  (`lobbying-influence-mapper` / `xref.py anomaly`)
```
xref.py anomaly --year 2025 --factor 5
```
Output: Loc Nation is the #1 income outlier. **Human judgment:** the raw sum read **$180M
across 11 filings**; on inspecting the filings (Q1–Q4 + 7 amendments) reconciled to the
defensible **$80M** and folded **amendment-aware de-dup** into the tool. Loc Nation remains
the #1 outlier at **15.6×** the next real client (Qualcomm $5.13M).

### 6 · Verifiability round-trip  (`lobbying-influence-mapper` / `review.py`)
```
review.py "data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1"
```
Output: the raw Loc Nation filing — type "1st Quarter - Amendment", income $20,000,000,
posted by "REV DR CHRISTINA L CLEMENT", registrant "LOC COMMUNITY ASSOCIATION". Confirms the
claim → source contract.

### 7 · Coordinated messaging (method)  (`lobbying-influence-mapper` / `detect_coordination.py`)
```
detect_coordination.py clusters --year 2025 --min-members 6
```
Output: a **9-member bipartisan** cluster (span 2 days) reusing an identical CAP statistic
while reintroducing the American Dream and Promise Act (Feb 2025); a 6-member Maryland
firefighter-grant cluster.

### 8 · Organize  (`case-file` / `update-status`, `log`, `lint`, `brief`)
T-0001 chasing→**confirmed** (with source); T-0004 open→**cold** (reason recorded);
`lint`: clean (4 threads, 1 finding). **Human judgment:** parked Senate↔House as cold with a
recorded reason so it is not re-chased.

### 9 · Legal checks  (`checking-the-law`)
Two verdicts produced (`legal_checks/loc_nation.md`, `legal_checks/mcentee_fara.md`), both
**genuinely-unclear → for the panel**. **Human judgment:** framed each as a reporting
assessment/question for a lawyer, never a conclusion of illegality.

### 10 · Review surface  (`investigative-method` / `build_dashboard.py`)
Generated `review_dashboard.html` from the case file (thread board + findings + legal flags +
provenance links) for editor review.

### 11 · Cold thread re-verified  (`lobbying-influence-mapper` / `ingest.py house`, `xref.py mismatch`)
```
ingest.py --years 2025 --datasets house   →  resolve_entities.py  →
xref.py mismatch --year 2025 --min-gap 100000
```
Output: 108,518 House filings, 98.3% bridged; **36,643 comparable engagement-periods, 0
gaps >$100K**. **Human judgment:** the naive first pass showed 19 six-figure "gaps"; on
inspection every one was a quarterly-amendment artifact (original vs amendment across
chambers). Made the comparison amendment-aware on both chambers — same de-dup discipline
as Loc Nation — and all 19 collapsed to zero. T-0004 stays cold, now with a this-session
source record.

### 12 · Footnote the findings  (`howard-center-footnoter`, end-to-end)
```
extract_claims.py findings_draft.docx → ingest_sources.py sources/ →
(agent matches claims → verbatim engine outputs) → format_footnote.py →
insert_tracked_footnotes.py --flags flags.json
```
Output: `footnoter_demo/findings_draft_footnoted.docx` — 10 tracked-change footnotes
(9 sourced to real pipeline outputs + 1 ⟨NEEDS SOURCE⟩) and 2 margin comments.
**Human judgment:** matched each claim to the verbatim supporting passage with surrounding
context; flagged the DoD China-list date as `no_source` (real-world context, not a corpus
fact) and the Tencent ~5× multiplier as `context_concern` (the extract covers 2025 only) —
the skill never fabricates a source.

---

## Reproducibility
```
export GAIN_DATA_DIR=/path/to/data GAIN_WORKDIR=$PWD/build/workdir
python3 skills/lobbying-influence-mapper/scripts/ingest.py --years 2025 --datasets senate contributions press
python3 skills/lobbying-influence-mapper/scripts/resolve_entities.py
python3 skills/lobbying-influence-mapper/scripts/xref.py gatekeeper --filer lobbyist --year 2025 --top 12
python3 skills/lobbying-influence-mapper/scripts/xref.py anomaly --year 2025 --factor 5
```
External enrichment (committee roles, FEC denominator, FARA) falls back to shipped snapshots,
so the core findings re-run with no API key and no network.
