#!/usr/bin/env python3
"""casefile — deterministic investigation-state tooling for the Case File skill.

No LLM, no third-party packages: pure Python standard library, so every command
(`brief`, `lint`, `update-status`, `log`, `rollup`, `init`) replays identically.
The machine owns the invariants (the state machine, required fields, source
binding); the agent owns the narrative (thread bodies, journal prose).

Case file layout (see references/file_formats.md):

    casefile/
      brief.md            # the question, scope, finding bar (stable, human-owned)
      workflow.md         # the reproducible analysis procedure (optional but recommended)
      entities.yaml       # entity registry: canonical id, type, status, why-it-matters
      threads/T-0042.md   # one file per thread: YAML front-matter + free-text body
      findings.yaml       # confirmed findings, each with >=1 source record id
      journal.md          # append-only, timestamped session log
      .state.json         # derived rollup cache (regenerable; never hand-edited)

Usage:
    python3 casefile.py init        [--dir PATH] [--template PATH]
    python3 casefile.py brief       [--dir PATH]
    python3 casefile.py lint        [--dir PATH] [--corpus-index PATH]
    python3 casefile.py update-status --thread T-0042 --to cold [--reason ...] [--source ID ...] [--dir PATH]
    python3 casefile.py log         --session S3 "message"        [--dir PATH]
    python3 casefile.py rollup      [--dir PATH]

Exit codes: 0 = ok; 1 = lint found problems / invalid transition; 2 = usage error.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys

# --------------------------------------------------------------------------
# Thread state machine (see SKILL.md / case-file-spec.md).
#
#        open --> chasing --> confirmed
#          |         |
#          |         +--> cold  (reason required; revivable to chasing)
#          +---------+--> killed (reason required; terminal)
# --------------------------------------------------------------------------
STATUSES = ("open", "chasing", "confirmed", "cold", "killed")
TRANSITIONS = {
    "open": {"chasing", "cold", "killed"},
    "chasing": {"confirmed", "cold", "killed"},
    "confirmed": set(),          # terminal (a finding, not re-opened here)
    "cold": {"chasing"},         # revive
    "killed": set(),             # terminal
}
REASON_REQUIRED = {"cold", "killed"}
SOURCE_REQUIRED = {"confirmed"}
ACTIVE = {"open", "chasing"}     # must carry a next_action


# ==========================================================================
# Minimal YAML reader (subset sufficient for this skill's files).
# Supports: mappings, block sequences ("- item"), inline flow lists ("[a, b]")
# incl. multi-line, block scalars (">" folded and "|" literal), quoted strings,
# comments, and scalar type coercion. No anchors, tags, or flow maps.
# ==========================================================================
def _strip_inline_comment(s):
    out, quote, i = [], None, 0
    while i < len(s):
        c = s[i]
        if quote:
            out.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            out.append(c)
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out).rstrip()


def _coerce(v):
    v = v.strip()
    if v == "" or v is None:
        return None
    if (v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'"):
        return v[1:-1]
    if v[0] == "[" and v[-1] == "]":
        inner = v[1:-1].strip()
        return [_coerce(x) for x in _split_top_commas(inner)] if inner else []
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d*\.\d+", v):
        return float(v)
    return v


def _split_top_commas(s):
    parts, depth, quote, cur = [], 0, None, []
    for c in s:
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
            cur.append(c)
        elif c in "[":
            depth += 1
            cur.append(c)
        elif c in "]":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p.strip() for p in parts]


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def yaml_load(text):
    # Physical lines, keeping indentation; drop nothing yet (block scalars need raw).
    lines = text.split("\n")
    node, _ = _parse_block(lines, 0, 0)
    return node if node is not None else {}


def _next_content(lines, i):
    """Index of the next non-blank, non-comment-only line at/after i, else len."""
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        return i
    return i


def _parse_block(lines, i, min_indent):
    i = _next_content(lines, i)
    if i >= len(lines):
        return None, i
    ind = _indent(lines[i])
    if ind < min_indent:
        return None, i
    body = _strip_inline_comment(lines[i].strip())
    if body.startswith("- "):
        return _parse_seq(lines, i, ind)
    if body == "-":
        return _parse_seq(lines, i, ind)
    return _parse_map(lines, i, ind)


def _parse_map(lines, i, ind):
    result = {}
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            break
        cur_ind = _indent(lines[i])
        if cur_ind != ind:
            break
        raw = _strip_inline_comment(lines[i].strip())
        m = re.match(r"^([^:]+):(.*)$", raw)
        if not m:
            break
        key = m.group(1).strip().strip('"\'')
        rest = m.group(2).strip()
        if rest in (">", "|", ">-", "|-", ">+", "|+"):
            val, i = _read_block_scalar(lines, i + 1, ind, rest[0])
            result[key] = val
        elif rest.startswith("[") and rest.count("[") != rest.count("]"):
            # multi-line inline flow list
            buf = rest
            i += 1
            while i < len(lines) and buf.count("[") != buf.count("]"):
                buf += " " + _strip_inline_comment(lines[i].strip())
                i += 1
            result[key] = _coerce(buf)
        elif rest == "":
            child, i = _parse_block(lines, i + 1, ind + 1)
            result[key] = child if child is not None else None
        else:
            result[key] = _coerce(rest)
            i += 1
    return result, i


def _parse_seq(lines, i, ind):
    items = []
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            break
        cur_ind = _indent(lines[i])
        if cur_ind != ind:
            break
        raw = _strip_inline_comment(lines[i].strip())
        if not (raw == "-" or raw.startswith("- ")):
            break
        inline = raw[1:].strip()
        if inline == "":
            child, i = _parse_block(lines, i + 1, ind + 1)
            items.append(child)
        elif inline[0] in "\"'[":
            # quoted scalar or inline flow list — never a mapping item
            items.append(_coerce(inline))
            i += 1
        elif re.match(r"^[^:\[\]]+:(\s|$)", inline):
            # sequence item that is itself a mapping; reparse with a virtual map
            synthetic, i = _parse_map_from_inline(lines, i, ind, inline)
            items.append(synthetic)
        else:
            items.append(_coerce(inline))
            i += 1
    return items, i


def _parse_map_from_inline(lines, i, ind, inline):
    """A '- key: val' item: first key sits after the dash; subsequent keys are
    indented to align under the first key."""
    dash_col = ind
    key_col = dash_col + 2
    result = {}
    m = re.match(r"^([^:]+):(.*)$", inline)
    key = m.group(1).strip().strip('"\'')
    rest = m.group(2).strip()
    if rest in (">", "|", ">-", "|-", ">+", "|+"):
        val, i = _read_block_scalar(lines, i + 1, key_col, rest[0])
        result[key] = val
    elif rest == "":
        child, i = _parse_block(lines, i + 1, key_col + 1)
        result[key] = child
        i = i
    else:
        result[key] = _coerce(rest)
        i += 1
    # continuation keys aligned at key_col
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            break
        if _indent(lines[i]) != key_col:
            break
        raw = _strip_inline_comment(lines[i].strip())
        if raw.startswith("- "):
            break
        m = re.match(r"^([^:]+):(.*)$", raw)
        if not m:
            break
        k = m.group(1).strip().strip('"\'')
        rest = m.group(2).strip()
        if rest in (">", "|", ">-", "|-", ">+", "|+"):
            val, i = _read_block_scalar(lines, i + 1, key_col, rest[0])
            result[k] = val
        elif rest.startswith("[") and rest.count("[") != rest.count("]"):
            buf = rest
            i += 1
            while i < len(lines) and buf.count("[") != buf.count("]"):
                buf += " " + _strip_inline_comment(lines[i].strip())
                i += 1
            result[k] = _coerce(buf)
        elif rest == "":
            child, i = _parse_block(lines, i + 1, key_col + 1)
            result[k] = child
        else:
            result[k] = _coerce(rest)
            i += 1
    return result, i


def _read_block_scalar(lines, i, parent_ind, style):
    collected, block_ind = [], None
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            collected.append("")
            i += 1
            continue
        cur = _indent(line)
        if cur <= parent_ind:
            break
        if block_ind is None:
            block_ind = cur
        collected.append(line[block_ind:])
        i += 1
    while collected and collected[-1] == "":
        collected.pop()
    if style == "|":
        return "\n".join(collected), i
    # folded: blank lines -> newline, others joined by space
    out, buf = [], []
    for ln in collected:
        if ln == "":
            if buf:
                out.append(" ".join(buf))
                buf = []
            out.append("")
        else:
            buf.append(ln.strip())
    if buf:
        out.append(" ".join(buf))
    return "\n".join(out).strip(), i


# ==========================================================================
# Case file model
# ==========================================================================
def _parse_front_matter(path):
    """Return (meta_dict, body_str) for a thread markdown file."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml_load(parts[1])
            return (meta or {}), parts[2].lstrip("\n")
    return {}, text


