# The lobbying record has no gatekeeper — findings summary

**Investigation:** what's the strongest newsworthy story in a corpus of US congressional press
releases and Senate + House lobbying-disclosure filings, 2022–2026 Q1.
**Status:** one confirmed finding, verified and fact-checked; ready for reporting-out (comment,
lawyer review) before publication.
**A note on framing:** this is a story about a **system**, not about the individual who filed. The
person may sincerely hold unusual beliefs; nothing here asserts she did anything wrong. Every number
below has been re-derived from the raw data and carries its source.

---

## The story in plain terms

The federal government keeps an official, public ledger of who lobbies Congress and for how much. It
is the record journalists, researchers, and watchdogs rely on to follow the money in Washington. It
runs on an **honour system**: anyone can register online, type in whatever numbers they like, and the
filing publishes immediately — **nobody checks it on the way in.**

In 2025 that gap produced a striking result. A single person registered a fictitious country — the
"State of Loc Nation Global Public Benefit Corporation" — and filed official lobbying reports claiming
**$20 million every quarter, $80 million for the year.** That one fabricated figure is more than
twenty times larger than any real lobbying client's fees, and larger than the biggest real in-house
lobbying budget in the country. It sailed straight into the official database, was copied into the
House's system too, and quietly inflated the national lobbying totals — and **nothing flagged it.**

And almost nothing happens after the fact either. The government's own auditor shows the disclosure
law is enforced overwhelmingly against people who **fail to file at all** — usually with letters and
phone calls — while there is **no documented case of anyone ever being penalised for filing a false
number.** On paper, a knowingly false filing can draw fines or even prison; in practice the machinery
isn't pointed at false content, and it just sits in the record.

So the story isn't "one weird filing." It's that the disclosure system has **no gatekeeper on the way
in and effectively none on the way out** — and this one vivid filing proves it.

---

## The confirmed finding, with the specifics

### 1. A fabricated entity reported $80 million in 2025 lobbying fees

- **What it is.** Client "STATE OF LOC NATION GLOBAL PUBLIC BENEFIT CORPORATION," self-described in the
  filing as an *"Established sovereign govt: drafting formal constitution, laws, negotiating treaties."*
  The registrant ("Loc Community Association") registered to lobby for itself from a Dover, Delaware
  registered-agent address; the sole lobbyist's "covered position" (prior government job) is listed as
  *"Head of State Black USA."* The filing ties the money to bill H.R. 40 (a reparations-study bill), a
  $500-quadrillion damages claim, and a demand that the Bureau of Engraving & Printing print a new
  currency.
  *Source: `data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1`;
  live public copy: https://lda.senate.gov/filings/public/filing/4d5b1cb0-0971-43b8-958b-d260e2be8af1/print/*

- **The $80 million — how counted.** $20,000,000 reported for each of the four quarters of 2025,
  counted **one figure per quarter** (amendment-aware, so amendments aren't double-counted): 4 × $20M =
  **$80M**. The entity reports no "expenses" figure, so there is no competing number.
  *Always describe this as "reported/claimed," not "spent" — no money changed hands.*
  *(A naïve sum of every amendment plus the mirrored House copies reaches $180M; we deliberately use the
  conservative $80M.)*
  *Source: the four quarterly filings for client_id 61287, 2025; registration
  `data/senate/2024/filings/filings_2024.json#5000632b-e40b-4762-affc-551b46a40c91`.*

### 2. It dwarfs every real client by the fee measure — and tops the biggest real budget

- By **reported income** (the fee a client pays outside lobbying firms), 2025: Loc Nation **$80.0M**,
  then the next-largest real clients are AIPAC $3.76M and Nippon Steel $3.42M. Loc is **~21× the
  next-largest.**
- Its claimed $80M even **exceeds the single largest *real* lobbying budget in the country** — the U.S.
  Chamber of Commerce's **$70.3M** in reported in-house **expenses** (next: National Association of
  Realtors $54.1M, PhRMA $37.9M).
- **Honest wording caveat:** do **not** call it flatly "the biggest lobbying client in America." That's
  true only by the income measure; large organizations that lobby in-house report comparable *real*
  money in the separate "expenses" field. The defensible claim is the income-rank (~21×) plus the
  Chamber comparison.
  *Source: amendment-aware client rankings by income and by expenses, 2025 Senate filings.*

- As a **single filing**, the $20M quarterly figure is ~**6× the largest legitimate single filing** in
  four years of data (the next-biggest is $3.5M, Industrial Energy Consumers of America, 2023).
  *Source: max single-filing income scan, 2022–2025.*

### 3. It measurably distorted the national totals

- Loc's $80M is **~1.3% of all reported federal lobbying dollars in 2025** (income + expenses =
  $6.25B), or **2.78%** if you look only at the client-fee **income** side ($2.88B).
- **Honest caveat:** these totals are computed from the raw corpus with an amendment-dedup rule and run
  higher than commonly published figures (e.g., OpenSecrets ~$4–4.5B/yr, different dedup) — so present
  the percentage with its denominator stated, and **lead with the conservative ~1.3%**, not as an
  official statistic.
  *Source: amendment-aware sums of income and expenses, 2025 Senate filings.*

### 4. The "no gatekeeper on the way in" is structural, not a one-year blip

- The share of filings carrying **no dollar figure at all** (neither income nor expenses) is stable at
  **~24–26% every year, 2022–2025.** Among **quarterly activity reports specifically**, about
  **10–12% every year** report neither figure — a strikingly consistent rate.
