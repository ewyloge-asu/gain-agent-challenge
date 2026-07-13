# Generality demo — the same assembly line on a NON-lobbying beat

The challenge asks for skills that "would generalize past this particular investigation."
Two features make that real in this bundle: **S0 scope-framing** (the topic/scope dialogue
that selects or synthesizes a beat-pack, so nothing is hardwired to lobbying) and
**web-search-for-data** (active acquisition of outside datasets/APIs, not just the
provided reference corpus). This folder is a live run of both on a completely different
beat: **Medicare hospital up-coding** (the cross-domain test dataset a teammate proposed).

## What was run (all reproducible)

**1 · S0 scope-framing** (`investigative-method/tools/scope.py`) — the healthcare question
produced a case brief + a *synthesized* beat-pack (note: `domain: healthcare`, not the
lobbying pack; the explicit domain wins over keyword hints):

```bash
python3 tools/scope.py --dir casefile \
  --question "Which hospitals show billing patterns consistent with Medicare up-coding, and did their reimbursements outpace peers?" \
  --entities "hospitals, CMS, Medicare Administrative Contractors" \
  --from 2020-01-01 --to 2025-12-31 --jurisdiction "US federal" --domain healthcare \
  --finding-bar "a named-provider billing pattern deviating from peer baseline, sourced to CMS records"
```
→ `casefile/brief.md` + `casefile/beatpack.json` (generic pack: profile with robodoig,
acquire with find_data).

**2 · Web-search-for-data** (`investigative-method/tools/find_data.py`) — three legs:

- **Curated catalog** (offline backbone): correctly ranked **CMS / data.cms.gov** first
  for this topic.
- **Live CKAN catalog query** (any portal via `--catalog`; here data.ca.gov, since
  data.gov retired its public CKAN API): surfaced the California **Provider Suspended and
  Ineligible List** and hospital inpatient datasets.
- **Suggested web searches** for the agent's own search capability. Running the tool's
  `site:.gov` query surfaced **HHS-OIG report OEI-02-18-00380** ("Trend Toward More
  Expensive Inpatient Hospital Stays…"), the primary source that defines exactly the
  up-coding-vulnerable billing patterns the scoped question asks about.

```bash
python3 tools/find_data.py "medicare hospital billing up-coding fraud" \
  --catalog https://data.ca.gov --out found_sources.json
```
→ `found_sources.json` (the reproducible acquisition snapshot).

**3 · Snapshot the best hit** (`investigative-method/tools/fetch_source.py`) — the OIG
report is snapshotted with URL, timestamp, and sha256 so the acquisition step re-runs
offline:

```bash
python3 tools/fetch_source.py "https://oig.hhs.gov/reports/all/2021/trend-toward-more-expensive-inpatient-hospital-stays-in-medicare-emerged-before-covid-19-and-warrants-further-scrutiny/" \
  --name oig_upcoding_report --out-dir snapshots
```
→ `snapshots/oig_upcoding_report.html` + `.meta.json` (provenance).

## Why this matters for the rubric

From here the generic pipeline takes over — profile the CMS files with `robodoig`, flag
deviations from the peer baseline (the beat-pack's anomaly rule), track threads in the
case file, run `checking-the-law` with a synthesized law pack (False Claims Act), footnote
the draft. **No lobbying-specific code is involved at any step.** The lobbying corpus is
one beat-pack; this folder is the proof, not the promise.