class CaseFile:
    def __init__(self, root):
        self.root = root
        self.threads_dir = os.path.join(root, "threads")
        self.entities_path = os.path.join(root, "entities.yaml")
        self.findings_path = os.path.join(root, "findings.yaml")
        self.journal_path = os.path.join(root, "journal.md")
        self.state_path = os.path.join(root, ".state.json")

    def exists(self):
        return os.path.isdir(self.root)

    def threads(self):
        out = []
        if not os.path.isdir(self.threads_dir):
            return out
        for name in sorted(os.listdir(self.threads_dir)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(self.threads_dir, name)
            meta, body = _parse_front_matter(path)
            meta.setdefault("id", os.path.splitext(name)[0])
            out.append({"path": path, "file": name, "meta": meta, "body": body})
        return out

    def thread_by_id(self, tid):
        for t in self.threads():
            if str(t["meta"].get("id")) == tid:
                return t
        return None

    def entities(self):
        if not os.path.isfile(self.entities_path):
            return {}
        with open(self.entities_path, encoding="utf-8") as fh:
            return yaml_load(fh.read()) or {}

    def entity_ids(self):
        ids = set()
        for group in (self.entities() or {}).values():
            if isinstance(group, list):
                for e in group:
                    if isinstance(e, dict) and e.get("canonical_id"):
                        ids.add(str(e["canonical_id"]))
        return ids

    def findings(self):
        if not os.path.isfile(self.findings_path):
            return {}
        with open(self.findings_path, encoding="utf-8") as fh:
            return yaml_load(fh.read()) or {}


def _as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ==========================================================================
# Commands
# ==========================================================================
def cmd_init(cf, template):
    if cf.exists() and os.listdir(cf.root):
        print("refusing to init: %s already exists and is not empty" % cf.root, file=sys.stderr)
        return 2
    if template and os.path.isdir(template):
        shutil.copytree(template, cf.root, dirs_exist_ok=True)
        print("initialized case file from template at %s" % cf.root)
        return 0
    os.makedirs(cf.threads_dir, exist_ok=True)
    for fn, seed in (
        ("brief.md", "# Investigation Brief\n\n## The question\n\n## Scope\n\n## What counts as a finding (the bar)\n"),
        ("entities.yaml", "# Entity registry. Each entry: canonical_id, display, type/status, why.\nmembers: []\nfirms: []\nclients: []\n"),
        ("findings.yaml", "# Findings ledger. Each finding needs >=1 source_record.\nfindings: []\nlegal_flags: []\n"),
        ("journal.md", "# Journal - append-only session log\n"),
    ):
        with open(os.path.join(cf.root, fn), "w", encoding="utf-8") as fh:
            fh.write(seed)
    print("initialized empty case file at %s" % cf.root)
    return 0


def cmd_rollup(cf):
    threads = cf.threads()
    by_status = {s: [] for s in STATUSES}
    for t in threads:
        st = t["meta"].get("status", "open")
        by_status.setdefault(st, []).append(t["meta"].get("id"))
    findings = _as_list((cf.findings() or {}).get("findings"))
    state = {
        "generated": _now(),
        "counts": {s: len(by_status.get(s, [])) for s in STATUSES},
        "threads_total": len(threads),
        "findings_total": len(findings),
        "entities_total": len(cf.entity_ids()),
        "threads_by_status": by_status,
    }
    with open(cf.state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
    return state


def _priority(t):
    p = t["meta"].get("priority")
    try:
        return int(p)
    except (TypeError, ValueError):
        return 9999


def cmd_brief(cf):
    threads = cf.threads()
    active = sorted(
        [t for t in threads if t["meta"].get("status") in ACTIVE],
        key=_priority,
    )
    cold = [t for t in threads if t["meta"].get("status") == "cold"]
    confirmed = [t for t in threads if t["meta"].get("status") == "confirmed"]
    entities = cf.entities() or {}

    print("=" * 68)
    print("CASE FILE BRIEF  ·  %s" % cf.root)
    print("generated %s (deterministic; no model reasoning)" % _now())
    print("=" * 68)

    print("\nOPEN / CHASING THREADS (by priority) — start here:")
    if not active:
        print("  (none)")
    for t in active:
        m = t["meta"]
        na = (m.get("next_action") or "").strip().replace("\n", " ")
        print("  [%s] P%s %s — %s" % (m.get("status", "?")[:4].upper(),
                                      m.get("priority", "?"), m.get("id"),
                                      m.get("title", "")))
        print("        next: %s" % (na if na else "*** MISSING next_action ***"))

    print("\nRECENT ACTIVITY (last journal entries):")
    for line in _tail_journal(cf, 12):
        print("  " + line)

    print("\nCOLD THREADS — do NOT re-chase without new information:")
    cold_any = False
    for t in cold:
        cold_any = True
        reason = (t["meta"].get("reason") or "").strip().replace("\n", " ")
        print("  %s %s — reason: %s" % (t["meta"].get("id"),
                                        t["meta"].get("title", ""),
                                        reason or "(no reason recorded — lint will flag)"))
    if not cold_any:
        print("  (none)")

    print("\nKEY ENTITIES:")
    shown = 0
    for group, members in entities.items():
        if not isinstance(members, list):
            continue
        for e in members:
            if not isinstance(e, dict):
                continue
            if str(e.get("status", "")).lower() in ("key", "flag"):
                why = (e.get("why") or "").strip().replace("\n", " ")
                print("  [%s] %s — %s" % (e.get("status", "").upper(),
                                          e.get("display", e.get("canonical_id")),
                                          why[:110]))
                shown += 1
    if not shown:
        print("  (none flagged key)")

    print("\nSCOREBOARD: %d confirmed · %d active · %d cold · %d total threads"
          % (len(confirmed), len(active), len(cold), len(threads)))
    print("=" * 68)
    return 0


def _tail_journal(cf, n):
    if not os.path.isfile(cf.journal_path):
        return ["(no journal yet)"]
    with open(cf.journal_path, encoding="utf-8") as fh:
        lines = [l.rstrip() for l in fh if l.strip()]
    return lines[-n:] if lines else ["(journal empty)"]


def cmd_lint(cf, corpus_index):
    problems = []
    known_sources = None
    if corpus_index and os.path.isfile(corpus_index):
        known_sources = set()
        with open(corpus_index, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if s:
                    known_sources.add(s)

    entity_ids = cf.entity_ids()
    threads = cf.threads()
    for t in threads:
        m, tid = t["meta"], t["meta"].get("id")
        status = m.get("status")
        if status not in STATUSES:
            problems.append("%s: unknown status %r" % (tid, status))
        if status in ACTIVE and not (m.get("next_action") or "").strip():
            problems.append("%s: %s thread has empty next_action" % (tid, status))
        if status in REASON_REQUIRED and not (m.get("reason") or "").strip():
            problems.append("%s: %s thread has no reason recorded" % (tid, status))
        if status in SOURCE_REQUIRED and not _as_list(m.get("source_records")):
            problems.append("%s: confirmed thread has no source_records" % tid)
        for eid in _as_list(m.get("entities")):
            if entity_ids and str(eid) not in entity_ids:
                problems.append("%s: references entity %r missing from registry" % (tid, eid))
        if known_sources is not None:
            for sid in _as_list(m.get("source_records")):
                if str(sid) not in known_sources:
                    problems.append("%s: source %r not in corpus index" % (tid, sid))

    findings = _as_list((cf.findings() or {}).get("findings"))
    for f in findings:
        if not isinstance(f, dict):
            continue
        fid = f.get("id", "?")
        if not _as_list(f.get("source_records")):
            problems.append("finding %s: no source_records" % fid)

    if problems:
        print("LINT: %d problem(s) found" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("LINT: clean — all invariants satisfied (%d threads, %d findings)"
          % (len(threads), len(findings)))
    return 0


def _serialize_scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if "\n" in s or ": " in s or s.strip() != s or s == "":
        return json.dumps(s, ensure_ascii=False)
    return s


def _dump_front_matter(meta):
    order = ["id", "title", "status", "priority", "reason", "workflow_step",
             "entities", "findings", "source_records", "next_action"]
    keys = [k for k in order if k in meta] + [k for k in meta if k not in order]
    out = ["---"]
    for k in keys:
        v = meta[k]
        if isinstance(v, list):
            if not v:
                out.append("%s: []" % k)
            elif all(not isinstance(x, (list, dict)) for x in v) and len(", ".join(map(str, v))) < 76:
                out.append("%s: [%s]" % (k, ", ".join(_serialize_scalar(x) for x in v)))
            else:
                out.append("%s:" % k)
                for x in v:
                    out.append("  - %s" % _serialize_scalar(x))
        elif k in ("next_action", "reason") and isinstance(v, str) and len(v) > 60:
            out.append("%s: >" % k)
            for chunk in _wrap(v, 88):
                out.append("  " + chunk)
        else:
            out.append("%s: %s" % (k, _serialize_scalar(v)))
    out.append("---")
    return "\n".join(out)


def _wrap(text, width):
    words, line, lines = text.split(), "", []
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return lines or [""]


def cmd_update_status(cf, tid, to, reason, sources):
    t = cf.thread_by_id(tid)
    if not t:
        print("no thread %s" % tid, file=sys.stderr)
        return 2
    if to not in STATUSES:
        print("unknown target status %r" % to, file=sys.stderr)
        return 2
    m = t["meta"]
    frm = m.get("status", "open")
    if to == frm:
        print("thread %s already %s" % (tid, to), file=sys.stderr)
        return 2
    if to not in TRANSITIONS.get(frm, set()):
        allowed = ", ".join(sorted(TRANSITIONS.get(frm, set()))) or "(none — terminal)"
        print("illegal transition %s -> %s for %s. allowed: %s"
              % (frm, to, tid, allowed), file=sys.stderr)
        return 1
    if to in REASON_REQUIRED and not (reason or "").strip():
        print("transition to %s requires --reason" % to, file=sys.stderr)
        return 1
    if to in SOURCE_REQUIRED:
        merged = _as_list(m.get("source_records")) + list(sources or [])
        if not merged:
            print("transition to %s requires >=1 --source" % to, file=sys.stderr)
            return 1

    m["status"] = to
    if reason:
        m["reason"] = reason
    if sources:
        m["source_records"] = _as_list(m.get("source_records")) + list(sources)
    if to in ("cold", "killed", "confirmed"):
        m.pop("next_action", None)

    new_fm = _dump_front_matter(m)
    with open(t["path"], "w", encoding="utf-8") as fh:
        fh.write(new_fm + "\n\n" + t["body"].rstrip() + "\n")

    # auto-log the transition
    _append_journal(cf, "auto", "%s: %s -> %s%s" % (
        tid, frm, to, (" (%s)" % reason if reason else "")))
    cmd_rollup(cf)
    print("%s: %s -> %s" % (tid, frm, to))
    return 0


def _append_journal(cf, session, message):
    stamp = _now()
    entry = "\n---\n### %s · session %s\n%s\n" % (stamp, session, message)
    with open(cf.journal_path, "a", encoding="utf-8") as fh:
        fh.write(entry)


def cmd_log(cf, session, message):
    if not message.strip():
        print("empty log message", file=sys.stderr)
        return 2
    _append_journal(cf, session, message)
    print("logged to journal (session %s)" % session)
    return 0


# ==========================================================================
# CLI
# ==========================================================================
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    p = argparse.ArgumentParser(prog="casefile", description=__doc__.split("\n")[0])
    p.add_argument("--dir", default="casefile", help="path to the case file directory")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="scaffold a new case file")
    sp.add_argument("--template", default=None, help="copy this template directory")

    sub.add_parser("brief", help="deterministic session-start digest")

    sp = sub.add_parser("lint", help="enforce case-file invariants")
    sp.add_argument("--corpus-index", default=None,
                    help="file of known source IDs, one per line")

    sp = sub.add_parser("update-status", help="move a thread through the state machine")
    sp.add_argument("--thread", required=True)
    sp.add_argument("--to", required=True, choices=STATUSES)
    sp.add_argument("--reason", default=None)
    sp.add_argument("--source", action="append", default=[], dest="sources")

    sp = sub.add_parser("log", help="append a timestamped journal entry")
    sp.add_argument("--session", default="manual")
    sp.add_argument("message")

    sub.add_parser("rollup", help="regenerate .state.json rollup cache")

    args = p.parse_args(argv)
    cf = CaseFile(os.path.abspath(args.dir))

    if args.cmd != "init" and not cf.exists():
        print("no case file at %s (run: casefile --dir %s init)"
              % (cf.root, args.dir), file=sys.stderr)
        return 2

    if args.cmd == "init":
        return cmd_init(cf, args.template)
    if args.cmd == "brief":
        return cmd_brief(cf)
    if args.cmd == "lint":
        return cmd_lint(cf, args.corpus_index)
    if args.cmd == "update-status":
        return cmd_update_status(cf, args.thread, args.to, args.reason, args.sources)
    if args.cmd == "log":
        return cmd_log(cf, args.session, args.message)
    if args.cmd == "rollup":
        cmd_rollup(cf)
        print("wrote %s" % cf.state_path)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
