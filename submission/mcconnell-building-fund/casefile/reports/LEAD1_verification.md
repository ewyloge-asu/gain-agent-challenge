# Lead 1 — verified: the $80-million "sovereign nation" that walked into the official record

*A close read of the actual filings, who filed them, how they got accepted, and whether this is
one oddball or a symptom of a system with no gatekeeper. Every claim below cites the exact source
record so you can pull it yourself.*

---

## 1. Is it real, and does it say what we thought? — Yes, verified.

I opened the raw filing exactly as it sits in the Senate's own data. It is not a misread. The
record even carries its **own live Senate links**, which is how anyone can independently confirm it:

- Machine record: `https://lda.senate.gov/api/v1/filings/4d5b1cb0-0971-43b8-958b-d260e2be8af1/`
- Human-readable print page: `https://lda.senate.gov/filings/public/filing/4d5b1cb0-0971-43b8-958b-d260e2be8af1/print/`

**What the filing actually contains** (Q1 2025 amendment, source
`data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1`):

- **Income (fee):** `"20000000.00"` — twenty million dollars for one quarter.
- **Client:** "STATE OF LOC NATION GLOBAL PUBLIC BENEFIT CORPORATION," self-described as an
  *"Established sovereign govt: drafting formal constitution, laws, negotiating treaties, et al."*
- **Registrant (the "firm"):** "LOC COMMUNITY ASSOCIATION," c/o Christina Loren Clement LLC,
  8 The Green, Suite A, Dover, Delaware — a registered-agent address, not a K Street lobby shop.
- **The lobbyist:** Rev. Dr. Christina L. Clement, whose listed *"covered position"* (the box for
  prior government jobs) reads **"Head of State Black USA."**
- **What the money is for, in the filing's own words:** *"federal funding anticipated $20 million
  for H.R. 40 research… Anticipated award $500 quadrillion; land return and all assets… anticipated
  printing by the Bureau of Engra[v]ing and Printing of the LND aka Black USD…"*, citing UCC filing
  numbers and a DC federal court case (1:24-cv-00479-RC).
- **Agencies it claims to lobby:** Bureau of Engraving & Printing (which literally prints US
  currency), Bureau of Land Management, Bureau of Economic Analysis, plus the House and Senate.

So the summary was accurate. This is a real, accepted, published federal lobbying filing declaring
a fictitious "sovereign nation" as a $20-million-a-quarter client.

---

## 2. Who filed it, and how does something like this end up in the official record?

**One person filed all of it.** Every Loc Nation filing was submitted by the same individual —
Christina L. Clement — signing across filings as "REV DR CHRISTINA L CLEMENT," "on behalf of LCA"
(Loc Community Association), and, on several, **"HH Empress Queen Christina Clement."** She is both
the registrant's contact *and* the sole listed lobbyist. (Sources: the `posted_by_name` field on
each filing; timeline below.)

**The paper trail, in order:**

| Date posted | Filing | Income | Filed by |
|---|---|---|---|
| 2024-09-09 | Registration (LD-1) | — | "/CHRISTINA LOREN CLEMENT LLC/ in entities capacity" |
| 2024-11-08 | Q3 2024 report | none | Christina Clement on behalf of LCA |
| 2025-01-30 | Q4 2024 report | none | REV DR CHRISTINA L CLEMENT on behalf of LCA |
| 2025-03-16 | Q1 2025 report | none | REV DR CHRISTINA L CLEMENT on behalf of LCA |
| 2025-03-25 | Q1 2025 **amendment** | **$20,000,000** | REV DR CHRISTINA L CLEMENT |
| 2025-04→06 | Q2 2025 + 4 amendments | $20,000,000 | incl. "HH Empress Queen Christina Clement" |
| 2025-10 / 11 | Q4 and Q3 2025 reports | $20,000,000 ea. | Christina Clement |
| 2026-02-25 | Q4 2025 amendment | $20,000,000 | Rev Dr Christina Clement |

(Registration source: `data/senate/2024/filings/filings_2024.json#5000632b-e40b-4762-affc-551b46a40c91`.)

**How it gets accepted — the mechanism.** Federal lobbying disclosure runs on an **honour system**.
Under the Lobbying Disclosure Act, anyone can create an account on the Senate's electronic filing
portal, **self-register** a "registrant" and "client" (the LD-1), and then **self-file** quarterly
activity reports (the LD-2), electronically certifying the information is true. There is **no
substantive pre-publication review** of who you are or whether your numbers are plausible: the
income box is a free-text dollar figure the filer types in. Once submitted, the filing publishes
immediately to the public database and API — the same database journalists, watchdogs and academics
treat as authoritative. The Secretary of the Senate can refer *non-compliance* (people who don't
file) to the Justice Department, but nothing in the pipeline sanity-checks the *content* of a filing
that is submitted. That is exactly how a self-declared "Empress" could register a "sovereign nation"
and post $80 million into the national lobbying ledger.

