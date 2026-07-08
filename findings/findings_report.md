# Findings Report — Lobbying Influence Mapper

**Corpus:** GAIN federal lobbying + press corpus, 2022–2026 Q1 (Senate/House LDA
filings, LD-203 contributions, congressional press releases).
**Tooling:** the `lobbying-influence-mapper` skill in this submission. Every
number below is regenerable with `scripts/run_all.sh` and traceable to a source
record via `scripts/review.py` (see [traces](../traces/)).

**Sourcing convention:** claims labeled *[corpus]* come directly from disclosure
records in the dataset (with provenance ids). Claims labeled *[context]* are
publicly reported real-world background included to explain why a corpus pattern
is newsworthy; a reporter should confirm these independently before publishing.

---

## Finding 1 (headline): Lobbyist money pools around the gavel

**Claim.** In 2025, lobbyist- and registrant-reported LD-203 contributions
concentrated heavily on **congressional leadership and the chairs of the
money committees** — the exact members who control whether a bill moves.

**Evidence [corpus].** Top 2025 recipients of contributions filed by *lobbyists*
(resolved from `honoree_name` to a `bioguide`), by total dollars:

| Member | Party/State | Lobbyist $ (2025) | Distinct registrants giving |
|---|---|---:|---:|
| Brett Guthrie | R-KY | $637,025 | 157 |
| Jason Smith | R-MO | $573,100 | 104 |
| Mark R. Warner | D-VA | $542,059 | 157 |
| Steve Scalise | R-LA | $437,865 | 59 |
| Mike Johnson | R-LA | $432,959 | 40 |
| Thom Tillis | R-NC | $420,003 | 122 |
| Tom Cole | R-OK | $389,171 | 88 |
| John Thune | R-SD | $385,201 | 87 |
| J. French Hill | R-AR | $363,630 | 96 |
| Bill Cassidy | R-LA | $337,721 | 115 |

**External verification [corpus + outside data].** Joining this leaderboard to
committee assignments from the public `unitedstates/congress-legislators` dataset
(via the skill's connector), **10 of the top 20 recipients are committee chairs
or ranking members**, and they chair the highest-stakes panels:

- Brett Guthrie — **Chair, House Energy & Commerce**
- Jason Smith — **Chair, House Ways & Means**
- Tom Cole & Ken Calvert — **House Appropriations** (Cole chairs full cmte)
- J. French Hill — **Chair, House Financial Services**
- Bill Cassidy — **Chair, Senate HELP**
- Thom Tillis / Mark Warner — **Chair / Ranking, Senate Banking**
- Dan Sullivan — **Chair, Senate Armed Services** subcommittee, Commerce

Most of the remaining top recipients (Mike Johnson = Speaker, Scalise = Majority
Leader, Thune = Senate Majority Leader, Jeffries = Minority Leader, Katherine
Clark = Minority Whip) are floor leadership the committee file does not tag.

**Case study — Brett Guthrie (E&C Chair) [corpus].** As Guthrie took the Energy &
Commerce gavel, contributions to him climbed steadily:

- 2022: $1,004,204 (492 items) → 2023: $935,138 → 2024: $2,080,232 →
  **2025: $2,636,376 (1,046 items)**

His top 2025 sources sit squarely in E&C's jurisdiction (health, energy,
telecom): American Clinical Laboratory Assn ($64k), SpaceX ($57.5k), CVS Health
($55k), Eli Lilly ($52.5k), BrightSpring Health Services ($50k), Exxon Mobil
($45.5k). One verified example: a **$25,000** contribution honoring "Rep. Brett
Guthrie" from **BrightSpring Health Services** (a Louisville, KY firm — Guthrie's
home state), `data/senate/2025/contributions/contributions_2025.json#9e7cef9a-bfff-4f83-944b-9411c727c521`.

