"""Config-driven external-dataset connector.

The point of this module is that the skill is NOT locked to the three provided
corpora. It defines a small registry of external sources, fetches with an
on-disk cache, and degrades gracefully offline so an evaluator can re-run the
skill without secrets (the reproducibility gate) while still being able to
refresh live data when keys/network are available.

Worked example shipped + reproducible with NO API KEY:
  - `unitedstates/congress-legislators` (public GitHub): current legislators +
    committee membership. Used to VERIFY that pay-the-gatekeeper recipients are
    in fact committee chairs/leaders.

Shipped + reproducible, also NO key:
  - FARA active foreign-agent registry (corroborates the foreign-influence story).
  - Voteview bulk roll-call CSVs (the vote dimension of "act": participation,
    party-unity, ideology). Snapshots to assets/votes.json.

Wired + documented, key-based (optional "act" leg):
  - Congress.gov v3 API (sponsored legislation; bill policy areas for
    vote-alignment) -- needs CONGRESS_GOV_API_KEY. Falls back to cache/message.
  - FEC (api.open.fec.gov, DEMO_KEY ok) is registered the same way.

Retargeting to a brand-new dataset = adding one SOURCES entry; everything else
(cache, offline fallback, provenance) is reused.

Usage:
  python connector.py refresh-committees      # build the no-key snapshot
  python connector.py committee G000558        # roles for one bioguide
  python connector.py annotate-gatekeeper --year 2025 --filer lobbyist --top 20
  python connector.py legislation G000558 --congress 119   # needs key
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

import common as C

SOURCES = {
    "unitedstates": {
        "base": "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/",
        "key_env": None,
        "files": {
            "legislators": "legislators-current.yaml",
            "membership": "committee-membership-current.yaml",
            "committees": "committees-current.yaml",
        },
    },
    "congress_gov": {"base": "https://api.congress.gov/v3/", "key_env": "CONGRESS_GOV_API_KEY"},
    "fec": {"base": "https://api.open.fec.gov/v1/", "key_env": "FEC_API_KEY"},
    "fara": {"base": "https://efile.fara.gov/api/v1/", "key_env": None,
             "base_active": "https://efile.fara.gov/api/v1/Registrants/json/Active"},
    # Voteview: public bulk roll-call CSVs, no key. The "act" leg's vote dimension.
    "voteview": {"base": "https://voteview.com/static/data/out/", "key_env": None},
}

# Voteview cast_code semantics (https://voteview.com/articles/data_help_votes).
VV_YEA = {"1", "2", "3"}      # yea / paired yea / announced yea
VV_NAY = {"4", "5", "6"}      # announced nay / paired nay / nay
VV_PRESENT = {"7", "8"}        # present
VV_PARTY = {"100": "D", "200": "R", "328": "I"}

SNAPSHOT = lambda: C.workdir() / "external_snapshots" / "committees.json"
# Shipped offline copy (committed to the skill) so committee verification works
# with no network and no API key -- the reproducibility fallback.
SHIPPED_SNAPSHOT = Path(__file__).resolve().parent.parent / "assets" / "committees.json"


def _cache_dir():
    d = C.workdir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch(url: str, refresh: bool = False, binary: bool = False):
    """Cached HTTP GET. Returns text (or bytes). Cache key = hash(url)."""
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    cf = _cache_dir() / (h + (".bin" if binary else ".txt"))
    if cf.exists() and not refresh:
        return cf.read_bytes() if binary else cf.read_text()
    req = urllib.request.Request(url, headers={"User-Agent": "gain-skill/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    cf.write_bytes(data)
    return data if binary else data.decode("utf-8", "replace")


def refresh_committees(refresh=True):
    """Build a stdlib-readable JSON snapshot of bioguide -> committee roles.

    Needs PyYAML only at refresh time (the source files are YAML). The shipped
    snapshot is plain JSON, so the rest of the skill stays dependency-free."""
    try:
        import yaml  # optional, only for refresh
    except ImportError:
        print("Refresh needs PyYAML (one-off): pip install pyyaml", file=sys.stderr)
        return None
    s = SOURCES["unitedstates"]
    membership = yaml.safe_load(fetch(s["base"] + s["files"]["membership"], refresh))
    committees = yaml.safe_load(fetch(s["base"] + s["files"]["committees"], refresh))
    legislators = yaml.safe_load(fetch(s["base"] + s["files"]["legislators"], refresh))

    cname = {c["thomas_id"]: c["name"] for c in committees if "thomas_id" in c}
    party_abbrev = {"Democrat": "D", "Republican": "R", "Independent": "I"}
    bio_by_name, fec_xwalk = {}, {}
    for L in legislators:
        ids = L.get("id", {})
        bid = ids.get("bioguide")
        nm = L.get("name", {})
        if not bid:
            continue
        # official_full is the canonical display name ("J. French Hill", not "J. Hill")
        bio_by_name[bid] = (nm.get("official_full")
                            or f"{nm.get('first','')} {nm.get('last','')}".strip())
        terms = L.get("terms", [])
        last_term = terms[-1] if terms else {}
        chamber = {"rep": "House", "sen": "Senate"}.get(last_term.get("type"))
        # Authoritative FEC candidate-id crosswalk (avoids name guessing for
        # common names like "Mike Johnson"); keep ids matching current chamber.
        fec = ids.get("fec") or []
        prefix = {"House": "H", "Senate": "S"}.get(chamber)
        fec_xwalk[bid] = {"chamber": chamber,
                          "fec": [f for f in fec if not prefix or f.startswith(prefix)] or fec,
                          "party": party_abbrev.get(last_term.get("party"),
                                                     last_term.get("party")),
                          "state": last_term.get("state")}

    out = {}
    for comm_id, members in membership.items():
        base_id = comm_id[:4]
        label = cname.get(comm_id) or cname.get(base_id) or comm_id
        for m in members:
            bid = m.get("bioguide")
            if not bid:
                continue
            out.setdefault(bid, {"name": bio_by_name.get(bid), "roles": []})
            out[bid]["roles"].append({
                "committee": label, "committee_id": comm_id,
                "title": m.get("title", "Member"), "rank": m.get("rank"),
            })
    # Attach the FEC crosswalk + chamber/party/state for every member we know
    # about (not just those with committee roles) so enrich-finance can resolve
    # ids offline and roster-seeded member rows carry full identity fields.
    for bid, x in fec_xwalk.items():
        out.setdefault(bid, {"name": bio_by_name.get(bid), "roles": []})
        out[bid]["chamber"] = x["chamber"]
        out[bid]["fec_ids"] = x["fec"]
        out[bid]["party"] = x["party"]
        out[bid]["state"] = x["state"]
    SNAPSHOT().parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT().write_text(json.dumps(
        {"_source": s["base"] + s["files"]["membership"],
         "_note": "Generated by connector.py refresh-committees; public, no key.",
         "members": out}, indent=2))
    print(f"wrote {SNAPSHOT()}  ({len(out)} members with committee roles)", file=sys.stderr)
    return out


def load_snapshot():
    # prefer a freshly refreshed snapshot in the workdir; otherwise fall back to
    # the committed offline copy so the skill runs without network/keys.
    for p in (SNAPSHOT(), SHIPPED_SNAPSHOT):
        if p.exists():
            return json.loads(p.read_text()).get("members", {})
    return None


def committee_role(bioguide):
    snap = load_snapshot()
    if snap is None:
        return None
    return snap.get(bioguide)


def _leadership_or_chair(roles):
    """Summarize a member's gatekeeper status from committee titles."""
    tags = []
    for r in roles or []:
        t = (r["title"] or "").lower()
        if "chair" in t and "vice" not in t:
            tags.append(f"CHAIR {r['committee']}")
        elif "ranking" in t:
            tags.append(f"RANKING {r['committee']}")
    return tags


