"""Cross-dataset entity resolution.

Two deterministic resolvers, both written to generalize beyond this corpus:

  1. honoree -> member: maps the free-text `honoree_name` on Senate LD-203
     contribution line items to a congressional member `bioguide_id`. Titles
     ("Sen.", "Rep.") and casing vary; we key on LAST|FIRST and fall back to a
     unique-last-name match. This is the "pay -> named member" link.

  2. senateID bridge: links House LD-2 filings to Senate filings for the SAME
     engagement using the confirmed `senateID = registrantID-clientID` format,
     with a normalized-name fallback when the bridge id is absent. This is the
     Senate<->House reconciliation backbone.

Both write their output to tables so every later query is a cheap join and
every match records its method (auditable).

Usage: python resolve_entities.py
"""
from __future__ import annotations

import sys
import common as C


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def resolve_honorees(con):
    cur = con.cursor()
    # member lookup tables
    members = list(cur.execute("SELECT bioguide, name, name_key FROM members"))
    by_key = {}
    by_last = {}
    for m in members:
        if m["name_key"]:
            by_key.setdefault(m["name_key"], []).append(m["bioguide"])
            last = m["name_key"].split("|")[0]
            by_last.setdefault(last, set()).add(m["bioguide"])

    # aggregate every distinct honoree with its money footprint
    rows = cur.execute(
        """SELECT honoree_name, honoree_key,
                  COUNT(*) n_items, COALESCE(SUM(amount),0) total
           FROM contribution_items
           WHERE honoree_name IS NOT NULL AND TRIM(honoree_name) <> ''
           GROUP BY honoree_name, honoree_key"""
    ).fetchall()

    out = []
    stats = {"exact": 0, "lastname_unique": 0, "unmatched": 0}
    for r in rows:
        key = r["honoree_key"] or ""
        bio = None
        method = "unmatched"
        cands = by_key.get(key)
        if cands and len(set(cands)) == 1:
            bio, method = cands[0], "exact"
        elif cands and len(set(cands)) > 1:
            bio, method = None, "ambiguous_key"
        else:
            last = key.split("|")[0] if key else ""
            lc = by_last.get(last)
            if lc and len(lc) == 1:
                bio, method = next(iter(lc)), "lastname_unique"
        if method in stats:
            stats[method] += 1
        elif method == "ambiguous_key":
            stats["unmatched"] += 1
        out.append((r["honoree_name"], r["honoree_key"], bio, method,
                    r["n_items"], r["total"]))
    cur.execute("DELETE FROM honoree_resolution")
    cur.executemany(
        "INSERT OR REPLACE INTO honoree_resolution VALUES (?,?,?,?,?,?)", out)
    con.commit()

    matched_items = cur.execute(
        """SELECT COUNT(*) FROM contribution_items ci
           JOIN honoree_resolution hr ON ci.honoree_name = hr.honoree_name
           WHERE hr.bioguide IS NOT NULL""").fetchone()[0]
    total_items = cur.execute(
        "SELECT COUNT(*) FROM contribution_items WHERE honoree_name IS NOT NULL").fetchone()[0]
    log(f"[honoree] {len(out)} distinct honorees | exact={stats['exact']} "
        f"lastname_unique={stats['lastname_unique']} unmatched={stats['unmatched']}")
    log(f"[honoree] contribution items resolved to a member: {matched_items}/{total_items} "
        f"({100*matched_items/max(total_items,1):.1f}%)")


def build_bridge(con):
    cur = con.cursor()
    cur.execute("DELETE FROM xref_engagements")
    # Primary: senateID bridge (registrant_id + client_id both present)
    bridged = cur.execute(
        """SELECT h.house_id, h.senate_registrant_id, h.senate_client_id,
                  MIN(s.filing_uuid) suuid,
                  MIN(s.registrant_name) rname, MIN(s.client_name) cname
           FROM house_filings h
           JOIN senate_filings s
             ON s.registrant_id = h.senate_registrant_id
            AND s.client_id     = h.senate_client_id
           WHERE h.senate_registrant_id IS NOT NULL
             AND h.senate_client_id IS NOT NULL
           GROUP BY h.house_id""").fetchall()
    rows = [(b["senate_registrant_id"], b["senate_client_id"], b["house_id"],
             b["suuid"], b["rname"], b["cname"], "senateID_bridge") for b in bridged]

    bridged_ids = {b["house_id"] for b in bridged}

    # Fallback: normalized org+client name match for House filings whose
    # senateID didn't resolve to a Senate filing in the store.
    namematch = cur.execute(
        """SELECT h.house_id, h.senate_registrant_id, h.senate_client_id,
                  MIN(s.filing_uuid) suuid,
                  MIN(s.registrant_name) rname, MIN(s.client_name) cname
           FROM house_filings h
           JOIN senate_filings s
             ON s.registrant_name_norm = h.organization_name_norm
            AND s.client_name_norm     = h.client_name_norm
           WHERE h.organization_name_norm <> '' AND h.client_name_norm <> ''
           GROUP BY h.house_id""").fetchall()
    for b in namematch:
        if b["house_id"] in bridged_ids:
            continue
        rows.append((b["senate_registrant_id"], b["senate_client_id"], b["house_id"],
                     b["suuid"], b["rname"], b["cname"], "name_match"))

    cur.executemany("INSERT INTO xref_engagements VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()

    n_house = cur.execute("SELECT COUNT(*) FROM house_filings").fetchone()[0]
    n_bridge = sum(1 for r in rows if r[6] == "senateID_bridge")
    n_name = sum(1 for r in rows if r[6] == "name_match")
    log(f"[bridge] house filings={n_house} | linked via senateID={n_bridge} "
        f"| linked via name fallback={n_name} | total linked={len(rows)} "
        f"({100*len(rows)/max(n_house,1):.1f}%)")


def main():
    con = C.connect()
    C.init_schema(con)
    resolve_honorees(con)
    build_bridge(con)
    con.close()


if __name__ == "__main__":
    main()
