# Comparison of Three Approaches

Three people each took a solo run at the same challenge before comparing notes. This
document explains what each one produced and how the approaches differ — written to make
sense on its own. (For background on the challenge and the terms used here, see
[`findings_brief.md`](./findings_brief.md) and [`tool_pitch.md`](./tool_pitch.md).)

**The challenge, as a reminder:** produce (1) a newsworthy finding from a corpus of federal
lobbying records, and (2) a reusable tool ("Agent Skill") that lets an AI reproduce that
kind of investigation. The three attempts are by Shelby, Allie, and Evan (this submission).

---

## The one-line version

- **Shelby** wrote the best *map of the territory* — a memo of story ideas — but has not
  built anything yet.
- **Allie** built a polished package focused on *spotting suspicious filings*, wrapped in a
  lot of newsroom process (checklists, audit trails, reporter memos).
- **Evan** built a package focused on *connecting the datasets and verifying against outside
  official records*, on top of a reusable query engine.

---

## What each person produced

### Shelby — a story-ideas memo (nothing built yet)
A single 7-page PDF. It is a thinking document, not a finished submission:

- A short plain-English primer on how U.S. lobbying disclosure works (useful onboarding).
- A write-up of the same "Loc Nation" oddity the other two attempts also surfaced.
- **Eight candidate story angles**, each tagged with how well a tool built around it would
  generalize to future investigations.
- A recommendation: pursue the foreign-agent (FARA) angle or the "revolving door" angle
  first. Notably, it ranked the "lobbyist money to committee chairs" idea **last**, calling
  it well-worn ground.

There is no code, no tool, and no verified findings — it is the strongest *framing* of the
three, but it stops at ideas.

### Allie — an anomaly-spotting package (complete)
A large, finished submission whose headline is the **Loc Nation filing** treated as the
main story (a disclosure-integrity angle), plus four secondary leads (AI/data-center
lobbying, crypto, tariffs, and post-election "access money").

- The tool, `lobbying-disclosure-anomaly-triage`, works as a **scanner**: it sweeps the
  filings for unusual patterns, builds topic "evidence packets," and produces a "claim
  ledger" (a spreadsheet tracking each factual claim and its status).
- Its real strength is **newsroom process**: a claim ledger, an HTML review dashboard,
  reporter assignment memos, a "red-team" self-critique, and verification scripts. It is very
  disciplined about labeling what is self-reported vs. confirmed.

### Evan — an influence-mapping engine (complete)
This submission's headline is **pay-the-gavel** (lobbyist money pools around committee
gatekeepers, and their bills follow), backed by a second headline on the **foreign revolving
door**.

- The tool, `lobbying-influence-mapper`, works as a **connector + query engine**: it loads
  everything into one database, links the same entity across datasets, and then allows
  investigative questions and pulls in **outside official data** to verify — the
  congressional roster, Congress.gov bills, FEC fundraising, and Voteview votes.
- Its strengths are **cross-dataset linkage**, **external verification against ground truth**,
  and a **reproducibility ladder** that keeps everything re-runnable offline.

---

## Side by side

| Question | Shelby | Allie | Evan |
|---|---|---|---|
| How far did it get? | Ideas memo only | Complete package | Complete package |
| Main finding | (Recommends FARA or revolving-door angle) | The Loc Nation filing as a disclosure-integrity story | Pay-the-gavel: lobbyist money → committee gatekeepers |
| Other leads | 8 candidate angles | AI, crypto, tariffs, access-money | Foreign revolving door; Loc Nation as a flag; messaging method; a disproved lead |
| The tool | None built | A scanner for suspicious filings + evidence packets | A connector + question-answering engine across datasets |
| Outside data used | Suggested, not used | A light FEC spot-check | Five outside sources, all saved for offline replay |
| Strongest at | Framing and breadth of ideas | Newsroom process & discipline | Linking datasets & verifying against official records |
| Main gap | Nothing is built | Headline rests on one fringe filing | Headline is a more familiar topic (offset with hard external proof) |

---

## What all three attempts hit independently

Working separately, all three flagged the **same Loc Nation $180M oddity**, noticed the
**clean Senate↔House link** in the filings, and pointed at the **revolving-door / FARA**
seam. When three people independently land on the same things, that is good evidence those
signals are real.

---

## Three open questions across the approaches

1. **Is Loc Nation the headline or a footnote?** Allie's submission makes it the main story;
   Evan's treats it as an integrity *flag* behind two bigger findings. Shelby's memo warned
   it might be "a handful of weird filings — interesting but not headline-grade." A single
   framing is preferable to two submissions disagreeing.
2. **Pay-the-gavel was ranked low, then proven out.** Shelby's memo ranked it last as
   well-worn. The external verification in Evan's submission (official committee roster +
   Congress.gov bills + FEC fundraising) is what turns a familiar topic into a defensible,
   sourced story.
3. **The approaches are complementary, not just competing.** A combined entry is realistic:
   Allie's claim-ledger and editorial discipline + Evan's dataset-linking and outside-data
   verification + Shelby's framing memo as the justification — weighed against picking a
   single winner.