def cmd_committee(con, a):
    role = committee_role(a.bioguide)
    if role is None:
        print(json.dumps({"error": "no snapshot; run refresh-committees first"})); return
    print(json.dumps({"bioguide": a.bioguide, **(role or {"roles": []}),
                       "gatekeeper_tags": _leadership_or_chair((role or {}).get("roles"))},
                      indent=2))


def cmd_annotate_gatekeeper(con, a):
    """Join the in-corpus 'pay' leaderboard with EXTERNAL committee roles to
    test the hypothesis that money concentrates on chairs/leaders."""
    snap = load_snapshot()
    if snap is None:
        print(json.dumps({"error": "no snapshot; run refresh-committees first"})); return
    cur = con.cursor()
    where = ["hr.bioguide IS NOT NULL"]; p = []
    if a.year: where.append("sc.filing_year=?"); p.append(a.year)
    if a.filer: where.append("sc.filer_type=?"); p.append(a.filer)
    rows = cur.execute(
        f"""SELECT m.name,m.party,m.state,m.chamber,hr.bioguide,
                   COUNT(*) items, COALESCE(SUM(ci.amount),0) total
            FROM contribution_items ci
            JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
            JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
            JOIN members m ON m.bioguide=hr.bioguide
            WHERE {' AND '.join(where)}
            GROUP BY hr.bioguide ORDER BY total DESC LIMIT ?""", p + [a.top]).fetchall()
    out = []
    n_gatekeeper = 0
    for r in rows:
        role = snap.get(r["bioguide"]) or {}
        tags = _leadership_or_chair(role.get("roles"))
        if tags:
            n_gatekeeper += 1
        out.append({"name": r["name"], "party": r["party"], "state": r["state"],
                    "total": r["total"], "items": r["items"],
                    "committee_roles": tags or [rr["title"] + " " + rr["committee"]
                                                for rr in role.get("roles", [])][:3]})
    print(json.dumps({"filter": {"year": a.year, "filer": a.filer},
                      "n_top": len(out),
                      "n_with_chair_or_ranking": n_gatekeeper,
                      "recipients": out}, indent=2, default=str))