*(This is my plain-English description of how the LDA e-filing system works. Before publishing, this
mechanism should be confirmed on the record with the Secretary of the Senate's Office of Public
Records and the House Clerk — see "what to still nail down.")*

---

## 3. One-off, or a system with no gatekeeper? — Both, and that's the point.

I tested this two ways. The honest answer: **the fabricated dollar figure is a single-actor event,
but it is a symptom of a systemic design with no gatekeeper.**

**On the money, Loc Nation is genuinely unique.** Across four full years of filings, it is the
**only** client with *any* single report above $3.5 million. The next-largest single filing in the
entire corpus is a legitimate $3.5M (CarbonLeaf/Industrial Energy Consumers, 2023); normal
top-tier filings run $1–1.6M. Loc Nation's $20M/quarter is ~6× the biggest real filing on record.
There is no swarm of $20M fakes — just this one.

**On the bizarre content, also unique.** The tell-tale sovereign-citizen language appears *only*
in Loc Nation filings and nowhere else in the data: "quadrillion" (16 filings — all Loc Nation),
"Black USD" (14 — all Loc Nation), "sovereign citizen" (4 — all Loc Nation).

**But the vulnerability it exposes is systemic, and measurable:**

- **It moved the national numbers.** Counting one report per quarter, Loc Nation's fake $80 million
  equals **2.78% of *all* reported lobbying income in the United States for 2025** — $80M out of a
  ~$2.88 billion national total (amendment-aware). One person, filing from a Delaware mailbox,
  inflated the country's reported lobbying fees by nearly 3%, and nothing caught it.
- **It's the #1 "client" in America by this measure** — larger than Qualcomm, big pharma, or any
  real corporation — purely because no check exists.
- **The same open door produces pervasive gaps.** **35% of all 2025 Senate filings (37,557 of
  108,199) carry no income or expense figure at all.** The very design that let a fabricated $80M
  through is the design that leaves a third of the ledger blank. A researcher ranking "top spenders"
  off this data, unaware, would put a self-declared empress at the top.

**So which story is it?** It's not "one weird filing" and stop there. The weird filing is the
*vivid proof* of the real story: **the federal lobbying-disclosure system has no gatekeeper — it
will accept and publish an obviously fictitious $80-million filing, that filing silently distorts
the totals everyone relies on, and the same absence of validation leaves a third of the data
empty.** Loc Nation is the way in; the system is the story.

---

## 4. What's confirmed vs. what to still nail down

**Confirmed from the records (traceable to source ids above):** the filings exist and are live on
lda.senate.gov; the $20M/quarter figures; the single filer and her self-descriptions; the sovereign
-citizen content; that Loc Nation is the sole >$3.5M client and the sole source of the red-flag
language; the 2.78% distortion of the 2025 income total; the 35% null-income rate.

**Still to nail down before anything is published (leads, not yet facts):**
1. **Confirm the mechanism on the record** — interview the Secretary of the Senate's Office of
   Public Records and the House Clerk: is there any content review, and have these specific filings
   been flagged or referred?
2. **Who is Christina Clement / what is the DC court case** (1:24-cv-00479-RC)? Public court records
   and her 2024 presidential-campaign references are checkable and give the human story its context.
   Approach with care and fairness — this may be one person's sincere, unusual crusade, not a scam.
3. **Whether the Senate/House have since removed or amended the filings** (the record shows a 2026
   amendment, so the account was still active).
4. **How widespread blank/implausible filings are over time** — I measured 2025; extend to 2022–2024
   to show the gap is structural, not a one-year fluke.

**Guardrails:** give Christina Clement and the relevant offices a fair chance to comment before
publishing; the records support "this is what was disclosed and what the system accepted," not any
claim about intent. Nothing here asserts a crime.

---

### Source index (pull any of these to verify)
- Q1 2025 $20M filing: `data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1`
- Original 2024 registration: `data/senate/2024/filings/filings_2024.json#5000632b-e40b-4762-affc-551b46a40c91`
- House mirror (same client, senateID 401108853-61287): `house/2025_1stQuarter_XML/301694892.xml`
- Live public page: `https://lda.senate.gov/filings/public/filing/4d5b1cb0-0971-43b8-958b-d260e2be8af1/print/`
- Distortion + null-rate figures: reproducible from the built store (2025 income total $2.88B; Loc $80M = 2.78%; nulls 37,557/108,199 = 35%).
