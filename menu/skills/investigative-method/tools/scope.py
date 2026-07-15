#!/usr/bin/env python3
"""
S0 — Scope & framing (the antecedent to analysis).

Pins down WHAT is being investigated before any analysis runs, then materializes that
scope as the case file's brief.md and a beatpack.json that tells the rest of the pipeline
which domain pack + outside sources to use. This is what lets the tool run on ANY dataset:
the scope selects (or synthesizes) the beat-pack.

Usage:
  # interactive (asks clarifying questions):
  python3 scope.py --dir casefile --interactive

  # non-interactive (scriptable / reproducible):
  python3 scope.py --dir casefile \
      --question "Do lobbyist contributions concentrate on committee gatekeepers?" \
      --entities "committee chairs, registered lobbyists" \
      --from 2025-01-01 --to 2025-12-31 \
      --jurisdiction "US federal" --domain lobbying \
      --finding-bar "a sourced pattern a reporter would chase, not a dataset summary"

Standard library only. No network. Writes brief.md + beatpack.json under --dir.
"""
import argparse
import datetime as dt
import json
import os
import sys

# --- Beat-pack knowledge -----------------------------------------------------
# A beat-pack is a MAP (which data, which entity keys, which laws, which outside
# sources). It is never the answer — the primary data/text always is — but it lets
# the pipeline jump straight to the right sources for a domain.

LOBBYING_PACK = {
    "domain": "lobbying",
    "summary": "US federal lobbying & money-in-politics (LDA filings, LD-203 "
               "contributions, congressional press).",
    "entity_keys": ["bioguide_id (members)", "senateID/houseID (filing bridge)",
                    "registrant/client names (resolve)"],
    "external_sources": [
        {"name": "congress-legislators", "kind": "roster", "needs_key": False,
         "why": "verify committee roles (the 'gatekeep' leg)"},
        {"name": "Congress.gov", "kind": "api", "needs_key": True,
         "why": "sponsored bills + policy areas (the 'act' leg)"},
        {"name": "FEC", "kind": "api", "needs_key": True,
         "why": "campaign-finance denominator (lobbyist $ as share of receipts)"},
        {"name": "Voteview", "kind": "bulk", "needs_key": False,
         "why": "roll-call votes / party-unity context"},
        {"name": "FARA", "kind": "bulk", "needs_key": False,
         "why": "foreign-agent cross-check"},
    ],
    "law_packs": ["us-influence-law", "us-campaign-finance-law"],
    "anomaly_rules": "round-number million income, self-referential registrant/client, "
                     "many unrelated issue codes, income>>peers.",
    "engine_notes": "Load filings into a dataframe, resolve entities to canonical ids, "
                    "and de-dup amendments (a filing amends a prior one; keep the latest "
                    "version per registrant/client/period) before any spend aggregate.",
}

GENERIC_PACK = {
    "domain": "generic",
    "summary": "No prebuilt pack for this beat — synthesize a minimal one.",
    "entity_keys": ["<the join key(s) in your data — resolve to canonical ids>"],
    "external_sources": [],
    "law_packs": [],
    "anomaly_rules": "learn the baseline first (types, distributions, normal ranges), "
                     "then flag deviations from normal.",
    "engine_notes": "Profile the data first (pandas .describe()/.info(), groupbys, "
                    "correlations) before spending reasoning budget on it; use "
                    "tools/find_data.py to locate relevant outside datasets/APIs for "
                    "this topic.",
}

LOBBYING_HINTS = ("lobby", "lobbying", "lobbyist", "influence", "campaign finance",
                  "lda", "ld-203", "fara", "registrant", "revolving door", "pac",
                  "contribution", "committee", "congress")


def pick_beatpack(domain: str, question: str) -> dict:
    domain = (domain or "").strip()
    if domain.lower() in ("lobbying", "influence", "campaign-finance"):
        return dict(LOBBYING_PACK)
    # An explicitly stated non-lobbying domain WINS over hint auto-detection —
    # the user's framing is authoritative; hints only fill in when no domain given.
    if not domain:
        import re
        text = question.lower()
        if any(re.search(rf"\b{re.escape(h)}\b", text) for h in LOBBYING_HINTS):
            pack = dict(LOBBYING_PACK)
            pack["auto_detected"] = True
            return pack
    pack = dict(GENERIC_PACK)
    if domain:
        pack["domain"] = domain
        pack["summary"] = f"Custom beat '{domain}' — synthesize a minimal pack."
    return pack


CLARIFYING_QUESTIONS = [
    ("question", "What is the ONE question this investigation is trying to answer?"),
    ("entities", "Who/what are the key entities (people, orgs, agencies)? comma-separated"),
    ("date_from", "Earliest date in scope (YYYY-MM-DD, blank = all)?"),
    ("date_to", "Latest date in scope (YYYY-MM-DD, blank = all)?"),
    ("jurisdiction", "Jurisdiction / geography (e.g. 'US federal')?"),
    ("domain", "Domain/beat (e.g. 'lobbying', 'procurement', 'healthcare')?"),
    ("finding_bar", "What would count as a real finding (not just a data summary)?"),
    ("data_path", "Where is the primary data? (file or folder path)"),
]


