# Workflow — Reproducible Analysis Procedure

*The spine of this case file. Adapted from the team's Methodology & Replication Guide.
Every thread and finding cites a step below plus the underlying records, so the work
re-runs and an editor can audit it.*

## Principle

Push extraction, filtering, and aggregation to deterministic Python (standard library
only — `json`, `pathlib`, `collections`, `re`, `xml.etree.ElementTree`). No external data
packages. The agent reasons over the *outputs*; it does not scan the raw corpus. Every run
is reproducible (fixed keyword lists, `seed=42` for sampling).

## Environment

| Tool | Notes |
|---|---|
| Python 3.10+ | standard library only |
| python-docx | report generation only (`pip install python-docx --break-system-packages`) |
| Bash / Linux sandbox | run scripts, explore structure |

## Data

| Dataset | Format | Path | Scale |
|---|---|---|---|
| Senate LDA filings | JSON | `data/senate/{year}/filings/filings_{year}.json` | ~108K filings/yr |
| Senate LD-203 contributions | JSON | `data/senate/{year}/contributions/contributions_{year}.json` | semi-annual |
| House LDA filings | XML (one file/filing) | `data/house/{year}_{Q}_XML/*.xml` | 409,650 files |
| Congress press releases | JSONL | `data/congress_press/{year}/*.jsonl` (2026 at root) | ~200K+ releases |

Key fields: `general_issue_code` (ALI code; **EDU = Education**, no sub-codes),
free-text `description`, `registrant.name`, `client.name`, `income`/`expenses`,
`lobbyists[].covered_position` (revolving-door flag), and for press releases
`member.bioguide_id` (the join key to Congress.gov).

## Procedure

### Step 0 — orient
Read `data_manual.md` and `data/senate/constants/lobbying_activity_issues.json` to confirm
the ALI code system and folder layout before writing any analysis code.

### Step 1 — Senate EDU aggregation · `analyze_senate_edu.py`
Include a filing if **any** activity has `general_issue_code == "EDU"`. Aggregate total
income/expenses, top clients, top registrants, top government entities targeted, and sample
descriptions, by year. *Caveat: income/expenses is total quarterly spend for the filer, not
education-only.*

### Step 2 — Senate topic deep dive · `analyze_senate_edu_deep.py`
(1) Restrict to education-focused orgs (name contains university/college/school/education/…)
to separate genuine education spenders from multi-issue filers. (2) Tag each EDU
description against **10 policy-topic keyword buckets** (school choice, student loans,
Title I/K-12, higher ed/Pell, workforce, research/STEM, HBCUs, AI/ed-tech, DOGE/Dept of
Ed, international). Counts are mentions, not unique filers.

### Step 3 — House sampled XML · `analyze_house_edu_sample.py`
409,650 XML files. Take a **stratified random sample of up to 2,000 files per quarterly
directory, `seed=42`**, then extrapolate by `ratio = total_files / files_sampled`.
Dual filter: `.//alis/ali_Code == "EDU"` OR any of 25 education keywords in
`.//specific_issues/description`. *Extrapolated counts carry ~5–10% sampling error.*

### Step 4 — press releases · `analyze_press_edu.py`
Combine `title` + `text`; flag if any of 22 education keywords appear. Tag topics with 8
regex patterns (`re.search`, e.g. `AI.*education`). Break down by year, member
(name/party/chamber), and party. Member metadata incl. `bioguide_id` is in each record.

### Step 5 — revolving door
Scan `lobbyists[].covered_position` on EDU activities for non-empty prior government roles;
emit `lobbyist_name | covered_position | client`. *Covered positions are self-disclosed —
verify each against congressional directories / agency records / contemporaneous coverage.*

### Step 6 — contribution cross-reference (LD-203)
Each contribution record has `contribution_items[]` with `payee`, `honoree`,
`contributor_name`, `amount`. Match the education/school-choice registrant + lobbyist names
against contributions whose `honoree` matches target sponsors/committee members.
*LD-203 covers contributions by lobbyists and firm PACs only — NOT clients, client PACs, or
executives. FEC cross-reference is required for the full picture.*

### Step 7 — "say vs. pay" correlation (the high-value extension)
The manual's flagship cross-dataset test: when lobbying activity/spend on an issue spikes
in a quarter, does congressional press-release language on that issue shift in the same or
following quarter? Count EDU lobbying contacts targeting each chamber by quarter; count
education press releases by topic by month; test whether release mentions **lag** lobbying
contact by 1–2 months. *Correlational only — timing suggests, it does not prove.*

## Standing caveats (apply to every finding)

- Spend cannot be disaggregated by issue.
- Data is self-reported; many filings lack income/expenses/state.
- House figures are sampled and extrapolated (~5–10% error).
- Keyword matching is broad; some non-education noise survives.
- Registrant + client filing separately can double-count spend.
- 2026 is Q1 only.
- **Correlation is not causation** — contribution + lobbying contact of the same member is
  documented; influence is a reporting question, not a data conclusion.

## How the workflow maps into this case file

Each step produces candidate leads → **threads** (`threads/`). Confirmed, source-bound
claims graduate to **`findings.yaml`**. Every thread/finding records: the **step + script**
that produced it, the **source records**, and a **next action**. Entities named across
steps are registered once in **`entities.yaml`**.

## Scripts referenced

`analyze_senate_edu.py`, `analyze_senate_edu_deep.py`, `analyze_house_edu_sample.py`,
`analyze_press_edu.py`, `school_choice_deep.py`, `ecca_contributions.py`,
`build_report.py`, `build_methodology.py` — all in the AI Lobbying Challenge folder.

*Source: Methodology_Replication_Guide + Education_Lobbying_Analysis (coworker, June 2026).*
