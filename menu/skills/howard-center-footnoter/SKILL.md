---
name: howard-center-footnoter
description: The Howard Center Footnoter — audit existing footnotes and generate new ones for a draft article in the Howard Center for Investigative Journalism's footnoting style. Inserts new footnotes and footnote-body upgrades into a Word document as tracked changes, and surfaces concerns (no source found, possible out-of-context quoting, existing footnote that doesn't support the claim) as Word margin comments. Use when the user has a draft article (.docx) and reporting materials and asks for "footnoting", "fact-check footnotes", "Howard Center style citations", or to audit existing footnotes against the standard. Works best when the user provides both the draft and a folder of source materials (PDFs, transcripts, URL list); the skill can also do limited web research as a fallback.
---

# The Howard Center Footnoter

A footnoting skill built around the standards of the Howard Center for
Investigative Journalism at Arizona State University.

The skill does three jobs on an investigative draft:

1. **Audits any existing footnotes** in the draft against the Howard Center
   standard and proposes improvements as tracked changes.
2. **Adds new footnotes** to factual claims that aren't yet sourced, also as
   tracked changes.
3. **Flags concerns as Word margin comments** when a claim has no support
   anywhere, when the matched source's full context suggests the quote may be
   used misleadingly, or when an existing footnote doesn't actually support
   the claim it's attached to.

Tracked changes are for proposed *edits*. Comments are for *concerns* that
need a human judgment. Both go into the same output .docx so reporters,
editors, fact-checkers, and lawyers can review everything in one pass.

## Why Howard Center–style footnoting matters

Footnoting isn't a bibliography exercise. In an investigative newsroom, a good
footnote is a tool that:

**Catches problems in real time, for the reporter.** Most reporters who carefully
footnote their own work catch their own mistakes in the process. You go to write
"the company laid off 800 employees in 2024" and reach for your source — and
notice the press release actually said *"up to 800"*. Or the article you cited
turns out to support a related-but-different claim. The discipline of pulling a
verbatim quote into a footnote forces you to confront the exact words the source
used. That's a quality-control loop that happens before the story leaves your
desk, not after.

**Speeds up fact-check, legal, and editor review.** A fact-checker who can
verify a claim by reading the footnote alone — without clicking through and
hunting around in a 200-page PDF — can clear ten times as many claims per hour.
A lawyer doing pre-publication review can see in one glance whether a claim is
grounded in a primary source or a third-party characterization. An editor can
spot a paraphrase masquerading as a quote, or a quote pulled out of context,
without re-reporting the story. Good footnotes turn a slow, expensive process
into a fast one.

**Protects against out-of-context quotes.** This is why the skill insists every
footnote include the supporting passage **plus a sentence or two of surrounding
context from the source**, not just the literal quoted words. A line like
*"I never authorized that payment"* could be honest or it could be a setup —
the *next* line of the transcript might be *"…until after the board signed off."*
The footnote should make the surrounding context visible so the reviewer can
judge whether the quote is being used fairly.

**Creates a paper trail an editor or lawyer can audit later.** When a
correction request lands six months after publication, a story whose every
factual claim is footnoted to a primary source can be defended (or corrected)
in an afternoon. A story without that paper trail can't.

## How to use this skill

Give the agent **both** of these:

1. **The draft article** as a `.docx` file. If the draft already has some
   footnotes, leave them in — the skill will audit them.
2. **All of your reporting materials**, organized in a folder:
   - PDFs of documents (court filings, reports, press releases, saved web pages)
   - Plain-text or markdown reporting notes (.txt, .md)
   - Interview transcripts (`.vtt`, `.srt`, or saved `.txt` from Trint/Otter)
   - A `urls.txt` file with one URL per line for sources that live on the web
   - Other `.docx` files (e.g. saved emails, internal memos)

Then ask the skill to footnote your draft. It will:

1. **Read your existing footnotes** and judge each one against the Howard
   Center standard. If a footnote is missing a quote, missing a date, links to
   the wrong page of a PDF, doesn't include surrounding context, or doesn't
   actually support the claim it's attached to, the skill proposes a
   replacement.
2. **Identify factual claims that aren't yet footnoted** — statistics, direct
   quotes, attributed assertions, named facts about people and organizations,
   dates, superlatives, conclusions drawn from your reporting.
