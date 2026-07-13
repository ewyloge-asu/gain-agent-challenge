"""Provenance / review interface.

Turns a provenance id (the `prov` column every ingested row carries) back into
the exact raw source record, so a human editor can verify any claim in seconds
without re-running the pipeline. Provenance formats produced by ingest.py:

  data/.../file.jsonl#L<line>            -> one press-release JSON object
  data/.../filings_YYYY.json#<uuid>      -> one Senate filing/contribution
  data/.../NNN.xml                       -> one House LD filing (raw XML)

Usage:
  python review.py "data/senate/2025/contributions/contributions_2025.json#9e7cef9a-..."
  python review.py "data/congress_press/2026/2026-01.jsonl#L42"
  python review.py "data/house/2025_1stQuarter_XML/301846542.xml"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import common as C


def resolve(prov: str, data_root: Path | None = None) -> str:
    data_root = data_root or C.data_dir().parent  # prov is relative to corpus parent
    path_part, _, frag = prov.partition("#")
    fp = (data_root / path_part)
    if not fp.exists():
        # tolerate prov stored relative to data/ itself
        alt = C.data_dir() / Path(path_part).relative_to(Path(path_part).parts[0]) \
            if Path(path_part).parts and Path(path_part).parts[0] == "data" else None
        if alt and alt.exists():
            fp = alt
    if not fp.exists():
        return json.dumps({"error": f"source file not found for prov: {prov}",
                           "looked_at": str(fp)})

    if fp.suffix == ".xml":
        return fp.read_text()

    if frag.startswith("L"):
        ln = int(frag[1:])
        with open(fp) as fh:
            for i, line in enumerate(fh, 1):
                if i == ln:
                    return json.dumps(json.loads(line), indent=2)
        return json.dumps({"error": f"line {ln} not found"})

    # JSON array keyed by filing_uuid
    recs = json.loads(fp.read_text())
    for r in recs:
        if r.get("filing_uuid") == frag:
            return json.dumps(r, indent=2)
    return json.dumps({"error": f"filing_uuid {frag} not found in {path_part}"})


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    print(resolve(sys.argv[1]))


if __name__ == "__main__":
    main()
