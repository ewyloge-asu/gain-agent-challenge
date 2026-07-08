"""Cross-reference query engine (CLI).

The agent calls these subcommands instead of scanning raw files. Every command
returns aggregated numbers plus provenance pointers, and supports --json for
machine-readable output that feeds the review/state tools.

Subcommands:
  member     pay (contributions received) + say (press output) for one member
  client     full lobbying footprint for one client (Senate + House)
  gatekeeper rank members by lobbyist money received (the "pay" leaderboard)
  anomaly    top lobbying clients by reported income + outlier flagging
  mismatch   Senate vs House income discrepancies on the SAME engagement
  lobbyist   revolving-door view: covered positions + who they lobby for
  say        the 'say' leg: a member's press output tagged into policy domains
  say-vs-do  press domains vs. sponsored-bill policy areas on a shared taxonomy
             (where a member talks about a domain more/less than they legislate)
  timeline   one member's DATED contributions interleaved with their sponsored
             bills + monthly press volume (the 'pay -> say -> act' cadence)

Usage examples:
  python xref.py gatekeeper --filer lobbyist --year 2025 --top 25
  python xref.py client "NIPPON STEEL"
  python xref.py member "Brett Guthrie"
  python xref.py mismatch --year 2025 --min-gap 50000
  python xref.py anomaly --year 2025
  python xref.py --json timeline "Brett Guthrie" --year 2025
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common as C

# Heuristic industry tagger for the money→bills timeline. Coarse by design and
# labeled as such in output; used to show whether dated money clusters in the
# same domains as a member's sponsored bills.
_INDUSTRY_KW = [
    ("Health/Pharma", ("HEALTH", "PHARMA", "MEDIC", "ONCOLOG", "HOSPITAL", "CLINIC",
                        "LILLY", "CVS", "PFIZER", "BRIGHTSPRING", "HALOMD", "BIOTECH",
                        "BIOSCI", "DRUG", "DIALYSIS", "NURS", "MERCK", "AMGEN", "ABBVIE")),
    ("Energy/Utilities", ("ENERGY", "EXXON", "CHEVRON", " OIL", "GAS ", "ELECTRIC",
                          "POWER", "NUCLEAR", "SOLAR", "UTILIT", "PETROLEUM")),
    ("Telecom/Tech", ("TELECOM", "SPECTRUM", "BROADBAND", "WIRELESS", "SPACEX",
                      "SATELLITE", "INTERNET", "AT&T", "VERIZON", "COMCAST", "T-MOBILE",
                      "CHARTER", "CTIA", "SEMICONDUCT")),
    ("Auto/Commerce", ("AUTO", "MOTOR", "VEHICLE", "SUBARU", "LKQ", "TOYOTA")),
    ("Finance", ("BANK", "FINANC", "CAPITAL", "INSUR", "INVEST", "SECURITIES")),
]


def _industry(name):
    u = (name or "").upper()
    for label, kws in _INDUSTRY_KW:
        if any(k in u for k in kws):
            return label
    return "Other"


def out(obj, as_json):
    if as_json:
        print(json.dumps(obj, indent=2, default=str))
    else:
        _pretty(obj)


def _pretty(obj, indent=0):
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print(f"{pad}{k}:")
                _pretty(v, indent + 1)
            else:
                print(f"{pad}{k}: {v}")
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict):
                print(f"{pad}- " + "  ".join(f"{k}={v[k]}" for k in v))
            else:
                print(f"{pad}- {v}")
    else:
        print(f"{pad}{obj}")


def resolve_member(con, ident):
    cur = con.cursor()
    row = cur.execute("SELECT * FROM members WHERE bioguide=?", (ident,)).fetchone()
    if row:
        return dict(row)
    key = C.lastname_key(ident)
    rows = cur.execute("SELECT * FROM members WHERE name_key=?", (key,)).fetchall()
    if len(rows) == 1:
        return dict(rows[0])
    rows = cur.execute("SELECT * FROM members WHERE name LIKE ?", (f"%{ident}%",)).fetchall()
    return dict(rows[0]) if len(rows) == 1 else None


def cmd_member(con, a):
    m = resolve_member(con, a.who)
    if not m:
        out({"error": f"could not resolve member '{a.who}'"}, a.json); return
    cur = con.cursor()
    bio = m["bioguide"]
    pay_by_year = [dict(r) for r in cur.execute(
        """SELECT sc.filing_year year, COUNT(*) items, COALESCE(SUM(ci.amount),0) total
           FROM contribution_items ci
           JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
           JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
           WHERE hr.bioguide=?
           GROUP BY sc.filing_year ORDER BY year""", (bio,))]
    top_payers = [dict(r) for r in cur.execute(
        """SELECT sc.registrant_name registrant, sc.filer_type,
                  COUNT(*) items, COALESCE(SUM(ci.amount),0) total
           FROM contribution_items ci
           JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
           JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
           WHERE hr.bioguide=?
           GROUP BY sc.registrant_name, sc.filer_type
           ORDER BY total DESC LIMIT ?""", (bio, a.top))]
    say_by_year = [dict(r) for r in cur.execute(
        """SELECT substr(date,1,4) year, COUNT(*) releases
           FROM press_releases WHERE member_bioguide=?
           GROUP BY year ORDER BY year""", (bio,))]
    prov = [dict(r) for r in cur.execute(
        """SELECT ci.honoree_name, ci.amount, ci.item_date, ci.prov
           FROM contribution_items ci
           JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
           WHERE hr.bioguide=? ORDER BY ci.amount DESC LIMIT 5""", (bio,))]
    out({"member": m, "pay_by_year": pay_by_year, "top_payers": top_payers,
         "say_by_year": say_by_year, "provenance_samples": prov}, a.json)


def cmd_client(con, a):
    cur = con.cursor()
    key = C.norm_org(a.name)
    like = f"%{key}%"
    senate = [dict(r) for r in cur.execute(
        """SELECT filing_year year, COUNT(*) filings, COALESCE(SUM(income),0) income,
                  COUNT(DISTINCT registrant_id) registrants
           FROM senate_filings WHERE client_name_norm LIKE ?
           GROUP BY filing_year ORDER BY year""", (like,))]
    registrants = [dict(r) for r in cur.execute(
        """SELECT registrant_name, COUNT(*) filings, COALESCE(SUM(income),0) income
           FROM senate_filings WHERE client_name_norm LIKE ?
           GROUP BY registrant_name ORDER BY income DESC LIMIT ?""", (like, a.top))]
    issues = [dict(r) for r in cur.execute(
        """SELECT sa.issue_code, COUNT(*) n
           FROM senate_filings sf JOIN senate_activities sa ON sa.filing_uuid=sf.filing_uuid
           WHERE sf.client_name_norm LIKE ? GROUP BY sa.issue_code ORDER BY n DESC LIMIT 15""", (like,))]
    govent = [dict(r) for r in cur.execute(
        """SELECT sa.gov_entities, COUNT(*) n
           FROM senate_filings sf JOIN senate_activities sa ON sa.filing_uuid=sf.filing_uuid
           WHERE sf.client_name_norm LIKE ? AND sa.gov_entities<>''
           GROUP BY sa.gov_entities ORDER BY n DESC LIMIT 10""", (like,))]
    countries = [dict(r) for r in cur.execute(
        """SELECT client_country, COUNT(*) n FROM senate_filings
           WHERE client_name_norm LIKE ? GROUP BY client_country ORDER BY n DESC""", (like,))]
    house = [dict(r) for r in cur.execute(
        """SELECT report_year year, COUNT(*) filings, COALESCE(SUM(income),0) income
           FROM house_filings WHERE client_name_norm LIKE ?
           GROUP BY report_year ORDER BY year""", (like,))]
    prov = [dict(r) for r in cur.execute(
        """SELECT filing_uuid, registrant_name, income, prov FROM senate_filings
           WHERE client_name_norm LIKE ? ORDER BY income DESC LIMIT 5""", (like,))]
    out({"query_key": key, "senate_by_year": senate, "house_by_year": house,
         "top_registrants": registrants, "top_issues": issues,
         "top_gov_entities": govent, "client_countries": countries,
         "provenance_samples": prov}, a.json)


def cmd_gatekeeper(con, a):
    cur = con.cursor()
    where = ["hr.bioguide IS NOT NULL"]
    params = []
    if a.year:
        where.append("sc.filing_year=?"); params.append(a.year)
    if a.filer:
        where.append("sc.filer_type=?"); params.append(a.filer)
    rows = [dict(r) for r in cur.execute(
        f"""SELECT m.name, m.party, m.state, m.chamber, hr.bioguide,
                   COUNT(*) items, COALESCE(SUM(ci.amount),0) total,
                   COUNT(DISTINCT sc.registrant_id) distinct_registrants
            FROM contribution_items ci
            JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
            JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
            JOIN members m ON m.bioguide=hr.bioguide
            WHERE {' AND '.join(where)}
            GROUP BY hr.bioguide ORDER BY total DESC LIMIT ?""",
        params + [a.top])]
    out({"filter": {"year": a.year, "filer_type": a.filer},
         "top_recipients": rows}, a.json)


def cmd_anomaly(con, a):
    cur = con.cursor()
    params = []
    yr = ""
    if a.year:
        yr = "WHERE filing_year=?"; params.append(a.year)
    rows = [dict(r) for r in cur.execute(
        f"""SELECT client_name, COUNT(*) filings, COALESCE(SUM(income),0) income,
                   COUNT(DISTINCT registrant_id) registrants
            FROM senate_filings {yr}
            GROUP BY client_name_norm ORDER BY income DESC LIMIT ?""",
        params + [a.top])]
    incomes = [r["income"] for r in rows if r["income"]]
    flagged = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1]["income"] if i + 1 < len(rows) else 0
        r["x_over_next"] = round(r["income"] / nxt, 1) if nxt else None
        if r["x_over_next"] and r["x_over_next"] >= a.factor:
            flagged.append(r["client_name"])
    out({"year": a.year, "top_clients_by_income": rows,
         "outliers_over_factor": {"factor": a.factor, "clients": flagged}}, a.json)


def cmd_mismatch(con, a):
    """Senate vs House reported income for the same engagement + period."""
    cur = con.cursor()
    period_map = {"Q1": "first_quarter", "Q2": "second_quarter",
                  "Q3": "third_quarter", "Q4": "fourth_quarter"}
    rows = cur.execute(
        """SELECT x.registrant_name, x.client_name, x.house_id, x.senate_filing_uuid,
                  h.income h_income, h.report_type, h.report_year,
                  h.senate_registrant_id, h.senate_client_id
           FROM xref_engagements x
           JOIN house_filings h ON h.house_id=x.house_id
           WHERE x.match_method='senateID_bridge' AND h.income IS NOT NULL""").fetchall()
    results = []
    for r in rows:
        period = period_map.get(r["report_type"])
        if not period:
            continue
        s = cur.execute(
            """SELECT filing_uuid, income, prov FROM senate_filings
               WHERE registrant_id=? AND client_id=? AND filing_year=? AND filing_period=?
                 AND income IS NOT NULL
               ORDER BY income DESC LIMIT 1""",
            (r["senate_registrant_id"], r["senate_client_id"], r["report_year"], period)).fetchone()
        if not s:
            continue
        gap = abs((r["h_income"] or 0) - (s["income"] or 0))
        if gap >= a.min_gap:
            results.append({
                "registrant": r["registrant_name"], "client": r["client_name"],
                "year": r["report_year"], "period": r["report_type"],
                "house_income": r["h_income"], "senate_income": s["income"],
                "gap": gap, "house_id": r["house_id"],
                "senate_filing_uuid": s["filing_uuid"], "senate_prov": s["prov"]})
    results.sort(key=lambda d: -d["gap"])
    out({"min_gap": a.min_gap, "count": len(results),
         "mismatches": results[:a.top]}, a.json)


def cmd_lobbyist(con, a):
    cur = con.cursor()
    like = f"%{C.norm_person(a.name)}%"
    rows = [dict(r) for r in cur.execute(
        """SELECT sal.lobbyist_name, sal.covered_position,
                  sf.client_name, sf.registrant_name, COUNT(*) n, sal.prov
           FROM senate_activity_lobbyists sal
           JOIN senate_filings sf ON sf.filing_uuid=sal.filing_uuid
           WHERE sal.lobbyist_name_norm LIKE ? AND sal.covered_position<>''
           GROUP BY sal.lobbyist_name, sf.client_name
           ORDER BY n DESC LIMIT ?""", (like, a.top))]
    out({"lobbyist_query": a.name, "engagements": rows}, a.json)


def cmd_say(con, a):
    """The 'say' leg: a member's press output tagged into policy domains, so a
    yearly release count becomes a topic profile. Tier 0 (no snapshot needed)."""
    m = resolve_member(con, a.who)
    if not m:
        out({"error": f"could not resolve member '{a.who}'"}, a.json); return
    bio = m["bioguide"]; cur = con.cursor()
    rows = cur.execute(
        "SELECT date, title, text, prov FROM press_releases WHERE member_bioguide=?",
        (bio,)).fetchall()
    total = len(rows)
    counts, samples, tagged = {}, {}, 0
    for r in rows:
        ds = C.domains_in_text(C.press_topic_text(r["title"], r["text"]))
        if ds:
            tagged += 1
        for d in ds:
            counts[d] = counts.get(d, 0) + 1
            samples.setdefault(d, {"date": r["date"], "title": r["title"], "prov": r["prov"]})
    domains = [{"domain": d, "releases": n,
                "share_of_tagged": round(n / tagged, 3) if tagged else 0,
                "sample": samples[d]}
               for d, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    by_year = [dict(r) for r in cur.execute(
        """SELECT substr(date,1,4) year, COUNT(*) releases
           FROM press_releases WHERE member_bioguide=?
           GROUP BY year ORDER BY year""", (bio,))]
    out({"member": {"bioguide": bio, "name": m["name"], "party": m.get("party"),
                    "state": m.get("state")},
         "summary": {"total_releases": total, "releases_with_a_topic": tagged},
         "by_year": by_year,
         "say_domains": domains[:a.top],
         "_note": "topics are keyword-tagged (coarse, multi-label); see methodology.md"},
        a.json)


def cmd_say_vs_do(con, a):
    """Join the 'say' leg (press domains) to the 'act' leg (sponsored-bill policy
    areas, from the Tier-1 legislation snapshot) on the shared domain taxonomy —
    surfacing where a member talks about a domain far more (or less) than they
    legislate in it. Descriptive juxtaposition, not a motive claim."""
    m = resolve_member(con, a.who)
    if not m:
        out({"error": f"could not resolve member '{a.who}'"}, a.json); return
    bio = m["bioguide"]; cur = con.cursor()

    say, say_tagged = {}, 0
    for r in cur.execute("SELECT title, text FROM press_releases WHERE member_bioguide=?", (bio,)):
        ds = C.domains_in_text(C.press_topic_text(r["title"], r["text"]))
        if ds:
            say_tagged += 1
        for d in ds:
            say[d] = say.get(d, 0) + 1

    act, act_tagged, bills_seen = {}, 0, 0
    snap = Path(__file__).resolve().parent.parent / "assets" / "legislation.json"
    have_act = snap.exists()
    if have_act:
        mem = json.loads(snap.read_text()).get("members", {}).get(bio, {})
        for b in mem.get("recent_bills", []):
            bills_seen += 1
            d = C.domain_for_policy_area(b.get("policy_area"))
            if d:
                act_tagged += 1
                act[d] = act.get(d, 0) + 1

    rows = []
    for d in sorted(set(say) | set(act)):
        ss = round(say.get(d, 0) / say_tagged, 3) if say_tagged else 0
        as_ = round(act.get(d, 0) / act_tagged, 3) if act_tagged else 0
        rows.append({"domain": d, "say_releases": say.get(d, 0), "say_share": ss,
                     "act_bills": act.get(d, 0), "act_share": as_,
                     "say_minus_act": round(ss - as_, 3)})
    rows.sort(key=lambda x: -abs(x["say_minus_act"]))
    talks_more = [r["domain"] for r in rows if r["say_minus_act"] >= 0.10][:5]
    acts_more = [r["domain"] for r in rows if r["say_minus_act"] <= -0.10][:5]
    out({"member": {"bioguide": bio, "name": m["name"], "party": m.get("party"),
                    "state": m.get("state")},
         "say": {"releases_with_a_topic": say_tagged},
         "act": {"have_snapshot": have_act, "bills_seen": bills_seen,
                 "bills_with_policy_area": act_tagged},
         "alignment": rows,
         "reads": {"talks_more_than_legislates": talks_more,
                   "legislates_more_than_talks": acts_more},
         "_note": ("press topics are keyword-tagged and bill policy areas are "
                   "Congress.gov's; both mapped to a coarse shared taxonomy. "
                   "Descriptive, not causal.")},
        a.json)


def cmd_timeline(con, a):
    """Interleave a member's DATED lobbyist contributions with the introduction
    dates of their sponsored bills (from the Tier-1 legislation snapshot) — the
    concrete 'pay → act' cadence for one member. Temporal juxtaposition only;
    not a causal claim."""
    m = resolve_member(con, a.who)
    if not m:
        out({"error": f"could not resolve member '{a.who}'"}, a.json); return
    bio = m["bioguide"]; cur = con.cursor()
    where = ["hr.bioguide=?", "ci.item_date<>''"]; p = [bio]
    if a.year:
        where.append("sc.filing_year=?"); p.append(a.year)
    if a.filer:
        where.append("sc.filer_type=?"); p.append(a.filer)
    rows = cur.execute(
        f"""SELECT ci.item_date d, ci.amount amt, sc.registrant_name reg,
                   ci.contributor_name contr, ci.prov
            FROM contribution_items ci
            JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
            JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
            WHERE {' AND '.join(where)} ORDER BY ci.item_date""", p).fetchall()
    contribs = [{"date": r["d"], "amount": r["amt"], "registrant": r["reg"],
                 "industry": _industry(r["reg"] or r["contr"]), "prov": r["prov"]}
                for r in rows]
    monthly, ind = {}, {}
    for c in contribs:
        e = monthly.setdefault(c["date"][:7], {"month": c["date"][:7], "total": 0.0, "count": 0})
        e["total"] += c["amount"] or 0; e["count"] += 1
        ind[c["industry"]] = ind.get(c["industry"], 0) + (c["amount"] or 0)
    bills = []
    snap = Path(__file__).resolve().parent.parent / "assets" / "legislation.json"
    if snap.exists():
        mem = json.loads(snap.read_text()).get("members", {}).get(bio, {})
        bills = [{"date": b.get("introduced"), "bill": f"{b.get('type')}{b.get('number')}",
                  "policy_area": b.get("policy_area"), "title": b.get("title"),
                  "latest_action": b.get("latest_action")}
                 for b in mem.get("recent_bills", []) if b.get("introduced")]
        bills.sort(key=lambda x: x["date"])
    # 'say' cadence: monthly press volume over the same window, for visual
    # comparison against the money/bills timeline.
    pw = ["member_bioguide=?", "date<>''"]; pp = [bio]
    if a.year:
        pw.append("substr(date,1,4)=?"); pp.append(str(a.year))
    monthly_press = {}
    for r in cur.execute(f"SELECT date FROM press_releases WHERE {' AND '.join(pw)}", pp):
        mm = r["date"][:7]
        monthly_press[mm] = monthly_press.get(mm, 0) + 1
    total_sum = round(sum(c["amount"] or 0 for c in contribs), 2)
    date_range = [contribs[0]["date"], contribs[-1]["date"]] if contribs else None
    top = sorted(contribs, key=lambda c: -(c["amount"] or 0))[:a.top]
    out({"member": {"bioguide": bio, "name": m["name"], "party": m.get("party"),
                    "state": m.get("state")},
         "summary": {"dated_contributions": len(contribs),
                     "total": total_sum,
                     "date_range": date_range,
                     "bills_tracked": len(bills),
                     "press_releases": sum(monthly_press.values()),
                     "money_by_industry": dict(sorted(ind.items(), key=lambda kv: -kv[1]))},
         "monthly_money": [monthly[k] for k in sorted(monthly)],
         "monthly_press": [{"month": k, "releases": monthly_press[k]} for k in sorted(monthly_press)],
         "bills": bills,
         "top_contributions": top,
         "_note": "industry tags are heuristic; temporal juxtaposition is not causation"},
        a.json)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("member"); p.add_argument("who"); p.add_argument("--top", type=int, default=15)
    p = sub.add_parser("client"); p.add_argument("name"); p.add_argument("--top", type=int, default=15)
    p = sub.add_parser("gatekeeper")
    p.add_argument("--year", type=int); p.add_argument("--filer", choices=["lobbyist", "organization"])
    p.add_argument("--top", type=int, default=25)
    p = sub.add_parser("anomaly")
    p.add_argument("--year", type=int); p.add_argument("--top", type=int, default=15)
    p.add_argument("--factor", type=float, default=5.0)
    p = sub.add_parser("mismatch")
    p.add_argument("--year", type=int); p.add_argument("--min-gap", type=float, default=50000)
    p.add_argument("--top", type=int, default=25)
    p = sub.add_parser("lobbyist"); p.add_argument("name"); p.add_argument("--top", type=int, default=20)
    p = sub.add_parser("say"); p.add_argument("who"); p.add_argument("--top", type=int, default=15)
    p = sub.add_parser("say-vs-do"); p.add_argument("who")
    p = sub.add_parser("timeline"); p.add_argument("who")
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--filer", choices=["lobbyist", "organization"], default="lobbyist")
    p.add_argument("--top", type=int, default=12)

    a = ap.parse_args()
    con = C.connect()
    {"member": cmd_member, "client": cmd_client, "gatekeeper": cmd_gatekeeper,
     "anomaly": cmd_anomaly, "mismatch": cmd_mismatch, "lobbyist": cmd_lobbyist,
     "say": cmd_say, "say-vs-do": cmd_say_vs_do,
     "timeline": cmd_timeline}[a.cmd](con, a)
    con.close()


if __name__ == "__main__":
    main()
