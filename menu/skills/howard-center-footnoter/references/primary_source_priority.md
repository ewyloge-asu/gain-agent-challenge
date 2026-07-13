# Primary-source priority — reference

This file is the authoritative rule for which source to pick when more than one
candidate could support a claim. It applies most heavily during web research
(when you're searching outside the reporter's folder), but the same priority
should be used to break ties inside the folder too.

The rule is simple: **always cite the closest source to the underlying fact**.
A government inspector general report is closer than a news article about that
report. The interviewee is closer than someone summarizing the interview.
The court filing is closer than a press release about the filing.

## The three tiers

### Tier 1 — Primary source. Prefer first, always.

A document, recording, or statement created by the entity or person making the
claim, or the official record of an event. Examples by claim type:

| Claim type | Primary source |
|---|---|
| A government action, finding, ruling, contract, audit | The agency's own report, register, docket, or press release; the GAO, CRS, or IG document; an SEC EDGAR filing |
| A court ruling, complaint, motion, or sentence | The filing itself on PACER, CourtListener, or the court's official docket |
| A company's financials, headcount, or product claim | The company's 10-K/10-Q/proxy on EDGAR; the official press release; the corporate website |
| A bill, law, or amendment | Congress.gov, state legislature site, the bill text itself, the official roll-call vote |
| A statistical claim from a study | The published study (peer-reviewed paper, BLS / Census / CDC dataset, the IPUMS extract). Cite the table or page, not a journalist's paraphrase |
| A quote from a named person | The transcript, recording, or the person's own statement on their own channel (official social account, op-ed they wrote, interview they gave) |
| A regulatory rule | The Federal Register notice, the rule text, the agency's rulemaking docket |
| A police or incident report | The report itself, obtained via records request, with redactions noted |
| A foreign-government action | The originating government's own document (translated), an international body's primary record (UN, IMF, IAEA) |
| A historical event | A primary contemporary document (memo, telegram, archive scan), a verified database (national archives), or the official record |

### Tier 2 — Authoritative secondary source. Use only when no Tier-1 is available, and flag if used.

A reputable third party reporting on or summarizing a Tier-1 source, where the
third party adds editorial judgment or verification. Examples:

- An established newsroom's reporting on a court filing (when the filing isn't
  publicly available for free) — Reuters, AP, the New York Times, the Wall
  Street Journal, the Washington Post, ProPublica, the major regional papers.
- A think-tank or research-institute analysis citing primary data (Brookings,
  Pew, RAND, Urban Institute, AEI, CBPP) — cite the institute's report, not
  the press release about it.
- A trade publication with a track record on a specialized beat (Inside Health
  Policy, Politico Pro, Defense News) when reporting events not yet on the
  primary source's site.
- A reputable wire service summary.

When you use Tier 2, **say so in the footnote**: "as reported by Reuters,"
"per AP," etc. And mark the match `source_tier: "authoritative_secondary"` so
the editor sees it. Confidence cannot be `high` for a Tier-2 source.

### Tier 3 — Unacceptable. Reject; do not footnote here.

These cannot be the endpoint of a Howard Center footnote. They can be used as
*discovery tools* (a Wikipedia article whose footnotes lead you to the real
source is fine), but the footnote itself must cite the primary source that the
Tier-3 page led you to.

- Wikipedia, Wiktionary, any wiki
- AI chatbots, AI-generated overviews, LLM-search results, "AI Overview" cards
- Content farms, listicle sites, SEO sites
- Personal blogs and Substacks (unless the blog *is* the primary source — e.g.
  the person being quoted runs that blog)
- Social media as the sole source for a factual claim (unless the social-media
  post itself is the fact you're attributing — then it's Tier 1, but always
  with a Wayback archive URL alongside)
- Aggregators that strip attribution (Google Snippets, News.com.au syndications,
  etc.)
- Press-release distribution sites (PR Newswire, Business Wire) when the
  original is on the issuer's own website — go to the issuer
- Anything where the actual author or publisher cannot be identified

If the only source you can find for a claim is Tier 3, that's a **no_source**
flag. Do not footnote.

## Decision tree for web research

When the reporter's folder doesn't cover a claim and the user authorized web
research, walk this tree:

