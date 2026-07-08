"""Carve a tiny, self-consistent demo corpus out of the full GAIN dataset.

This is a BUILD-TIME tool (run once, by the skill author) to produce the
`demo_data/` that ships inside the skill so it runs out of the box. Recipients
do not need it — they either use the shipped `demo_data/` or point
`GAIN_DATA_DIR` at the full corpus. It is included for transparency and so the
sample can be regenerated/retuned.

It keeps the exact on-disk layout `ingest.py` expects (press JSONL under
`congress_press/<year>/`, 2026 at the root; Senate filings/contributions JSON
arrays under `senate/<year>/`), so the same scripts run unchanged.

Usage:
    python make_demo_data.py --src /path/to/full/data --dest ../demo_data
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import common as C

# Featured members: present in the shipped assets/legislation.json snapshot, so
# the Tier-1 "act" leg (say-vs-do / timeline) works offline for them.
FEATURED = {
    "W000805": "Mark Warner",     # Senate, press-rich -> say / say-vs-do
    "G000558": "Brett Guthrie",   # House, pay-the-gavel headline (E&C chair)
    "S001176": "Steve Scalise",   # House leadership
    "S001195": "Jason Smith",     # House, Ways & Means chair
    "T000476": "Thom Tillis",     # Senate
}
# Clients that anchor the foreign-revolving-door and integrity-flag demos.
FEATURED_CLIENTS = ("NIPPON STEEL", "TENCENT", "LOC NATION")

PRESS_YEARS = (2025, 2026)
PRESS_CAP_PER_MEMBER_YEAR = 120
CONTRIB_FILING_CAP = 400
SENATE_SAMPLE_TEXTURE = 90   # diverse "normal" filings so anomaly has a leaderboard


def _featured_name_keys() -> set[str]:
    return {C.lastname_key(n) for n in FEATURED.values()}


def sample_press(src: Path, dest: Path) -> int:
    kept = 0
    for year in PRESS_YEARS:
        # mirror the real layout: 2022-2025 live under <year>/, 2026 at the root
        if (src / "congress_press" / str(year)).is_dir():
            files = sorted((src / "congress_press" / str(year)).glob(f"{year}-*.jsonl"))
        else:
            files = sorted((src / "congress_press").glob(f"{year}-*.jsonl"))
        per_member = {}
        for fp in files:
            out_lines = []
            for line in fp.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                bio = (r.get("member") or {}).get("bioguide_id")
                if bio not in FEATURED:
                    continue
                key = (bio, year)
                if per_member.get(key, 0) >= PRESS_CAP_PER_MEMBER_YEAR:
                    continue
                per_member[key] = per_member.get(key, 0) + 1
                out_lines.append(line)
            if out_lines:
                rel = fp.relative_to(src)
                dst = dest / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("\n".join(out_lines) + "\n")
                kept += len(out_lines)
    return kept


def sample_contributions(src: Path, dest: Path, year: int = 2025) -> int:
    fp = src / "senate" / str(year) / "contributions" / f"contributions_{year}.json"
    if not fp.exists():
        return 0
    keys = _featured_name_keys()
    recs = json.loads(fp.read_text())
    out = []
    for r in recs:
        items = r.get("contribution_items") or []
        if any(C.lastname_key(it.get("honoree_name")) in keys for it in items):
            out.append(r)
            if len(out) >= CONTRIB_FILING_CAP:
                break
    dst = dest / "senate" / str(year) / "contributions" / f"contributions_{year}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out))
    return len(out)


def sample_filings(src: Path, dest: Path, year: int = 2025) -> int:
    fp = src / "senate" / str(year) / "filings" / f"filings_{year}.json"
    if not fp.exists():
        return 0
    recs = json.loads(fp.read_text())
    out, seen = [], set()
    # 1) every filing for a featured client (Nippon / Tencent / Loc Nation)
    for i, r in enumerate(recs):
        cn = C.norm_org((r.get("client") or {}).get("name"))
        if any(fc in cn for fc in FEATURED_CLIENTS):
            out.append(r); seen.add(i)
    # 2) a spread of "normal" filings so `anomaly` has a realistic leaderboard
    step = max(1, len(recs) // SENATE_SAMPLE_TEXTURE)
    for i in range(0, len(recs), step):
        if i not in seen:
            out.append(recs[i]); seen.add(i)
    dst = dest / "senate" / str(year) / "filings" / f"filings_{year}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out))
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="path to the full decompressed corpus (data/)")
    ap.add_argument("--dest", default=str(Path(__file__).resolve().parent.parent / "demo_data"))
    a = ap.parse_args()
    src = Path(a.src).expanduser().resolve()
    dest = Path(a.dest).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    print(f"src={src}\ndest={dest}")
    print(f"  press releases: {sample_press(src, dest)}")
    print(f"  senate filings: {sample_filings(src, dest)}")
    print(f"  contribution filings: {sample_contributions(src, dest)}")
    print("done. Build with: GAIN_DATA_DIR=%s python ingest.py --years 2025 2026 "
          "--datasets senate contributions press" % dest)


if __name__ == "__main__":
    main()
