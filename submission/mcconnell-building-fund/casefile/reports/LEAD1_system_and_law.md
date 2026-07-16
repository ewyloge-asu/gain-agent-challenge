# The "no gatekeeper" story — is the hole structural, and is a false filing even illegal?

*Two questions pinned down before showing anyone. Framing kept on the **system**, not the person who
filed — see the note on intent at the end, which is itself a reason not to make her the villain.
Every number traces to a source you can pull.*

---

## Question 1: Is the hole a lasting structural thing, or a one-year blip? — Structural.

I re-ran the two measures — how much of the ledger is blank, and how big the largest filing gets —
for every year, not just 2025. The pattern is stable and long-running.

| Year | Filings | Blank income | **Blank %** | Largest single filing | (who) |
|---|---|---|---|---|---|
| 2022 | 93,475 | 34,057 | **36%** | $1.54M | Qualcomm |
| 2023 | 95,261 | 34,422 | **36%** | $3.50M | Industrial Energy Consumers |
| 2024 | 96,816 | 33,988 | **35%** | $1.53M | Nippon Steel |
| 2025 | 108,199 | 37,557 | **35%** | **$20.0M** | **STATE OF LOC NATION** |
| 2026 Q1 | 24,347 | 8,179 | **34%** | $1.00M | Innovairrs & Co. |

Two things a reporter can say with confidence:

1. **A third of the ledger has always been blank.** The share of filings with *no dollar figure at
   all* sits at 34–36% every single year from 2022 through 2026. This is not a glitch or a bad year —
   it's how the system has continuously operated. Anyone totalling "lobbying spend" from this data is
   working with a third of the records missing their central number.

2. **Nothing enforces an upper sanity bound, and 2025 proves it.** In every normal year the biggest
   single filing tops out around $1.5–3.5 million. Then in 2025 one filing reports **$20 million** —
   roughly **6× the largest legitimate filing ever seen** in four years — and it posted, published,
   and mirrored into the House system with nothing flagging it. The ceiling didn't rise because
   lobbying got bigger; it rose because a fabricated number met no check.

So the vulnerability (no validation of who files or what they claim) is **permanent and structural.**
The specific $80M distortion is a 2025 event, but the open door that let it happen has been open the
whole time. *(Next step to make this airtight: repeat the null-rate for the House dataset and confirm
the same pattern pre-2022 if you extend the corpus.)*

Sources: all figures reproducible from the built store; per-year totals and the blank-income counts
above were computed directly from the Senate filings (`data/senate/<year>/filings/…`).

---

## Question 2: Is filing a false report actually illegal — or does it just sit there?

**I read the real statutes rather than going from memory.** Short answer: **on paper a knowing false
filing probably is illegal, but the law is built and used to chase people who *don't file* — not
people who file false content — so in practice a fabricated figure faces essentially no consequence
and simply sits in the public record. "Illegal in principle, effectively unenforced."** And there's an
important intent wrinkle that cuts in the filer's favour.

Here's the actual law, in plain terms.

### The lobbying law's own penalties — 2 U.S.C. § 1606
*(read at law.cornell.edu/uscode/text/2/1606, as-of 2026-07-15)*

- **Civil (§ 1606(a)):** someone who **"knowingly fails to… comply with any… provision of this
  chapter"** can be hit with a **civil fine up to $200,000.** Filing a report you know to be false is
  arguably a knowing failure to comply with the requirement to file accurate reports.
- **Criminal (§ 1606(b)):** someone who **"knowingly and corruptly fails to comply"** can be
  **imprisoned up to 5 years.** Higher bar — note the word *corruptly*.

So the lobbying statute does contain teeth for false filings. But look at how enforcement is wired.

### How it's actually enforced — 2 U.S.C. § 1605
*(read at law.cornell.edu/uscode/text/2/1605, as-of 2026-07-15)*

The Secretary of the Senate and Clerk of the House are told to *"review, and where necessary verify
and inquire to ensure the accuracy, completeness, and timeliness"* of filings. But the machinery that
follows is built entirely around **non-compliance** in the sense of missing/defective filings:

1. notify the filer **in writing** they may be non-compliant, then
2. only if they **fail to respond within 60 days**, refer them to the **U.S. Attorney for D.C.**

