#!/usr/bin/env python3
"""
Preliminary data analysis engine.

Loads a tabular data file (CSV/TSV/other delimited text, or Excel), infers a
type for every column, computes descriptive statistics for numeric columns,
finds pairs of numeric columns with |correlation| > 0.4, and renders two
charts (a grid of histograms, and a correlation heatmap). All results are
written to a single JSON file so the calling model can turn them into a
narrative report without re-deriving any numbers by hand.

Usage:
    python3 analyze.py <input_file> <output_dir> [--sheet SHEET_NAME]

Writes to <output_dir>:
    analysis.json            - all computed statistics (see schema below)
    histograms.png            - grid of histograms, one per numeric variable (if any)
    correlation_heatmap.png   - heatmap of the numeric correlation matrix (if >= 2 numeric vars)
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd

CORR_THRESHOLD = 0.4


def load_table(path, sheet=None):
    """Load a CSV/TSV/delimited-text or Excel file into a DataFrame.

    Returns (df, extra_info) where extra_info is a dict with notes worth
    surfacing to the user (e.g. other sheet names found, encoding fallback used).
    """
    extra = {}
    ext = os.path.splitext(path)[1].lower()

    if ext in (".xlsx", ".xls", ".xlsm"):
        xl = pd.ExcelFile(path)
        chosen = sheet or xl.sheet_names[0]
        if len(xl.sheet_names) > 1:
            extra["other_sheets"] = [s for s in xl.sheet_names if s != chosen]
        extra["sheet_used"] = chosen
        df = xl.parse(chosen)
    else:
        # CSV / TSV / other delimited text. Sniff the delimiter rather than
        # assuming a comma, since tab- and pipe-separated files are common too.
        last_err = None
        df = None
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(path, sep=None, engine="python", encoding=encoding)
                if encoding != "utf-8":
                    extra["encoding_used"] = encoding
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
        if df is None:
            raise RuntimeError(f"Could not parse {path} as delimited text: {last_err}")

    # Drop fully-empty unnamed columns that sometimes appear from trailing delimiters.
    unnamed_empty = [c for c in df.columns if str(c).startswith("Unnamed:") and df[c].isna().all()]
    if unnamed_empty:
        df = df.drop(columns=unnamed_empty)

    return df, extra


def infer_column_type(series):
    """Classify a column as 'integer', 'floating point', or 'text'.

    Pandas already gets this right most of the time via dtype, but object
    columns that are numeric-but-for-a-few-blanks (a common real-world case)
    get a second look: if every non-null value can be parsed as a number,
    the column is reclassified as numeric rather than left as text.
    """
    s = series.dropna()
    if len(s) == 0:
        return "text"  # nothing to go on; default rather than guess

    if pd.api.types.is_bool_dtype(series):
        return "text"  # booleans are categorical in spirit, not numeric

    if pd.api.types.is_integer_dtype(series):
        return "integer"

    if pd.api.types.is_float_dtype(series):
        # Could still be "really" an integer column that only looks like
        # float because missing values forced pandas to use float64.
        if np.all(np.mod(s, 1) == 0):
            return "integer"
        return "floating point"

    # Object/text dtype: check whether it's secretly numeric.
    coerced = pd.to_numeric(s, errors="coerce")
    if coerced.notna().all():
        if np.all(np.mod(coerced, 1) == 0):
            return "integer"
        return "floating point"

    return "text"


ID_NAME_RE = re.compile(r"(^|_)id$", re.IGNORECASE)


def describe_type_detail(name, series, base_type):
    """Produce a richer, human-readable type description on top of the base
    text/integer/floating-point category.

    The three base categories tell you how to compute statistics; they don't
    tell you whether a column is an identifier, a coded scale, or free text --
    context that makes a preliminary report far more useful. This adds that
    context using cheap, deterministic signals (name pattern, cardinality)
    rather than leaving it to guesswork on every run. These are heuristic
    hints, not certainties -- worth a sanity check against the data before
    stating them as fact in the report, especially on small datasets where
    cardinality-based signals are noisier.
    """
    s = series.dropna()
    n = len(s)
    if n == 0:
        return base_type.capitalize()

    if pd.api.types.is_bool_dtype(series):
        return "Boolean"

    unique_count = int(s.nunique())
    unique_ratio = unique_count / n
    id_like_name = bool(ID_NAME_RE.search(str(name).strip()))

    if base_type == "integer":
        if id_like_name or unique_ratio > 0.95:
            return "Integer (identifier)"
        if unique_count <= 12:
            return f"Integer (ordinal / coded scale, {unique_count} levels)"
        return "Integer (discrete numeric)"

    if base_type == "floating point":
        return "Floating point (continuous numeric)"

    # text
    if id_like_name or (unique_ratio > 0.9 and n > 20):
        return "Text (identifier / free text, unique per row)"
    if unique_count <= 20:
        return f"Text (categorical, {unique_count} levels)"
    return "Text (free text)"


def numeric_series(df, col, col_type):
    """Return the column as a clean numeric pandas Series (for stats/correlation)."""
    if col_type == "integer" and pd.api.types.is_integer_dtype(df[col]):
        return df[col].astype(float)
    return pd.to_numeric(df[col], errors="coerce")


def compute_stats(s):
    s = s.dropna()
    n = len(s)
    if n == 0:
        return None
    mean = float(s.mean())
    median = float(s.median())
    mn = float(s.min())
    mx = float(s.max())
    std = float(s.std(ddof=1)) if n > 1 else None
    return {
        "count": int(n),
        "mean": mean,
        "median": median,
        "min": mn,
        "max": mx,
        "std_dev": std,
        "range": mx - mn,
    }


def find_correlations(numeric_df, threshold=CORR_THRESHOLD):
    cols = numeric_df.columns.tolist()
    pairs = []
    if len(cols) < 2:
        return pairs
    corr = numeric_df.corr(method="pearson")
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if pd.isna(r):
                continue
            if abs(r) > threshold:
                pairs.append({"var1": cols[i], "var2": cols[j], "r": round(float(r), 4)})
    pairs.sort(key=lambda p: abs(p["r"]), reverse=True)
    return pairs


def make_histograms(numeric_df, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = numeric_df.columns.tolist()
    if not cols:
        return None
    n = len(cols)
    ncols = min(4, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), squeeze=False)
    for idx, col in enumerate(cols):
        ax = axes[idx // ncols][idx % ncols]
        data = numeric_df[col].dropna()
        ax.hist(data, bins=min(30, max(5, int(len(data) ** 0.5))), color="#4C72B0", edgecolor="white")
        ax.set_title(col, fontsize=10)
        ax.tick_params(labelsize=8)
    # Hide unused subplots
    for idx in range(n, nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def make_heatmap(numeric_df, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = numeric_df.columns.tolist()
    if len(cols) < 2:
        return None
    corr = numeric_df.corr(method="pearson")
    fig, ax = plt.subplots(figsize=(1 + 0.6 * len(cols), 1 + 0.6 * len(cols)))
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(cols, fontsize=8)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(corr.values[i, j]) > 0.6 else "black")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Preliminary data analysis")
    parser.add_argument("input_file")
    parser.add_argument("output_dir")
    parser.add_argument("--sheet", default=None, help="Excel sheet name (defaults to first sheet)")
    parser.add_argument("--corr-threshold", type=float, default=CORR_THRESHOLD)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    df, extra = load_table(args.input_file, sheet=args.sheet)

    variables = []
    numeric_cols = {}
    for col in df.columns:
        col_type = infer_column_type(df[col])
        missing = int(df[col].isna().sum())
        variables.append({
            "name": str(col),
            "type": col_type,
            "type_detail": describe_type_detail(col, df[col], col_type),
            "non_null_count": int(len(df) - missing),
            "missing_count": missing,
        })
        if col_type in ("integer", "floating point"):
            numeric_cols[col] = numeric_series(df, col, col_type)

    numeric_df = pd.DataFrame(numeric_cols) if numeric_cols else pd.DataFrame()

    numeric_stats = []
    for col in numeric_df.columns:
        stats = compute_stats(numeric_df[col])
        if stats is not None:
            stats["name"] = str(col)
            # report the type from `variables` list for consistency
            stats["type"] = next(v["type"] for v in variables if v["name"] == str(col))
            numeric_stats.append(stats)

    correlations = find_correlations(numeric_df, args.corr_threshold)

    charts = {"histograms": None, "correlation_heatmap": None}
    if len(numeric_df.columns) >= 1:
        hist_path = os.path.join(args.output_dir, "histograms.png")
        if make_histograms(numeric_df, hist_path):
            charts["histograms"] = "histograms.png"
    if len(numeric_df.columns) >= 2:
        heat_path = os.path.join(args.output_dir, "correlation_heatmap.png")
        if make_heatmap(numeric_df, heat_path):
            charts["correlation_heatmap"] = "correlation_heatmap.png"

    result = {
        "source_file": os.path.basename(args.input_file),
        "notes": extra,
        "n_records": int(len(df)),
        "n_variables": int(len(df.columns)),
        "variables": variables,
        "numeric_stats": numeric_stats,
        "correlation_threshold": args.corr_threshold,
        "correlations": correlations,
        "charts": charts,
    }

    out_json = os.path.join(args.output_dir, "analysis.json")
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Wrote {out_json}")
    print(f"Records: {result['n_records']}, Variables: {result['n_variables']}, "
          f"Numeric: {len(numeric_stats)}, Correlated pairs (|r|>{args.corr_threshold}): {len(correlations)}")


if __name__ == "__main__":
    main()