1. **Identify the underlying fact.** What is the actual thing being claimed?
   Who or what is the closest entity to that fact?
2. **Search directly for that entity's own record.** Use `site:agencyname.gov`,
   `site:sec.gov`, `courtlistener.com`, `congress.gov` searches; the agency's
   own press-release search; the company's investor-relations page.
3. **If you find a Tier-1 candidate, fetch the URL with
   `mcp__workspace__web_fetch` and confirm the supporting passage exists
   verbatim before recording the match.** If it doesn't, the candidate is
   wrong — don't cite it.
4. **If Tier 1 is genuinely unavailable**, look for a Tier-2 source. Same
   verification step — fetch and confirm the passage exists. Mark
   `source_tier: "authoritative_secondary"`, cap confidence at `medium`,
   include the wire/newsroom name in the footnote.
5. **If only Tier 3 is available**, emit a `no_source` flag with a message
   like: "Couldn't find a primary source. The closest match is
   en.wikipedia.org/..., which is Tier 3 and cannot be a footnote endpoint.
   Reporter should follow Wikipedia's cited references to the primary."

## Domain patterns the agent should recognize

These shortcuts let you classify a URL quickly. The helper
`scripts/check_source_tier.py` formalizes them.

**Tier 1 patterns** (high-confidence primary):
- `*.gov`, `*.mil` — U.S. federal/state agencies, military
- `*.gc.ca`, `*.gov.uk`, `*.europa.eu`, other country government TLDs
- `sec.gov/cgi-bin/browse-edgar`, `*.sec.gov` (SEC EDGAR)
- `congress.gov`, `*.senate.gov`, `*.house.gov`
- `courtlistener.com`, `pacer.uscourts.gov`, `supremecourt.gov`
- `federalregister.gov`
- `bls.gov`, `census.gov`, `cdc.gov`, `nih.gov`, `usgs.gov`
- `imf.org`, `worldbank.org`, `un.org`, `oecd.org`, `who.int`, `iaea.org`
- A company's *own* domain (`*.companyname.com`) for press releases or
  filings — but verify it's their official IR/press page

**Tier 2 patterns** (authoritative secondary):
- `reuters.com`, `apnews.com`, `nytimes.com`, `washingtonpost.com`,
  `wsj.com`, `bloomberg.com`, `propublica.org`, `ft.com`
- `brookings.edu`, `pewresearch.org`, `rand.org`, `urban.org`, `cbpp.org`,
  `kff.org`
- Major regional dailies (Boston Globe, LA Times, Chicago Tribune, Star
  Tribune, Atlanta Journal-Constitution, etc.)
- Established trade press (`politico.com/pro`, `defensenews.com`, etc.)
- Scientific journals (`nature.com`, `science.org`, `nejm.org`, etc.)

**Tier 3 patterns** (unacceptable):
- `wikipedia.org`, `wiktionary.org`, anything ending in `.wiki`
- `medium.com` (unless the author is the named source)
- `substack.com` (same)
- Personal blogs (single-author, no editorial process)
- AI-generated content (any URL that's an AI Overview or search-generated
  summary)
- Press-release distributors (`prnewswire.com`, `businesswire.com`,
  `globenewswire.com`) when the issuer's own site has the same release
- Content aggregators (`news.google.com` cards, `news.yahoo.com` reposts)
- Anything where you can't identify a named author or publisher

## When the rule conflicts with itself

Edge case: a wire-service story is the *only* contemporaneous record of an
event because the primary source is paywalled or has since taken the page
down. Use the wire story but:
- Add a Wayback Machine archive URL of the primary source if any version still
  exists in the archive.
- Mention in the footnote that the primary was taken down: "Issuer's press
  release archived at web.archive.org/..., no longer available on issuer's
  site."

This isn't a workaround; it's the right thing because the wire is then your
best available record of an event that *did* have a primary source.

## Quick gut checks

Before recording a match, ask:

- Could I get this fact from a `*.gov`, `*.edu`, or the entity's own website? If
  yes, search there first.
- Is the URL I'm about to cite the original publisher of this fact, or someone
  reporting on it? If reporting-on, can I go upstream?
- Would the entity being written about recognize this URL as theirs? If no, am
  I sure it's the most authoritative version?

If any of those flags a concern, escalate the search before recording.
