# Investigation Brief

## The question
What is the strongest genuinely newsworthy story hidden in a corpus of US congressional press
releases (2022–2026 Q1) and Senate + House lobbying-disclosure (LDA) filings (2022–2026 Q1)?
Started as a wide-net scan across all angles; converged on a systemic data-integrity/accountability
story about the lobbying-disclosure system itself.

## Scope
- Data: Senate LDA filings + contributions (2022–2026 Q1), House LDA filings (2025), congressional
  press releases (2022–2026 Q1). Store built with the lobbying-influence-mapper (SQLite, prov id on
  every row).
- Time: 2022-01 through 2026-03.
- Domain: US federal lobbying disclosure + congressional messaging.

## Confirmed lead
The federal lobbying-disclosure record has **no gatekeeper**. A single filer registered a fictitious
"sovereign nation" and reported **$80M** in 2025 lobbying fees — >20x any real client by that measure
and above the largest real in-house lobbying budget — and it published to the official record with
nothing checking it. On the back end, the government's own auditor shows the law is enforced almost
entirely against people who *fail to file*, with no documented penalty ever for false content.

## What counts as a finding (the bar)
(a) Traceable to specific source filings via prov id; (b) quantitatively unusual/contradictory vs a
sensible baseline, re-derived from raw data; (c) plausibly a story. Documented ≠ causation. Strongest
legal assertion is "possible, for a lawyer." Comment sought, never presumed.

## Framing rule
This is a story about the **system**, NOT the individual who filed. She may sincerely hold unusual
beliefs; nothing asserts wrongdoing. Every number carries its source and has been fact-checked.

## Angles checked and parked (see cold threads)
- Senate↔House filing discrepancies — reconcile well (largest 2025 gap ~$90k). Cold.
- Coordinated/astroturf messaging — clusters are ordinary joint bill reintroductions. Cold.
- Secondary live leads not pursued: gatekeeper committee-chair money (Guthrie); foreign influence
  (Nippon Steel / China-linked fintech); revolving door. Parked as open for later.

## Owner / audience
Owner: Mitul (non-journalist; wants jargon defined, sources shown). Analyst: Claude (Cowork),
sessions on 2026-07-15.
