# Findings Brief

A plain-English walk-through of what this investigation found in the data and why it
matters. It is written to be read cold — no prior knowledge of lobbying records assumed.
The companion document, [`tool_pitch.md`](./tool_pitch.md), explains the *software tool*
built to produce these findings. The formal, fully-sourced version is
[`findings/findings_report.md`](../findings/findings_report.md).

---

## First, what is this data?

U.S. law requires anyone paid to influence the federal government to file public
disclosures. This investigation draws on a large archive of those filings plus related
material, covering **January 2022 through March 2026**. Three kinds of records matter here:

- **Lobbying filings (the "LDA" records).** Under the *Lobbying Disclosure Act*, lobbying
  firms file quarterly reports saying who hired them, what issues they worked on, how much
  they were paid, and which individual lobbyists did the work. They appear in two formats —
  Senate filings (JSON) and House filings (XML) — that describe the same world.
- **Contribution reports ("LD-203").** Twice a year, lobbyists must separately disclose the
  political contributions they made — for example, money given to a specific member of
  Congress or their committee. This is the "who gave money to whom" record.
- **Congressional press releases.** What members of Congress publicly say, day to day.

A few terms used repeatedly:

| Term | Plain meaning |
|---|---|
| **Registrant** | The lobbying firm doing the work. |
| **Client** | Who hired and paid the firm. |
| **Lobbyist** | The individual person named as doing the lobbying. |
| **Committee chair** | The member who controls a committee — and therefore largely controls whether a bill in that area even gets a vote. Referred to here as a "gatekeeper." |
| **FARA** | A *separate* disclosure law for people working for **foreign** governments/companies. Stricter than ordinary lobbying disclosure. |

Two things worth stating up front. (1) These filings are **self-reported** — filers write
their own numbers, and almost no one audits them. So everything below describes what was
*disclosed*, not necessarily what physically happened. (2) Every number in this brief traces
back to the exact source record it came from, and the whole analysis regenerates with a
single command. That reproducibility is the point of the tool, described in the companion
document.

---

## The four numbers to anchor on

- **$4.0M+** — total lobbyist contributions (LD-203) to the top 12 recipients in 2025.
- **10 of 20** — of the 20 members who received the most lobbyist money, 10 are committee
  chairs or ranking members (the gatekeepers); the rest are floor leadership.
- **13–17%** — for the chairs of the big money committees, registered lobbyists alone
  account for this share of *all* the campaign money they raise. That is a large amount from
  one narrow source.
- **0 of 37,703** — a lead that was chased and *disproved*: out of 37,703 cases where the
  same lobbying engagement was filed in both the Senate and the House, zero showed a
  meaningful mismatch. It is reported here because a clean dead end is itself a credibility
  signal.

---

## Every lead chased, and where it landed

Five story ideas were each run all the way to a verdict instead of left as a maybe.

| The idea | What it claims | Where it landed | Role |
|---|---|---|---|
| **Pay-the-gavel** | Lobbyist money concentrates on the committee gatekeepers, and what those members do tracks their donors' interests | **Confirmed** | Main headline |
| **Foreign revolving door** | Foreign companies under U.S. scrutiny hired former U.S. officials to lobby for them | **Confirmed** | Second headline |
| **Loc Nation $180M** | One filer used the disclosure system to lodge $180M of fake-looking claims | **Flag** | Referred as possible system abuse |
| **Coordinated messaging** | An automated method can tell an organized multi-office campaign apart from ordinary partisan talking points | **Method** | A reusable capability, not a scoop |
| **Senate↔House gap** | The two chambers report different dollar figures for the same engagement | **Dead** | Disproved cleanly |

The rest of this document explains the two confirmed headlines in detail.

---

## Headline 1 — Lobbyist money pools around the people who control the agenda

**The claim, in one sentence:** the lobbyists' own money flows disproportionately to the
handful of members who decide whether legislation moves, and those members' legislative
behavior lines up with their donors' policy areas.

This was checked in three steps, labeled **pay → gatekeep → act**.

**Step 1 — PAY (who gets the money).** Using the LD-203 contribution reports, the analysis
totaled how much registered lobbyists gave to each member of Congress in 2025. The money is
heavily concentrated: the top 20 recipients pull in far more than the rest.

**Step 2 — GATEKEEP (are they the people who matter?).** The top recipients were then
checked against an official public roster of Congress (a dataset called
`congress-legislators` that maps every member to their committees). The result:
**10 of the top 20 are committee chairs or ranking members** — the people who control what
gets a hearing or a vote — and most of the others are party floor leaders. In other words,
the money is not spread evenly; it pools around the gatekeepers.

