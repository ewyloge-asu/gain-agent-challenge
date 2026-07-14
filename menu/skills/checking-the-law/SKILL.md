---
name: checking-the-law
description: Assess whether conduct uncovered in an investigation MAY implicate a specific law — by identifying the governing statute or regulation, reading its actual current text, and applying it element by element to the facts, never guessing from memory. Use whenever an investigation raises a legal question, on any beat or domain — campaign finance, disclosure duties, environmental rules, securities, procurement, privacy, labor, immigration — for any question of the form "is this illegal?", "did they have to report this?", "does this rule apply?". Returns a not-a-violation / possible-violation / genuinely-unclear assessment with the provision quoted and its limits — framed for an editor and a lawyer, never as a final legal conclusion.
---

# Checking the law

A lead often *looks* illegal ("they never reported it!", "she used to work there!") and turns out
to be perfectly legal once you read the actual rule — and occasionally the reverse. This skill
answers one narrow question at a time: **does this specific conduct plausibly violate this
specific law?** — by finding the governing provision, reading its real text, and applying it to
the facts. It is domain-independent: the same method works whether the question is about a
disclosure duty, an environmental permit, an employment rule, or a trading restriction.

**You are not a lawyer and this is not legal advice.** The output is a *reporting assessment* to
tell an editor whether a legal angle is worth a lawyer's review. Its most valuable outcome is
often "no violation — here's why," which *reframes* a lead from "possible crime" to "legal but
newsworthy pattern."

## When to use
An investigation surfaces a legal question that must be settled before the finding can be framed:
is the conduct prohibited, was a filing or disclosure required, does an exemption apply, has a
threshold been crossed. One question per run.

## The method

```
Legal check: <the one specific question>
- [ ] 1. State the question with the specific facts (who, in what role, what conduct, what dates,
         which jurisdiction)
- [ ] 2. Identify the governing law — see references/finding-the-law.md if you don't already
         have the citation (a domain law pack, if one exists for your beat, is a shortcut MAP,
         never the answer)
- [ ] 3. Read the ACTUAL current text of that provision from a Tier-1 primary source
         (references/sources.md); note URL + as-of date
- [ ] 4. Apply it element by element to the facts — including definitions, scope limits,
         thresholds, and exceptions
- [ ] 5. Conclude: not-a-violation / possible-violation / genuinely-unclear — with reasoning
- [ ] 6. State what fact would change the answer, and hand the verdict back verbatim
```

**Step 2 — identify the governing law.** When you don't already know which law governs, follow
[references/finding-the-law.md](references/finding-the-law.md): characterize the conduct and
jurisdiction, find the enforcing body, and search from topic to citation. If your investigation
ships a **domain law pack** (a pre-built map of the laws governing one beat, with their known
scope limits), use it to jump straight to the right provision — this bundle includes one worked
example, [references/packs/us-influence-law.md](references/packs/us-influence-law.md), for the US
lobbying/influence beat, and a second, [references/packs/us-campaign-finance-law.md](references/packs/us-campaign-finance-law.md),
for US campaign finance — two instances of the same format. A pack is a map; the current primary
text is always the answer.

**Step 3 — read the real text.** Never rely on a map, a news story, or memory; statutes have
subsections, definitions, thresholds, exceptions, and amendments.
[references/sources.md](references/sources.md) lists where to read law, tiered by trust — primary
legal text, the enforcing agency's official guidance, nonpartisan analysis, and what to treat as
pointers only. **Read the definitions section first** — most questions turn on a defined term.
Record the source URL and the date you read it: laws change.

**Step 4 — apply element by element.** Most provisions are a list of elements that must ALL hold,
wrapped in scope limits and exceptions. Walk each element against the facts. The scope limits and
exceptions are where "looks illegal" usually dies (a restriction that covers only one office, a
monetary threshold not met, an exemption that applies) — and where "looks fine" occasionally
turns into a real question. For the full dissection craft — decomposing into elements, the
definitions-first rule, thresholds and aggregation, state-of-mind words (why records rarely prove
*willfully*), safe harbors, amendment/effective-date checks, limitations periods, the five layers
of law, reading case law (holding vs. dicta, circuit splits), enforcement reality, and how to
WRITE about legality safely — see
[references/applying-the-law.md](references/applying-the-law.md).

**Worked examples.** Three complete checks in three domains (post-employment scope limits; an
environmental-permit question showing the enforcer's database as the missing element; an
insider-trading question showing the state-of-mind ceiling):
[references/examples.md](references/examples.md).

## Output

Hand this back to the verification workflow exactly:

```
LEGAL CHECK <question>
provision:   <statute/regulation + subsection>   (read at <url>, as-of <date>)
elements:    [ <element> — met? / not met? — why, from the facts ]
scope/limits: <the limit, threshold, or exception that matters here>
verdict:     not-a-violation | possible-violation | genuinely-unclear
reasoning:   <two or three sentences applying the text to the facts>
would-change: <the fact that would flip the verdict>
for-the-panel: <the question a lawyer should confirm, if any>
```

## Guardrails

**Always**
- Read the actual current text before concluding; cite the exact provision and your as-of date.
- Get the operative text from a **Tier 1** primary source ([references/sources.md](references/sources.md));
  use blogs/wikis/watchdog explainers only to find the citation, never as the law itself.
- Apply definitions, scope limits, and exceptions explicitly — that is usually the whole answer.
- Frame the result as an assessment for an editor/lawyer; surface a plausible violation as a
  *question for review*, never as your verdict.
- Prefer "not-a-violation, here's why" when the law clearly doesn't reach the facts — and let that
  reframe the finding to a legal-but-newsworthy pattern.

**Never**
- Answer from memory of "what the law probably says," or from a map/pack alone.
- State "X violated the law" as a conclusion — the strongest you assert is *possible*, for a lawyer.
- Confuse *unethical or newsworthy* with *illegal*; a legal pattern can still be a strong story.
- Claim or imply that anyone was contacted for comment. During analysis, no outreach has
  happened — never write "did not respond to a request for comment" or similar. When
  suggesting publishable framing, the correct instruction is: *the reporter should seek
  comment from every named party before publication, and a lawyer should review before
  publishing any quid-pro-quo implication.*
- Let a stale or repealed provision stand — check currency and effective dates.

## Building a law pack for your beat
If your investigation will raise the same family of legal questions repeatedly, spend an hour
building a domain pack: for each recurring question, record the governing provision, its key
defined terms, its scope limits/exceptions, the enforcing body and where its official guidance
lives, and the beat's known traps (stale indexed figures, entity-type ambiguities,
state-vs-federal splits). Keep it as a reference file next to this skill — the two included packs
(US influence; US campaign finance) show the format at two different scopes. The pack pays for
itself the second time a legal question comes up — but it never replaces reading the current text.

## Related skills
- **investigative-method** — calls this skill at its legal-question step and carries the verdict.
- A **beat skill** (in this bundle: lobbying-beat) — recognizes the patterns that raise legal
  questions and names the first innocent explanation before the law is even consulted.
