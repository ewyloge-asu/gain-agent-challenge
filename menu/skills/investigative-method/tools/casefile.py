#!/usr/bin/env python3
"""
Case file — durable, human-inspectable state for a records investigation.

Keeps everything a reporter (or the next session) needs to pick the work back up:
  brief.md         the scope (question / scope / finding bar) — human-owned, from scope.py
  beatpack.json     the domain pack picked at scoping — from scope.py
  threads/*.md      one file per lead, with a small front-matter block + free-text notes
  findings.json     findings that graduated from threads, and legal_flags for the panel/lawyer
  entities.json     resolved entities (canonical id, display name, status, why it matters)
  journal.jsonl     append-only session log ("what did I do, what did I learn")

Design goals: standard library only, plain text / JSON so a human can read and hand-edit
everything, and no dependency on anything outside this skill.

Thread front matter is a tiny "key: value" block between `---` lines. Supported value
shapes: bare string, integer, and `[a, b, c]` lists. Anything else is kept as a raw string.

Usage:
  python3 casefile.py --dir casefile init
  python3 casefile.py --dir casefile brief
  python3 casefile.py --dir casefile new-thread --title "..." --priority 2 \
      --next-action "..." --source-records prov_1,prov_2
  python3 casefile.py --dir casefile update-status T003 --to chasing --next-action "..."
  python3 casefile.py --dir casefile update-status T003 --to cold --reason "..."
  python3 casefile.py --dir casefile list [--status chasing]
  python3 casefile.py --dir casefile log "checked FEC filings for entity X"
  python3 casefile.py --dir casefile finding --title "..." --summary "..." \
      --source-records prov_1,prov_2
  python3 casefile.py --dir casefile legal-flag --issue "..." --status open \
      --source-records prov_1
  python3 casefile.py --dir casefile entity --group people --id jdoe \
      --display "Jane Doe" --status confirmed --why "chairs the committee"
  python3 casefile.py --dir casefile lint
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


# --- tiny front-matter codec (stdlib only, no PyYAML dependency) -------------

def _parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [p.strip().strip('"').strip("'") for p in inner.split(",")]
    if raw.startswith('"') and raw.endswith('"') or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    return raw


def _format_value(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def parse_front_matter(text: str):
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    meta = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = _parse_value(val)
    return meta, body


def render_front_matter(meta: dict, body: str) -> str:
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {_format_value(v)}")
    lines.append("---")
    lines.append(body.rstrip("\n"))
    lines.append("")
    return "\n".join(lines)


# --- case file -----------------------------------------------------------

class CaseFile:
    STATUSES = ("open", "chasing", "confirmed", "cold", "killed")

    def __init__(self, root: str):
        self.root = os.path.abspath(root)

    def exists(self) -> bool:
        return os.path.isdir(self.root)

    @property
    def threads_dir(self):
        return os.path.join(self.root, "threads")

    @property
    def findings_path(self):
        return os.path.join(self.root, "findings.json")

    @property
    def entities_path(self):
        return os.path.join(self.root, "entities.json")

    @property
    def journal_path(self):
        return os.path.join(self.root, "journal.jsonl")

    @property
    def brief_path(self):
        return os.path.join(self.root, "brief.md")

    # -- init --

    def init(self):
        os.makedirs(self.threads_dir, exist_ok=True)
        if not os.path.exists(self.brief_path):
            with open(self.brief_path, "w") as f:
                f.write(
                    "# Case Brief\n\n"
                    "_No scope recorded yet. Run tools/scope.py --interactive "
                    "(or edit this file directly) before analysis.\n"
                )
        for path, default in (
            (self.findings_path, {"findings": [], "legal_flags": []}),
            (self.entities_path, {}),
        ):
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump(default, f, indent=2)
        if not os.path.exists(self.journal_path):
            open(self.journal_path, "w").close()

    # -- threads --

    def _thread_files(self):
        return sorted(glob.glob(os.path.join(self.threads_dir, "*.md")))

    def threads(self):
        out = []
        for path in self._thread_files():
            with open(path, encoding="utf-8") as f:
                meta, body = parse_front_matter(f.read())
            meta.setdefault("id", os.path.splitext(os.path.basename(path))[0])
            out.append({"meta": meta, "body": body, "path": path})
        return out

    def _next_thread_id(self) -> str:
        nums = []
        for f in self._thread_files():
            m = re.search(r"(\d+)", os.path.basename(f))
            if m:
                nums.append(int(m.group(1)))
        return f"T{(max(nums) + 1) if nums else 1:03d}"

    def new_thread(self, title: str, priority: int = 3, next_action: str = "",
                   source_records=None, status: str = "open") -> str:
        tid = self._next_thread_id()
        meta = {
            "id": tid,
            "title": title,
            "status": status,
            "priority": priority,
            "next_action": next_action,
        }
        if source_records:
            meta["source_records"] = source_records
        path = os.path.join(self.threads_dir, f"{tid}.md")
        with open(path, "w") as f:
            f.write(render_front_matter(meta, ""))
        return tid

    def update_thread(self, thread_id: str, **changes):
        path = os.path.join(self.threads_dir, f"{thread_id}.md")
        if not os.path.exists(path):
            raise SystemExit(f"! no such thread: {thread_id}")
        with open(path, encoding="utf-8") as f:
            meta, body = parse_front_matter(f.read())
        for k, v in changes.items():
            if v is None:
                continue
            meta[k] = v
        with open(path, "w") as f:
            f.write(render_front_matter(meta, body))

    # -- findings / legal flags --

    def findings(self) -> dict:
        if not os.path.exists(self.findings_path):
            return {"findings": [], "legal_flags": []}
        with open(self.findings_path, encoding="utf-8") as f:
            doc = json.load(f)
        doc.setdefault("findings", [])
        doc.setdefault("legal_flags", [])
        return doc

    def _save_findings(self, doc: dict):
        with open(self.findings_path, "w") as f:
            json.dump(doc, f, indent=2)

    def add_finding(self, title: str, summary: str, source_records) -> str:
        doc = self.findings()
        fid = f"F{len(doc['findings']) + 1:03d}"
        doc["findings"].append({
            "id": fid, "title": title, "summary": summary,
            "source_records": source_records or [],
        })
        self._save_findings(doc)
        return fid

    def add_legal_flag(self, issue: str, status: str, source_records) -> str:
        doc = self.findings()
        lid = f"L{len(doc['legal_flags']) + 1:03d}"
        doc["legal_flags"].append({
            "id": lid, "issue": issue, "status": status,
            "source_records": source_records or [],
        })
        self._save_findings(doc)
        return lid

    # -- entities --

    def entities(self) -> dict:
        if not os.path.exists(self.entities_path):
            return {}
        with open(self.entities_path, encoding="utf-8") as f:
            return json.load(f)

    def upsert_entity(self, group: str, canonical_id: str, display: str,
                       status: str, why: str):
        doc = self.entities()
        doc.setdefault(group, [])
        for en in doc[group]:
            if en.get("canonical_id") == canonical_id:
                en.update({"display": display, "status": status, "why": why})
                break
        else:
            doc[group].append({"canonical_id": canonical_id, "display": display,
                                "status": status, "why": why})
        with open(self.entities_path, "w") as f:
            json.dump(doc, f, indent=2)

    # -- journal --

    def log(self, message: str):
        entry = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "note": message}
        with open(self.journal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def journal(self):
        if not os.path.exists(self.journal_path):
            return []
        with open(self.journal_path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # -- lint --

    def lint(self):
        problems = []
        for t in self.threads():
            m = t["meta"]
            st = m.get("status", "open")
            if st not in self.STATUSES:
                problems.append(f"{m.get('id')}: unknown status '{st}'")
            if st in ("chasing", "open") and not m.get("next_action"):
                problems.append(f"{m.get('id')} ({st}): missing next_action")
            if st in ("cold", "killed") and not m.get("reason"):
                problems.append(f"{m.get('id')} ({st}): missing reason")
            if st == "confirmed" and not m.get("source_records"):
                problems.append(f"{m.get('id')} (confirmed): no source_records — "
                                 "nothing to round-trip to a raw source")
        doc = self.findings()
        for f in doc["findings"]:
            if not f.get("source_records"):
                problems.append(f"finding {f.get('id')}: no source_records")
        for lf in doc["legal_flags"]:
            if not lf.get("source_records"):
                problems.append(f"legal_flag {lf.get('id')}: no source_records")
        return problems


# --- CLI -------------------------------------------------------------------

def _print_brief(cf: CaseFile):
    if os.path.exists(cf.brief_path):
        print(open(cf.brief_path, encoding="utf-8").read())
    else:
        print("(no brief.md yet — run init)")
    threads = cf.threads()
    if threads:
        print(f"\n## Threads ({len(threads)})\n")
        for t in threads:
            m = t["meta"]
            print(f"  [{m.get('status','open'):>9}] {m.get('id')}  {m.get('title','')}")
    j = cf.journal()
    if j:
        print(f"\n## Last journal entry\n  {j[-1]['ts']}  {j[-1]['note']}")


def main() -> int:
    p = argparse.ArgumentParser(description="Case-file: durable investigation state")
    p.add_argument("--dir", default="casefile")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("brief")
    sub.add_parser("lint")

    sp = sub.add_parser("list")
    sp.add_argument("--status")

    sp = sub.add_parser("new-thread")
    sp.add_argument("--title", required=True)
    sp.add_argument("--priority", type=int, default=3)
    sp.add_argument("--next-action", default="")
    sp.add_argument("--source-records", default="")
    sp.add_argument("--status", default="open")

    sp = sub.add_parser("update-status")
    sp.add_argument("thread_id")
    sp.add_argument("--to", dest="status", required=True)
    sp.add_argument("--next-action")
    sp.add_argument("--reason")
    sp.add_argument("--source-records")

    sp = sub.add_parser("log")
    sp.add_argument("message")

    sp = sub.add_parser("finding")
    sp.add_argument("--title", required=True)
    sp.add_argument("--summary", default="")
    sp.add_argument("--source-records", default="")

    sp = sub.add_parser("legal-flag")
    sp.add_argument("--issue", required=True)
    sp.add_argument("--status", default="open")
    sp.add_argument("--source-records", default="")

    sp = sub.add_parser("entity")
    sp.add_argument("--group", required=True)
    sp.add_argument("--id", dest="canonical_id", required=True)
    sp.add_argument("--display", required=True)
    sp.add_argument("--status", default="unconfirmed")
    sp.add_argument("--why", default="")

    args = p.parse_args()
    cf = CaseFile(args.dir)

    def split_csv(s):
        return [x.strip() for x in s.split(",") if x.strip()] if s else []

    if args.cmd == "init":
        cf.init()
        print(f"✓ case file ready at {cf.root}")
        return 0

    if not cf.exists():
        print(f"! no case file at {args.dir} — run `init` first", file=sys.stderr)
        return 2

    if args.cmd == "brief":
        _print_brief(cf)
    elif args.cmd == "list":
        for t in cf.threads():
            m = t["meta"]
            if args.status and m.get("status") != args.status:
                continue
            print(f"[{m.get('status','open'):>9}] {m.get('id')}  {m.get('title','')}"
                  f"  (next: {m.get('next_action','')})")
    elif args.cmd == "new-thread":
        tid = cf.new_thread(args.title, args.priority, args.next_action,
                             split_csv(args.source_records), args.status)
        print(f"✓ opened thread {tid}: {args.title}")
    elif args.cmd == "update-status":
        cf.update_thread(args.thread_id, status=args.status,
                          next_action=args.next_action, reason=args.reason,
                          source_records=split_csv(args.source_records) or None)
        print(f"✓ {args.thread_id} → {args.status}")
    elif args.cmd == "log":
        e = cf.log(args.message)
        print(f"✓ logged @ {e['ts']}")
    elif args.cmd == "finding":
        fid = cf.add_finding(args.title, args.summary, split_csv(args.source_records))
        print(f"✓ finding {fid}: {args.title}")
    elif args.cmd == "legal-flag":
        lid = cf.add_legal_flag(args.issue, args.status, split_csv(args.source_records))
        print(f"✓ legal flag {lid} ({args.status}): {args.issue}")
    elif args.cmd == "entity":
        cf.upsert_entity(args.group, args.canonical_id, args.display, args.status,
                          args.why)
        print(f"✓ entity [{args.group}] {args.canonical_id} ({args.status})")
    elif args.cmd == "lint":
        problems = cf.lint()
        if not problems:
            print("✓ lint clean — every confirmed/finding/legal_flag has a source; "
                  "every open/chasing thread has a next_action.")
        else:
            print(f"! {len(problems)} issue(s):")
            for pr in problems:
                print(f"  - {pr}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