**Step 3 — ACT (does their behavior follow?).** Finally, the members' actual legislative
behavior: each member's sponsored bills and the official policy area of each bill, pulled
from **Congress.gov** (the government's own legislation database). The bills line up with
the committee each member controls:

| Member | The committee they chair | What their recent bills are about | Bills sponsored |
|---|---|---|---:|
| Brett Guthrie | Energy & Commerce | Health ×9 · Energy ×3 · Environment ×2 · Telecom ×2 | 139 |
| Jason Smith | Ways & Means (taxes) | Taxation ×11 · Foreign Trade ×5 · Health ×3 | 123 |
| J. French Hill | Financial Services | Finance ×6 · International Affairs ×6 · Taxation ×4 | 147 |

**Putting the money in context (the "denominator").** A big dollar figure means little
without knowing how much a member raises overall. So each member's *total* campaign receipts
were pulled from the **Federal Election Commission (FEC)** to compute what fraction came
from registered lobbyists:

| Member | Role | Lobbyist $ (LD-203) | Total raised (FEC) | Lobbyist share |
|---|---|---:|---:|---:|
| Mike Carey | Ways & Means | $431K | $2.57M | 16.8% |
| Brett Guthrie | Chair, Energy & Commerce | $637K | $4.19M | 15.2% |
| Jason Smith | Chair, Ways & Means | $573K | $4.46M | 12.9% |
| Tom Cole | Chair, Appropriations | $389K | $3.21M | 12.1% |
| Steve Scalise | Majority Leader | $438K | $9.32M | 4.7% |
| Mike Johnson | Speaker | $433K | $17.5M | 2.5% |

The pattern: for the chairs of the committees that handle money and policy, registered
lobbyists are **13–17% of everything they raise**. Floor leaders (Scalise, Johnson) get
similar dollar amounts but raise so much more overall that lobbyists are a small slice.
*(One caveat: Senate fundraising is measured over a 6-year cycle vs. 2 years for the House,
so comparisons across chambers are directional, not exact.)*

**What is deliberately _not_ claimed.** Floor-vote records (**Voteview**, an academic
database of every congressional vote) show these members vote with their party 97–99% of
the time (Guthrie 97.8%, Speaker Johnson 99.8%). That means floor votes are explained by
party loyalty, not by donors — so this analysis does **not** claim "donors buy votes." The
defensible signal is which bills a member chooses to *sponsor*, because that is
discretionary and it tracks their donors' areas.

**One member up close (the micro-example).** In 2025, Brett Guthrie received $637K across
367 separate dated lobbyist contributions — and **51% of it arrived in the first quarter**,
right as the new Congress was organizing and committee gavels were being handed out. His
bill output stayed squarely in his committee's lane, and two of his health bills became
law. This is presented as **timing worth noting, not proof of cause and effect** — the
distinction matters and is treated carefully. (The dedicated `guthrie-money-timeline` view
shows this month by month.)

---

## Headline 2 — Foreign companies under U.S. scrutiny hired insiders, in plain sight

**The claim:** when foreign companies were facing hostile U.S. government action, they
spent heavily on lobbying and hired people with insider government credentials to do it —
all legal and disclosed, but newsworthy.

- **Tencent (China).** As the Chinese tech giant fought a U.S. Defense Department move to
  label it a "Chinese military company," its disclosed lobbying spend jumped roughly **5× to
  $4.04M in 2025**. One of the individuals registered to lobby for it, **John McEntee**,
  carries the disclosed background "Officer in the Executive Office of the President" — i.e.,
  a former senior White House official — working a single issue: the "erroneous trade
  restriction designation."
- **Nippon Steel (Japan).** As its bid to buy U.S. Steel was being blocked, its disclosed
  spend ramped from **$30K → $4.33M → $3.69M**. Its lead firm, Akin Gump, fielded former
  members of Congress and former trade officials.

**The FARA angle (why this is more than ordinary lobbying).** FARA is the stricter law for
representing *foreign* interests. The firms involved do hold FARA registrations, but
**McEntee does not** — meaning his Tencent work is disclosed under the lighter ordinary
lobbying regime rather than as a registered foreign agent. Confirming the precise foreign
"principal" behind each engagement requires FARA's foreign-principals dataset, a documented
next step.

---

## The three supporting findings

- **Flag — possible abuse of the disclosure system (Loc Nation).** A single filer submitted
  nine 2025 lobbying reports claiming **$20M each — $180M total**, about 35× the next real
  client. The filings are pseudo-legal reparations claims, not actual lobbying. This is
  flagged as possible misuse of a public system, and any "top spenders" total has to exclude
  it or it is nonsense.
- **Method — a coordinated-messaging detector.** A detector spots when many congressional
  offices push out near-identical statements in a tight time window (an organized campaign)
  versus generic partisan boilerplate. It surfaced, for example, a cluster of 26 releases
  from 20 members on a DHS/Noem theme. This is a reusable *capability* more than a single
  story.
- **Cold — the Senate/House consistency check.** A check of whether firms report different
  dollar figures to the two chambers for the same work found that, across 37,703 matched
  engagements, none differed by more than $100K. There is no scandal here — and it is
  documented so the lead is not re-chased.

---

## Caveats, ethics, and conflicts (read this before quoting any number)

- Every figure describes what was **disclosed** (self-reported), not independently verified
  cash flows.
- Real-world context — the DoD listing of Tencent, the U.S. Steel deal timeline — is labeled
  as such and should be independently confirmed before publication.
- The Loc Nation filings are flagged for possible referral, not asserted as a crime.
- The revolving-door relationships in Headline 2 are **disclosed and presumptively lawful**;
  the story is about the pattern, not wrongdoing.
- No one involved in this analysis has any relationship with any entity named here.
