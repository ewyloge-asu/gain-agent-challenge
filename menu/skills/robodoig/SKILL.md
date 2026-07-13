---
name: robodoig
description: "Runs a preliminary/exploratory analysis on a tabular data file (CSV, TSV, other delimited text, or Excel) and produces a Word document report describing the dataset: record count, a list of variables with their inferred type (text, integer, floating point), descriptive statistics (mean, median, min, max, standard deviation, range) for every numeric variable, and any pairs of numeric variables whose correlation coefficient is above 0.4 or below -0.4, plus histogram and correlation-heatmap charts. Use this skill whenever the user uploads or references a data file (csv, tsv, xlsx, xls) and asks for an initial look, a data profile, exploratory data analysis (EDA), a data quality check, a 'first pass' summary, or wants to understand 'what's in this dataset' before deeper analysis — even if they don't use the words 'preliminary analysis' explicitly."
---

# Preliminary Data Analysis

> **Why "robodoig":** named in tribute to Steve Doig — the Pulitzer-winning pioneer of
> computer-assisted reporting and longtime Knight Chair at ASU's Cronkite School — whose
> first move with any new dataset is exactly what this skill automates: profile it,
> learn what's normal, and let the deviations point to the story.

## What this produces

A Word document that answers four questions about a data table: how big is it, what's in each column, what do the numeric columns look like, and which numeric columns move together. This is meant to be the first thing you hand someone before any deeper modeling or analysis — a quick, trustworthy orientation to a dataset.

## Why a script does the math

Descriptive statistics and correlation coefficients need to be exactly right — a report that gets the mean or a correlation slightly wrong is worse than no report, because it looks authoritative. Rather than eyeballing a spreadsheet or writing pandas code from scratch each time (which invites small inconsistencies between runs), use the bundled `scripts/analyze.py`. It loads the file, infers each column's type, computes every statistic, finds the correlated pairs, and renders both charts — all in one deterministic pass. Your job is to turn its output into a clear, well-organized report, not to re-derive the numbers.

## Workflow

### 1. Locate the input file and run the analysis script

```bash
python3 scripts/analyze.py <input_file> <output_dir>
```

This handles CSV, TSV, other delimited text (it sniffs the delimiter automatically), and Excel (`.xlsx`/`.xls`/`.xlsm`; pass `--sheet SHEET_NAME` if the workbook has multiple sheets and the user cares which one — otherwise it defaults to the first sheet and reports the other sheet names it found in `analysis.json`'s `notes` field).

If `pandas`, `numpy`, `matplotlib`, or `openpyxl` aren't installed, install them first: `pip install pandas numpy matplotlib openpyxl --break-system-packages`.

The script writes `<output_dir>/analysis.json` plus (when applicable) `histograms.png` and `correlation_heatmap.png`. Read the JSON — it contains everything needed for the report:

- `n_records`, `n_variables`, `source_file`, `notes` (encoding fallback or other Excel sheets found, if any)
- `variables`: every column's name, its base `type` (`"integer"`, `"floating point"`, or `"text"` — this is what determines which stats get computed), a richer `type_detail` (e.g. `"Integer (identifier)"`, `"Integer (ordinal / coded scale, 5 levels)"`, `"Text (categorical, 4 levels)"`, `"Text (free text)"`), and non-null/missing counts
- `numeric_stats`: count, mean, median, min, max, std_dev, and range for each numeric column
- `correlations`: pairs of numeric variables with |r| > 0.4, sorted by strength, already deduplicated (no A-B and B-A repeats)
- `charts`: relative filenames of the generated PNGs (a value is `null` if there weren't enough numeric columns to produce that chart — e.g. no histogram grid when there are zero numeric columns, no heatmap when there's only one)

Don't recompute any of these numbers yourself — read them straight from the JSON into the report.

### 2. Build the Word report

Use the docx skill (read its SKILL.md for the docx-js mechanics) to assemble a `.docx` with this structure:

```markdown
# Preliminary Data Analysis: [source file name]

## Dataset Overview
[Prose: record count, variable count, and a one-line note on missing data if any
columns had a non-trivial number of missing values. Mention other Excel sheets
found, if applicable.]

## Variables
[Table: Variable | Type | Non-null Count | Missing Count. Use each column's
`type_detail` for the Type cell (e.g. "Integer (identifier)", "Text
(categorical, 4 levels)") rather than the bare "integer"/"floating
point"/"text" label — the richer description is more useful and is exactly
why the script computes it. Trust it as a starting point, but a sentence
of your own judgment is welcome if a column's role is obvious from its name
or values and the heuristic undersells it.]

## Descriptive Statistics
[Table, one row per numeric variable: Variable | Mean | Median | Min | Max |
Std. Dev. | Range. Round displayed values to a sensible precision (e.g. 2-3
significant decimal places) — the underlying JSON keeps full precision, the
report should be readable.]
[Insert histograms.png here, if present]

## Correlations
[If correlations is non-empty: table of Variable 1 | Variable 2 | r, sorted
strongest first, plus a sentence or two noting the strongest relationship(s)
in plain language (e.g. "height and weight move together closely"). Insert
correlation_heatmap.png here.]
[If correlations is empty but there were 2+ numeric variables: say plainly
that no pairs exceeded the ±0.4 threshold — that's a real, useful finding,
not a gap in the report.]
[If there were fewer than 2 numeric variables: note that correlation analysis
wasn't applicable, and say why (e.g. only one numeric column).]
```

Adapt headings/wording naturally — this is a skeleton, not a template to fill in mechanically. If the dataset has an interesting quirk (e.g. one column is almost entirely missing, or a numeric column is actually a coded categorical like a 5-point scale), it's worth a sentence of commentary rather than silently reporting the numbers.

### 3. Fact-check the report before delivering it

Writing a table by hand always carries a small risk of a transcription slip — a digit typed wrong, a correlation quoted from memory instead of copied, a stat left out. Since every number in the report is supposed to come verbatim from `analysis.json`, that kind of slip is checkable with certainty rather than by re-reading and hoping. Run:

```bash
python3 scripts/verify_report.py <report.docx> <output_dir>/analysis.json
```

This extracts the report's text and confirms every record/variable count, every descriptive statistic, and every correlation pair actually appears in it — and separately flags any correlation mentioned in the report that *doesn't* match a pair in `analysis.json` (a sign one was misremembered or invented while writing). It exits with code 0 and prints "No discrepancies found" when everything checks out. If it exits 1, it lists exactly what's missing or mismatched — fix the report and rerun until it's clean before sharing the file. Don't skip this step just because the report looks fine on a read-through; the whole point is that it catches things a read-through won't. (It shells out to `pandoc` to read the docx's text — the same tool the docx skill relies on for text extraction, so it should already be available.)

### 4. Edge cases worth handling explicitly

- **No numeric columns at all**: skip the Descriptive Statistics and Correlations sections' tables, and say so — a dataset of all-text columns is a valid (if unusual) result, not an error.
- **Very wide datasets (many numeric columns)**: the histogram grid and heatmap already scale to fit all of them, but call out in the text if the correlation table is long — consider only narrating the top few strongest pairs in prose while the full table still lists everything.
- **A column that's "numeric" but really an ID** (e.g. customer ID, ZIP code): `type_detail` already flags these as `"Integer (identifier)"` when the name matches a pattern like `id`/`customer_id` or every value is unique. Still worth a sentence in the stats/correlations sections noting that an identifier's mean or correlation isn't business-meaningful, even though the script computes it like any other numeric column.
- **Multiple sheets in an Excel file**: mention the sheet you analyzed and which others exist, so the user can ask for a different one if needed.