**The "act" leg [corpus + outside data].** With a free Congress.gov key
(`connector.py enrich-act`, snapshot shipped at `assets/legislation.json`), the
sponsored-legislation of the money-committee chairs tracks their committee
jurisdiction — i.e., the policy areas where their donors do business. Policy
areas of each chair's most recent 25 sponsored bills:

- **Brett Guthrie** (E&C Chair): Health ×9, Energy ×3, Environmental Protection
  ×2, Science/Tech/Communications ×2, Commerce ×2 — the entire E&C jurisdiction.
  Examples: the *SAT Streamlining Act* (telecom/spectrum) and *MVP Act* (health).
- **Jason Smith** (Ways & Means Chair): Taxation ×11, Foreign Trade ×5 — squarely
  Ways & Means.
- **J. French Hill** (Financial Services Chair): Finance & Financial Sector ×6,
  International Affairs ×6 — Financial Services and its international-finance remit.

**The vote dimension [corpus + outside data].** Joining the same members to
Voteview roll-call data (`connector.py enrich-votes`, no key, snapshot
`assets/votes.json`) sharpens — and disciplines — the "act" claim. These
gatekeepers are **near-perfect party-line votes**: Guthrie votes with his party
**97.8%** of the time (12 defections of 547 votes, 99.3% participation); Jason
Smith 97.8%, Scalise 98.5%, Speaker Johnson 99.8%. Crucially, when we tabulate the
*policy areas* of Guthrie's 80 most recent bill-linked floor votes
(`connector.py vote-align G000558`), they spread across **all** subjects
(procedural "Congress" votes, Agriculture, Environment, Defense…) rather than
clustering in E&C. The honest read: **floor votes are essentially party-determined
and span everything that reaches the floor, so vote-level "donor alignment" is
confounded by party and we do not claim it.** The discretionary signal that *does*
track donors is **bill sponsorship** (what a member chooses to push), above.
Voteview's value here is (a) participation/loyalty context and (b) a reusable
lookup so a reporter can check any specific money→vote hypothesis.

**The denominator [corpus + outside data].** Ground-truthed against each member's
FEC current-campaign receipts (`connector.py enrich-finance`, snapshot at
`assets/fec_totals.json`; candidate ids from the authoritative
`unitedstates/congress-legislators` bioguide→FEC crosswalk), registered
**lobbyists alone** account for a striking share of the money-committee chairs'
*entire* campaign haul:

| Member | LD-203 lobbyist $ (2025) | FEC receipts (current cycle) | Lobbyist share |
|---|---:|---:|---:|
| Brett Guthrie (E&C) | $637,025 | $4.19M | **15.2%** |
| Mike Carey (W&M) | $431,398 | $2.57M | **16.8%** |
| Jason Smith (W&M) | $573,100 | $4.46M | **12.9%** |
| Tom Cole (Approps) | $389,171 | $3.21M | **12.1%** |
| Mike Johnson (Speaker) | $432,959 | $17.5M | 2.5% |
| Steve Scalise (Maj. Leader) | $437,865 | $9.32M | 4.7% |

The pattern sharpens the story: floor leaders (Johnson, Scalise) raise vastly more
overall, so lobbyist money is a small slice; but for the chairs who actually move
legislation, **registered lobbyists are ~13–17% of all money raised.** (Caveat:
Senate receipts span up to a 6-year cycle vs. House 2-year, so cross-chamber
shares are directional; see `methodology.md`.)

**Why it's newsworthy.** This is the structural shape of access-buying made
measurable across all three legs — **pay** (LD-203 dollars), **gatekeeping**
(committee chairs verified against public data), and **act** (sponsored bills
that track donor jurisdictions) — plus a real denominator showing how large the
lobbyist slice is for the members who control whether a bill moves.

