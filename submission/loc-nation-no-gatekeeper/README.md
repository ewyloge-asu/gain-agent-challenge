# Finding: the lobbying-disclosure record has no gatekeeper

Produced by running investigative Agent Skills against the GAIN US congressional
lobbying corpus (2022–2026 Q1) in a Claude Cowork session.

**The story:** the federal lobbying-disclosure system has no one checking filings on the way
in, so a single person registered a fictitious "sovereign nation" and reported **$80 million**
in 2025 lobbying fees — more than any real client by that measure, and more than the largest
real in-house lobbying budget in the country — and it posted straight into the official public
record. The government's own auditor (GAO) shows almost nothing happens afterward: enforcement
is aimed at people who fail to file, with no documented case of anyone ever penalised for a
false figure.

## What's in this folder

| File | What it is |
|---|---|
| `FINDINGS_SUMMARY.md` | **The findings report** — story in plain terms, then every claim with its corrected figure, counting method, source, and caveats. |
| `interaction-trace/interaction-trace.html` | **The interaction trace, rendered** — human turns and skill invocations highlighted; open in any browser. |
| `interaction-trace/interaction-trace.jsonl` | The interaction trace, **raw JSON** (the full session log the page was rendered from). |
| `working-papers/LEAD1_*.md` | The four intermediate memos — initial verification, system-and-law, enforcement record, and the adversarial fact-check pass. |
| `casefile/` | The auditable case file written by the `case-file` skill (brief, threads, findings.yaml, entities, journal). |

## Skills invoked (the trace is keyed to these)
`/investigative-method` · `/lobbying-influence-mapper` · `/checking-the-law`
(plus `case-file`, used via its CLI)

## Verification
Every figure re-derives from the raw corpus. The central filing is live on the government site:
https://lda.senate.gov/filings/public/filing/4d5b1cb0-0971-43b8-958b-d260e2be8af1/print/
Enforcement figures: GAO-25-107523. Statutes: 2 U.S.C. §§ 1605–1606, 18 U.S.C. § 1001.