3. **Match each unsourced claim to your reporting materials.** If the folder
   doesn't cover a claim, the skill will (with your permission) do limited
   web research to find a primary source.
4. **Write a new Howard-Center-format footnote** for each match, with the
   supporting passage plus surrounding context.
5. **Insert footnotes as tracked changes** so you, your editor, and your
   fact-checker can review every proposed edit.
6. **Flag concerns as Word margin comments** when something can't be
   resolved by adding a footnote — see the three flag types below.
7. **Report a short summary** in chat, surfacing the most uncertain matches
   and any claims it couldn't find a source for.

### Three things that become margin comments instead of footnotes

A footnote means "here's the source." A comment means "human, look at this."
Use comments — not footnotes — for these three situations:

- **`no_source`** — Nothing in the reporting folder *or* on the web supports
  the claim. The footnote would just say ⟨NEEDS SOURCE⟩ anyway; a margin
  comment is more visible to the editor and clearer about what's needed.
  Message should say what was searched and what wasn't found.
- **`context_concern`** — A source exists, but reading the full surrounding
  passage suggests the quote may misrepresent what the source actually meant.
  The footnote can still go in (so the reporter sees the source), but a
  comment flags the concern so the reporter can decide whether to soften the
  framing, add caveats, or re-report. Message should quote the broader
  context and explain the concern.
