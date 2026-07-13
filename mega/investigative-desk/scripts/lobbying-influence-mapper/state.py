"""Investigation-state tracker.

Keeps a long-running investigation oriented across sessions so the agent (and
the journalist) never has to re-brief from scratch: which threads are open,
which went cold, which entities matter, and which findings are locked. Backed
by a single JSON file so it is diffable and human-editable.

Usage:
  python state.py thread add "pay-the-gavel" --note "lobbyist money vs chairs"
  python state.py thread set pay-the-gavel --status confirmed
  python state.py entity add "Brett Guthrie" --kind member --id G000558 --note "E&C chair"
  python state.py lead add "Tencent hired John McEntee" --status hot
  python state.py show
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import common as C

STATUSES = ["open", "hot", "confirmed", "cold", "closed", "flagged"]


def _path():
    p = C.workdir() / "state" / "investigation.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load():
    p = _path()
    if p.exists():
        return json.loads(p.read_text())
    return {"threads": {}, "entities": {}, "leads": [], "log": []}


def _save(s):
    s["log"].append({"ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    _path().write_text(json.dumps(s, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("thread").add_subparsers(dest="op", required=True)
    ta = t.add_parser("add"); ta.add_argument("name"); ta.add_argument("--note", default="")
    ts = t.add_parser("set"); ts.add_argument("name"); ts.add_argument("--status", choices=STATUSES, required=True); ts.add_argument("--note", default="")

    e = sub.add_parser("entity").add_subparsers(dest="op", required=True)
    ea = e.add_parser("add"); ea.add_argument("name"); ea.add_argument("--kind", default="org"); ea.add_argument("--id", default=""); ea.add_argument("--note", default="")

    L = sub.add_parser("lead").add_subparsers(dest="op", required=True)
    la = L.add_parser("add"); la.add_argument("text"); la.add_argument("--status", choices=STATUSES, default="open")

    sub.add_parser("show")

    a = ap.parse_args()
    s = _load()
    if a.cmd == "thread" and a.op == "add":
        s["threads"][a.name] = {"status": "open", "note": a.note,
                                 "created": time.strftime("%Y-%m-%d")}
    elif a.cmd == "thread" and a.op == "set":
        s["threads"].setdefault(a.name, {})["status"] = a.status
        if a.note:
            s["threads"][a.name]["note"] = a.note
    elif a.cmd == "entity" and a.op == "add":
        s["entities"][a.name] = {"kind": a.kind, "id": a.id, "note": a.note}
    elif a.cmd == "lead" and a.op == "add":
        s["leads"].append({"text": a.text, "status": a.status,
                            "added": time.strftime("%Y-%m-%d")})
    elif a.cmd == "show":
        print(json.dumps({k: v for k, v in s.items() if k != "log"}, indent=2))
        return
    _save(s)
    print(f"ok ({a.cmd} {getattr(a,'op','')})", file=sys.stderr)


if __name__ == "__main__":
    main()
