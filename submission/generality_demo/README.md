# Generality test — the FULL assembly line on a non-lobbying beat

The challenge asks for skills that "would generalize past this particular investigation."
This folder is the proof: the same pipeline that produced the lobbying findings, run
**end-to-end on a different beat with zero lobbying-specific code** — Medicare hospital
billing (the cross-domain test a teammate proposed). Every stage below actually ran; every
artifact is in this folder.

## The run, stage by stage

**1 · S0 scope-framing** (`investigative-method/tools/scope.py`) — the healthcare question
produced a case brief + a *synthesized* `healthcare` beat-pack (not the lobbying pack):

```bash
python3 tools/scope.py --dir casefile \
  --question "Which hospitals show billing patterns consistent with Medicare up-coding, and did their reimbursements outpace peers?" \
  --domain healthcare --jurisdiction "US federal" --from 2020-01-01 --to 2025-12-31 \
  --finding-bar "a named-provider billing pattern deviating from peer baseline, sourced to CMS records"
```
→ `casefile/brief.md` + `casefile/beatpack.json`

**2 · Web-search-for-data** (`tools/find_data.py`) — three legs, all live: the curated
catalog ranked **CMS/data.cms.gov** first; a live CKAN query (data.ca.gov) surfaced the
state's suspended-provider list; the tool's suggested `site:.gov` search surfaced
**HHS-OIG report OEI-02-18-00380** — which recommends targeted review of *stays billed at
the highest severity level* and *the hospitals that frequently bill them*. That report
defined the anomaly rule for stage 5. → `found_sources.json`

**3 · Snapshot the sources** (`tools/fetch_source.py`) — the OIG report **and three CMS
data slices** (simple pneumonia at its three severity tiers: DRG 193 "with MCC" / 194
"with CC" / 195 "without") fetched from the live data.cms.gov API and stored with URL,
timestamp, and sha256 → `snapshots/` (4,079 provider×DRG rows, re-runs offline).

**4 · Profile** (`robodoig/scripts/analyze.py`) — the combined slice profiled
deterministically: 4,079 records, 10 variables typed, descriptive stats, 3 correlated
pairs, histograms + correlation heatmap → `profile/analysis.json`, `profile/*.png`.

**5 · Discover** (the generic beat-pack anomaly rule: *learn the baseline, flag
deviations*) — per provider (≥50 pneumonia discharges): share billed at the highest
severity tier. National median **74.4%**; top outliers bill **90–92%**
→ `leads_upcoding_signal.json` (25 ranked leads with method + caveats).

**The human-judgment moment (this is the tool working as designed):** the naive first
pass returned a wall of providers at exactly **100%** — which turned out to be a **CMS
small-cell suppression artifact** (provider×DRG cells under 11 discharges are withheld,
hiding the lower-severity rows). 120 providers were flagged as artifacts and excluded,
and the artifact-aware method is recorded in the output. Same discipline that caught the
Loc Nation amendment double-count and the 19 phantom cross-chamber gaps.

**6 · Organize** (`case-file`) — thread `T-0001` opened (status: chasing, next action
recorded), session journal logged, lint clean → `casefile/`, and a generated
`review_dashboard.html`.

## What this demonstrates

| Stage | Lobbying corpus | This beat |
|---|---|---|
| Scope | lobbying beat-pack | synthesized healthcare pack |
| Acquire | provided corpus + connectors | live API discovery + sha256 snapshots |
| Profile | mapper ingest/schema | robodoig on any table |
| Discover | gatekeeper/anomaly commands | peer-baseline deviation rule |
| Organize | real case file (4 threads) | this case file (1 thread, chasing) |

These are **leads, not findings** — severity mix can reflect real patient acuity
(transfer centers, teaching hospitals). The recorded next actions (case-mix adjustment,
multi-year trend per the OIG method, the sepsis DRG pair) are where a reporter would take
it. That's the point: the tool got a brand-new beat from a blank question to a ranked,
source-stamped, artifact-checked lead list in one session.