FARA_SNAPSHOT = lambda: C.workdir() / "external_snapshots" / "fara_active.json"
SHIPPED_FARA = Path(__file__).resolve().parent.parent / "assets" / "fara_active.json"


def _load_fara(refresh=False):
    """FARA active foreign-agent registrants. No key required. Cached + shipped."""
    if not refresh:
        for p in (FARA_SNAPSHOT(), SHIPPED_FARA):
            if p.exists():
                return json.loads(p.read_text())
    url = SOURCES["fara"]["base_active"]
    data = json.loads(fetch(url, refresh))
    FARA_SNAPSHOT().parent.mkdir(parents=True, exist_ok=True)
    FARA_SNAPSHOT().write_text(json.dumps(data))
    return data


def cmd_fara(con, a):
    """Cross-check lobbying-firm/lobbyist names against the FARA foreign-agent
    registry. A firm lobbying for a foreign client that does NOT appear in FARA
    is using the LDA exemption rather than registering as a foreign agent --
    legal, but a reportable gray area. Names default to the Finding-2 roster."""
    try:
        data = _load_fara(a.refresh)
    except Exception as e:
        print(json.dumps({"status": "offline", "error": str(e),
                          "hint": "needs network once; result is then cached/shipped"}))
        return
    rows = data["REGISTRANTS_ACTIVE"]["ROW"]
    fara_names = [(r.get("Name", ""), r.get("Registration_Number"),
                   r.get("Registration_Date")) for r in rows]
    targets = a.names or [
        "AKIN GUMP", "BALLARD", "BROWNSTEIN", "HOGAN LOVELLS", "MERCURY",
        "MCENTEE", "GEPHARDT", "VOX GLOBAL",
    ]
    out = []
    for t in targets:
        tu = C.norm_org(t) or t.upper()
        hits = [{"fara_name": n, "reg_no": rn, "reg_date": rd}
                for (n, rn, rd) in fara_names if tu.split()[0] in n.upper()]
        out.append({"query": t, "in_fara": bool(hits), "matches": hits[:3]})
    print(json.dumps({"fara_active_count": len(rows), "checked": out,
                      "note": "in_fara=False for a foreign-client lobbyist => likely LDA exemption to FARA"},
                     indent=2, default=str))


def cmd_fec(con, a):
    """Look up a member's FEC campaign-finance totals (ground-truth context for
    the 'pay' leaderboard). Uses DEMO_KEY by default (rate-limited); set
    FEC_API_KEY for real use. Cached after first fetch."""
    key = os.environ.get(SOURCES["fec"]["key_env"], "DEMO_KEY")
    base = SOURCES["fec"]["base"]
    try:
        s = json.loads(fetch(f"{base}candidates/search/?q={urllib.parse.quote(a.name)}"
                             f"&api_key={key}&per_page=5", a.refresh))
    except urllib.error.HTTPError as e:
        print(json.dumps({"status": "error", "code": e.code,
                          "hint": "DEMO_KEY is rate-limited; set FEC_API_KEY"})); return
    cands = [{"name": r.get("name"), "candidate_id": r.get("candidate_id"),
              "office": r.get("office"), "party": r.get("party_full"),
              "state": r.get("state")} for r in s.get("results", [])]
    print(json.dumps({"query": a.name, "demo_key": key == "DEMO_KEY",
                      "candidates": cands}, indent=2, default=str))


