#!/usr/bin/env python3
"""
Retrieve an external source and SNAPSHOT it, so any finding that uses it re-runs offline
(the reproducibility gate). Generalizes the mapper connector's caching to any URL.

Writes two files under the snapshot dir:
  <slug>.<ext>         the raw bytes
  <slug>.meta.json     {url, fetched_at, status, content_type, sha256, bytes, slug}

Usage:
  python3 fetch_source.py "https://api.congress.gov/v3/bill?api_key=..." --out-dir snapshots
  python3 fetch_source.py "https://catalog.data.gov/dataset/xyz" --name datagov_xyz

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request


def slugify(url: str, name: str | None) -> str:
    if name:
        base = name
    else:
        base = re.sub(r"^https?://", "", url)
        base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")
    return base[:80] or "source"


def ext_for(content_type: str, url: str) -> str:
    ct = (content_type or "").lower()
    if "json" in ct:
        return "json"
    if "csv" in ct:
        return "csv"
    if "html" in ct:
        return "html"
    if "xml" in ct:
        return "xml"
    if "pdf" in ct:
        return "pdf"
    m = re.search(r"\.([a-z0-9]{1,5})(?:\?|$)", url.lower())
    return m.group(1) if m else "bin"


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch + snapshot an external source")
    p.add_argument("url")
    p.add_argument("--out-dir", default="snapshots")
    p.add_argument("--name", help="explicit slug for the snapshot files")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--max-bytes", type=int, default=50_000_000)
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    req = urllib.request.Request(
        args.url, headers={"User-Agent": "investigative-method/0.1 (records-investigation)"})
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            status = getattr(r, "status", 200)
            content_type = r.headers.get("Content-Type", "")
            raw = r.read(args.max_bytes + 1)
    except Exception as e:
        print(f"! fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if len(raw) > args.max_bytes:
        print(f"! response exceeds --max-bytes ({args.max_bytes}); aborting.",
              file=sys.stderr)
        return 1

    slug = slugify(args.url, args.name)
    ext = ext_for(content_type, args.url)
    data_path = os.path.join(args.out_dir, f"{slug}.{ext}")
    meta_path = os.path.join(args.out_dir, f"{slug}.meta.json")
    with open(data_path, "wb") as f:
        f.write(raw)
    meta = {
        "url": args.url,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "content_type": content_type,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "slug": slug,
        "data_file": os.path.basename(data_path),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"✓ snapshot: {data_path}  ({len(raw)} bytes, {content_type or 'unknown type'})")
    print(f"  meta:     {meta_path}  sha256={meta['sha256'][:16]}…")
    print("  (commit the snapshot so this source re-runs with no network.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
