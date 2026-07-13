#!/usr/bin/env python3
"""
Generate a self-contained review dashboard (single HTML, no server, no deps) from a
case file — the human-verification surface for an investigation. Renders the brief, the
thread board (open/chasing/confirmed/cold with reasons + source records), findings, legal
flags, and key entities, so an editor can review by clicking rather than re-running the work.

Reuses the case-file skill's own YAML/front-matter parser (single source of truth) by
importing it from the sibling skill in the bundle.

Usage:
  python3 build_dashboard.py --dir ../../casefile --out review_dashboard.html
"""
import argparse
import html
import importlib.util
import os
import sys


def _load_casefile_module():
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.normpath(os.path.join(here, "..", "..", "case-file", "scripts",
                                          "casefile.py"))
    if not os.path.exists(cand):
        sys.exit(f"! cannot find case-file skill at {cand} (need it in the bundle)")
    spec = importlib.util.spec_from_file_location("casefile", cand)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def e(x):
    return html.escape(str(x if x is not None else ""))


STATUS_COLORS = {"confirmed": "#1a7f37", "chasing": "#9a6700", "open": "#0969da",
                 "cold": "#6e7781", "killed": "#cf222e"}


def render(cf, C):
    threads = cf.threads()
    findings_doc = cf.findings() or {}
    findings = findings_doc.get("findings") or []
    legal = findings_doc.get("legal_flags") or []
    entities = cf.entities() or {}
    brief = ""
    bpath = os.path.join(cf.root, "brief.md")
    if os.path.exists(bpath):
        brief = open(bpath, encoding="utf-8").read()

    by_status = {}
    for t in threads:
        by_status.setdefault(t["meta"].get("status", "open"), []).append(t)

    parts = []
    parts.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Investigation Review Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
 :root {{ --bg:#F6F5F1; --card:#fff; --ink:#191919; --mut:#747474; --line:#E8E8E8;
          --maroon:#8C1D40; --maroon-tint:#F8F4F4; --teal:#005B64;
          --sans:'Libre Franklin',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
          --serif:'Source Serif 4',Georgia,serif;
          --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace; }}
 * {{ box-sizing:border-box; }}
 body {{ font:15px/1.6 var(--sans); margin:0; background:var(--bg); color:var(--ink);
        -webkit-font-smoothing:antialiased; }}
 header {{ background:var(--maroon); color:#fff; padding:20px 28px; }}
 header h1 {{ margin:0 0 4px; font-size:20px; font-weight:800; letter-spacing:-.01em; }}
 header p {{ margin:0; color:#DAB8BD; font-family:var(--serif); }}
 main {{ max-width:1000px; margin:0 auto; padding:24px 20px 60px; }}
 a {{ color:var(--maroon); }}
 .row {{ display:flex; gap:14px; flex-wrap:wrap; margin:16px 0; }}
 .stat {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
          padding:12px 16px; min-width:110px; }}
 .stat b {{ font-size:22px; display:block; font-weight:800; }}
 .stat span {{ color:var(--mut); font-size:11px; font-family:var(--mono);
          text-transform:uppercase; letter-spacing:.04em; }}
 section {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
            padding:18px 20px; margin:16px 0; }}
 h2 {{ font-size:16px; margin:0 0 12px; border-bottom:1px solid var(--line);
       padding-bottom:8px; font-weight:700; }}
 .thread {{ border-left:4px solid var(--line); padding:8px 12px; margin:10px 0;
            background:var(--maroon-tint); border-radius:0 8px 8px 0; }}
 .pill {{ display:inline-block; color:#fff; font-size:10.5px; font-weight:600;
          font-family:var(--mono); padding:3px 9px; border-radius:20px;
          text-transform:uppercase; letter-spacing:.03em; }}
 .thread h3 {{ margin:6px 0 4px; font-size:15px; font-weight:700; }}
 .meta {{ color:var(--mut); font-size:13.5px; font-family:var(--serif); }}
 code {{ background:var(--bg); border:1px solid var(--line); padding:1px 5px;
         border-radius:5px; font-size:12px; font-family:var(--mono); word-break:break-all; }}
 pre {{ white-space:pre-wrap; background:var(--bg); padding:12px; border-radius:8px;
        border:1px solid var(--line); font-size:13px; font-family:var(--mono); }}
 .flag {{ border-left:4px solid #892312; }} details summary {{ cursor:pointer; font-weight:600; }}
 .src {{ font-size:12px; font-family:var(--mono); }} .src a {{ color:var(--teal); }}
</style></head><body>
<header><h1>Investigation Review Dashboard</h1>
<p>Generated from the case file — every claim links to a source record. No server, no login.</p></header>
<main>""")

    counts = {s: len(by_status.get(s, [])) for s in
              ("confirmed", "chasing", "open", "cold", "killed")}
    parts.append('<div class="row">')
    for label, key in (("Confirmed", "confirmed"), ("Chasing", "chasing"),
                       ("Open", "open"), ("Cold", "cold"),
                       ("Findings", None), ("Legal flags", None)):
        if key:
            val = counts.get(key, 0)
        else:
            val = len(findings) if label == "Findings" else len(legal)
        parts.append(f'<div class="stat"><b>{val}</b><span>{e(label)}</span></div>')
    parts.append('</div>')

    # Threads by status
    parts.append('<section><h2>Thread board</h2>')
    order = ["confirmed", "chasing", "open", "cold", "killed"]
    for st in order:
        for t in by_status.get(st, []):
            m = t["meta"]
            color = STATUS_COLORS.get(st, "#6e7781")
            parts.append(f'<div class="thread" style="border-left-color:{color}">')
            parts.append(f'<span class="pill" style="background:{color}">{e(st)}</span> '
                         f'<span class="meta">{e(m.get("id"))} · P{e(m.get("priority","?"))}</span>')
            parts.append(f'<h3>{e(m.get("title",""))}</h3>')
            if m.get("next_action"):
                parts.append(f'<div class="meta"><b>Next:</b> {e(m.get("next_action"))}</div>')
            if m.get("reason"):
                parts.append(f'<div class="meta"><b>Cold reason:</b> {e(m.get("reason"))}</div>')
            for s in (m.get("source_records") or []) if isinstance(m.get("source_records"), list) else ([m["source_records"]] if m.get("source_records") else []):
                parts.append(f'<div class="src"><b>source:</b> <code>{e(s)}</code></div>')
            body = (t.get("body") or "").strip()
            if body:
                parts.append(f'<details><summary>notes</summary><pre>{e(body)}</pre></details>')
            parts.append('</div>')
    parts.append('</section>')

    # Findings
    if findings:
        parts.append('<section><h2>Findings</h2>')
        for f in findings:
            if not isinstance(f, dict):
                continue
            parts.append(f'<div class="thread" style="border-left-color:#1a7f37">')
            parts.append(f'<h3>{e(f.get("title",""))} <span class="meta">({e(f.get("id"))})</span></h3>')
            if f.get("summary"):
                parts.append(f'<div class="meta">{e(f.get("summary"))}</div>')
            for s in f.get("source_records") or []:
                parts.append(f'<div class="src"><b>source:</b> <code>{e(s)}</code></div>')
            parts.append('</div>')
        parts.append('</section>')

    # Legal flags
    if legal:
        parts.append('<section><h2>Legal flags — for the panel</h2>')
        for f in legal:
            if not isinstance(f, dict):
                continue
            parts.append('<div class="thread flag">')
            parts.append(f'<h3>{e(f.get("id"))} <span class="meta">status: {e(f.get("status"))}</span></h3>')
            parts.append(f'<div class="meta">{e(f.get("issue"))}</div>')
            for s in f.get("source_records") or []:
                parts.append(f'<div class="src"><b>source:</b> <code>{e(s)}</code></div>')
            parts.append('</div>')
        parts.append('</section>')

    # Entities
    parts.append('<section><h2>Key entities</h2>')
    for group, items in entities.items():
        if not isinstance(items, list):
            continue
        for en in items:
            if not isinstance(en, dict):
                continue
            parts.append(f'<div class="meta">[{e(en.get("status","")).upper()}] '
                         f'<b>{e(en.get("display", en.get("canonical_id")))}</b> '
                         f'(<code>{e(en.get("canonical_id"))}</code>) — {e(en.get("why",""))}</div>')
    parts.append('</section>')

    # Brief
    parts.append(f'<section><h2>Case brief (scope)</h2><pre>{e(brief)}</pre></section>')
    parts.append('</main></body></html>')
    return "".join(parts)


def main():
    p = argparse.ArgumentParser(description="Generate a review dashboard from a case file")
    p.add_argument("--dir", default="casefile")
    p.add_argument("--out", default="review_dashboard.html")
    args = p.parse_args()
    C = _load_casefile_module()
    cf = C.CaseFile(os.path.abspath(args.dir))
    if not cf.exists():
        sys.exit(f"! no case file at {args.dir}")
    html_out = render(cf, C)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"✓ wrote {args.out} ({len(html_out):,} bytes) — open in a browser")


if __name__ == "__main__":
    main()
