# Source-type templates

Concrete formatting templates for each source type the skill is likely to encounter.
These are operationalized versions of the patterns in `footnote_format.md`.

When `scripts/format_footnote.py` runs, it routes each matched source through one of
these templates based on the source's `type` field. If a source has an unusual type
not listed here, fall back to the general template at the bottom of this file.

In every template:
- `{title}` is the human-readable source name.
- `{date}` is the most specific date available, formatted as the source itself uses
  (don't reformat `June 2021` as `06/2021`).
- `{quote}` is the verbatim supporting passage, in double quotes.
- `{position}` is the page-and-paragraph cue or timecode.
- `{url}` is the first-click-accessible URL. Hyperlink it on a meaningful keyword
  string, not on the raw URL.

---

## Government report (GAO, CRS, agency IG, etc.)

```
{report_id}, {title}, {date}, p. {page} of PDF, {position}: "{quote}"
```

Example:
> GAO-21-385, Sex Trafficking: Online Platforms and Federal Prosecutions, June 2021,
> p. 2 of PDF, top graf: "Two events in April 2018 disrupted the landscape …"

---

## Court filing / docket entry

```
{case_name}, {court}, Case No. {case_no}, {filing_type}, filed {date}, p. {page} of
PDF, {position}: "{quote}"
```

Example:
> United States v. Doe, D.D.C., Case No. 1:24-cv-00479-RC, Motion to Dismiss, filed
> January 12, 2025, p. 4 of PDF, second graf: "The court finds plaintiff's claims
> facially deficient …"

Always use PACER or CourtListener URLs over commercial aggregators. If the filing is
on a fee-walled docket, save a PDF to the project drive and link to that.

---

## Lobbying / financial-disclosure filing

```
{filing_form} filing by {registrant} for {client}, filed {date} with {filer_office},
filing UUID {uuid}: "{quote from the specific_issues description or activity
description}"
```

Example:
> LD-2 filing by LOC COMMUNITY ASSOCIATION for STATE OF LOC NATION GLOBAL PUBLIC
> BENEFIT CORPORATION, filed Q1 2025 with the Secretary of the Senate, filing UUID
> 842e03af-220d-407b-823e-cee25fcd50a2:
> https://lda.senate.gov/filings/public/filing/842e03af-220d-407b-823e-cee25fcd50a2/print/:
> "Lobbying $ in LND (ISO4217) Permalink.cc …"

---

## Police / incident report

```
{report_type} {report_id} See page {page} of the PDF, {position}: "{quote}"
```

Example:
> Incident Report V20070196 See page 9 of the PDF, middle of 3rd graf: "While in the
> lobby I observed what appeared to be bruising …"

If the report is on a paywalled or restricted site, save a PDF to the project drive
and footnote the PDF path.

---

## Corporate filing (10-K, proxy, press release)

```
{company} {filing_type} {fiscal_period}, p. {page}, "{section or graphic}":
"{quote}" (or for charts: {reading-of-the-chart} [= {arithmetic}])
```

Example:
> Roblox Corporation 2024 Proxy Statement and 2023 Annual Report p. 105, "By Age"
> graphic: Age of users in 2023: Under 9yo 21%; 9-12yo 21%; 13-16yo 16% = 58% are
> under 16.

For SEC filings, link to the official EDGAR page, not a third-party aggregator.

---

## Transcript (Trint, Otter, or a saved text transcript)

```
{transcript_url} T/C {hh:mm:ss}: "{verbatim quote, with internal timecodes preserved
if they appeared in the transcript}"
```

Example:
> https://app.trint.com/public/7f99a8bc-6ae5-47ad-9c6f-a5375d6225c T/C 00:12:47:
> "But really the biggest thing is, is, is parental awareness …"

When the transcript is not online (a local .txt), footnote the file name and shared
drive path, and include the timecode if available.

---

## Interview (live, not transcribed online)

```
Interview with {name}, {title and affiliation}, by {reporter} on {date}.
{recording_location or transcript_path}, T/C {hh:mm:ss}: "{verbatim quote}"
```

If you only have a paraphrase rather than a verbatim quote, write:

```
Interview with {name}, {title and affiliation}, by {reporter} on {date}.
{recording_location or transcript_path}, T/C {hh:mm:ss}. Paraphrase: {paraphrase}.
```

Mark the footnote `confidence: medium` whenever the supporting text is paraphrased.

---

## News article

```
{publication} article from {date}. "{quote, with [...] for elisions}"
```

Example:
> State Press article from 3/27/26. "ASU's budget proposal encapsulates academic
> fee proposals not previously approved by the board …"

Prefer the publication's own URL over an aggregator's republished version.

---

## Press release / official statement

```
{issuing_organization} press release, "{release_title}", {date}: "{quote}"
```

Always link to the issuing organization's own URL. Save a PDF to the project drive
in case the release is taken down.

---

## Database query / original data analysis

```
Analysis by {reporter_or_team} of {dataset_name}, downloaded from {dataset_url}
on {date}. Query: {one-line description of the filter/aggregation}. Result:
{numeric result}. Workbook: {workbook_url_or_path}.
```

Example:
> Analysis by Howard Center reporter J. Smith of Senate LDA quarterly filings,
> 2022–2025, downloaded from https://lda.senate.gov/api/v1/filings/ on 2026-03-15.
> Query: filings where `lobbying_activities[].general_issue_code == 'HCR'` AND
> `client.name` contains 'PHRMA'. Result: 47 filings totaling $42.16M in reported
> income. Workbook saved at <path>.

Original analysis footnotes must always make the methodology auditable. A fact-
checker should be able to re-run the query.

---

## Social media post (X, Bluesky, Threads, Mastodon, etc.)

```
@{handle} on {platform}, {date}, {url} — archived at {wayback_url}: "{post text}"
```

Always include the Wayback archive URL. Posts get deleted.

---

## Email

```
Email from {sender} to {recipient}, {date}, subject: "{subject}", saved at
{path_or_url}. {position cue if multi-page}: "{verbatim relevant text}"
```

The email itself must be saved as a PDF to the project's shared drive. The footnote
links to the saved PDF.

---

## Webpage (general)

```
{site_name} page "{page_title}", captured {date}, {url} — archived at {wayback_url}:
"{quote}"
```

For any webpage you cite, save it to the Wayback Machine and include the archived
URL. If you can't archive it, note that in the summary report so the reporter does.

---

## General fallback

When no template above fits:

```
{descriptive_source_name}, {date if available}, {position cue or page if relevant}:
"{verbatim quote}" — {url if available}
```

If you find yourself reaching for the fallback often, propose a new template to the
user — the protocol is supposed to be evolvable.

---

## Notes on hyperlinks

- The hyperlink anchor should be a **meaningful phrase from the footnote**, not the
  raw URL. For example, link "GAO-21-385" to the GAO URL, not the whole sentence.
- When the link points to a PDF, prefer a fragment URL that jumps to the right
  page (`...report.pdf#page=9`) or a comment-anchor URL produced by Adobe / a
  similar reader's "Link to this comment" feature.
- Never use URL shorteners (bit.ly, etc.) in footnotes. They obscure the destination
  and can be revoked.
