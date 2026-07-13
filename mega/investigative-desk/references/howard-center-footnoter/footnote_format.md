# Howard Center footnote format — reference

This file gives you the canonical format for Howard Center footnotes, drawn directly
from the Howard Center's own footnoting guides. Read this file when producing
footnotes if you have any doubt about format.

## The five required components

Every footnote must include:

1. **Source identity** — name of the document, publication, agency, report number,
   interviewee, or transcript. Be specific enough that a fact-checker can locate the
   source independently of the hyperlink.
2. **First-click-accessible hyperlink** — a URL the reader can open without logging in
   or requesting access. For PDFs, prefer a link that jumps to the relevant page or
   anchor comment (the "Link to this comment" trick in PDF readers).
3. **Date** — published, sent, captured, or recorded. Use the most specific date
   available (`3/27/26` for a news article, `June 2021` for a GAO report,
   `April 25, 2025` for a court filing).
4. **Position cue (for documents)** — page number plus a position descriptor
   ("top graf", "middle of 3rd graf", "By Age graphic"). For audio or transcripts, a
   **timecode** (`T/C 00:12:47` or `[00:13:00]`).
5. **Verbatim supporting passage with surrounding context** — the actual words from
   the source that support the claim, enclosed in quotation marks, *plus a sentence
   or two of surrounding context from the source*. The story might quote three
   words, but the footnote should quote those three words plus what came before and
   after them in the source. This protects against out-of-context quoting and lets
   a fact-checker, editor, or lawyer judge fair use without re-reporting the story.
   For a number drawn from a chart, replace the quote with a tight description of
   where in the chart the number comes from and the arithmetic you used (e.g.
   "Under 9yo 21%; 9-12yo 21%; 13-16yo 16% = 58% are under 16.").

## Three style principles

- **Precise.** The quoted passage must directly support the claim. Don't include a
  quote that "kind of" relates — find the actual supporting line.
- **Concise.** As short as it can be while staying accurate. Don't dump three
  paragraphs when one sentence does the job.
- **Easy to read.** Hyperlink key words, not raw URLs. A reader scanning the footnote
  shouldn't have to wade through a 200-character URL string.

## Format-neutral structure

Don't worry about a particular bibliography style or about the ordering of the link
vs. the quote vs. the date. Focus on: clear source, working link, exact relevant
quote.

A working template, in plain prose:

> `<source title or description>` `<date>` `<page/position cue>`: "`<verbatim
> supporting quote>`" [hyperlink on key words]

Some footnotes won't need every element (e.g. an interview won't have a page
number). Some will need extras (e.g. an arithmetic note for a chart). Use judgment.

## Canonical examples (verbatim from the Howard Center guide)

### A government report (GAO)

> GAO-21-385, Sex Trafficking: Online Platforms and Federal Prosecutions, June 2021,
> p. 2 of PDF, top graf: "Two events in April 2018 disrupted the landscape of the
> online commercial sex market. First, federal authorities seized the largest online
> platform for buying and selling commercial sex, backpage.com. Second, the Allow
> States and Victims to Fight Online Sex Trafficking Act of 2017 (FOSTA) was
> enacted. These events led many who controlled platforms in this market to
> relocate their platforms overseas. Additionally, with backpage.com no longer in
> the market, buyers and sellers moved to other online platforms, and the market
> became fragmented."

Pattern: `<report number>, <title>, <month year>, p. <n> of PDF, <position cue>:
"<quote>"`.

### A police / incident report

> Incident Report V20070196 See page 9 of the PDF, middle of 3rd graf: "While in
> the lobby I observed what appeared to be bruising and other markings on her legs.
> I asked her how she got bruises on her legs and she stated that they were not
> bruises. told me that they're burn marks and that her 'pimp' did it to her. She
> immediately corrected herself and stated that her 'ex-pimp' would beat her up."

Pattern: `<report ID> See page <n> of the PDF, <position cue>: "<quote>"`.

### A chart or graphic with arithmetic

> Roblox Corporation 2024 Proxy Statement and 2023 Annual Report p. 105, "By Age"
> graphic: Age of users in 2023: Under 9yo 21%; 9-12yo 21%; 13-16yo 16% = 58% are
> under 16.

Pattern: `<document title> p. <n>, <graphic name>: <reading-of-the-chart>
[= arithmetic shown explicitly]`.

### A transcript (Trint / Otter)

> https://app.trint.com/public/7f99a8bc-6ae5-47ad-9c6f-a5375d6225c T/C 00:12:47:
> "But really the biggest thing is, is, is parental awareness and education to the
> kids and just understanding that this is a real problem. And, you know, the
> easiest way to to never run into that situation is prevention in the first place.
> [00:13:00][13.8]"

Pattern: `<transcript URL> T/C <hh:mm:ss>: "<verbatim, with internal timecodes
preserved if they were in the transcript>"`.