def _top_gatekeepers(con, year, filer, top):
    where = ["hr.bioguide IS NOT NULL"]; p = []
    if year:
        where.append("sc.filing_year=?"); p.append(year)
    if filer:
        where.append("sc.filer_type=?"); p.append(filer)
    return con.execute(
        f"""SELECT m.bioguide, m.name, m.party, m.state, m.chamber,
                   COUNT(*) items, COALESCE(SUM(ci.amount),0) total
            FROM contribution_items ci
            JOIN honoree_resolution hr ON ci.honoree_name=hr.honoree_name
            JOIN senate_contributions sc ON sc.filing_uuid=ci.filing_uuid
            JOIN members m ON m.bioguide=hr.bioguide
            WHERE {' AND '.join(where)}
            GROUP BY hr.bioguide ORDER BY total DESC LIMIT ?""", p + [top]).fetchall()


def _ship(workdir_name, payload):
    """Write a Tier-1/2 result to the workdir snapshot AND the shipped assets
    copy, so keyed findings reproduce offline."""
    wp = C.workdir() / "external_snapshots" / workdir_name
    wp.parent.mkdir(parents=True, exist_ok=True)
    wp.write_text(json.dumps(payload, indent=2, default=str))
    ap = Path(__file__).resolve().parent.parent / "assets" / workdir_name
    ap.write_text(json.dumps(payload, indent=2, default=str))
    return ap


def cmd_enrich_act(con, a):
    """Tier 1: pull sponsored legislation (+ policy areas) for the top
    'pay' recipients, so we can ask whether their bills track their donors."""
    key = os.environ.get(SOURCES["congress_gov"]["key_env"])
    if not key:
        print(json.dumps({"status": "offline", "message": "set CONGRESS_GOV_API_KEY"})); return
    import collections
    rows = _top_gatekeepers(con, a.year, a.filer, a.top)
    snap, summary = {}, []
    for r in rows:
        url = (f"{SOURCES['congress_gov']['base']}member/{r['bioguide']}/sponsored-legislation"
               f"?api_key={key}&limit={a.limit}")
        try:
            data = json.loads(fetch(url, a.refresh))
        except urllib.error.HTTPError as e:
            data = {"_error": e.code}
        bills = [{"type": b.get("type"), "number": b.get("number"),
                  "title": (b.get("title") or "")[:140],
                  "policy_area": (b.get("policyArea") or {}).get("name"),
                  "introduced": b.get("introducedDate"),
                  "latest_action": (b.get("latestAction") or {}).get("text")}
                 for b in data.get("sponsoredLegislation", [])]
        total_sponsored = (data.get("pagination") or {}).get("count")
        areas = collections.Counter(b["policy_area"] for b in bills if b["policy_area"])
        snap[r["bioguide"]] = {"name": r["name"], "party": r["party"], "state": r["state"],
                                "lobbyist_total": r["total"], "total_sponsored": total_sponsored,
                                "top_policy_areas": areas.most_common(5), "recent_bills": bills}
        summary.append({"name": r["name"], "lobbyist_$": r["total"],
                        "sponsored": total_sponsored,
                        "top_policy_areas": areas.most_common(3)})
    path = _ship("legislation.json", {"_source": "Congress.gov v3 sponsored-legislation",
                                       "filter": {"year": a.year, "filer": a.filer},
                                       "members": snap})
    print(json.dumps({"shipped": str(path), "summary": summary}, indent=2, default=str))


