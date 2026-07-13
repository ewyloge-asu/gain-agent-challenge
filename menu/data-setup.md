# Data setup (one convention for the whole bundle)

This bundle is a set of Agent Skills that **run inside a code-executing agent** (Claude
Code, Cursor, or Cowork with code execution) — they read files and run scripts. That is the
supported runtime; the plain chat box can't execute the pipeline.

## 1. Where the data lives (we do NOT host it)

Every registered team/evaluator already receives the GAIN corpus from Northwestern, and it's
~8.6 GB, so the bundle does **not** ship or host it. Instead, point the skills at it with one
environment variable:

```bash
export GAIN_DATA_DIR=/path/to/data        # the corpus root (see data_manual.md layout)
export GAIN_WORKDIR="$PWD/build"          # where generated artifacts/DBs go
```

Expected layout under `GAIN_DATA_DIR` (from `data_manual.md`):

```
data/
  congress_press/**/*.jsonl
  senate/<year>/{filings,contributions}/*.json
  house/<year>_*_XML/*.xml
```

**Try it with no corpus:** `lobbying-influence-mapper/demo_data/` is a ~6 MB self-consistent
slice, so the pipeline runs out of the box before you supply the full corpus.

## 2. Works on ANY dataset (not just this corpus)

For a non-lobbying investigation, don't assume this schema. Start at **S0 scope-framing**
(`investigative-method/tools/scope.py`) — it selects/synthesizes a beat-pack — then:

- hand tabular data to `robodoig` to profile it, and
- use `investigative-method/tools/find_data.py "<topic>"` to locate relevant outside
  datasets/APIs, and `fetch_source.py <url>` to snapshot the ones you pull in.

## 3. Python & dependencies

**Python 3.9+.** The core findings pipeline (`lobbying-influence-mapper`,
`investigative-method` tools, `case-file`) is **standard library only — nothing to
install.** Two optional skills use third-party packages and say so clearly when missing:

| Skill | Needs | Install |
|---|---|---|
| `robodoig` | pandas, numpy, matplotlib, openpyxl | `pip install pandas numpy matplotlib openpyxl` |
| `howard-center-footnoter` | python-docx, lxml (+ pdfplumber for PDF sources) | `pip install python-docx lxml pdfplumber` |

## 4. Optional API keys

Some outside sources need a free key. Run the shared helper — it tells you where to get each
one and writes a gitignored `credentials.env`:

```bash
python3 setup_keys.py            # interactive
python3 setup_keys.py --check    # status only
```

**Keys never gate the core run.** Every skill works at Tier 0 (offline) from shipped
snapshots; keys only unlock richer enrichment. Any keyed fetch is snapshotted so keyed
findings still re-run with no network and no key.

## 5. Reproducibility contract

- Deterministic tools do the heavy lifting; the agent reasons over small aggregates.
- Every number carries a provenance id; `lobbying-influence-mapper/scripts/review.py "<prov>"`
  round-trips it to the raw record.
- Snapshots (`assets/*.json`, `snapshots/`) make findings re-runnable offline.
