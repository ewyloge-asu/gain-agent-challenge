#!/usr/bin/env python3
"""Render raw agent-session transcripts (JSONL) into one readable HTML page.

Input : raw/<name>.jsonl  — one JSON record per line, {"role": "user"|"assistant",
        "message": {"content": str | [ {type: text|tool_use, ...}, ... ]}} plus
        occasional {"type": "turn_ended"} markers.
Output: sessions.html — every prompt, every reasoning message, every tool call with
        its full arguments, in order, one collapsible section per session.

Standard library only.  Usage:  python3 render_traces.py [--raw raw] [--out sessions.html]
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

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
 .u>summary{background:var(--teal-tint);color:var(--teal);}
 .a>summary{background:var(--maroon-tint);color:var(--maroon);}
 .t>summary{background:var(--gold-tint);color:var(--gold);}
 .body{padding:10px 14px;}
 pre{font-family:var(--mono);background:var(--paper2);border:1px solid var(--line);
     border-radius:8px;padding:10px;overflow:auto;font-size:12.5px;white-space:pre-wrap;
     word-break:break-word;margin:8px 0;}
 .toolname{font-weight:700;color:var(--gold);}
 .count{font-weight:400;color:var(--mut);font-size:11.5px;}
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
           f'<p class="mut">{html.escape(note)} · raw log: '
           f'<a href="raw/{path.name}">{path.name}</a></p>']
    n_user = n_tool = 0
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
            n_user += 1
            text = "\n\n".join(b.get("text", "") for b in blocks(d.get("message", {}))
                               if b.get("type") == "text")
            out.append(
                '<details class="msg u"><summary>HUMAN — prompt / judgment '
                f'<span class="count">#{n_user}</span></summary>'
                f'<div class="body"><pre>{html.escape(text)}</pre></div></details>')
        elif role == "assistant":
            for b in blocks(d.get("message", {})):
                if b.get("type") == "text" and b.get("text", "").strip():
                    out.append(
                        '<details class="msg a"><summary>AGENT — reasoning / report'
                        '</summary><div class="body">'
                        f'<pre>{html.escape(b["text"])}</pre></div></details>')
                elif b.get("type") == "tool_use":
                    n_tool += 1
                    args = json.dumps(b.get("input", {}), indent=1, default=str)
                    out.append(
                        '<details class="msg t"><summary>TOOL CALL — '
                        f'<span class="toolname">{html.escape(str(b.get("name")))}</span>'
                        f'<span class="count">#{n_tool}</span></summary>'
                        f'<div class="body"><pre>{html.escape(args)}</pre></div></details>')
    out.insert(1, f'<p class="mut">{n_user} human messages · {n_tool} tool calls</p>')
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
<title>Interaction traces — full session logs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<nav><a href="https://ewyloge-asu.github.io/gain-agent-challenge/">← back to the site</a> &nbsp;·&nbsp; {' · '.join(toc)}</nav>
<div class="wrap">
<h1>Interaction traces — full session logs</h1>
<p class="mut">Complete model-session logs: every human prompt (teal), every agent
reasoning message (maroon), and every tool call with its full arguments (gold), in
order. Raw JSONL for each session is in <code>raw/</code>. The curated map keying these
sessions to the findings is <a href="trace_index.md">trace_index.md</a>. The transcript
format records prompts, reasoning, and tool inputs; the verbatim <b>outputs</b> of every
key invocation are captured in <code>outputs/</code> (one file per indexed step, plus the
full clean-workdir re-run transcript), and all of them regenerate from the commands
shown.</p>
{''.join(sections)}
</div></body></html>"""
    Path(a.out).write_text(page)
    print(f"wrote {a.out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
