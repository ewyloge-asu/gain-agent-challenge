# Methodology, limits, and caveats

## Data is self-reported
LDA filings and LD-203 contributions are filed by registrants/lobbyists. They
contain errors, omissions, and (rarely) abuse. Findings describe *what was
disclosed*, which is not always what occurred.

## Known data-quality facts (measured on this corpus)
- ~34–36% of Senate filings have `null` income every year. Spend totals are
  therefore lower bounds and "top spender" rankings are sensitive to who reports.
- `income` is reported per filing/period; a client's annual spend is the sum of
  its quarterly filings (avoid double counting amendments — `filing_type` ending
  in `A`).
- Abusive filings exist: a single filer ("State of Loc Nation…") submitted nine
  2025 filings each claiming $20M, inflating the naive 2025 top-spender ranking by
  $180M. Always run `anomaly` and inspect outliers before quoting aggregates.

## Entity resolution
- Honoree→member resolution is exact LAST|FIRST key, then unique-last-name
  fallback. ~62% of contribution items resolve to a member; the rest are PACs,
  party committees (NRSC/DSCC), or non-members. Ambiguous keys (multiple members
  share LAST|FIRST) are left unmatched rather than guessed.
- `match_method` is recorded on every resolved row; prefer `senateID_bridge` and
  `exact` over `name_match`/`lastname_unique` when a claim must be airtight.
- The `members` table is derived from the press corpus (~480–490 members), so a
  member with no scraped press releases will not resolve. Use the connector's
  legislators snapshot to widen coverage if needed.

## Coordinated-messaging detector
Detects *verbatim* sentence reuse (≥80 chars). It will not catch paraphrase. The
`specificity` score is a heuristic, not a classifier. Bipartisan + tight-window +
specific clusters are strong candidates; confirm by reading the releases.

## Press "say" leg (`xref.py say` / `say-vs-do`)
The press releases are tagged into a coarse shared policy taxonomy
(`common.POLICY_DOMAINS`) so "what a member talks about" can be lined up against
"what a member sponsors" (Congress.gov `policy_area`) and lobbying issue codes.
Caveats:
- **Press coverage is Senate-heavy.** The scraped corpus has ~1,000+ releases for
  the most active senators but only a handful for many House members (e.g. Guthrie
  16, Jason Smith 10). Per-member `say` is robust for senators and prolific House
  members; for low-volume members it is anecdotal. (Coverage also grows year over
  year — 19.7K releases in 2022 → 48.3K in 2025 — partly a scraper artifact, so
  baseline on a stable member set for any time series.)
- **Topic tags are keyword heuristics**, matched on the **title + lede (first ~500
  chars)** rather than the full body. This is deliberate: the body's long tail and
  the office/committee footer add noise (a chair of "Energy & Commerce" would match
  "energy" on every release). Tags are multi-label and coarse; they are a triage
  signal, not a classifier.
- **`say-vs-do` denominators differ in size.** "Say" is computed over potentially
  hundreds of releases; "act" comes from the most recent ~25 sponsored bills, of
  which only the ones with an assigned `policy_area` count (often <10). So a domain
  share gap is **directional** — read it as "talks about X far more than the recent
  bill mix would suggest," then confirm against the member's full record. It is not
  a hypocrisy claim; it is a lead.

## FARA cross-check
`connector.py fara` matches on registrant *name presence* in FARA's active list,
which confirms a firm holds *some* FARA registration but not the specific foreign
principal. A firm registered in FARA for principal X may still represent another
client under the LDA. Treat an *absence* from FARA by a foreign-client lobbyist
(e.g. John McEntee) as the stronger signal; confirm principal-level claims with
FARA's foreign-principals records before publishing.

## FEC denominator (enrich-finance)
`connector.py enrich-finance` resolves members to FEC candidate ids via the
authoritative `unitedstates/congress-legislators` bioguide→FEC crosswalk (not name
matching), then reports their current-campaign receipts as the denominator for the
LD-203 lobbyist total. Two caveats:
- **Cycle window differs by chamber.** House totals cover a 2-year cycle; Senate
  totals (election-full) can span up to 6 years. So a senator's "lobbyist share of
  receipts" is computed over a longer window and is **not strictly comparable** to
  a House member's. Treat cross-chamber shares as directional.
- **Receipts ≠ LD-203 universe.** FEC receipts include all itemized/unitemized
  individual and PAC money; the LD-203 figure is only what registrants/lobbyists
  themselves reported. The share answers "how big is the disclosed-lobbyist slice
  of all money raised," not "what fraction came from lobbying interests."

## Sponsored-legislation alignment (enrich-act)
Policy-area tallies come from the most recent N (default 25) sponsored bills, not
the member's full record, and Congress.gov's `policyArea` is a single assigned
category per bill. Alignment between a chair's bills and their committee
jurisdiction is descriptive evidence of "act," not proof a specific donor's bill
was advanced. For vote-level alignment, add a roll-call source (GovTrack/Voteview).

## Roll-call votes (Voteview) — votes track party, not donors
`connector.py enrich-votes`/`vote-align` add Voteview roll-call data, but interpret
carefully:
- The well-funded gatekeepers vote with their party **97–99%** of the time, so
  floor votes are almost perfectly predicted by party. Any "voted with donor
  interests" measure is therefore **confounded by party-line voting** and is not
  claimed as evidence of influence.
- Floor votes also span *every* policy area (members vote on whatever reaches the
  floor, plus procedural "Congress" votes), so a member's *votes* do not cluster
  in their committee/donor jurisdiction the way their *sponsored bills* do.
- Cast codes follow Voteview's scheme (1–3 Yea, 4–6 Nay, 7–8 Present); party-unity
  is computed only on votes where the member's party had a clear majority.
- `vote-align` is **sampled and capped** (default 80 most recent bill-linked
  votes) and depends on Congress.gov `policyArea` (one assigned category per bill).
The defensible discretionary "act" signal remains **bill sponsorship**, not votes.

## Causation
"Pay → say → act" correlations (e.g., contributions rising as a member takes a
gavel) are suggestive, not causal. State the timeline and let readers judge.
