#!/usr/bin/env python3
"""
format_footnote.py — Render Howard-Center-style footnotes from match decisions.

Usage:
    python format_footnote.py --matches matches.json --sources sources.json \\
        [--out footnotes.json]

Reads:
    matches.json    — Output from the agent's matching step in workflow step 5.
                      Shape: { "matches": [ {match_record}, ... ] }
                      Where each match_record is:
                        {
                          "claim_id": "claim_0007",
                          "claim_sentence": "...",
                          "source_id": "src_0003" | null,
                          "segment_id": "src_0003_p002_g01" | null,
                          "supporting_quote": "..." | null,
                          "context_quote": "..." | null,    # PREFERRED
                          "url_override": "..." | null,     # optional
                          "confidence": "high" | "medium" | "low" | "none"
                        }
                      "context_quote" is the supporting_quote PLUS one or two
                      sentences of surrounding context from the source. If
                      provided, the footnote uses it instead of supporting_quote
                      — this is what protects against out-of-context quoting.

    sources.json    — Output from ingest_sources.py.

Writes:
    footnotes.json  — One record per claim:
                        {
                          "claim_id": "claim_0007",
                          "rendered_footnote": "GAO-21-385, ... 'quote'",
                          "url": "...",  # used to build the Word hyperlink
                          "confidence": "...",
                          "match_status": "matched" | "needs_source"
                        }

Templates live in references/source_type_templates.md. This script is the
operational stub of those templates — when a new source type is added there,
add a corresponding render_*() function here.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def _find_source(sources: list[dict], source_id: str | None) -> dict | None:
    if not source_id:
        return None
    for s in sources:
        if s["source_id"] == source_id:
            return s
    return None


def _find_segment(source: dict, segment_id: str | None) -> dict | None:
    if not source or not segment_id:
        return None
    for seg in source.get("segments", []):
        if seg["segment_id"] == segment_id:
            return seg
    return None


# ---------- Renderers per source type --------------------------------------
def render_pdf(source: dict, segment: dict, quote: str) -> str:
    title = source.get("title") or Path(source["path_or_url"]).stem
    date = source.get("date") or ""
    pos = segment.get("position", "") if segment else ""
    parts = [title]
    if date:
        parts.append(date)
    if pos:
        parts.append(pos)
    head = ", ".join([p for p in parts if p])
    return f'{head}: "{quote}"'.strip()


def render_text(source: dict, segment: dict, quote: str) -> str:
    title = source.get("title") or Path(source["path_or_url"]).stem
    date = source.get("date") or ""
    pos = segment.get("position", "") if segment else ""
    parts = [title]
    if date:
        parts.append(date)
    if pos:
        parts.append(pos)
    head = ", ".join([p for p in parts if p])
    return f'{head}: "{quote}"'.strip()


def render_docx(source: dict, segment: dict, quote: str) -> str:
    return render_text(source, segment, quote)


def render_transcript(source: dict, segment: dict, quote: str) -> str:
    url_or_path = source["path_or_url"]
    tc = segment.get("timecode") or segment.get("position") or ""
    if tc and not tc.startswith("T/C"):
        tc = f"T/C {tc}"
    return f'{url_or_path} {tc}: "{quote}"'.strip()


def render_url(source: dict, segment: dict, quote: str) -> str:
    title = source.get("title") or source["path_or_url"]
    date = source.get("date") or ""
    if date:
        return f'{title}, captured {date}: "{quote}"'
    return f'{title}: "{quote}"'


def render_needs_source(claim_sentence: str) -> str:
    short = claim_sentence.strip()
    if len(short) > 140:
        short = short[:137].rstrip() + "..."
    return f"⟨NEEDS SOURCE: {short}⟩"


_RENDERERS = {
    "pdf": render_pdf,
    "text": render_text,
    "docx": render_docx,
    "transcript": render_transcript,
    "url": render_url,
}


# ---------- Main rendering -------------------------------------------------
def render_match(match: dict, sources: list[dict]) -> dict:
    claim_id = match["claim_id"]
    confidence = match.get("confidence", "none")
    claim_sentence = match.get("claim_sentence", "")
    # Prefer the wider context_quote over the bare supporting_quote.
    # The Howard Center protocol calls for surrounding context so reviewers
    # can judge whether the quote is being used fairly.
    quote = (
        (match.get("context_quote") or "").strip()
        or (match.get("supporting_quote") or "").strip()
    )

    if not match.get("source_id") or confidence == "none":
        return {
            "claim_id": claim_id,
            "rendered_footnote": render_needs_source(claim_sentence),
            "url": None,
            "confidence": "none",
            "match_status": "needs_source",
        }

    source = _find_source(sources, match["source_id"])
    if not source:
        return {
            "claim_id": claim_id,
            "rendered_footnote": render_needs_source(
                f"{claim_sentence} (matched source not found: {match['source_id']})"
            ),
            "url": None,
            "confidence": "none",
            "match_status": "needs_source",
        }

    segment = _find_segment(source, match.get("segment_id"))
    if not quote:
        # Fall back to the segment text, trimmed wide enough to give context.
        seg_text = (segment or {}).get("text", "")
        quote = _trim_quote(seg_text, max_chars=480)

    renderer = _RENDERERS.get(source["type"], render_text)
    rendered = renderer(source, segment, quote)
    url = match.get("url_override") or source.get("path_or_url")

    return {
        "claim_id": claim_id,
        "rendered_footnote": rendered,
        "url": url,
        "confidence": confidence,
        "match_status": "matched",
    }


def _trim_quote(text: str, max_chars: int = 480) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    # Try to end on a sentence boundary.
    cut = text[:max_chars]
    last_period = cut.rfind(". ")
    if last_period > max_chars * 0.5:
        return cut[:last_period + 1].strip()
    return cut.rstrip() + " [...]"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matches", required=True, help="matches.json")
    ap.add_argument("--sources", required=True, help="sources.json")
    ap.add_argument("--out", help="footnotes.json output path (default: stdout)")
    args = ap.parse_args()

    matches_data = json.loads(Path(args.matches).read_text(encoding="utf-8"))
    sources_data = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    matches = matches_data.get("matches") or matches_data
    sources = sources_data.get("sources") or sources_data

    rendered = [render_match(m, sources) for m in matches]

    output = {
        "n_footnotes": len(rendered),
        "n_matched": sum(1 for r in rendered if r["match_status"] == "matched"),
        "n_needs_source": sum(1 for r in rendered if r["match_status"] == "needs_source"),
        "footnotes": rendered,
    }
    text = json.dumps(output, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"Wrote {args.out}\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