- **`existing_footnote_flag`** — An existing footnote points to a real
  source, but that source doesn't actually support the claim it's attached
  to (e.g., the link goes to a press release that discusses a related topic
  but doesn't contain the specific number cited). Don't auto-replace —
  flag for human judgment.

For claims with no source at all, the skill *also* inserts a tracked-change
`⟨NEEDS SOURCE⟩` placeholder in the footnote position, so the gap is visible
both in the margin and at the bottom of the page. The skill never fabricates
a source.

### Source quality: always go primary first

When the skill searches the web for a missing source, it follows a strict
priority: **primary sources first, authoritative secondary only when primary
isn't available, and certain kinds of sites are never acceptable as a footnote
endpoint at all.**

- **Primary** — the entity making the claim, or the official record of the
  event: a `*.gov`, `*.mil`, or `*.gov.uk` page, an SEC filing on EDGAR, a
  court docket on PACER or CourtListener, the company's own press release on
  its own domain, the originating researcher's published paper, the
  interviewee's own statement.
- **Authoritative secondary** — established newsrooms and research institutes
  reporting on a primary source: Reuters, AP, the New York Times, ProPublica,
  Brookings, Pew, etc. Used only when primary isn't available; the footnote
  names the secondary source explicitly ("as reported by Reuters"), and
  confidence is capped at medium.
- **Unacceptable as a footnote endpoint** — Wikipedia, AI-generated overviews,
  PR-distribution wires (PR Newswire, BusinessWire) when the issuer's own page
  exists, Medium and Substack posts where the author isn't the named source,
  content farms, news aggregators. These can be *discovery tools* (Wikipedia's
  citations can lead you to a primary source) but the footnote cannot end
  there. If the only thing the skill can find is Tier 3, that's a
  `no_source` flag, not a footnote.

The detailed taxonomy, per-claim-type examples, decision tree, and domain
patterns live in
[references/primary_source_priority.md](references/primary_source_priority.md).
Read that file before doing web research.

The script `scripts/check_source_tier.py` classifies a URL by domain pattern
and is the fastest first-pass filter on a candidate URL:

```bash
python scripts/check_source_tier.py "https://www.gao.gov/products/gao-25-107523"
# → tier: "primary", rationale: "Government Accountability Office"
```

## When to trigger this skill

Trigger when the user:

- Hands you a draft .docx (with or without existing footnotes) and asks for
  footnotes, fact-check citations, or "Howard Center footnotes".
- Asks you to audit, review, or upgrade existing footnotes against a standard.
- Hands you a draft plus a folder of sources and asks you to "footnote it".
- Asks for citations formatted in the Howard Center's investigative-journalism
  style.

Do **not** trigger this skill for academic citation styles (APA, MLA, Chicago),
general bibliography work, or simple inline web citations like `[1]`. Those are
different from the Howard Center protocol, which is designed so a fact-checker,
lawyer, or editor can verify a claim on first click without leaving the footnote.

## What a Howard Center footnote must include

Every footnote must include:

1. **The source** (document title, publication, agency name, report number,
   interviewee, transcript URL, etc.).
2. **A first-click-accessible hyperlink** — no logins, no paywalls.
3. **The date** (published, sent, captured, recorded, interviewed). Use the
   most specific date available.
4. **A position cue** — page number plus a paragraph descriptor (`"p. 2, top
   graf"`, `"p. 9, middle of 3rd graf"`) for documents, or a timecode
   (`T/C 00:12:47`) for audio.
5. **The supporting passage, with surrounding context**, in quotation marks.
   Not just the words the story quotes — the sentence before and the sentence
   after as well, so a reviewer can see the quote in context. If the claim
   draws on a number from a chart, replace the quote with a tight description
   of how to read the chart and the arithmetic.

The exhaustive reference for the format — including verbatim examples from
real Howard Center stories — is in
[references/footnote_format.md](references/footnote_format.md). Read that file
before producing footnotes if you have any doubt about the format.

## Detailed workflow

For each invocation, do the following **in order**:

### Step 1 — Confirm inputs

Identify the draft file (`.docx` path) and the sources folder. If the user
supplied only a draft, ask whether they want the skill to attempt web research
for missing sources, or to mark uncited claims for the reporter to handle.

### Step 2 — Audit existing footnotes

Run `scripts/extract_existing_footnotes.py <draft.docx>`. The script returns
a JSON list of every existing footnote in the draft, each with:
- The footnote's internal Word ID
- The paragraph it's attached to and the sentence around the reference
- The current body text of the footnote

For each existing footnote, judge it against the standard (the six required
components above). Mark it as:
- `keep` — meets the standard.
- `improve` — needs a fixed quote, added context, a missing date, a corrected
  link, or other content additions. Generate the replacement text.
- `replace` — wrong source entirely. Generate a new footnote text from a
  better source.
- `flag` — points to a source that doesn't actually support the claim it's
  attached to. Don't auto-replace; surface it to the reporter.

Record decisions in an `upgrades.json` file (see schema below).

### Step 3 — Extract claims from the draft

Run `scripts/extract_claims.py <draft.docx>`. It returns a JSON list of
factual claims that need footnotes. The script also notes which claims
**already have an existing footnote attached** (so you don't double-footnote
them). See
[references/claim_extraction_rules.md](references/claim_extraction_rules.md)
for what counts.

### Step 4 — Ingest the sources folder

Run `scripts/ingest_sources.py <sources_dir>`. It walks the folder, extracts
text with positional metadata (page numbers for PDFs, timecodes for
transcripts, paragraph numbers for text), and emits a JSON index.

### Step 5 — Match each unsourced claim to a source

For each claim from step 3 that doesn't already have a satisfactory existing
footnote, do the matching yourself with semantic judgment (not a script):

1. Read the claim sentence.
2. Read the candidate segments from the source index that contain the claim's
   distinctive terms (names, numbers, dates, agencies).
3. Pick the single best-supporting segment, or mark `match_status:
   "no_source"` if nothing in the folder supports it.
4. **Always capture surrounding context, not just the literal quote.** Pull
   the sentence before and the sentence after the supporting line, when
   they exist in the same segment. The combined `context_quote` is what goes
   in the footnote.
5. If `no_source` and the user authorized web research, do this:
   a. Use `WebSearch` to look for a **primary** source first. Read
      [references/primary_source_priority.md](references/primary_source_priority.md)
      if you're not sure what counts as primary.
   b. For each candidate URL, classify its tier with
      `python scripts/check_source_tier.py <URL>`.
   c. **Prefer `tier: "primary"`. Only fall back to
      `tier: "authoritative_secondary"` after a real attempt to find a
      primary source has failed** — meaning you've searched the entity's own
      site, the relevant `.gov`, and the obvious primary databases for that
      claim type.
   d. Reject any candidate whose tier is `"unacceptable"`. A Wikipedia page,
      a PR Newswire repost, or an AI Overview cannot be a footnote endpoint;
      use them as discovery tools to reach the primary, then cite the primary.
   e. If the classifier returns `tier: "unknown"`, fetch the page with
      `mcp__workspace__web_fetch`, identify the publisher, and classify by
      hand using the rubric in `references/primary_source_priority.md`.
   f. Once you have a viable candidate, **fetch the URL and confirm the
      supporting passage exists verbatim in the page** before recording the
      match. Never cite a URL you haven't read.
6. Record each match as `{claim_id, source_id, segment_id, supporting_quote,
   context_quote, source_tier, confidence}`:
   - `source_tier`: `"primary"` | `"authoritative_secondary"` | `null` (for
     folder-only sources where tier isn't meaningful).
   - `confidence`: `"high"` only if the source is `primary` AND the quote is
     verbatim. `"medium"` if either condition is missing. `"low"` if the
     source supports a related-but-not-identical claim or you had to
     paraphrase.

### Step 6 — Format every footnote (new and upgraded)

Run `scripts/format_footnote.py --matches matches.json --sources sources.json
--out footnotes.json`. The script renders each match into a Howard-Center-
format footnote string using the templates in
[references/source_type_templates.md](references/source_type_templates.md).
For low-confidence or no-source claims, the rendered text is a placeholder
`⟨NEEDS SOURCE: <description>⟩`.

For upgrades from step 2, build a parallel `upgrades.json` whose
`improved_footnote` and `improved_url` fields hold the agent's proposed
replacement text and URL.

### Step 7 — Decide which claims warrant a Word comment

Walk the matches from step 5 and the upgrades from step 2. For each one, ask:

- **No source anywhere?** Emit a flag with `flag_type: "no_source"`. Message
  should describe what you searched and why nothing was found.
- **Source exists but its broader context conflicts with how the story uses
  it?** Emit a flag with `flag_type: "context_concern"`. Message should
  quote the broader passage and explain the concern.
- **Existing footnote points to the wrong source?** Set the upgrade action
  to `"flag"` (not `"improve"` or `"replace"`) and provide a `reason`. The
  insert script will attach a comment automatically.

Record the standalone flags in a `flags.json`:

```json
{
  "flags": [
    {
      "claim_id": "claim_0006",
      "paragraph_index": 3,
      "flag_type": "no_source",
      "message": "Searched the reporting folder and web for 'largest fee hike in recent ASU history' — no source supports the comparison. Reporter should attribute or remove."
    },
    {
      "claim_id": "claim_0012",
      "flag_type": "context_concern",
      "message": "The quoted sentence is supported, but the next sentence in the source reverses the position: '…until the board reviewed the auditor's recommendation, after which the policy was reinstated.' Suggest reframing or quoting more fully."
    }
  ]
}
```

### Step 8 — Insert footnotes, upgrades, and comments into the draft

```bash
python scripts/insert_tracked_footnotes.py \
    --draft draft.docx \
    --claims claims.json \
    --footnotes footnotes.json \
    --upgrades upgrades.json \
    --flags flags.json \
    --out draft_footnoted.docx \
    --author "Claude"
```

The script:
- **Adds new footnotes** at the end of each footnoted sentence, with the
  reference number wrapped in a `<w:ins>` tracked-change element.
- **Upgrades existing footnotes** by wrapping the old body in `<w:del>` and
  the new body in `<w:ins>`. Track Changes view shows the old text struck
  through and the new text underlined — accept or reject one at a time.
- **Attaches Word comments** to paragraphs for every flag. Comments appear
  in Word's margin, prefixed with the flag type (`[No source found]`,
  `[Possible out-of-context quoting]`, `[Existing footnote may not support
  the claim]`) so editors can scan them at a glance.

### Step 9 — Report a summary

Print a short table:
- Existing footnotes audited (kept / improved / replaced / flagged)
- New footnotes inserted by confidence (high / medium / low)
- Margin comments attached, by flag type
- The output `.docx` path

Also surface the **3 most uncertain edits** by quoting the claim alongside the
matched supporting text, so the user can spot-check before opening the file.

## Calling the scripts efficiently

Each script does deterministic heavy lifting (PDF parsing, .docx XML
manipulation, tracked-change wrapping). The agent reserves its reasoning for
the steps only an agent can do well: judging existing footnotes against the
standard, and matching claims to source segments. Don't re-do work the
scripts already did by reading PDFs or .docx files yourself.

## Web research fallback

When a claim has no folder source and the user authorized web research, follow
the full primary-source priority workflow described in Step 5 above:

1. Search with terms derived from the claim's distinctive nouns and numbers,
   biasing the search toward the entity's own site (`site:agencyname.gov`,
   `site:sec.gov`, `site:courtlistener.com`, etc.) before general queries.
