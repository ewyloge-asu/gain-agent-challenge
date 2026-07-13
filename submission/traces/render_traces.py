#!/usr/bin/env python3
"""Render raw agent-session transcripts (JSONL) into one readable HTML page.

Input : raw/<name>.jsonl  — one JSON record per line, {"role": "user"|"assistant",
        "message": {"content": str | [ {type: text|tool_use, ...}, ... ]}} plus
        occasional {"type": "turn_ended"} markers.
Output: sessions.html — every prompt, every reasoning message, every tool call with
        its full arguments, in order, one collapsible section per session.

Standard library only.  Usage:  python3 render_traces.py [--raw raw] [--out sessions.html]
"""
import argparse
import html
import json
from pathlib import Path

CSS = """
 body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
      background:#0d1117;color:#e6edf3;}
 .wrap{max-width:1000px;margin:0 auto;padding:24px 20px 80px;}
 h1{font-size:26px;margin:8px 0 4px;} h2{font-size:20px;margin:36px 0 8px;}
 .mut{color:#9198a1;} a{color:#4493f8;text-decoration:none;} a:hover{text-decoration:underline;}
 .msg{border:1px solid #30363d;border-radius:10px;margin:10px 0;overflow:hidden;}
 .msg>summary{padding:8px 14px;cursor:pointer;font-weight:600;font-size:13px;
      letter-spacing:.03em;list-style:none;display:flex;gap:10px;align-items:baseline;}
 .msg>summary::-webkit-details-marker{display:none;}
 .u>summary{background:rgba(68,147,248,.14);color:#79b8ff;}
 .a>summary{background:rgba(63,185,80,.10);color:#7ee2a8;}
 .t>summary{background:rgba(210,153,34,.10);color:#e3b341;}
 .body{padding:10px 14px;}
 pre{background:#010409;border:1px solid #30363d;border-radius:8px;padding:10px;
     overflow:auto;font-size:12.5px;white-space:pre-wrap;word-break:break-word;margin:8px 0;}
 .toolname{font-weight:700;color:#e3b341;}
 .count{font-weight:400;color:#9198a1;font-size:12px;}
 nav{position:sticky;top:0;background:rgba(13,17,23,.95);border-bottom:1px solid #30363d;
     padding:10px 20px;font-size:14px;z-index:5;}
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
<title>Interaction traces — full session logs</title><style>{CSS}</style></head><body>
<nav>{' · '.join(toc)}</nav>
<div class="wrap">
<h1>Interaction traces — full session logs</h1>
<p class="mut">Complete model-session logs: every human prompt (blue), every agent
reasoning message (green), and every tool call with its full arguments (yellow), in
order. Raw JSONL for each session is in <code>raw/</code>. The curated map keying these
sessions to the findings is <a href="trace_index.md">trace_index.md</a>. Deterministic
tool outputs are reproduced by re-running the commands shown (see the submission README);
the platform's transcript format records prompts, reasoning, and tool inputs.</p>
{''.join(sections)}
</div></body></html>"""
    Path(a.out).write_text(page)
    print(f"wrote {a.out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