def _fec_candidate(name, state, chamber, key, refresh=False):
    # Push office/state into the FEC query so common names (e.g. "Mike Johnson")
    # disambiguate server-side instead of paginating past a client-side filter.
    office = {"House": "H", "Senate": "S"}.get(chamber)
    q = f"{SOURCES['fec']['base']}candidates/search/?q={urllib.parse.quote(name)}&api_key={key}&per_page=20"
    if office:
        q += f"&office={office}"
    if state:
        q += f"&state={state}"
    try:
        res = json.loads(fetch(q, refresh)).get("results", [])
    except urllib.error.HTTPError:
        res = []
    if res:
        return res[0]
    # Fallback: drop the q text and rely on office+state (handles middle-name
    # mismatches like "James Michael Johnson" vs the display name).
    last = name.replace(".", "").split()[-1]
    q2 = f"{SOURCES['fec']['base']}candidates/search/?q={urllib.parse.quote(last)}&api_key={key}&per_page=50"
    if office:
        q2 += f"&office={office}"
    if state:
        q2 += f"&state={state}"
    try:
        res = json.loads(fetch(q2, refresh)).get("results", [])
    except urllib.error.HTTPError:
        res = []
    return res[0] if res else None


def _fec_totals_for_cycle(cid, key, target, refresh=False):
    """Return the candidate's totals row for their ACTIVE campaign: the smallest
    election cycle >= target that actually has receipts. This handles both House
    (every cycle is an election) and Senate (totals live under the next election
    year, e.g. a 2025 senator up in 2028 reports under cycle 2028)."""
    try:
        rows = json.loads(fetch(f"{SOURCES['fec']['base']}candidate/{cid}/totals/"
                                f"?api_key={key}&sort=-cycle&election_full=true&per_page=20",
                                refresh)).get("results", [])
    except urllib.error.HTTPError:
        return None
    cands = []
    for t in rows:
        cyc = t.get("candidate_election_year") or t.get("cycle")
        rcpt = t.get("receipts") or t.get("contributions")
        if cyc and cyc >= target and rcpt:
            cands.append((cyc, t))
    if not cands:
        return None
    cands.sort(key=lambda x: x[0])  # smallest qualifying cycle = current campaign
    return cands[0][1]


def cmd_enrich_finance(con, a):
    """Tier 2: pull each top recipient's FEC current-campaign receipts so the
    LD-203 lobbyist total has a real denominator (what share of their money it
    is). Candidate ids come from the authoritative bioguide->FEC crosswalk in the
    committees snapshot (no fragile name matching for common names)."""
    key = os.environ.get(SOURCES["fec"]["key_env"], "DEMO_KEY")
    target = a.year if a.year % 2 == 0 else a.year + 1  # 2025 -> 2026 cycle floor
    xwalk = load_snapshot() or {}
    rows = _top_gatekeepers(con, a.year, a.filer, a.top)
    snap, summary = {}, []
    for r in rows:
        info = xwalk.get(r["bioguide"], {})
        fec_ids = info.get("fec_ids") or []
        if not fec_ids:  # fallback: name search if crosswalk missing the member
            cand = _fec_candidate(r["name"], r["state"], r["chamber"], key, a.refresh)
            fec_ids = [cand["candidate_id"]] if cand else []
        best = None
        for cid in fec_ids:
            tot = _fec_totals_for_cycle(cid, key, target, a.refresh)
            if tot and (best is None or (tot.get("receipts") or 0) > (best[1].get("receipts") or 0)):
                best = (cid, tot)
        if not best:
            snap[r["bioguide"]] = {"name": r["name"], "fec_match": None, "fec_ids": fec_ids}
            summary.append({"name": r["name"], "fec": "no match"}); continue
        cid, tot = best
        receipts = tot.get("receipts") or tot.get("contributions")
        snap[r["bioguide"]] = {"name": r["name"], "chamber": r["chamber"],
                                "fec_candidate_id": cid,
                                "fec_cycle": tot.get("candidate_election_year"),
                                "coverage": [tot.get("coverage_start_date"), tot.get("coverage_end_date")],
                                "fec_receipts": receipts,
                                "fec_individual": tot.get("individual_contributions"),
                                "fec_disbursements": tot.get("disbursements"),
                                "ld203_lobbyist_total": r["total"]}
        share = (r["total"] / receipts) if receipts else None
        summary.append({"name": r["name"], "chamber": r["chamber"],
                        "ld203_lobbyist_$": r["total"], "fec_receipts": receipts,
                        "fec_cycle": tot.get("candidate_election_year"),
                        "lobbyist_share_of_receipts": round(share, 4) if share else None,
                        "fec_id": cid})
    path = _ship("fec_totals.json",
                 {"_source": "FEC api.open.fec.gov candidate totals (election_full)",
                  "_note": "fec_receipts = current-campaign receipts; Senate windows "
                           "span up to 6yr vs House 2yr, so cross-chamber shares are "
                           "directional, not strictly comparable.",
                  "cycle_floor": target, "members": snap})
    print(json.dumps({"shipped": str(path), "summary": summary}, indent=2, default=str))