2. Classify every candidate URL with `scripts/check_source_tier.py` and the
   rubric in [references/primary_source_priority.md](references/primary_source_priority.md).
3. Pick the highest-tier candidate that actually contains the supporting
   passage. **Primary beats secondary; secondary beats unknown; unacceptable
   is never used.**
4. Fetch the candidate URL with `mcp__workspace__web_fetch` and confirm the
   supporting passage is in the page before recording the match. Don't cite
   a page you haven't read.
5. Remind the reporter in the summary to save the URL to the Wayback Machine.
6. Set `source_tier` on the match. `confidence: "high"` is only valid for
   `primary` sources with verbatim quotes; `authoritative_secondary` caps at
   `medium`.

If nothing of Tier 1 or Tier 2 quality covers the claim, emit a `no_source`
flag. A bad source is worse than no source — the reporter needs to know.

## When to read the reference files

- **First time using this skill in a session**, read
  [references/footnote_format.md](references/footnote_format.md) to
  internalize the format.
- **Before any web research**, read
  [references/primary_source_priority.md](references/primary_source_priority.md)
  so you know which sources to prefer and which to reject.
- **When formatting an unusual source type** (court filing, Trint transcript,
  tweet), read
  [references/source_type_templates.md](references/source_type_templates.md).
- **When deciding whether a sentence needs a footnote**, read
  [references/claim_extraction_rules.md](references/claim_extraction_rules.md).