def ask_interactive() -> dict:
    print("\nS0 — Scope & framing. Answer a few clarifying questions "
          "(Enter to skip any).\n")
    ans = {}
    for key, prompt in CLARIFYING_QUESTIONS:
        try:
            ans[key] = input(f"  • {prompt}\n    > ").strip()
        except EOFError:
            ans[key] = ""
    return ans


def render_brief(a: dict, pack: dict) -> str:
    scope_bits = []
    if a.get("entities"):
        scope_bits.append(f"- Entities: {a['entities']}")
    span = " to ".join([x for x in (a.get("date_from"), a.get("date_to")) if x])
    if span:
        scope_bits.append(f"- Timeframe: {span}")
    if a.get("jurisdiction"):
        scope_bits.append(f"- Jurisdiction: {a['jurisdiction']}")
    if a.get("domain"):
        scope_bits.append(f"- Domain/beat: {a['domain']}  (beat-pack: {pack['domain']})")
    if a.get("data_path"):
        scope_bits.append(f"- Primary data: {a['data_path']}")
    scope_block = "\n".join(scope_bits) if scope_bits else "- (scope not yet specified)"
    finding_bar = a.get("finding_bar") or (
        "A sourced pattern a reporter would chase (undisclosed relationship, timing "
        "anomaly, spending pattern) — not a summary of what the dataset contains.")
    sources = ", ".join(s["name"] for s in pack["external_sources"]) or \
        "use tools/find_data.py"
    law = ", ".join(pack["law_packs"]) or "(none — synthesize if legal Qs arise)"
    lines = [
        "# Case Brief",
        "",
        f"_Generated by S0 scope-framing on {dt.date.today().isoformat()}. Human-owned "
        "after this: edit freely as the investigation sharpens._",
        "",
        "## The question",
        a.get("question") or "(state the one question here)",
        "",
        "## Scope",
        scope_block,
        "",
        "## What counts as a finding (the finding bar)",
        finding_bar,
        "",
        f"## Beat-pack selected: `{pack['domain']}`",
        pack["summary"],
        "",
        f"- Entity keys: {', '.join(pack['entity_keys'])}",
        f"- Outside sources to seek: {sources}",
        f"- Law packs: {law}",
        f"- Engine notes: {pack['engine_notes']}",
        "",
        "## Scope-adjustment log",
        "S0 is a loop. If acquisition/analysis suggests the story is broader or narrower",
        "than the above, ask the user, then record the change here (and in the journal).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="S0 scope-framing → case brief + beat-pack")
    p.add_argument("--dir", default="casefile", help="case-file directory")
    p.add_argument("--interactive", action="store_true", help="ask clarifying questions")
    p.add_argument("--question")
    p.add_argument("--entities")
    p.add_argument("--from", dest="date_from")
    p.add_argument("--to", dest="date_to")
    p.add_argument("--jurisdiction")
    p.add_argument("--domain", default="")
    p.add_argument("--finding-bar", dest="finding_bar")
    p.add_argument("--data-path", dest="data_path")
    p.add_argument("--force", action="store_true", help="overwrite existing brief.md")
    args = p.parse_args()

    if args.interactive:
        a = ask_interactive()
    else:
        a = {k: getattr(args, k) or "" for k in
             ("question", "entities", "date_from", "date_to", "jurisdiction",
              "domain", "finding_bar", "data_path")}

    if not a.get("question"):
        print("! No question given. S0 needs at least a question "
              "(--question or --interactive).", file=sys.stderr)
        return 2

    pack = pick_beatpack(a.get("domain", ""), a.get("question", ""))

    os.makedirs(args.dir, exist_ok=True)
    os.makedirs(os.path.join(args.dir, "threads"), exist_ok=True)
    brief_path = os.path.join(args.dir, "brief.md")
    if os.path.exists(brief_path) and not args.force:
        print(f"! {brief_path} exists. Use --force to overwrite (S0 loop = intentional).",
              file=sys.stderr)
        return 3
    with open(brief_path, "w") as f:
        f.write(render_brief(a, pack))
    with open(os.path.join(args.dir, "beatpack.json"), "w") as f:
        json.dump(pack, f, indent=2)

    print(f"\n✓ Scope framed. Wrote:\n  - {brief_path}\n  - "
          f"{os.path.join(args.dir, 'beatpack.json')}")
    print(f"\n  Beat-pack: {pack['domain']}"
          + ("  (auto-detected as lobbying)" if pack.get("auto_detected") else ""))
    print("\nNext:")
    print(f"  1. Find & snapshot outside data: tools/find_data.py \"<topic>\", then "
          f"tools/fetch_source.py \"<url>\" --out-dir {args.dir}/snapshots.")
    print(f"  2. Track leads across sessions: install the case-file skill and run "
          f"../case-file/scripts/casefile.py --dir {args.dir} init (it reads this "
          "brief.md as-is).")
    print(f"  3. Once you have a case file: tools/build_dashboard.py --dir {args.dir} "
          "--out review_dashboard.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
