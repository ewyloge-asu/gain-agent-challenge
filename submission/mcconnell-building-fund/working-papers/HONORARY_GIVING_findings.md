# The "in honor of" money channel — findings memo

**Investigation:** Beyond capped campaign donations, companies give money "in honor of" politicians —
to charities, foundations, buildings, archives, and honoring events tied to them. Who gives, how much,
where does it go, and does anything cluster or stand out?
**Data:** Senate LD-203 semiannual contribution reports, 2022 – 2026 Q1 (`data/senate/*/contributions/`).
**Status:** Pattern confirmed from records; top items cross-checked against outside sources; legality
checked against the actual statute. Ready for reporting-out (comment + lawyer review) before any use.
**A framing note up front:** this money is *disclosed and legal*. It goes to charities and entities,
not to members personally. Nothing here asserts anyone broke a law. The story is the *channel* and
*where it concentrates* — a lightly-watched lane that sits beside the capped campaign-money lane.

---

## What this channel is

Every lobbying registrant must file a semiannual "LD-203" report. Alongside its capped political (FECA)
contributions, it must itemize a second kind of money: **"Honorary Expenses"** — payments made to honor
or recognize a specific member of Congress or executive-branch official. In the data this is the
`contribution_type = "he"` line item, with three fields that tell the story: **who paid** (the filer),
**the payee** (where the money went — a charity, foundation, building fund, or event vendor), and the
**honoree** (the politician it was "in honor of").

This is the channel Congress deliberately made visible in 2007 (see the legal section). It is the money
that is *not* a campaign contribution — and, unlike campaign contributions, **it is not capped.**

## The shape of it — who, how much, where

Across 2022 through 2026 Q1 there are **4,291 honorary items totaling ~$134.4 million reported**, running
a steady ~$30–38M a year. A few structural facts:

- **The giver is the company, not an individual.** On 93% of items the "contributor" field just says
  "SELF" — the real giver is the filing registrant. The biggest corporate givers by this measure are
  Amazon ($7.16M), State Farm ($5.94M), Meta ($5.40M), AARP ($3.86M), Comcast ($3.44M), Toyota ($3.43M),
  Morgan Stanley ($3.40M), Chevron ($3.09M), and Google ($2.91M).
- **Where it goes is highly concentrated.** The single largest destination bucket is the
  **caucus-affiliated nonprofits**:

  | Recipient cluster | Reported (he) | Distinct corporate funders |
  |---|---|---|
  | Congressional Black Caucus Foundation | ~$25.5M | 101 |
  | Congressional Hispanic Caucus Institute + Leadership Institute | ~$22.7M | 80 |
  | Asian Pacific American Institute for Congressional Studies (APAICS) | ~$5.0M | 39 |

  These are the galas and scholarship foundations tied to the caucuses; corporate lobbying interests
  fund them "in honor of" caucus members. This is the backbone of the whole channel by dollar volume.

