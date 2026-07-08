# Invocation log (finding → skill invocation → key output)

All commands run from the skill root with `GAIN_DATA_DIR` set to the corpus and
`GAIN_WORKDIR=build`. Outputs abbreviated; full outputs are reproducible.

## Setup (foundation)
```
$ python scripts/ingest.py --years 2022 2023 2024 2025 2026 --datasets senate contributions press
  [senate filings 2025] 108225 filings, 203427 activities, 543990 lobbyist-rows
  [contributions 2025] 39438 reports, 149182 items
  [press 2025] 48318 releases, 477 members   (+2022-2024,2026)
$ python scripts/ingest.py --years 2025 --datasets house
  [house 2025_*_XML] 108518 filings total (~40s)
$ python scripts/resolve_entities.py
  [honoree] items resolved to a member: 394177/636833 (61.9%)
  [bridge] house linked: senateID=48904 + name=57767 = 106671/108518 (98.3%)
```

## Finding 1 — pay-the-gavel
```
$ python scripts/xref.py gatekeeper --filer lobbyist --year 2025 --top 15
  Brett Guthrie  R-KY  $637,024.84  (157 distinct registrants)
  Jason Smith    R-MO  $573,100     ; Mark Warner D-VA $542,059 ; ...
$ python scripts/connector.py annotate-gatekeeper --year 2025 --filer lobbyist --top 20
  n_with_chair_or_ranking: 10/20  (Guthrie=CHAIR E&C, Smith=CHAIR Ways&Means, ...)
$ python scripts/connector.py committee G000558
  Brett Guthrie -> CHAIR House Committee on Energy and Commerce
$ python scripts/xref.py member "Brett Guthrie"
  pay_by_year: 2022 $1,004,204 -> 2024 $2,080,232 -> 2025 $2,636,376
  top_payers: Amer. Clinical Lab Assn, SpaceX, CVS, Eli Lilly, BrightSpring, Exxon
$ python scripts/review.py "data/senate/2025/contributions/contributions_2025.json#9e7cef9a-bfff-4f83-944b-9411c727c521"
  -> BrightSpring Health Services (Louisville, KY), $25,000 honoring Rep. Brett Guthrie
$ python scripts/connector.py enrich-act --year 2025 --filer lobbyist --top 12   # Congress.gov key
  Guthrie(E&C): Health x9, Energy x3, Env. Protection x2, SciTechComm x2 ; 139 sponsored
  Jason Smith(W&M): Taxation x11, Foreign Trade x5 ; French Hill(FS): Finance x6, Intl Affairs x6
  -> shipped assets/legislation.json  (chairs' bills track their committee jurisdiction)
$ python scripts/connector.py enrich-finance --year 2025 --filer lobbyist --top 12   # FEC key
  Guthrie 15.2% of $4.19M ; Carey 16.8% of $2.57M ; Jason Smith 12.9% of $4.46M
  Mike Johnson(Speaker) 2.5% of $17.5M ; Scalise 4.7% of $9.32M
  -> shipped assets/fec_totals.json  (lobbyist share of total receipts; ids via committees crosswalk)
$ python scripts/connector.py enrich-votes --year 2025 --filer lobbyist --top 12    # Voteview, no key
  Guthrie: 547/551 votes, party-unity 97.8% (12 defections), dim1 0.427
  Smith 97.8% ; Scalise 98.5% ; Johnson(Speaker) 99.8% ; Warner(D) 89.7%
  -> shipped assets/votes.json  (gatekeepers are ~97-99% party-line votes)
$ python scripts/connector.py vote-align G000558 --max-bills 80                      # Voteview x Congress.gov
  policy areas of 80 recent bill-linked votes: Congress 16, Agriculture 11, Environment 8, ...
  -> floor votes span ALL areas (party-determined), unlike sponsorship -> sponsorship is the cleaner 'act' signal
$ python scripts/xref.py --json timeline "Brett Guthrie" --year 2025                  # money-cadence micro-example
  367 dated contributions, $637,025 ; Q1 (Jan-Mar) = $327K = 51% (front-loaded)
  bills: 25 sponsored (mostly E&C jurisdiction); HR2483 -> PL 119-44, HR7218 -> PL 118-142
  -> 'pay -> act' cadence for one member (temporal juxtaposition, not causation)
```

