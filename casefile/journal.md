# Journal - append-only session log

---
### 2026-07-12T18:56:57 · session auto
T-0001: chasing -> confirmed

---
### 2026-07-12T18:56:57 · session auto
T-0004: open -> cold (Prior result: 37,703 matched engagements, 0 gaps >100K. House not re-ingested this session; revive only if house data shows gaps.)

---
### 2026-07-12T18:56:57 · session S1
Ran 2025 senate+contributions+press; fixed resolver (Guthrie resolves, 80.5%) and amendment-aware dedup (Loc Nation 80M). Confirmed pay-the-gavel; parked senate-house.

---
### 2026-07-12T20:15:34 · session manual
Resolver upgrade session: campaign-committee honorees ('Guthrie for Congress' etc.) now resolve to members (conservative unique-match extractor); roster members enriched with party/state + canonical names. Coverage 80.5% -> 81.8%. Leaderboard re-verified: Guthrie #1 at $694K (177 registrants); FEC denominator refreshed (Guthrie ~17%). Report/traces/casefile updated.

---
### 2026-07-12T21:04:41 · session manual
Cold-thread re-verification: House 2025 re-ingested (108,518 filings, 98.3% bridged). 36,643 comparable engagement-periods, 0 gaps >100K after making xref.py mismatch amendment-aware on BOTH chambers (19 phantom gaps were amendment artifacts). Also: Tencent 5x re-derived from corpus (800K 2024 -> 4.04M 2025); FEC denominator method note added; generality demo (Medicare) + full session logs packaged.

## 2026-07-14 — feedback-round revision
- Re-derived the Baldwin pharma lead (from Shelby's hand analysis) with the pipeline before
  publishing: opened T-0005, logged F-0002 with the two Takeda→NORD filing UUIDs; method
  discrepancy vs. the hand count documented in traces/outputs/13.
- Product renamed Case Agent → Agent of Record. Guardrail added to skills after Katie's
  test produced "did not respond to a request for comment" language: comment is sought,
  never presumed. De-encoded S0/bucket shorthand in user-facing skill text.
