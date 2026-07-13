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

import json
import sys
from pathlib import Path

import common as C


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def seed_members_from_roster(con):
    """Seed the members table from the authoritative congress-legislators roster
    snapshot (assets/committees.json) so honoree resolution can reach EVERY member
    — not just the ones who happen to appear in the press corpus. Without this the
    leaderboard is silently biased toward press-active (Senate-heavy) members and
    drops House members like committee chairs. The roster is authoritative for
    identity fields: it backfills missing party/state/chamber and its canonical
    name (official_full) replaces press-derived variants; press name forms are
    kept as aliases at resolution time."""
    path = Path(__file__).resolve().parent.parent / "assets" / "committees.json"
    if not path.exists():
        log("[roster] no committees.json snapshot; skipping member seed")
        return
    data = json.loads(path.read_text())
    members = data.get("members", {})
    rows = []
    for bio, info in members.items():
        name = (info.get("name") or "").strip()
        if not name:
            continue
        chamber = info.get("chamber")
        if not chamber:
            for role in info.get("roles", []):
                c = (role.get("committee") or "")
                if c.startswith("Senate"):
                    chamber = "Senate"
                    break
                if c.startswith("House"):
                    chamber = "House"
                    break
        rows.append((bio, name, C.lastname_key(name),
                     info.get("party"), info.get("state"), chamber))
    cur = con.cursor()
    before = cur.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    cur.executemany("INSERT OR IGNORE INTO members VALUES (?,?,?,?,?,?)", rows)
    # Backfill identity fields on rows that predate the enriched snapshot (or came
    # from a press corpus that lacked them) so no member reads party=None.
    cur.executemany(
        """UPDATE members SET party=COALESCE(party,?), state=COALESCE(state,?),
                              chamber=COALESCE(chamber,?)
           WHERE bioguide=?""",
        [(r[3], r[4], r[5], r[0]) for r in rows])
    # The roster's name is canonical (official_full, e.g. "J. French Hill", not
    # "J. Hill") — adopt it wherever it differs, and keep name_key in sync.
    cur.executemany(
        "UPDATE members SET name=?, name_key=? WHERE bioguide=? AND name<>?",
        [(r[1], r[2], r[0], r[1]) for r in rows])
    # One party vocabulary: press-derived rows say "Republican"/"Democrat",
    # the roster says "R"/"D" — normalize to the single-letter form.
    cur.execute("""UPDATE members SET party = CASE party
                     WHEN 'Republican' THEN 'R' WHEN 'Democrat' THEN 'D'
                     WHEN 'Democratic' THEN 'D' WHEN 'Independent' THEN 'I'
                     ELSE party END""")
    con.commit()
    after = cur.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    filled = cur.execute(
        "SELECT COUNT(*) FROM members WHERE party IS NOT NULL AND state IS NOT NULL"
    ).fetchone()[0]
    log(f"[roster] roster members={len(rows)} | members table {before} -> {after} "
        f"(+{after - before} seeded) | rows with party+state: {filled}/{after}")


def resolve_honorees(con):
    cur = con.cursor()
    # member lookup tables — recompute keys fresh from name so improvements to
    # lastname_key take effect without a re-ingest, and roster-seeded members are
    # keyed consistently with press-derived ones.
    members = list(cur.execute("SELECT bioguide, name FROM members"))
    # Alias name forms per member: the press corpus carries the spoken/nickname
    # form ("Mike Turner") where the roster is canonical ("Michael R. Turner");
    # index both so either form of an honoree resolves.
    aliases = {}
    for r in cur.execute(
            """SELECT DISTINCT member_bioguide, member_name FROM press_releases
               WHERE member_bioguide IS NOT NULL AND member_name IS NOT NULL"""):
        aliases.setdefault(r["member_bioguide"], set()).add(r["member_name"])
    by_key = {}
    by_last = {}
    for m in members:
        names = {m["name"]} | aliases.get(m["bioguide"], set())
        keys = set()
        for name in names:
            keys.add(C.lastname_key(name))
            # Canonical names may lead with an initial ("C. Scott Franklin",
            # "J. French Hill") while honorees write the spoken form ("Scott
            # Franklin") — index the initial-dropped alias too.
            toks = C.norm_person(name).split()
            if len(toks) >= 3 and len(toks[0]) == 1:
                keys.add(f"{toks[-1]}|{toks[1]}")
        for key in keys:
            if key:
                by_key.setdefault(key, set()).add(m["bioguide"])
                by_last.setdefault(key.split("|")[0], set()).add(m["bioguide"])

    # aggregate every distinct honoree with its money footprint
    rows = cur.execute(
        """SELECT honoree_name, honoree_key,
                  COUNT(*) n_items, COALESCE(SUM(amount),0) total
           FROM contribution_items
           WHERE honoree_name IS NOT NULL AND TRIM(honoree_name) <> ''
           GROUP BY honoree_name, honoree_key"""
    ).fetchall()

    def match_person(key):
        """(bioguide, method) for a LAST|FIRST key; require a unique member."""
        cands = by_key.get(key)
        if cands and len(cands) == 1:
            return next(iter(cands)), "exact"
        if cands and len(cands) > 1:
            return None, "ambiguous_key"
        last = key.split("|")[0] if key else ""
        lc = by_last.get(last)
        if lc and len(lc) == 1:
            return next(iter(lc)), "lastname_unique"
        return None, "unmatched"

    out = []
    stats = {"exact": 0, "lastname_unique": 0,
             "campaign_exact": 0, "campaign_lastname_unique": 0, "unmatched": 0}
    for r in rows:
        # recompute the key fresh from the honoree text (do not trust the value
        # stored at ingest time, which used an older normalization).
        key = C.lastname_key(r["honoree_name"])
        bio, method = match_person(key)
        if bio is None:
            # Campaign-committee honorees ("Guthrie for Congress", "Friends of
            # Glenn Thompson"): extract the candidate name, then match it the
            # same way — still requiring a unique member.
            cand = C.campaign_candidate_name(r["honoree_name"])
            if cand:
                cbio, cmethod = match_person(C.lastname_key(cand))
                if cbio is not None:
                    bio, method = cbio, "campaign_" + cmethod
        if method in stats:
            stats[method] += 1
        else:  # ambiguous_key or any other non-terminal method
            stats["unmatched"] += 1
        out.append((r["honoree_name"], key, bio, method,
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
        f"lastname_unique={stats['lastname_unique']} "
        f"campaign_exact={stats['campaign_exact']} "
        f"campaign_lastname_unique={stats['campaign_lastname_unique']} "
        f"unmatched={stats['unmatched']}")
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
    seed_members_from_roster(con)
    resolve_honorees(con)
    build_bridge(con)
    con.close()


if __name__ == "__main__":
    main()
