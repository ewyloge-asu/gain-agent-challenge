# Journal - append-only session log

---
### 2026-07-15T14:25:09 · session S1
Wide-net scan -> converged on the LDA 'no gatekeeper' story. Verified the fabricated $80M Loc Nation filing from raw JSON + House mirror; confirmed unique on both dollar amount and content.

---
### 2026-07-15T14:25:09 · session S1
Read statutes (2 USC 1606/1605, 18 USC 1001) and GAO-25-107523: illegal-in-principle-but-unenforced; enforcement aimed at non-filers. Fact-checked every figure; corrected 'biggest client' framing, distortion denominator (~1.3% all-in), and blank-rate (~25%/~10%).

---
### 2026-07-15T14:25:09 · session S1
NEXT SESSION START HERE: finding is confirmed from records. Remaining = reporting-out: seek comment (incl. filer), interview Senate/House filing offices, obtain DOJ 1605(b) reports, lawyer review of 1001(c). Secondary open leads: Guthrie money, Nippon/China foreign influence, revolving door.

---
### 2026-07-15T15:54:46 · session S2
Mapped the LD-203 'in honor of' channel (Honorary Expenses, type=he): 4,291 items / ~$134.4M, 2022-2026Q1. Givers=registrants (contributor='SELF'). Clusters: caucus nonprofits (CBCF ~$25.5M/101 funders; CHCI+CHLI ~$22.7M/80; APAICS ~$5.0M/39) and individual power centers. Standouts: RPK 'Mitch McConnell Building' fund ~$1.525M (Pfizer $1M etc., web-verified) and largest single item State Farm $2.65M->Habitat 'in honor of' Rep. Foxx (money verified real). checking-the-law on 2 USC 1604(d)(1)(E): uncapped disclosure requirement added by HLOGA 2007 -> legal-but-unscrutinized, NOT a violation. Threads T-0004..T-0006 confirmed; findings F-005..F-007.

---
### 2026-07-15T15:54:46 · session S2
NEXT SESSION START HERE (honorary channel): reporting-out only. Seek comment from State Farm, Pfizer/AT&T/Microsoft, RPK/McConnell office, CBCF/CHCI, Rep. Foxx. Optional deepening: IRS 990 corporate-donor share for CBCF/CHCI; whether KY-press-reported Comcast/MetLife/Altria RPK gifts appear in federal LD-203 (they do NOT in Senate data = disclosure-completeness angle); honorary-degree/commencement items are a distinct sub-pattern (universities reporting the value of degrees to officials), not cash to members.

---
### 2026-07-15T16:05:24 · session S3
Chased the McConnell-building disclosure gap. Got the complete outside record (KREF Q4-2022 via Ky Lantern): 6 donors, $1.65M — Pfizer $1M, MetLife $300k, Altria $100k, Comcast $100k, AT&T $100k, Delta $50k. Reconciled vs full federal LD-203: Pfizer/AT&T/Delta DISCLOSED ($1.15M); MetLife/Altria/Comcast NOT disclosed ($500k) despite all three being heavy LD-203 filers (their only KY federal items are FECA PAC gifts). checking-the-law on 2 USC 1604(d)(1)(E)/(1602 defs): appears required but turns on unsettled 'named for/in recognition of' reading -> possible, for a lawyer, not a violation. Thread T-0007 (chasing), finding F-008 w/ legal_flag. Deliverables in investigation_honorary/.

---
### 2026-07-15T16:16:37 · session S3
Extended McConnell-building reconciliation to FULL period (2022-2025). Outside record = KREF cumulative via Ky Lantern 2026-01-07: ~$4.43M, ~22 named donors + 16 small, for the completed $4.4M HQ. Federal LD-203: only 4 disclosed (Pfizer/AT&T/Microsoft/Delta = $1.475M); 13 federal registrants gave but filed NO building he item (~$2.12M); ~$829k from non-filers incl #2 donor NWO Resources $500k. Single-quarter view (3/$500k) understated it. F-008 revised; deliverable full_reconciliation_table.csv + updated memo.

---
### 2026-07-15T16:23:24 · session S3
FINAL: verification pass over every figure (verify_all.py) - channel $134.4M/4,291 items/93.1% SELF; caucus clusters CBCF $25.5M, CHCI+CHLI $22.7M, APAICS $5.0M; building-fund reconciliation buckets sum EXACTLY to $4,426,645 (disclosed $1.475M/4, registrant-no-disclose $2.1225M/13, non-filer $0.829M/6); federal-filer split $1.475M vs $2.1225M. Caught+removed one overstatement: Toyota's $100k Kennedy Center gift honors ~14 bipartisan members, NOT McConnell specifically - dropped from the 'disclosed other McConnell honoraria' examples (kept only Airbnb/AEI $1,500 and Boeing/Hudson $50k, which are McConnell-specific). Consolidated summary saved to casefile/reports/LEAD2_honorary_giving_summary.md.