- **Honest caveat / correction:** an earlier draft said "a third of filings are blank." That over-counted
  — it counted only the income field, but in-house filers legitimately use the expenses field instead,
  and registrations/no-activity reports legitimately carry no dollar amount. The corrected figures above
  are the ones to use, and this is a **supporting** detail, not a pillar.
  *Source: null-income vs null-both-fields counts by filing_type and year, 2022–2025 Senate filings.*

### 5. There is essentially no consequence for a false filing — "illegal in principle, unenforced"

- **The law does have teeth on paper.** A *knowing* false lobbying filing can draw a civil fine up to
  **$200,000** (2 U.S.C. § 1606(a)); a *knowing and corrupt* one, up to **5 years** in prison
  (§ 1606(b)); and the general false-statements law (18 U.S.C. § 1001) may also reach it.
  *Sources: https://www.law.cornell.edu/uscode/text/2/1606 · https://www.law.cornell.edu/uscode/text/2/1605 ·
  https://www.law.cornell.edu/uscode/text/18/1001 (read 2026-07-15).*
- **In practice it's aimed at non-filers, not false content.** Per the government's own auditor
  (GAO-25-107523, *2024 Lobbying Disclosure* audit), over **2015–2024** the U.S. Attorney received
  **3,566** referrals for failing to file activity reports and **2,000** for failing to file
  contribution reports — **all for non-filing.** Enforcement actions "**include letters, emails, and
  telephone calls**"; **63%** of referrals were still pending. In all of **2024** DOJ took **one** civil
  action (a **$65,000** settlement against a repeat non-filer) and **zero** criminal actions; there have
  been **no** JACK Act prosecutions ever. GAO records **no** case of enforcement for a false figure.
  *Source: https://www.gao.gov/products/gao-25-107523 (read in full).*
- **The intent catch — and why it points at the system, not the filer.** Every legal hook requires a
  culpable state of mind ("knowingly," "corruptly," "willfully") — i.e., intent to deceive. A filer who
  *sincerely* believes the money is owed may fall outside these statutes entirely. So if she filed
  sincerely, the law may not treat her as a wrongdoer at all — yet the false $80M still entered the
  record and still distorted the totals. Either way, the failure is the **absent gatekeeper**, not the
  individual.

---

## What is confirmed vs. what still needs reporting-out

**Confirmed from primary records (each traceable above):** the filings exist and are live on
lda.senate.gov; the $80M (4 × $20M, amendment-aware); the single self-filer; the sovereign-nation
content; that Loc is ~21× the next client by income and above the Chamber's real budget; the ~1.3%
distortion; the ~10–12% blank-rate among activity reports and its year-to-year stability; the statutory
penalties; and the GAO enforcement figures.

**Still to do before publishing (leads / verification, not yet facts):**
1. **Seek comment** from every named party — including the filer — and treat her fairly as a person who
   may sincerely hold unusual beliefs.
2. **Confirm the enforcement reality on the record:** interview the Secretary of the Senate's Office of
   Public Records / House Clerk (is there any content review?) and obtain DOJ's semiannual **§ 1605(b)**
   enforcement reports — the authoritative all-time count.
3. **Lawyer review** of whether 18 U.S.C. § 1001(c) actually reaches LDA filings, and of any wording
   that implies wrongdoing.
4. **Re-verify** the pre-2015 settlement dollar amounts against their original GAO reports before
   printing them.
5. Optionally extend the blank-rate check to the **House** dataset and pre-2022 years to show the gap is
   long-standing beyond this corpus.

**Guardrails:** the strongest legal statement the records support is *possible, for a lawyer* — never
"X broke the law." No party has been contacted yet, so no "declined to comment" language. Keep the
spotlight on the system.

---

## The two sentences to stand behind

> A single filer registered a fictitious "sovereign nation" and reported **$80 million** in federal
> lobbying fees for 2025 — more than 20 times any real client by that measure, and more than the largest
> real in-house lobbying budget in the country — and it posted to the official public record with nothing
> checking it.

> The government's own auditor shows the disclosure law is enforced almost entirely against people who
> **fail to file**, mostly with letters and calls — a single $65,000 civil settlement in 2024, no
> criminal prosecutions — with **no documented case** of anyone ever penalised for filing a false figure.

---

### Source index
- Fabricated filing (Q1 2025): `data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1` · public: https://lda.senate.gov/filings/public/filing/4d5b1cb0-0971-43b8-958b-d260e2be8af1/print/
- Original registration (2024): `data/senate/2024/filings/filings_2024.json#5000632b-e40b-4762-affc-551b46a40c91`
- House mirror (senateID 401108853-61287): `house/2025_1stQuarter_XML/301694892.xml`
- Rankings, totals, blank-rate: computed from `data/senate/<year>/filings/filings_<year>.json` (amendment-aware dedup; methods stated inline)
- Law: 2 U.S.C. § 1606, § 1605; 18 U.S.C. § 1001 — law.cornell.edu (read 2026-07-15)
- Enforcement: GAO-25-107523, *2024 Lobbying Disclosure* — https://www.gao.gov/products/gao-25-107523
- Detailed working papers (in this folder): `LEAD1_verification.md`, `LEAD1_system_and_law.md`, `LEAD1_enforcement_record.md`, `LEAD1_factcheck.md`