# ---------------------------------------------------------------------------
# Voteview (roll-call votes) -- the vote dimension of the "act" leg. No key.
# ---------------------------------------------------------------------------
def _vv_csv(kind, chamber_letter, congress, refresh=False):
    url = f"{SOURCES['voteview']['base']}{kind}/{chamber_letter}{congress}_{kind}.csv"
    return list(csv.DictReader(io.StringIO(fetch(url, refresh))))


def _vv_chamber_letter(chamber):
    return {"House": "H", "Senate": "S"}.get(chamber)


def _voting_profiles(chamber_letter, congress, bioguides, refresh=False):
    """One pass over a chamber's roll-call file: returns a voting profile per
    requested bioguide (participation, party-unity, ideology). Party-unity needs
    the whole chamber's party tallies, so we build them in the same pass."""
    members = _vv_csv("members", chamber_letter, congress, refresh)
    icpsr_party = {m["icpsr"]: m["party_code"] for m in members}
    bio_to_icpsr = {m["bioguide_id"]: m["icpsr"] for m in members if m.get("bioguide_id")}
    meta_by_icpsr = {m["icpsr"]: m for m in members}
    targets = {bio_to_icpsr[b]: b for b in bioguides if b in bio_to_icpsr}
    if not targets:
        return {}

    rollcalls = {r["rollnumber"]: r for r in _vv_csv("rollcalls", chamber_letter, congress, refresh)}
    # party_tally[party][rollnumber] = [yea, nay]; member_casts[icpsr][rollnumber] = code
    party_tally, member_casts = {}, {i: {} for i in targets}
    for row in _vv_csv("votes", chamber_letter, congress, refresh):
        rn, ic, code = row["rollnumber"], row["icpsr"], row["cast_code"]
        p = icpsr_party.get(ic)
        if p:
            t = party_tally.setdefault(p, {}).setdefault(rn, [0, 0])
            if code in VV_YEA:
                t[0] += 1
            elif code in VV_NAY:
                t[1] += 1
        if ic in member_casts:
            member_casts[ic][rn] = code

    out = {}
    for ic, bio in targets.items():
        m = meta_by_icpsr[ic]
        party = icpsr_party.get(ic)
        casts = member_casts[ic]
        yea = sum(1 for c in casts.values() if c in VV_YEA)
        nay = sum(1 for c in casts.values() if c in VV_NAY)
        present = sum(1 for c in casts.values() if c in VV_PRESENT)
        total_rc = len(rollcalls)
        with_party = against = 0
        for rn, code in casts.items():
            side = "Y" if code in VV_YEA else ("N" if code in VV_NAY else None)
            if not side:
                continue
            tally = party_tally.get(party, {}).get(rn)
            if not tally or tally[0] == tally[1]:
                continue
            party_side = "Y" if tally[0] > tally[1] else "N"
            if side == party_side:
                with_party += 1
            else:
                against += 1
        unity = with_party / (with_party + against) if (with_party + against) else None
        out[bio] = {
            "name": m.get("bioname"), "party": VV_PARTY.get(party, party),
            "state": m.get("state_abbrev"), "icpsr": ic,
            "nominate_dim1": float(m["nominate_dim1"]) if m.get("nominate_dim1") else None,
            "rollcalls_in_congress": total_rc,
            "votes_cast": yea + nay + present, "yea": yea, "nay": nay, "present": present,
            "participation_rate": round((yea + nay + present) / total_rc, 4) if total_rc else None,
            "party_unity_rate": round(unity, 4) if unity is not None else None,
            "votes_against_own_party": against,
        }
    return out


def cmd_votes(con, a):
    """Single-member roll-call profile from Voteview (no key)."""
    chamber = (load_snapshot() or {}).get(a.bioguide, {}).get("chamber")
    letters = [_vv_chamber_letter(chamber)] if chamber else ["H", "S"]
    for L in letters:
        prof = _voting_profiles(L, a.congress, [a.bioguide], a.refresh)
        if prof:
            print(json.dumps(prof[a.bioguide], indent=2, default=str)); return
    print(json.dumps({"status": "not_found",
                      "message": f"{a.bioguide} not in Voteview {a.congress}th"}, default=str))


