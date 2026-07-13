#!/usr/bin/env python3
"""
Web-search-for-data (acquisition, part of BUILDING the story — not just checking it).

Given a topic, propose relevant public datasets/APIs to pull in. It:
  1. queries the live data.gov CKAN catalog (keyless) when the network is available,
  2. always ranks a curated catalog of high-value investigative sources by topic, and
  3. emits ready-to-run web-search queries for the agent to widen the net with its own
     web-search capability.

Results are written to a JSON snapshot so the acquisition step re-runs reproducibly.

Usage:
  python3 find_data.py "pharmaceutical lobbying drug pricing"
  python3 find_data.py "california hospital medicare" --rows 8 --out found_sources.json
  python3 find_data.py "school vouchers" --offline      # skip network, curated only

Standard library only.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

# Curated catalog of sources that recur in records investigations. Each entry has
# keyword tags so we can rank by topic overlap. This is the offline backbone; the live
# CKAN query and the agent's web search extend it.
CURATED = [
    {"name": "FEC campaign finance", "url": "https://api.open.fec.gov/developers/",
     "kind": "api", "needs_key": True,
     "tags": ["campaign", "finance", "contribution", "pac", "donor", "election",
              "money", "politics", "candidate"]},
    {"name": "Congress.gov API", "url": "https://api.congress.gov/",
     "kind": "api", "needs_key": True,
     "tags": ["congress", "bill", "legislation", "vote", "sponsor", "committee",
              "member", "law"]},
    {"name": "FARA (foreign agents)", "url": "https://efile.fara.gov/ords/fara/f?p=1381:1",
     "kind": "bulk", "needs_key": False,
     "tags": ["foreign", "lobbying", "influence", "agent", "principal", "fara"]},
    {"name": "Senate LDA API", "url": "https://lda.senate.gov/api/",
     "kind": "api", "needs_key": False,
     "tags": ["lobbying", "lda", "registrant", "client", "disclosure", "senate"]},
    {"name": "USAspending", "url": "https://api.usaspending.gov/",
     "kind": "api", "needs_key": False,
     "tags": ["contract", "grant", "spending", "procurement", "federal", "award",
              "vendor"]},
    {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar/sec-api-documentation",
     "kind": "api", "needs_key": False,
     "tags": ["sec", "securities", "company", "filing", "stock", "insider",
              "10-k", "financial"]},
    {"name": "CourtListener / RECAP", "url": "https://www.courtlistener.com/help/api/rest/",
     "kind": "api", "needs_key": True,
     "tags": ["court", "docket", "lawsuit", "judicial", "case", "legal", "pacer"]},
    {"name": "Federal Register", "url": "https://www.federalregister.gov/developers/api/v1",
     "kind": "api", "needs_key": False,
     "tags": ["regulation", "rule", "agency", "comment", "rulemaking", "federal"]},
    {"name": "CMS / Medicare data", "url": "https://data.cms.gov/",
     "kind": "bulk", "needs_key": False,
     "tags": ["medicare", "medicaid", "hospital", "health", "healthcare", "cms",
              "provider", "claims", "fraud"]},
    {"name": "GAO reports", "url": "https://www.gao.gov/reports-testimonies",
     "kind": "bulk", "needs_key": False,
     "tags": ["oversight", "audit", "gao", "government", "accountability"]},
    {"name": "Voteview roll calls", "url": "https://voteview.com/data",
     "kind": "bulk", "needs_key": False,
     "tags": ["vote", "roll call", "congress", "ideology", "party"]},
    {"name": "data.gov catalog", "url": "https://catalog.data.gov/dataset",
     "kind": "catalog", "needs_key": False,
     "tags": ["dataset", "government", "open data", "catalog"]},
]


def rank_curated(topic: str, limit: int = 8):
    words = {w for w in topic.lower().replace("/", " ").split() if len(w) > 2}
    scored = []
    for s in CURATED:
        score = sum(1 for t in s["tags"] if any(w in t or t in w for w in words))
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    out = [dict(s, match_score=score) for score, s in scored[:limit]]
    if not out:  # nothing matched — offer the general catalog + broad sources
        out = [dict(s, match_score=0) for s in CURATED if s["kind"] == "catalog"]
    return out


def query_ckan(topic: str, rows: int, timeout: float, catalog: str):
    """Query any CKAN portal's package_search (data.gov, data.ca.gov, EU portals, …).

    data.gov retired its public CKAN action API in 2026; override --catalog to point at
    any live CKAN portal, or rely on the curated list + your own web search.
    """
    base = catalog.rstrip("/") + "/api/3/action/package_search"
    url = base + "?" + urllib.parse.urlencode({"q": topic, "rows": rows})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 investigative-method"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if not data.get("success", True):
        raise RuntimeError("CKAN returned success=false")
    results = []
    for item in data.get("result", {}).get("results", []):
        org = (item.get("organization") or {}).get("title", "")
        slug = item.get("name", "")
        results.append({
            "name": item.get("title", "").strip(),
            "org": org,
            "url": catalog.rstrip("/") + "/dataset/" + slug,
            "notes": (item.get("notes", "") or "")[:240].replace("\n", " ").strip(),
            "resources": item.get("num_resources", len(item.get("resources", []))),
        })
    return results


def suggested_searches(topic: str):
    return [
        f'{topic} dataset',
        f'{topic} API data download',
        f'{topic} site:.gov data',
        f'{topic} bulk data csv OR json',
        f'{topic} FOIA OR "public records" dataset',
    ]


def main() -> int:
    p = argparse.ArgumentParser(description="Find relevant public datasets/APIs for a topic")
    p.add_argument("topic", help="the investigation topic / keywords")
    p.add_argument("--rows", type=int, default=6, help="live catalog results to fetch")
    p.add_argument("--catalog", default="https://catalog.data.gov",
                   help="CKAN portal base URL (override for any live CKAN catalog)")
    p.add_argument("--offline", action="store_true", help="skip network; curated only")
    p.add_argument("--timeout", type=float, default=12.0)
    p.add_argument("--out", help="write JSON snapshot here (for reproducible acquisition)")
    args = p.parse_args()

    out = {"topic": args.topic, "catalog": args.catalog,
           "curated": rank_curated(args.topic),
           "data_gov": [], "data_gov_error": None,
           "suggested_web_searches": suggested_searches(args.topic)}

    if not args.offline:
        try:
            out["data_gov"] = query_ckan(args.topic, args.rows, args.timeout, args.catalog)
        except Exception as e:  # portal moved / network blocked — degrade gracefully
            out["data_gov_error"] = f"{type(e).__name__}: {e}"

    # human-readable
    print(f"\n=== Data sources for: {args.topic} ===\n")
    print("Curated investigative sources (ranked by topic match):")
    for s in out["curated"]:
        key = " [needs free key]" if s.get("needs_key") else ""
        print(f"  • {s['name']} ({s['kind']}){key}\n      {s['url']}")
    print(f"\nLive CKAN catalog ({args.catalog}):")
    if out["data_gov"]:
        for s in out["data_gov"]:
            print(f"  • {s['name']}  [{s['resources']} resources]  {s['org']}\n"
                  f"      {s['url']}")
    elif args.offline:
        print("  (offline mode — skipped; re-run without --offline to query data.gov)")
    elif out["data_gov_error"]:
        print(f"  (unavailable: {out['data_gov_error']})")
    else:
        print("  (no results)")
    print("\nWiden the net — run these with your web-search capability, then "
          "tools/fetch_source.py the best hit:")
    for q in out["suggested_web_searches"]:
        print(f"  - {q}")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\n✓ snapshot written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
