#!/usr/bin/env python3
"""
Automated fact-checker for a RoboDoig report.

Every number in a RoboDoig report is supposed to come straight out of
analysis.json -- nothing is computed by the model while writing the
report. That means any discrepancy between the two is a transcription
error (a digit typed wrong, a stat left out, a correlation misquoted),
not a disagreement about the underlying math. This script catches that
class of mistake deterministically, by extracting the report's text and
checking that every figure from analysis.json actually appears in it --
and, for correlations specifically, that no *extra* coefficient above
the threshold shows up that analysis.json doesn't know about (a sign a
correlation was misremembered or invented while writing).

This is a safety net, not a substitute for reading the report. It only
catches missing/mismatched numbers; it can't judge whether the prose
around them is a fair characterization of the data.

Usage:
    python3 verify_report.py <report.docx> <analysis.json>

Exit code 0 = no discrepancies found. Exit code 1 = issues found (review
before sending the report along).
"""
import json
import re
import subprocess
import sys
import tempfile


def extract_text(docx_path):
    """Pull plain text out of the docx via pandoc (same tool the docx skill
    uses for text extraction), then undo the escaping pandoc adds so plain
    substring search works (e.g. 'annual\\_income' -> 'annual_income')."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp_path = tmp.name
    result = subprocess.run(["pandoc", docx_path, "-o", tmp_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed to read {docx_path}: {result.stderr}")
    with open(tmp_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace("\\_", "_").replace("\\-", "-").replace("\\$", "$")
    # Strip thousand-separator commas so "34,737.04" also matches "34737.04".
    text_nocommas = re.sub(r"(?<=\d),(?=\d{3}(\D|$))", "", text)
    return text, text_nocommas


def num_candidates(value):
    """A handful of plausible rounded string forms for a number, since the
    report is allowed to round for readability."""
    return {f"{value:.0f}", f"{value:.1f}", f"{value:.2f}", f"{value:.3f}"}


def find_correlation_mentions(text, variable_names):
    """Find (var_a, var_b, value) triples: lines where two known variable
    names appear together with a decimal number in [-1, 1] -- this is what
    a correlation table row looks like once pandoc flattens it to text
    (one row per line), and it also catches prose like 'r = 0.92' as long
    as both variable names are mentioned in the same sentence/line. Matching
    on co-occurring names rather than requiring an 'r =' prefix is what
    makes this work against table cells, which are bare numbers.
    """
    names = sorted(variable_names, key=len, reverse=True)
    results = []
    for line in text.split("\n"):
        present = [n for n in names if n and n in line]
        if len(present) < 2:
            continue
        for token in re.findall(r"-?\d*\.\d+|-?\d+", line):
            try:
                val = float(token)
            except ValueError:
                continue
            if -1.0 <= val <= 1.0:
                results.append((present[0], present[1], val))
    return results


def main():
    if len(sys.argv) != 3:
        print("Usage: verify_report.py <report.docx> <analysis.json>")
        sys.exit(2)

    report_path, analysis_path = sys.argv[1], sys.argv[2]

    with open(analysis_path) as f:
        analysis = json.load(f)

    text, text_nc = extract_text(report_path)

    issues = []

    # --- Record / variable counts ---
    if str(analysis["n_records"]) not in text_nc:
        issues.append(f"Record count {analysis['n_records']} not found anywhere in the report text.")
    if str(analysis["n_variables"]) not in text_nc:
        issues.append(f"Variable count {analysis['n_variables']} not found anywhere in the report text.")

    # --- Every variable name mentioned ---
    for v in analysis["variables"]:
        name = v["name"]
        if name not in text and name not in text_nc:
            issues.append(f"Variable '{name}' is never mentioned in the report text.")

    # --- Every numeric stat present, at some reasonable rounding ---
    for s in analysis.get("numeric_stats", []):
        for key in ("mean", "median", "min", "max", "std_dev", "range"):
            val = s.get(key)
            if val is None:
                continue
            if not any(c in text_nc for c in num_candidates(val)):
                issues.append(
                    f"{s['name']}.{key} = {val:.3f} doesn't appear (at any common rounding) in the report text."
                )

    # --- Correlations: every expected pair should show up with its variable
    # names and r-value co-located (whether in a table row or in prose) ---
    variable_names = [v["name"] for v in analysis["variables"]]
    mentions = find_correlation_mentions(text_nc, variable_names)

    def mention_matches(c):
        a, b, r = c["var1"], c["var2"], c["r"]
        return any(
            {m[0], m[1]} == {a, b} and abs(abs(m[2]) - abs(r)) < 0.015
            for m in mentions
        )

    for c in analysis.get("correlations", []):
        if not mention_matches(c):
            issues.append(
                f"Correlation {c['var1']} ~ {c['var2']} (r = {c['r']:.3f}) from analysis.json wasn't found "
                f"anywhere the two variable names and a matching r-value appear together in the report."
            )

    # --- No extra correlations above threshold that analysis.json doesn't know about ---
    threshold = analysis.get("correlation_threshold", 0.4)
    expected_pairs = {
        (frozenset({c["var1"], c["var2"]}), round(abs(c["r"]), 2)) for c in analysis.get("correlations", [])
    }
    for a, b, val in mentions:
        if abs(val) > threshold + 0.01:
            pair = frozenset({a, b})
            if not any(pair == ep and abs(round(abs(val), 2) - er) < 0.02 for ep, er in expected_pairs):
                issues.append(
                    f"Report mentions {a} ~ {b} with a value of {val:.3f} (magnitude above the {threshold} "
                    f"threshold) that doesn't match any pair in analysis.json's correlations list -- "
                    f"double-check this wasn't misremembered or invented while writing."
                )

    print(f"Checked {report_path} against {analysis_path}")
    print(f"  Variables: {len(analysis['variables'])}, numeric stats: {len(analysis.get('numeric_stats', []))}, "
          f"correlations: {len(analysis.get('correlations', []))}")

    if issues:
        print(f"\n{len(issues)} discrepanc{'y' if len(issues) == 1 else 'ies'} found:")
        for i in issues:
            print(f"  - {i}")
        sys.exit(1)
    else:
        print("\nAll figures verified against analysis.json. No discrepancies found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