def cmd_enrich_votes(con, a):
    """Voteview voting profiles for the top contribution recipients -> the vote
    dimension of 'act'. Keyless; snapshots assets/votes.json."""
    xwalk = load_snapshot() or {}
    rows = _top_gatekeepers(con, a.year, a.filer, a.top)
    by_chamber = {}
    for r in rows:
        ch = xwalk.get(r["bioguide"], {}).get("chamber") or r["chamber"]
        by_chamber.setdefault(_vv_chamber_letter(ch), []).append(r["bioguide"])
    profiles = {}
    for L, bios in by_chamber.items():
        if not L:
            continue
        profiles.update(_voting_profiles(L, a.congress, bios, a.refresh))
    lobby = {r["bioguide"]: r["total"] for r in rows}
    for bio, p in profiles.items():
        p["ld203_lobbyist_total"] = lobby.get(bio)
    summary = [{"name": p["name"], "party": p["party"], "ideology_dim1": p["nominate_dim1"],
                "participation": p["participation_rate"], "party_unity": p["party_unity_rate"],
                "against_party": p["votes_against_own_party"]}
               for p in profiles.values()]
    path = _ship("votes.json", {"_source": f"Voteview {a.congress}th Congress roll calls",
                                "congress": a.congress, "members": profiles})
    print(json.dumps({"shipped": str(path), "summary": summary}, indent=2, default=str))


def _parse_bill_number(bill_number):
    """Voteview 'bill_number' (e.g. 'HR 8739', 'S 1234', 'HJRES 1') -> (type, number)
    for the Congress.gov bill endpoint. Returns None for procedural votes."""
    if not bill_number:
        return None
    s = bill_number.upper().replace(" ", "")
    for t in ("HCONRES", "SCONRES", "HJRES", "SJRES", "HRES", "SRES", "HR", "S"):
        if s.startswith(t):
            num = s[len(t):]
            if num.isdigit():
                return t.lower(), num
    return None


def _policy_area(congress, btype, number, key, refresh=False):
    url = f"{SOURCES['congress_gov']['base']}bill/{congress}/{btype}/{number}?api_key={key}"
    try:
        d = json.loads(fetch(url, refresh))
    except urllib.error.HTTPError:
        return None
    return ((d.get("bill") or {}).get("policyArea") or {}).get("name")


def cmd_vote_align(con, a):
    """Tie a member's substantive floor votes to bill policy areas (Congress.gov
    key), so we can ask whether they vote where their donors operate. Capped +
    sampled by design; snapshots assets/vote_align_<bioguide>.json."""
    key = os.environ.get(SOURCES["congress_gov"]["key_env"])
    if not key:
        print(json.dumps({"status": "offline", "message": "set CONGRESS_GOV_API_KEY"})); return
    chamber = (load_snapshot() or {}).get(a.bioguide, {}).get("chamber")
    L = _vv_chamber_letter(chamber) or "H"
    members = _vv_csv("members", L, a.congress, a.refresh)
    icpsr = next((m["icpsr"] for m in members if m.get("bioguide_id") == a.bioguide), None)
    name = next((m["bioname"] for m in members if m.get("bioguide_id") == a.bioguide), a.bioguide)
    if not icpsr:
        print(json.dumps({"status": "not_found"})); return
    rollcalls = {r["rollnumber"]: r for r in _vv_csv("rollcalls", L, a.congress, a.refresh)}
    casts = {row["rollnumber"]: row["cast_code"]
             for row in _vv_csv("votes", L, a.congress, a.refresh) if row["icpsr"] == icpsr}
    # most recent bill-linked votes first, capped to keep the one-off bounded
    linked = []
    for rn, code in casts.items():
        rc = rollcalls.get(rn)
        if not rc:
            continue
        b = _parse_bill_number(rc.get("bill_number"))
        if b:
            linked.append((rc.get("date", ""), rn, code, b, rc.get("bill_number")))
    linked.sort(reverse=True)
    linked = linked[: a.max_bills]
    import collections
    areas, voted = collections.Counter(), []
    for date, rn, code, (bt, num), label in linked:
        pa = _policy_area(a.congress, bt, num, key, a.refresh)
        side = "Yea" if code in VV_YEA else ("Nay" if code in VV_NAY else "Other")
        if pa:
            areas[pa] += 1
        voted.append({"date": date, "bill": label, "policy_area": pa, "vote": side})
    payload = {"_source": f"Voteview {a.congress}th + Congress.gov policy areas",
               "_note": f"sampled: {len(linked)} most recent bill-linked votes",
               "bioguide": a.bioguide, "name": name,
               "policy_area_distribution": areas.most_common(),
               "votes": voted}
    path = _ship(f"vote_align_{a.bioguide}.json", payload)
    print(json.dumps({"shipped": str(path), "name": name,
                      "sampled_votes": len(linked),
                      "policy_area_distribution": areas.most_common(8)}, indent=2, default=str))