**Micro-example — Guthrie's money cadence vs. his bills [corpus + outside data].**
`xref.py timeline "Brett Guthrie"` interleaves his **367 dated 2025 lobbyist
contributions ($637,025)** with his sponsored-bill dates. The money is
front-loaded: **$327K (51%) arrives in Q1** (Jan–Mar 2025) as the 119th Congress
organizes and chairs take gavels. Over the same window his sponsored output sits
squarely in E&C jurisdiction — health, energy, telecom, environment, commerce —
and **two of his health bills became public law** (HR2483 SUPPORT Act → PL 119-44;
HR7218 BOLD Infrastructure → PL 118-142). This is the "pay → act" cadence for one
member, shown concretely; it is **temporal juxtaposition, not causation** (no
contribution is tied to any bill; the SUPPORT Act is bipartisan opioid policy).

**Reproduce:** `xref.py gatekeeper --filer lobbyist --year 2025`;
`xref.py --json timeline "Brett Guthrie" --year 2025`;
`connector.py annotate-gatekeeper --year 2025 --filer lobbyist`;
`connector.py enrich-act --year 2025 --filer lobbyist --top 12`;
`connector.py enrich-finance --year 2025 --filer lobbyist --top 12`;
`connector.py enrich-votes --year 2025 --filer lobbyist --top 12`;
`connector.py vote-align G000558`; `xref.py member "Brett Guthrie"`.

---

## Finding 2 (headline): Foreign companies under U.S. scrutiny hired insiders — disclosed in plain sight

### 2a. Tencent and the former White House officer

**Evidence [corpus].** Tencent America's reported lobbying spend was flat at
~$800k/year (2022–2024) then **jumped ~5x to $4.04M in 2025** (24 filings, 6
registrants). Among the registrants is **John McEntee**, whose LDA
`covered_position` is disclosed as **"Officer in the Executive Office of the
President."** His registration lobbies on a single, pointed issue —
*"Erroneous trade restriction designation"* (issue code TRD) —
`filing_uuid b8b09920-a089-4e40-badb-eaaa93cf6a8d`. Other Tencent registrants
include Brownstein Hyatt ($3.4M), Hogan Lovells, MO Strategies, and Mercury
Public Affairs.

**Context [context].** Tencent was added to the U.S. Department of Defense's list
of "Chinese military companies" in January 2025; John McEntee is widely reported
as the former director of the Presidential Personnel Office in the Trump White
House. A company fighting a national-security designation retaining a former
senior White House official is a textbook revolving-door + foreign-influence
story — and the disclosure data names the former government role itself.

### 2b. Nippon Steel's bipartisan all-star bench

**Evidence [corpus].** Nippon Steel's reported spend ramped from $30k (2023) →
**$4.33M (2024)** → $3.69M (2025), lobbying on trade (TRD) and targeting the
**White House Office, Commerce, USTR, Treasury, State, and the NSC**. Its lead
registrant, **Akin Gump**, fielded a roster studded with former government
heavyweights (from `covered_position` [corpus]):

- **Ileana Ros-Lehtinen** and **Filemon Vela** — former Members of Congress
- **Brian Pomper** — former Chief International Trade Counsel, Senate Finance
- **Stephen Kho** — former Acting Chief Counsel for China Enforcement, USTR
- **Clete Willems** — former Deputy Assistant to the President (trade)
- plus former chiefs of staff/counsel to Sens. McConnell and Schumer

Trump-aligned **Ballard Partners** also registered for Nippon Steel.

**Context [context].** Nippon Steel's ~$14B bid for U.S. Steel was blocked on
CFIUS grounds in January 2025 and later revived under a renegotiated arrangement —
explaining the spend ramp and the White House/CFIUS-agency targeting. The deal
surfaces in the press corpus too: **81 releases mention "U.S. Steel," 43 mention
"Nippon"** [corpus], giving a "say" dimension to pair with the "pay."

