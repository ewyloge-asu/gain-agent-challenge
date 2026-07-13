# What counts as a factual claim that needs a footnote

The Howard Center's footnoting guide is unambiguous: **every statement of fact in a
story needs to be checked and footnoted to its source.** This file operationalizes
what that means for the skill, so the agent and `scripts/extract_claims.py` agree on
what to extract.

## Sentences that need a footnote

Any sentence that asserts a verifiable claim about the world. Concretely:

### 1. Statistics and numbers
Any cardinal number, percentage, dollar amount, count, age, distance, vote total,
spending figure, or rate.

Examples: "PhRMA spent $42 million on lobbying in 2025."
"58% of Roblox users in 2023 were under 16."
"Three witnesses testified at the hearing."

### 2. Direct quotes
Anything in quotation marks attributed to a person, document, or organization.

Example: She said, "I never authorized that payment."

### 3. Attributed assertions
A claim presented as someone else's statement, opinion, or finding — whether or not
the quote is verbatim.

Examples: "Smith argued that the contracts were never signed."
"GAO found that 63 percent of cases remain unresolved."

### 4. Named facts about identifiable people, organizations, or places
Anyone's title, role, employer, age, residence, criminal record, or relationship to
another named entity.

Examples: "Jane Doe, the company's chief financial officer …"
"Acme Corp, headquartered in Delaware …"
"The Ohio-based firm employs 1,200 workers."

### 5. Dates and historical events
Any concrete date, year, or event reference (when it happened, who was president,
whether something was legal).

Examples: "The bill passed on March 15, 2024."
"Under the 2017 tax law …"

### 6. Causal or sequential claims about events
"X caused Y", "X happened before Y", "Because X, the company did Y."

### 7. Comparative claims
"Larger than", "first to", "most expensive", "more than any other".

Superlatives are especially likely to be wrong — flag them with
`claim_type: comparison_or_superlative` so the reporter sees them flagged.

### 8. Legal, medical, scientific, or technical assertions
Anything where domain expertise determines truth: "is unconstitutional", "is
contraindicated for", "has a half-life of", "violates Section 230".

### 9. Conclusions drawn from original Howard Center reporting
If a sentence synthesizes or summarizes data the Howard Center reporters collected
or analyzed, it still needs a footnote — to a methodology note or workbook, even
when there's no third-party source.

## Sentences that do NOT need a footnote

- **Common knowledge.** "Congress meets in Washington, D.C." "Cars have wheels."
- **Pure narration or transitions.** "Then she left the building."
- **Authorial framing that doesn't make a verifiable claim.** "It was a difficult
  decision." (When the sentence simply sets a scene.) But "It was an unprecedented
  decision" needs a footnote because "unprecedented" is a verifiable comparison.
- **Direct address or rhetorical framing.** "Here's what happened next."

When in doubt: **flag it as needing a footnote.** Over-footnoting can be pruned in
review; under-footnoting risks a correction.

## Sentences that need TWO or more footnotes

Some sentences contain multiple distinct claims:

> "PhRMA spent $42 million on lobbying in 2025, more than triple its 2015 budget."

This sentence asserts:
1. PhRMA's 2025 lobbying spend was $42 million.
2. PhRMA's 2015 lobbying spend was less than ~$14 million (implied by "more than
   triple").
3. The 2025 figure is more than triple the 2015 figure (a comparative claim that
   follows from 1 and 2).

The extraction script should mark this sentence with `multi_claim: true` and list
each sub-claim. Each gets its own footnote.

## The extraction script's behavior

`scripts/extract_claims.py` returns a JSON list. Each entry is shaped like:

```json
{
  "id": "claim_0007",
  "paragraph_index": 3,
  "sentence_index": 1,
  "char_span": [142, 218],
  "sentence_text": "PhRMA spent $42 million on lobbying in 2025.",
  "claim_type": "statistic",
  "distinctive_terms": ["PhRMA", "$42 million", "lobbying", "2025"],
  "multi_claim": false,
  "needs_footnote": true,
  "rationale": "Specific dollar figure attributed to a named organization in a named year."
}
```

`distinctive_terms` is what the matching step uses to scan candidate sources — it
should be the few high-signal terms that would let you locate the supporting
passage in a corpus.

## Operating under uncertainty

When the script can't decide whether a sentence is factual:

- If it contains any number, name, date, or quotation → `needs_footnote: true`.
- If the sentence is narrative and contains no verifiable assertions →
  `needs_footnote: false`.
- Otherwise → `needs_footnote: true` (err on flagging).

The agent loop can then re-classify in step 4 if a flagged sentence turns out to be
genuinely narrative — but the default is to flag.
