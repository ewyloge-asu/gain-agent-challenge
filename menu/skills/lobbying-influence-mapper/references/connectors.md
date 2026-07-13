# External connectors

`connector.py` keeps the skill from being locked to the provided corpus. It is a
small registry of external sources plus a cached fetcher with offline fallback.

## Design
- `SOURCES` maps a source name to `{base, key_env, ...}`.
- `fetch(url)` caches every response under `GAIN_WORKDIR/cache/<sha1>`; re-runs are
  offline and deterministic. `--refresh` bypasses the cache.
- Anything needing a secret degrades to a clear, actionable message instead of
  failing, so the core skill always runs.

## Shipped, no-key source: `unitedstates/congress-legislators`
Public GitHub YAML of current legislators + committee membership. `refresh-committees`
(needs PyYAML + network, one-off) compiles it into `assets/committees.json`
(plain JSON, committed). Used by `committee` and `annotate-gatekeeper` to verify
that contribution recipients are committee chairs/leaders. Works fully offline via
the shipped snapshot.

## Shipped, no-key source: FARA active foreign-agent registry
`connector.py fara [names...]` cross-checks lobbying firms/lobbyists against
FARA's active registrants (https://efile.fara.gov/api/v1/Registrants/json/Active).
Snapshot shipped at `assets/fara_active.json`; works offline. A foreign-client
lobbyist absent from FARA is likely using the LDA exemption (reportable gray
area). Caveat: presence confirms a firm holds *some* FARA registration; matching
to a specific foreign *principal* (e.g. Tencent) needs FARA's foreign-principals
dataset, which the public JSON endpoint does not expose cleanly (documented lead).

## Shipped, no-key source: Voteview roll-call votes
The vote dimension of the "act" leg. `connector.py` reads Voteview's public bulk
CSVs (`members`, `rollcalls`, `votes` per chamber/congress) — no key.
- `votes <bioguide>` → one member's roll-call profile: participation, party-unity,
  ideology (DW-NOMINATE dim1), defections.
- `enrich-votes --year 2025 --filer lobbyist --top 12` → the same profile for the
  top contribution recipients; snapshots `assets/votes.json`. Finding: the
  best-funded gatekeepers are ~97–99% party-line voters.
- `vote-align <bioguide> [--max-bills N]` → joins a member's bill-linked floor
  votes to Congress.gov **policy areas** (needs the Congress.gov key; sampled +
  capped) so you can ask whether they vote where their donors operate. Snapshots
  `assets/vote_align_<bioguide>.json`. The bioguide↔Voteview-icpsr crosswalk comes
  from Voteview's own `members` file (it carries `bioguide_id`).

## Wired, key-based sources (optional tiers)
- **Congress.gov v3** (`CONGRESS_GOV_API_KEY`, free): the "act" leg of pay → say
  → act. Free key: https://api.congress.gov/sign-up/.
  - `legislation <bioguide>` → one member's sponsored bills.
  - `enrich-act --year 2025 --filer lobbyist --top 12` → batch-pulls sponsored
    legislation + **policy areas** for the top contribution recipients and
    snapshots to `assets/legislation.json`. Lets you ask whether a chair's bills
    track the jurisdictions their donors operate in (they do — see findings).
  - Roll-call votes are only partially exposed by v3; add GovTrack/Voteview for
    true vote alignment.
- **FEC** (`FEC_API_KEY`; `DEMO_KEY` works rate-limited): ground-truth lobbyist
  contributions against total campaign finance.
  - `fec <name>` → candidate lookup / totals.
  - `enrich-finance --year 2025 --filer lobbyist --top 12` → batch-pulls each top
    recipient's current-campaign receipts and snapshots to `assets/fec_totals.json`,
    so the LD-203 lobbyist total has a real denominator (lobbyist share of all
    money raised). Candidate ids come from the bioguide→FEC crosswalk baked into
    `assets/committees.json` (authoritative — no fragile name matching for common
    names like "Mike Johnson").
  - **Cycle selection:** FEC organizes a candidate's totals by *election* cycle.
    House members file every 2 years (cycle 2026 = 2025–26); a senator's 2025
    money lives under their next election year (e.g. Thune, up in 2028, reports
    under cycle 2028). `enrich-finance` picks the smallest election cycle ≥ the
    LD-203-year's cycle that actually has receipts, which avoids both empty
    forward cycles and missing-senator nulls.

## Reproducibility rule
Keys may unlock richer tiers but must never gate the core (Tier 0) findings.
Snapshot every keyed fetch into `assets/` (committees, FARA, legislation, FEC
totals) so keyed findings still re-run offline. Keys are read from a gitignored
`credentials.env` via `common.load_credentials()`.

## Add a new dataset
Append one entry to `SOURCES` with its `base` URL and `key_env`, then write a thin
command that calls `fetch()` and joins the result to a `bioguide`/entity key. The
cache, offline behavior, and provenance handling are inherited. This is the
"retargetable to any concrete external dataset" property: the connector is the
reusable capability, the specific source is configuration.
