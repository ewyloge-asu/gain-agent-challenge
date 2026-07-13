"""Coordinated-messaging detector for the press-release corpus.

Finds verbatim sentences reused across many members in a time window, then
attaches signals that help a journalist separate ORGANIC party boilerplate
from a TARGETED campaign:

  - n_members        how many distinct members used the exact sentence
  - parties          D / R / I breadth (bipartisan reuse is a strong signal it
                     is NOT ordinary partisan boilerplate)
  - span_days        how tightly clustered in time (tight = coordinated push)
  - specificity      names a company/bill/$ figure (concrete asks, not slogans)

Two modes:
  clusters   rank the strongest coordinated sentences in a window
  keyword    show who used a given phrase and when (chase one thread)

Usage:
  python detect_coordination.py clusters --year 2025 --min-members 5 --top 30
  python detect_coordination.py keyword "strategy group" --top 40
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

import common as C

_BILL = re.compile(r"\b(H\.?R\.?|S\.?)\s?\d{1,5}\b", re.I)
_MONEY = re.compile(r"\$\s?\d")
_PROPER = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")


def _sentences(text):
    for raw in re.split(r"[\n.]", text or ""):
        s = re.sub(r"\s+", " ", raw).strip()
        if len(s) >= 80:
            yield s.lower(), s


def specificity(original_samples):
    """Heuristic 0-3: does the shared language make a concrete, chase-able ask?"""
    joined = " ".join(original_samples)
    score = 0
    if _BILL.search(joined):
        score += 1
    if _MONEY.search(joined):
        score += 1
    # a capitalized multi-word proper noun that isn't a generic opener
    if _PROPER.search(joined):
        score += 1
    return score


def load_rows(con, year=None, start=None, end=None):
    cur = con.cursor()
    q = "SELECT url, date, member_bioguide, member_name, member_party, member_state, text FROM press_releases WHERE member_bioguide IS NOT NULL"
    p = []
    if year:
        q += " AND substr(date,1,4)=?"; p.append(str(year))
    if start:
        q += " AND date>=?"; p.append(start)
    if end:
        q += " AND date<=?"; p.append(end)
    return cur.execute(q, p).fetchall()


def cmd_clusters(con, a):
    rows = load_rows(con, a.year, a.start, a.end)
    members = defaultdict(set)      # sentence -> {bioguide}
    parties = defaultdict(set)
    dates = defaultdict(list)
    sample = {}
    url = defaultdict(list)
    names = defaultdict(set)
    for r in rows:
        seen = set()
        for low, orig in _sentences(r["text"]):
            if low in seen:
                continue
            seen.add(low)
            members[low].add(r["member_bioguide"])
            parties[low].add((r["member_party"] or "?")[0])
            dates[low].append(r["date"])
            names[low].add(r["member_name"])
            sample.setdefault(low, orig)
            if len(url[low]) < 3:
                url[low].append(r["url"])
    clusters = []
    for low, mems in members.items():
        if len(mems) < a.min_members:
            continue
        ds = sorted(d for d in dates[low] if d)
        span = 0
        if len(ds) >= 2:
            try:
                from datetime import date
                a0 = date.fromisoformat(ds[0][:10]); a1 = date.fromisoformat(ds[-1][:10])
                span = (a1 - a0).days
            except ValueError:
                span = 0
        clusters.append({
            "n_members": len(mems),
            "parties": "".join(sorted(parties[low])),
            "span_days": span,
            "specificity": specificity([sample[low]]),
            "sentence": sample[low][:200],
            "sample_urls": url[low],
        })
    # rank: bipartisan + specific + many members + tight window bubble up
    clusters.sort(key=lambda c: (len(c["parties"]) > 1, c["specificity"],
                                  c["n_members"], -c["span_days"]), reverse=True)
    print(json.dumps({"window": {"year": a.year, "start": a.start, "end": a.end},
                      "n_releases": len(rows), "clusters": clusters[:a.top]},
                     indent=2, default=str))


def cmd_keyword(con, a):
    cur = con.cursor()
    rows = cur.execute(
        """SELECT date, member_name, member_party, member_state, title, url
           FROM press_releases WHERE lower(text) LIKE ? ORDER BY date""",
        (f"%{a.phrase.lower()}%",)).fetchall()
    hits = [dict(r) for r in rows]
    by_member = defaultdict(int)
    for h in hits:
        by_member[f"{h['member_name']} ({h['member_party']}-{h['member_state']})"] += 1
    print(json.dumps({"phrase": a.phrase, "n_hits": len(hits),
                      "distinct_members": len(by_member),
                      "members": by_member,
                      "timeline": hits[:a.top]}, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("clusters")
    p.add_argument("--year", type=int); p.add_argument("--start"); p.add_argument("--end")
    p.add_argument("--min-members", type=int, default=5); p.add_argument("--top", type=int, default=30)
    p = sub.add_parser("keyword")
    p.add_argument("phrase"); p.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    con = C.connect()
    (cmd_clusters if a.cmd == "clusters" else cmd_keyword)(con, a)
    con.close()


if __name__ == "__main__":
    main()
