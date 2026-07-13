#!/usr/bin/env bash
# Reproducibility runner: rebuild the store and regenerate every headline number.
# Usage: GAIN_DATA_DIR=/path/to/data bash scripts/run_all.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
: "${GAIN_DATA_DIR:?set GAIN_DATA_DIR to the decompressed corpus (the dir containing congress_press/ senate/ house/)}"
export GAIN_WORKDIR="${GAIN_WORKDIR:-$HERE/../../build}"
mkdir -p "$GAIN_WORKDIR"
echo "DATA=$GAIN_DATA_DIR  WORKDIR=$GAIN_WORKDIR"

echo "== [1/3] ingest =="
python3 "$HERE/ingest.py" --years 2022 2023 2024 2025 2026 --datasets senate contributions press
python3 "$HERE/ingest.py" --years 2025 --datasets house

echo "== [2/3] resolve entities =="
python3 "$HERE/resolve_entities.py"

echo "== [3/3] headline numbers =="
echo "-- Finding 1: pay-the-gavel (top lobbyist-money recipients, 2025) --"
python3 "$HERE/xref.py" gatekeeper --filer lobbyist --year 2025 --top 20
echo "-- Finding 1 (verified vs external committee roles) --"
python3 "$HERE/connector.py" annotate-gatekeeper --year 2025 --filer lobbyist --top 20
echo "-- Finding 1 (Tier 1/2 enrichment; uses keys from credentials.env if present, else offline snapshots) --"
python3 "$HERE/connector.py" enrich-act --year 2025 --filer lobbyist --top 12 || true
python3 "$HERE/connector.py" enrich-finance --year 2025 --filer lobbyist --top 12 || true
python3 "$HERE/connector.py" enrich-votes --year 2025 --filer lobbyist --top 12 || true   # Voteview, no key
echo "-- Finding 1 (say leg): press topics vs. sponsored bills for a press-rich recipient --"
python3 "$HERE/xref.py" say-vs-do "Mark Warner" || true
echo "-- Finding 2: foreign revolving door --"
python3 "$HERE/xref.py" client "TENCENT"
python3 "$HERE/xref.py" client "NIPPON STEEL"
echo "-- Finding 3 (flag): disclosure abuse / outliers --"
python3 "$HERE/xref.py" anomaly --year 2025 --factor 5
echo "-- Cold thread: Senate vs House income consistency --"
python3 "$HERE/xref.py" mismatch --year 2025 --min-gap 100000
echo "done."
