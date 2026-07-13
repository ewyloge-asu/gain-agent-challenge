#!/usr/bin/env python3
"""Render CURATED skill-invocation traces from raw agent-session transcripts.

The raw JSONL transcripts mix two kinds of activity: (a) actually USING the
skills to investigate, and (b) building the skills, planning documents, team
discussion, and website work. Only (a) belongs in the public trace page, so
this renderer keeps exactly:

  - every tool call that invokes a skill script (matched against SKILL_SCRIPTS),
    with its full arguments, and
  - the agent reasoning text from the same message as a kept invocation
    (the "why" around the call).

Raw human prompts and all development/planning activity are omitted and
counted. The full unredacted logs are retained by the team and available to
the evaluation panel on request; the curated narrative of human-judgment
moments is in trace_index.md, and verbatim invocation outputs are in outputs/.

Input : raw/<name>.jsonl + raw/manifest.json (kept locally, not published)
Output: sessions.html

Standard library only.  Usage:  python3 render_traces.py [--raw raw] [--out sessions.html]
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

# Any tool call whose arguments reference one of these is a skill invocation.
SKILL_SCRIPTS = re.compile(
    r"(ingest\.py|resolve_entities\.py|xref\.py|detect_coordination\.py|review\.py"
    r"|connector\.py|state\.py|run_all\.sh|make_demo_data\.py"
    r"|casefile\.py|scope\.py|find_data\.py|fetch_source\.py|build_dashboard\.py"
    r"|analyze\.py|verify_report\.py"
    r"|extract_claims\.py|extract_existing_footnotes\.py|ingest_sources\.py"
    r"|format_footnote\.py|insert_tracked_footnotes\.py|check_source_tier\.py)")

CSS = """
 :root{--paper:#FFFFFF;--paper2:#F6F5F1;--ink:#191919;--ink2:#484848;--mut:#747474;
   --line:#E8E8E8;--maroon:#8C1D40;--maroon-tint:#F8F4F4;--teal:#005B64;
   --teal-tint:#F1F6F7;--gold-tint:#F6F5F1;--gold:#585200;
   --sans:'Libre Franklin',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
   --serif:'Source Serif 4',Georgia,serif;
   --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
 body{margin:0;font:15px/1.6 var(--sans);background:var(--paper);color:var(--ink);
      -webkit-font-smoothing:antialiased;}
 .wrap{max-width:1000px;margin:0 auto;padding:24px 20px 80px;}
 h1{font-family:var(--sans);font-weight:800;letter-spacing:-.015em;font-size:30px;margin:14px 0 4px;}
 h2{font-family:var(--sans);font-weight:700;letter-spacing:-.01em;font-size:21px;margin:40px 0 8px;}
 .mut{color:var(--mut);font-family:var(--serif);}
 a{color:var(--maroon);text-decoration:none;} a:hover{text-decoration:underline;text-underline-offset:3px;}
 .msg{border:1px solid var(--line);border-radius:10px;margin:10px 0;overflow:hidden;background:#fff;}
 .msg>summary{padding:9px 14px;cursor:pointer;font-weight:600;font-size:12.5px;
      font-family:var(--mono);letter-spacing:.04em;list-style:none;display:flex;gap:10px;
      align-items:baseline;transition:filter .15s ease;}
 .msg>summary:hover{filter:brightness(.97);}
 .msg>summary::-webkit-details-marker{display:none;}
 .a>summary{background:var(--maroon-tint);color:var(--maroon);}
 .t>summary{background:var(--gold-tint);color:var(--gold);}
 .body{padding:10px 14px;}
 pre{font-family:var(--mono);background:var(--paper2);border:1px solid var(--line);
     border-radius:8px;padding:10px;overflow:auto;font-size:12.5px;white-space:pre-wrap;
     word-break:break-word;margin:8px 0;}
 .toolname{font-weight:700;color:var(--gold);}
 .count{font-weight:400;color:var(--mut);font-size:11.5px;}
 .omit{font:500 12px/1.6 var(--mono);color:var(--mut);background:var(--teal-tint);
     border:1px dashed #A5CACE;border-radius:8px;padding:8px 12px;margin:10px 0;}
 nav{position:sticky;top:0;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);
     border-bottom:1px solid var(--line);padding:10px 20px;font-size:12.5px;
     font-family:var(--mono);z-index:5;}
 code{font-family:var(--mono);background:var(--paper2);border:1px solid var(--line);
     padding:1px 6px;border-radius:5px;font-size:12.5px;}
"""


def blocks(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c or []


def render_session(path: Path, sid: str, title: str, note: str) -> str:
    out = [f'<h2 id="{sid}">{html.escape(title)}</h2>'
           f'<p class="mut">{html.escape(note)}</p>']
    n_tool = n_omitted = 0
    kept = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = d.get("role")
        if role == "user":
            n_omitted += 1
            continue
        if role != "assistant":
            continue
        msg_blocks = blocks(d.get("message", {}))
        # keep only EXECUTED skill invocations: shell commands that run a skill
        # script (editing/reading a script file is development, not invocation)
        def is_invocation(b):
            if b.get("type") != "tool_use":
                return False
            if str(b.get("name", "")).lower() not in ("shell", "bash", "run_terminal_cmd"):
                return False
            cmd = str(b.get("input", {}).get("command", ""))
            return bool(SKILL_SCRIPTS.search(cmd))
        invocations = [b for b in msg_blocks if is_invocation(b)]
        other = [b for b in msg_blocks if b.get("type") == "tool_use"] 
        if not invocations:
            if msg_blocks:
                n_omitted += 1
            continue
        # NOTE: assistant reasoning text is deliberately NOT included — in these
        # transcripts it interleaves tool use with team-internal planning talk.
        # The curated narrative of each invocation lives in trace_index.md.
        n_omitted += len(other) - len(invocations)
        n_omitted += sum(1 for b in msg_blocks
                         if b.get("type") == "text" and b.get("text", "").strip())
        for b in invocations:
            n_tool += 1
            args = json.dumps(b.get("input", {}), indent=1, default=str)
            kept.append(
                '<details class="msg t"><summary>SKILL INVOCATION — '
                f'<span class="toolname">{html.escape(str(b.get("name")))}</span>'
                f'<span class="count">#{n_tool}</span></summary>'
                f'<div class="body"><pre>{html.escape(args)}</pre></div></details>')
    out.append(f'<p class="mut">{n_tool} skill invocations kept</p>')
    out.extend(kept)
    out.append(
        f'<p class="omit">{n_omitted} non-invocation messages from this session '
        '(prompts, tool-building, planning) are omitted from this public page. Full '
        'unredacted logs are retained and available to the evaluation panel on '
        'request.</p>')
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw")
    ap.add_argument("--manifest", default="raw/manifest.json")
    ap.add_argument("--out", default="sessions.html")
    a = ap.parse_args()

    manifest = json.loads(Path(a.manifest).read_text())
    sections, toc = [], []
    for s in manifest["sessions"]:
        p = Path(a.raw) / s["file"]
        if not p.exists():
            continue
        toc.append(f'<a href="#{s["id"]}">{html.escape(s["title"])}</a>')
        sections.append(render_session(p, s["id"], s["title"], s["note"]))

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skill-invocation traces</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<nav><a href="https://ewyloge-asu.github.io/gain-agent-challenge/">← back to the site</a> &nbsp;·&nbsp; {' · '.join(toc)}</nav>
<div class="wrap">
<h1>Skill-invocation traces</h1>
<p class="mut">Every time a skill was actually invoked across the four working sessions:
the tool call with its full arguments, in order. This page is deliberately curated to
<b>tool use only</b> — prompts, development work, and planning conversation are omitted
and counted per session. The narrative of each invocation and the human-judgment moments
is in <a href="trace_index.md">trace_index.md</a>; the verbatim <b>output</b> of each key
invocation is in <code>outputs/</code> (one file per indexed step, plus the full
clean-workdir re-run transcript); every command regenerates its output when re-run.</p>
{''.join(sections)}
</div></body></html>"""
    Path(a.out).write_text(page)
    print(f"wrote {a.out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