**FARA cross-check [corpus + outside data].** Run against FARA's active
foreign-agent registry (no API key; snapshot shipped at
`assets/fara_active.json`), the firms representing these foreign clients —
**Akin Gump (FARA reg. 3492, since 1983), Ballard Partners, Brownstein Hyatt,
Hogan Lovells, and Mercury — all hold FARA registrations.** But the individual
registrant **John McEntee does *not* appear in FARA**, so his Tencent work
proceeds under the Lobbying Disclosure Act rather than as a registered foreign
agent — the LDA-vs-FARA election that is a recognized compliance gray area.
(Caveat: active-registrant presence confirms a firm holds *some* FARA
registration; confirming Tencent/Nippon as the specific foreign *principal*
requires FARA's foreign-principals dataset — a documented refinement.)

**Why it's newsworthy.** Two foreign corporations facing adverse U.S. government
action assembled rosters of former U.S. officials — disclosed, but not assembled
or contextualized anywhere until now — and at least one (McEntee) is doing
foreign-client work outside the FARA regime.

**Reproduce:** `xref.py client "TENCENT"`; `xref.py client "NIPPON STEEL"`;
`xref.py lobbyist "John McEntee"`; `connector.py fara`.

---

## Finding 3 (flag): The disclosure system has no gatekeeper of its own

**Claim + LEGAL/ETHICS FLAG.** The naive "biggest lobbying client of 2025" is
fictional. A single filer — **"State of Loc Nation Global Public Benefit
Corporation" / "LOC Community Association" (Delaware)** — submitted **nine 2025
LD-2 filings each reporting $20,000,000 of income ($180M total)**, ~35x the next
real client. The filings are not lobbying engagements: their text describes
pseudo-legal reparations claims tied to **HR 40**, a federal lawsuit
(1:24-cv-00479-RC), UCC filings, and a proposed "central bank for Black USA."

**Evidence [corpus].** Filings include
`filing_uuid 4d5b1cb0-0971-43b8-958b-d260e2be8af1` and eight more at $20M each;
all other ~108k 2025 filings report under $20M. Verify with
`review.py "<uuid>"`.

**Why it matters.** (1) It is a concrete demonstration that the LDA system
performs no validation — anyone can file anything, and it pollutes the official
record and any naive aggregate. (2) Per the challenge's ethics guidance, this is
flagged to the panel as a **possible misuse of a federal disclosure system**
that may warrant referral. Any spend analysis on this corpus must exclude it
(run `anomaly` first).

**Reproduce:** `xref.py anomaly --year 2025 --factor 5`.

---

## Supporting finding: coordinated messaging is detectable and separable

The coordination detector finds verbatim talking points reused across many
members and scores them so *targeted* campaigns separate from ordinary partisan
boilerplate. In Q1 2025 it surfaced tightly time-clustered (0–2 day) multi-member
letter campaigns — e.g., the USAID/impoundment "failure to expend appropriated
funds" letters and an Elon Musk–China-ties oversight letter — alongside bipartisan
boilerplate. Chasing the phrase "strategy group" returns **26 releases across 20
members** (Peter Welch ×6) driving the DHS/Secretary Noem contracting
investigation. This is a reusable method finding more than a standalone scoop.

**Reproduce:** `detect_coordination.py clusters --year 2025 --min-members 6`;
`detect_coordination.py keyword "strategy group"`.

## Cold thread (documented, not a story)

Across **37,703** Senate↔House engagements bridged by `senateID` where House
income is present, **zero** differ from the Senate-reported figure by more than
$100k. The two chambers' income disclosures are consistent; there is no
discrepancy story here. (`xref.py mismatch --year 2025 --min-gap 100000`.)

---

## Conflicts of interest
None known. No team member has a relationship with any entity named here.

## Possible legal violations flagged to the panel
- **Finding 3 (Loc Nation):** apparent misuse of the federal LDA filing system to
  lodge pseudo-legal/financial claims; not lobbying. Recommend referral for review.
- The revolving-door relationships in Finding 2 are **disclosed and presumptively
  lawful**; they are flagged as newsworthy, not as violations. Cooling-off-period
  compliance would require departure dates not in this corpus.