*(A related, non-campaign layer exists but is a separate, smaller-N story: Presidential Inaugural
Committee contributions ~$67.6M across 120 items, and Presidential Library contributions ~$22.4M across
120. Those are worth their own look but aren't "in honor of a member of Congress.")*

## The two standouts worth a closer look

### 1. Corporate lobbyists funding the "Mitch McConnell Building"

Setting aside the University of Louisville (which self-reports ~$2.5M of its own spending on the named
"McConnell Center" and "McConnell-Chao Archives" — that's the university, not influence money), the
sharp finding is corporate money flowing to the **Republican Party of Kentucky "Building Fund," whose
headquarters is literally named the "Mitch McConnell Building."** Eight honorary items, ~$1.525M, four
funders:

- **Pfizer — $1,000,000** (Dec 27, 2022)
- **AT&T — $100,000 × 3** (2022–2024)
- **Microsoft — $100,000** (2023) plus **$25,000** (2025)
- **Delta — $50,000 × 2** (2022)

**Verified outside the filings.** Kentucky Lantern, WKMS, and the Hoptown Chronicle all reported Pfizer's
$1M gift to the party building fund in January 2023, confirmed the HQ is named for McConnell, and named
additional corporate donors (Comcast, MetLife, Altria) to the same fund. So the filings match reality
here — and interestingly, some of those press-named donors (Comcast, MetLife, Altria) do **not** appear
in the federal LD-203 "he" data, which is itself a disclosure-completeness question worth chasing.
Broader "in honor of McConnell" corporate giving (think-tank galas at AEI and Hudson, the JFK Center)
adds up to ~$1.81M across 28 items / 18 funders.

### 2. The single largest honorary item — State Farm's $2.65M "in honor of" Rep. Virginia Foxx

The biggest honorary item in the entire four-year corpus: **State Farm reporting $2,650,000 to Habitat
for Humanity International, honoree "Rep. Virginia Foxx,"** dated Nov 20, 2025.

**This is exactly why we don't trust the form at face value.** Given the prior investigation's fabricated
$80M filing, a $2.65M line demands a check. It checks out: State Farm publicly announced in June 2025 it
was renewing its 30-year Habitat partnership and raising contributions to ~$2.6M for youth and
resilient-housing programs. The money and the relationship are real. **The reportable nuance is the
attribution** — routine, company-wide corporate philanthropy shows up on a federal *lobbying* disclosure
"in honor of" one specific sitting House member. Either Foxx was formally honored in connection with the
gift, or the honoree tag is loose. That's a question for State Farm and Foxx's office, not a violation.

## Is any line crossed? (the law, actually read)

**No clear legal line — and that's the point.** The governing provision is **2 U.S.C. § 1604(d)(1)(E)**
(read at law.cornell.edu, as-of 2026-07-15), added by the Honest Leadership and Open Government Act of
2007 (HLOGA, Pub. L. 110-81 § 203). It *requires* filers to disclose payments made:

- (i) to pay the cost of an **event honoring** a covered official;
- (ii) to an **entity named for**, or given **in recognition of**, a covered official;
- (iii) to an **entity the official establishes, finances, maintains, or controls**;
- (iv) to pay for a meeting/retreat/**event held in the official's name**.

Two things follow directly from the text. First, this is a **disclosure requirement, not a prohibition**
— Congress built this channel to be visible, and the filings above are doing exactly what the law asks.
Second, and central to your question: **there is no dollar cap.** Capped FECA campaign contributions are
disclosed elsewhere (and the statute's only threshold, $200, applies to those political contributions);
subparagraph (E) sets *no ceiling at all* and even carves out anything FEC-reportable, so these items are
by design the *uncapped, non-campaign* money. A company can give a member-named building fund $1M and
simply report it.

A bribery/gratuity or gift-rule question (chamber gift rules; 18 U.S.C. §§ 201, 1346) would only arise if
facts showed the money **personally benefited** a member or was tied to a **specific official act** — and
that cannot be shown from these filings. It is lawyers'-and-prosecutors' territory, not something to
assert. **Verdict: legal but under-scrutinized. Not a violation.**

## Before any of this is used

Seek comment from every named party — State Farm and Rep. Foxx; Pfizer, AT&T, Microsoft, Delta, the
Republican Party of Kentucky, and Sen. McConnell's office; and the Congressional Black Caucus Foundation
and Congressional Hispanic Caucus Institute. Have a lawyer review before publishing any influence
implication. No party has been contacted.

## Every number traces to a source

- Channel totals and clusters: `data/senate/2022..2026/contributions/contributions_*.json`,
  `contribution_type = "he"` — reproduced by `investigation_honorary/work/extract.py`, `profile.py`,
  `standouts.py`, `records.py`.
- Pfizer $1M item: `contributions_2022.json` filing_uuid `7fcdd899-5c8c-46cd-94c3-9fa9eb8993b5`.
- State Farm / Foxx item: `contributions_2025.json` filing_uuid `91514e3d-2443-4e6e-943c-0b9bd47e4de0`.
- Statute: 2 U.S.C. § 1604(d)(1)(E), https://www.law.cornell.edu/uscode/text/2/1604 (as-of 2026-07-15).
- Outside verification: Kentucky Lantern (Pfizer/RPK, Jan 2023); habitat.org newsroom (State Farm
  partnership renewal, 2025).

*Case file updated: threads T-0004 (channel map), T-0005 (McConnell building), T-0006 (State Farm/Foxx)
confirmed; findings F-005–F-007; in `investigation_lead1/casefile/`.*
