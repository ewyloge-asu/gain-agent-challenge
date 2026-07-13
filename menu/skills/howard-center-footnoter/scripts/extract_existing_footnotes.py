#!/usr/bin/env python3
"""
extract_existing_footnotes.py — List every footnote already in a draft .docx.

Usage:
    python extract_existing_footnotes.py <draft.docx> [--out existing.json]

Reads document.xml and footnotes.xml from the draft and emits a JSON list of
existing footnotes the agent can audit against the Howard Center standard:

    {
      "draft_path": "draft.docx",
      "n_existing_footnotes": 4,
      "existing_footnotes": [
        {
          "footnote_id": "1",
          "paragraph_index": 2,
          "sentence_around_reference": "...the sentence containing the footnote ref...",
          "body_text": "Existing footnote text",
          "body_hyperlinks": ["https://example.com/..."],
          "has_quote": true,
          "has_date_like_string": false,
          "has_page_or_timecode_cue": true,
          "char_length": 187,
          "raw_xml": "<w:footnote>...</w:footnote>"
        },
        ...
      ]
    }

The has_quote / has_date_like_string / has_page_or_timecode_cue flags are
quick heuristics. The agent uses them as starting signal, then makes the final
audit judgment (keep / improve / replace / flag) per the SKILL.md workflow.
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("lxml is required. Install with: pip install lxml\n")
    sys.exit(1)


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def w(tag: str) -> str:
    return f"{{{W}}}{tag}"


# ---------- Heuristic flags ----------------------------------------------
_QUOTE_RE = re.compile(r'["“][^"”]{8,}["”]')
_DATE_LIKE_RE = re.compile(
    r"\b(?:\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\b",
    re.IGNORECASE,
)
_PAGE_CUE_RE = re.compile(
    r"\b(?:p\.|page|pp\.|paragraph|graf|T/C|timecode|\d{1,2}:\d{2}(?::\d{2})?)\b",
    re.IGNORECASE,
)


def _extract_runs_text(elem: etree._Element) -> str:
    return "".join(
        (t.text or "")
        for t in elem.iter(w("t"))
    )


def _hyperlinks_in(elem: etree._Element, rels: dict) -> list[str]:
    """Return the list of URLs that any hyperlink in this element points to."""
    urls = []
    for hl in elem.iter(w("hyperlink")):
        rid = hl.get(f"{{{R}}}id")
        if rid and rid in rels:
            urls.append(rels[rid])
    return urls


def _read_rels(zf: zipfile.ZipFile, rels_path: str) -> dict[str, str]:
    """Return {Id: Target} for hyperlink relationships."""
    REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    out: dict[str, str] = {}
    try:
        rels_xml = zf.read(rels_path)
    except KeyError:
        return out
    root = etree.fromstring(rels_xml)
    HL = ("http://schemas.openxmlformats.org/officeDocument/2006/"
          "relationships/hyperlink")
    for rel in root.findall(f"{{{REL_NS}}}Relationship"):
        if rel.get("Type") == HL:
            out[rel.get("Id")] = rel.get("Target", "")
    return out


def extract(draft_path: Path) -> dict:
    with zipfile.ZipFile(draft_path, "r") as z:
        names = set(z.namelist())
        if "word/document.xml" not in names:
            raise RuntimeError("Not a valid .docx (no word/document.xml).")
        doc_xml = z.read("word/document.xml")
        fns_xml = z.read("word/footnotes.xml") if "word/footnotes.xml" in names else None
        fn_rels = (
            _read_rels(z, "word/_rels/footnotes.xml.rels")
            if "word/_rels/footnotes.xml.rels" in names else {}
        )

    document = etree.fromstring(doc_xml)
    body = document.find(w("body"))
    if body is None:
        return {
            "draft_path": str(draft_path),
            "n_existing_footnotes": 0,
            "existing_footnotes": [],
        }
    paragraphs = body.findall(w("p"))

    # Build a paragraph-index lookup for each footnote reference in the body.
    ref_to_para: dict[str, int] = {}
    ref_to_sentence: dict[str, str] = {}
    for i, p in enumerate(paragraphs):
        para_text = _extract_runs_text(p)
        for fr in p.iter(w("footnoteReference")):
            fid = fr.get(w("id"))
            if fid is None:
                continue
            ref_to_para[fid] = i
            # Best-effort: take the surrounding sentence (last . to end).
            last_dot = para_text.rfind(".", 0, len(para_text))
            sentence = para_text[max(0, last_dot + 1):].strip() or para_text
            ref_to_sentence[fid] = sentence

    existing = []
    if fns_xml is not None:
        footnotes_root = etree.fromstring(fns_xml)
        for fn in footnotes_root.findall(w("footnote")):
            fid = fn.get(w("id"))
            # Skip the standard separator footnotes that have negative or 0 ids
            if fid in ("-1", "0") or fn.get(w("type")):
                continue
            body_text = _extract_runs_text(fn).strip()
            urls = _hyperlinks_in(fn, fn_rels)
            existing.append({
                "footnote_id": fid,
                "paragraph_index": ref_to_para.get(fid),
                "sentence_around_reference": ref_to_sentence.get(fid),
                "body_text": body_text,
                "body_hyperlinks": urls,
                "has_quote": bool(_QUOTE_RE.search(body_text)),
                "has_date_like_string": bool(_DATE_LIKE_RE.search(body_text)),
                "has_page_or_timecode_cue": bool(_PAGE_CUE_RE.search(body_text)),
                "char_length": len(body_text),
            })

    return {
        "draft_path": str(draft_path),
        "n_existing_footnotes": len(existing),
        "existing_footnotes": existing,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("draft", help="Path to a .docx draft article")
    ap.add_argument("--out", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        sys.stderr.write(f"Draft not found: {draft_path}\n")
        return 1

    data = extract(draft_path)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"Wrote {args.out}\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