### Say leg (press topics; restores pay -> say -> act)
```
$ python scripts/xref.py say "Mark Warner" --top 6
  1235 releases (1057 tagged). domains: Health .21, Labor&Ed .21, Defense&Vets .18,
  Transport .17, Foreign Affairs .13, Tech&Telecom .12
$ python scripts/xref.py --json say-vs-do "Mark Warner"
  say tagged 1057 ; act: 25 bills (8 with a policy_area)
  talks_more_than_legislates: Defense&Vets, Transport, Foreign Affairs, Tech, Justice
  legislates_more_than_talks: Health, Government&Elections
  -> directional lead (act denom small); press is Senate-heavy, so robust here
$ python scripts/xref.py --json timeline "Mark Warner" --year 2025
  414 dated contributions + 370 press releases (monthly_press cadence alongside money)
```
Note: press coverage is Senate-skewed (Warner 1,235 releases vs. House Guthrie 16),
so `say`/`say-vs-do` are most robust for senators. Topics are keyword-tagged on
the title+lede (coarse, multi-label).

## Finding 2 — foreign revolving door
```
$ python scripts/xref.py client "TENCENT"
  senate_by_year: 2022 $800k ... 2024 $800k -> 2025 $4,040,000
  registrants: Brownstein Hyatt $3.4M, Hogan Lovells, MO Strategies, JOHN MCENTEE $400k
$ python scripts/xref.py lobbyist "John McEntee"   # (filing b8b09920-...)
  covered_position: "Officer in the Executive Office of the President"
  issue: TRD "Erroneous trade restriction designation"
$ python scripts/xref.py client "NIPPON STEEL"
  senate_by_year: 2023 $30k -> 2024 $4,330,000 -> 2025 $3,690,000
  registrants: AKIN GUMP $7.41M, BALLARD PARTNERS, VOX GLOBAL, GEPHARDT GROUP
  client_countries: US 22, JP 11 ; issues: TRD ; targets: White House/Commerce/USTR/NSC
  (covered positions: Ros-Lehtinen & Vela = former Members; Pomper = Sen Finance trade
   counsel; Kho = USTR China enforcement; Willems = Dep Asst to the President)
$ python scripts/connector.py fara          # no key; FARA active foreign-agent registry (559)
  AKIN GUMP=True  BALLARD=True  BROWNSTEIN=True  HOGAN LOVELLS=True  MERCURY=True
  MCENTEE=False  GEPHARDT=False  VOX GLOBAL=False
  # firms hold FARA regs; McEntee does NOT -> Tencent work under LDA, not FARA
```

## Finding 3 — disclosure abuse flag
```
$ python scripts/xref.py anomaly --year 2025 --factor 5
  STATE OF LOC NATION GLOBAL PUBLIC BENEFIT CORPORATION  $180,000,000  (35.1x next)
  outliers_over_factor: [STATE OF LOC NATION ...]
  # drilldown: 9 filings @ $20M each; text = HR40 reparations / lawsuit 1:24-cv-00479-RC
```

## Supporting — coordinated messaging
```
$ python scripts/detect_coordination.py clusters --start 2025-01-01 --end 2025-03-31 --min-members 6
  m=14 DI span=1d : "The Administration's failure to expend funds appropriated ..."
  m= 9 DI span=1d : "Elon Musk's financial ties to China ..."
$ python scripts/detect_coordination.py keyword "strategy group"
  n_hits 26, distinct_members 20 (Peter Welch x6) -> DHS/Noem investigation thread
```

## Cold thread — Senate vs House consistency
```
$ python scripts/xref.py mismatch --year 2025 --min-gap 100000
  comparison universe: 37,703 bridged engagements w/ house income ; count: 0
```

## Investigation state at end of session
```
$ python scripts/state.py show
  threads: pay-the-gavel=confirmed, foreign-revolving-door=confirmed,
           loc-nation-abuse=flagged, senate-house-mismatch=cold,
           coordinated-messaging=open
  leads(hot): cross-ref McEntee/Tencent + Nippon rosters vs FARA
```