There is no proactive fraud-detection unit, no audit of dollar figures, no automatic flag when a
single client reports 6× the largest filing in the country. The Secretary/Clerk are administrators,
not investigators, and the referral pipe leads to one over-loaded prosecutor's office. In practice
the enforcement that does happen is overwhelmingly against people who **didn't file at all** — not
people who filed fiction. That's why an $80M fabrication can sit live on lda.senate.gov indefinitely.

### The general false-statements law — 18 U.S.C. § 1001
*(read at law.cornell.edu/uscode/text/18/1001, as-of 2026-07-15)*

This is the government-wide "lying to the feds" statute (up to 5 years). It normally applies to the
executive branch, but **§ 1001(c)(1)** extends it to legislative-branch matters for, among other
things, *"a document required by law, rule, or regulation to be submitted to… any office or officer
within the legislative branch."* An LDA report — filed with the Secretary of the Senate / Clerk of the
House — plausibly fits that description, so a **knowingly and willfully** false filing could in
principle be reached by § 1001. Whether courts actually apply § 1001 to LDA filings is not
well-settled and should be confirmed with a lawyer.

### The catch that matters most — and why it protects the filer, not the system

Every one of these hooks requires a **culpable state of mind**: § 1606(a) "knowingly," § 1606(b)
"knowingly and **corruptly**," § 1001 "knowingly and **willfully**." These words mean the government
must prove the filer **knew the statement was false and intended to deceive.** A person who *sincerely*
(however mistakenly) believes her "nation" is genuinely owed the money may simply **not have that
intent** — which could put her outside these criminal statutes entirely.

That is exactly why the honest story points at the system, not the individual:

- If she filed sincerely, **the law may not treat her as a criminal at all** — yet the false $80M
  still entered the official record and still distorted the national total. The failure isn't her
  culpability; it's that **nothing in the system stops or corrects the entry regardless of intent.**
- If she filed knowing it was false, then on paper she likely broke § 1606 (and maybe § 1001) — **and
  still nothing happened**, because no one detects, notices, or refers false content. Either way the
  spotlight lands on the absent gatekeeper.

**Verdict for the editor/lawyer:** *possible violation of 2 U.S.C. § 1606 (and possibly 18 U.S.C.
§ 1001), but effectively unenforced — the statute's own machinery is aimed at non-filers, and the
intent requirement makes a sincere-belief filer hard to reach.* This is an assessment for a lawyer,
not a conclusion; do not assert that anyone broke the law.

---

## What this means for the story

You can now say all of the following, sourced:

- The disclosure system has **no gatekeeper**, and this is **structural** — a third of filings have
  lacked a dollar figure every year for at least four years, and there is no check that would catch a
  fabricated figure 6× larger than any real one.
- When a fabrication does appear, it **silently distorts the totals** everyone relies on (the 2025
  fake = 2.78% of all reported US lobbying income).
- The law **does** contain penalties for false filings, but they are **aimed at non-filers and
  effectively never used against false content**, and the intent requirement means even a knowing
  case is hard — so a false $80M figure **just sits there.**
- The system-level fix questions write themselves: should the Secretary/Clerk validate filings, cap or
  query implausible figures, or flag content the way the IRS or SEC screen returns?

**Before publishing:** confirm the enforcement reality on the record (Secretary of the Senate's Office
of Public Records; DOJ's semiannual LDA enforcement reports under § 1605(b) — these show how few
actions are ever brought); have a lawyer confirm whether § 1001(c) reaches LDA filings; and give every
named party, including the filer, a fair chance to comment. Keep the framing on the system; treat the
filer as a person who may sincerely hold unusual beliefs, not a villain.

---

### Source index
- LDA penalties: **2 U.S.C. § 1606** — https://www.law.cornell.edu/uscode/text/2/1606 (as-of 2026-07-15)
- LDA enforcement/review duties: **2 U.S.C. § 1605** — https://www.law.cornell.edu/uscode/text/2/1605 (as-of 2026-07-15)
- False statements: **18 U.S.C. § 1001** (see § 1001(c) legislative-branch limit) — https://www.law.cornell.edu/uscode/text/18/1001 (as-of 2026-07-15)
- Year-by-year blank-rate + largest-filing table: computed from `data/senate/<year>/filings/filings_<year>.json`.
- The fabricated filing itself: `data/senate/2025/filings/filings_2025.json#4d5b1cb0-0971-43b8-958b-d260e2be8af1`.