### A news article

> State Press article from 3/27/26. "ASU's budget proposal encapsulates academic
> fee proposals not previously approved by the board, new program and college fees,
> changes to existing fees and increases to tuition and fees greater than the
> maximum tuition range set by the board, according to the committee book for the
> meeting. [...] The proposal is for 25 new graduate program fees and two
> increases to graduate program fees. Also included is a new annual undergraduate
> and graduate provost advanced technology fee of $200, which, according to the
> committee book for the meeting, is 'to provide students access to artificial
> intelligence tools and platforms and other technologies.'"

Pattern: `<publication> article from <date>. "<quote, with [...] for elisions>"`.

## A note on quote context

When the story includes a direct quote from an interview or a document, the
footnote should NOT just quote the words that appear in the story. It should
quote the surrounding exchange. For example, if the story says:

> She told investigators, "I never authorized that payment."

The footnote should be something like:

> Interview with Jane Doe, CFO of Acme Corp, conducted by Howard Center reporter
> J. Smith on March 5, 2026, recording at <path>, T/C 14:18-14:42: "INVESTIGATOR:
> When the auditor asked you about the wire transfer, what did you say to her?
> DOE: I never authorized that payment. INVESTIGATOR: But the paperwork has your
> signature on it. DOE: Like I said, I never authorized it."

The extra context lets a fact-checker, editor, or lawyer see what the quoted
words mean *in their actual setting*. A quote that sounds damning in isolation
may turn out to be neutral or even exculpatory in context. A footnote that hides
the context — by quoting only the words the story uses — gives a false sense of
verification.

This applies to written sources too. If the story quotes a sentence from a court
filing, the footnote should quote the sentence plus a clause or two on either
side, so the reviewer can see how the supporting language relates to the rest
of the filing.

## How to handle special cases

### When the supporting passage is long
Use `[...]` to elide the middle while preserving the load-bearing endpoints. Don't
elide so aggressively that the quote loses its grounding.

### When the source is a database query or original analysis
Cite the database, the date of the query, and the parameters. If the analysis was
performed by the reporter, footnote it as such:

> Analysis by Howard Center reporter <Name> of Senate LDA quarterly filings,
> 2022–2025, downloaded from https://lda.senate.gov/api/v1/filings/ on <date>.
> Query: filings where `lobbying_activities[].general_issue_code == 'HCR'` AND
> `client.name` contains 'PHRMA'. Result: 47 filings totaling $42.16M in reported
> income. Workbook saved at <path or URL>.

### When the source is a person (interview)
Identify the interviewee, the interviewer (if not the bylined reporter), the date,
and either a transcript URL with timecode or the location of the recording. If the
quote is paraphrased rather than verbatim, mark it as such:

> Interview with <Name>, <title/affiliation>, by <reporter> on <date>. Trint:
> <URL> T/C <timecode>: "<verbatim quote>".

### When the source is a tweet or social-media post
Capture the URL **and** an archived version (Wayback). The original may disappear.

> @username on X (formerly Twitter), <date>, https://x.com/... — archived
> https://web.archive.org/...: "<post text>"

### When the source is an email
Note that the email itself should be saved as a PDF in the project's shared drive.
Cite the email by sender, recipient, date, and subject, plus the PDF path or URL.

> Email from <Sender> to <Recipient>, <date>, subject: "<subject>", saved at
> <path or URL>. <position cue if multi-page>: "<verbatim relevant text>"

## What a verifier should be able to do with a good footnote

After reading the footnote alone — without clicking the hyperlink — the verifier
should be able to:

1. Name the source.
2. Locate the specific passage that supports the claim.
3. Decide on the spot whether the source actually supports the claim.

If any of those three is impossible without clicking through, the footnote is
incomplete.