def cmd_legislation(con, a):
    """Congress.gov sponsored legislation = an 'act' proxy. Needs a key."""
    key = os.environ.get(SOURCES["congress_gov"]["key_env"])
    if not key:
        print(json.dumps({
            "status": "offline",
            "message": f"Set {SOURCES['congress_gov']['key_env']} to enable the "
                       "'act' leg (votes / sponsored bills) from Congress.gov. "
                       "Get a free key at https://api.congress.gov/sign-up/. "
                       "Results are cached after first fetch for offline re-runs."}))
        return
    url = (f"{SOURCES['congress_gov']['base']}member/{a.bioguide}/sponsored-legislation"
           f"?api_key={key}&limit=20")
    try:
        data = json.loads(fetch(url, a.refresh))
    except urllib.error.HTTPError as e:
        print(json.dumps({"status": "error", "code": e.code})); return
    bills = [{"number": b.get("number"), "title": (b.get("title") or "")[:120],
              "type": b.get("type"), "date": b.get("introducedDate")}
             for b in data.get("sponsoredLegislation", [])]
    print(json.dumps({"bioguide": a.bioguide, "sponsored": bills}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("refresh-committees")
    p = sub.add_parser("committee"); p.add_argument("bioguide")
    p = sub.add_parser("annotate-gatekeeper")
    p.add_argument("--year", type=int); p.add_argument("--filer", choices=["lobbyist", "organization"])
    p.add_argument("--top", type=int, default=20)
    p = sub.add_parser("legislation")
    p.add_argument("bioguide"); p.add_argument("--congress", type=int, default=119)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("fara")
    p.add_argument("names", nargs="*"); p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("fec")
    p.add_argument("name"); p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("enrich-act")  # Tier 1: sponsored legislation for top recipients
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--filer", choices=["lobbyist", "organization"], default="lobbyist")
    p.add_argument("--top", type=int, default=12); p.add_argument("--limit", type=int, default=20)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("enrich-finance")  # Tier 2: FEC receipts for top recipients
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--filer", choices=["lobbyist", "organization"], default="lobbyist")
    p.add_argument("--top", type=int, default=12); p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("votes")  # Voteview: one member's roll-call profile (no key)
    p.add_argument("bioguide"); p.add_argument("--congress", type=int, default=119)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("enrich-votes")  # Voteview profiles for top recipients (no key)
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--filer", choices=["lobbyist", "organization"], default="lobbyist")
    p.add_argument("--top", type=int, default=12); p.add_argument("--congress", type=int, default=119)
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("vote-align")  # Voteview votes x Congress.gov policy areas (key)
    p.add_argument("bioguide"); p.add_argument("--congress", type=int, default=119)
    p.add_argument("--max-bills", type=int, default=80, dest="max_bills")
    p.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    C.load_credentials()  # pull keys from gitignored credentials.env if present
    if a.cmd == "refresh-committees":
        refresh_committees(); return
    con = C.connect()
    {"committee": cmd_committee, "annotate-gatekeeper": cmd_annotate_gatekeeper,
     "legislation": cmd_legislation, "fara": cmd_fara, "fec": cmd_fec,
     "enrich-act": cmd_enrich_act, "enrich-finance": cmd_enrich_finance,
     "votes": cmd_votes, "enrich-votes": cmd_enrich_votes,
     "vote-align": cmd_vote_align}[a.cmd](con, a)
    con.close()


if __name__ == "__main__":
    main()