## Schemas

### matches.json (the agent's output between steps 5 and 6)

```json
{
  "matches": [
    {
      "claim_id": "claim_0002",
      "claim_sentence": "...",
      "source_id": "src_0003",
      "segment_id": "src_0003_p002_g01",
      "supporting_quote": "the literal sentence that supports the claim",
      "context_quote": "the sentence before. THE LITERAL SUPPORTING SENTENCE. The sentence after.",
      "source_tier": "primary",
      "url_override": null,
      "confidence": "high"
    }
  ]
}
```

If `context_quote` is empty, `format_footnote.py` falls back to
`supporting_quote`. Always include `context_quote` when possible.

`source_tier` is required for any match where the source came from web
research; it can be omitted for folder-only sources where the reporter has
already vetted the material. Web-found matches with `source_tier:
"authoritative_secondary"` should also include a brief note in the footnote
text identifying the secondary outlet ("as reported by Reuters").

### flags.json (the agent's output for step 7)

```json
{
  "flags": [
    {
      "claim_id": "claim_0006",
      "paragraph_index": 3,
      "flag_type": "no_source" | "context_concern",
      "message": "Human-readable explanation that will appear in the margin."
    }
  ]
}
```

`paragraph_index` is optional — the script will look it up from `claims.json`
via `claim_id` if not provided.

### upgrades.json (the agent's output for step 2)

```json
{
  "upgrades": [
    {
      "footnote_id": "3",
      "action": "improve",
      "reason": "Missing date and surrounding context.",
      "improved_footnote": "Full replacement footnote text in Howard Center format",
      "improved_url": "https://..."
    },
    {
      "footnote_id": "5",
      "action": "keep",
      "reason": "Meets standard."
    },
    {
      "footnote_id": "7",
      "action": "flag",
      "reason": "Source doesn't actually support the claim about FY24 spending.",
      "improved_footnote": null,
      "improved_url": null
    }
  ]
}
```

## What this skill does not do

- It does not run the broader Howard Center accuracy checklist (backgrounding
  sources, collecting contact info for everyone named, verifying quotes
  against audio recordings, AP-style acronym checks). Those are separate
  fact-check tasks for a different skill.
- It does not propose in-copy attribution rewrites ("According to the police
  report, …"). Editors handle that.
- It does not edit the draft's prose. Footnote insertions and upgrades are
  the only edits, all wrapped as tracked changes.
- It does not commit to a finding's truth. Confidence labels, "needs source"
  placeholders, and "flag" upgrades are how it surfaces uncertainty to the
  reporter.

## Output expectations

The skill always produces:

1. A new `.docx` with footnote references and footnote-body upgrades inserted
   as tracked changes.
2. A short summary report in chat (counts by action, the most uncertain
   edits).
3. (Optional, on request) A JSON sidecar of the audit and match decisions for
   human audit.
