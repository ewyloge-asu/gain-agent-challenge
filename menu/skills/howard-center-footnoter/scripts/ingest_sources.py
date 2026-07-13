#!/usr/bin/env python3
"""
ingest_sources.py — Index a folder of source materials.

Usage:
    python ingest_sources.py <sources_dir> [--out sources.json]

Walks a directory of sources, extracts text content with positional metadata
(page numbers for PDFs, timecodes for transcripts), and emits a JSON index
the agent loop can match claims against.

Supported source types:
    .pdf        — extracted with pdfplumber, page-by-page
    .txt, .md   — read as plain text, split into paragraphs
    .docx       — read with python-docx, paragraph-by-paragraph
    .vtt, .srt  — parsed as subtitle/transcript with timecodes
    urls.txt    — one URL per line, fetched if --fetch-urls is passed
                  (otherwise just registered as references)

Each source becomes a record:
    {
        "source_id": "src_0001",
        "type": "pdf" | "text" | "docx" | "transcript" | "url",
        "path_or_url": "...",
        "title": "best-effort title",
        "date": "best-effort date string or null",
        "segments": [
            {"segment_id": "...", "position": "p. 2" | "00:12:47" | "para 3",
             "text": "..."}
        ]
    }
"""
from __future__ import annotations


import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


def _try_import_pdfplumber():
    try:
        import pdfplumber  # noqa: F401
        return True
    except ImportError:
        return False


def _try_import_docx():
    try:
        from docx import Document  # noqa: F401
        return True
    except ImportError:
        return False


# ---------- PDF ingestion --------------------------------------------------
def ingest_pdf(path: Path, src_id: str) -> dict:
    import pdfplumber
    segments = []
    title = path.stem
    with pdfplumber.open(str(path)) as pdf:
        # Try to pull title from metadata.
        meta = pdf.metadata or {}
        if meta.get("Title"):
            title = meta["Title"]
        date_str = meta.get("CreationDate") or meta.get("ModDate") or None
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            # Split into rough paragraphs (double newline → para).
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            for j, para in enumerate(paragraphs, start=1):
                segments.append({
                    "segment_id": f"{src_id}_p{i:03d}_g{j:02d}",
                    "position": f"p. {i} of PDF, paragraph {j}",
                    "page": i,
                    "paragraph": j,
                    "text": para,
                })
    return {
        "source_id": src_id,
        "type": "pdf",
        "path_or_url": str(path),
        "title": title,
        "date": _clean_pdf_date(date_str) if date_str else None,
        "segments": segments,
    }


def _clean_pdf_date(s: str) -> str | None:
    if not s:
        return None
    # PDF dates look like D:20210601000000-04'00'
    m = re.search(r"D:(\d{4})(\d{2})(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return s


# ---------- DOCX ingestion -------------------------------------------------
def ingest_docx(path: Path, src_id: str) -> dict:
    from docx import Document
    doc = Document(str(path))
    segments = []
    for i, para in enumerate(doc.paragraphs, start=1):
        text = para.text.strip()
        if not text:
            continue
        segments.append({
            "segment_id": f"{src_id}_para{i:03d}",
            "position": f"paragraph {i}",
            "paragraph": i,
            "text": text,
        })
    core = doc.core_properties
    return {
        "source_id": src_id,
        "type": "docx",
        "path_or_url": str(path),
        "title": (core.title or path.stem),
        "date": (core.created.isoformat() if core.created else None),
        "segments": segments,
    }


# ---------- Plain text / markdown ingestion --------------------------------
def ingest_text(path: Path, src_id: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    segments = [{
        "segment_id": f"{src_id}_para{i:03d}",
        "position": f"paragraph {i}",
        "paragraph": i,
        "text": p,
    } for i, p in enumerate(paragraphs, start=1)]
    # Best-effort title: first non-blank line if short, else filename.
    first_line = paragraphs[0].split("\n")[0] if paragraphs else ""
    title = first_line if 0 < len(first_line) < 120 else path.stem
    return {
        "source_id": src_id,
        "type": "text",
        "path_or_url": str(path),
        "title": title,
        "date": _file_mtime(path),
        "segments": segments,
    }


def _file_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    except Exception:
        return ""


# ---------- VTT / SRT transcript ingestion ---------------------------------
_VTT_TIME = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[\.,]\d{3})"
)


def ingest_subtitle(path: Path, src_id: str) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    segments = []
    blocks = re.split(r"\n\s*\n", text)
    seg_n = 0
    for block in blocks:
        m = _VTT_TIME.search(block)
        if not m:
            continue
        start = m.group(1).replace(",", ".")
        # Lines after the timecode form the spoken text.
        lines = [
            ln for ln in block.split("\n")
            if ln.strip() and not _VTT_TIME.search(ln) and not ln.strip().isdigit()
        ]
        spoken = " ".join(lines).strip()
        if not spoken:
            continue
        seg_n += 1
        # Trim milliseconds for compactness.
        tc = start.split(".")[0]
        segments.append({
            "segment_id": f"{src_id}_tc{seg_n:04d}",
            "position": f"T/C {tc}",
            "timecode": tc,
            "text": spoken,
        })
    return {
        "source_id": src_id,
        "type": "transcript",
        "path_or_url": str(path),
        "title": path.stem,
        "date": _file_mtime(path),
        "segments": segments,
    }


# ---------- URL list -------------------------------------------------------
def ingest_url_list(path: Path, src_id_base: str) -> list[dict]:
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append({
            "source_id": f"{src_id_base}_{i:03d}",
            "type": "url",
            "path_or_url": line,
            "title": line,
            "date": None,
            "segments": [],   # URL bodies are fetched on demand by the agent
        })
    return out


# ---------- Walk + dispatch ------------------------------------------------
def walk(sources_dir: Path) -> Iterable[dict]:
    have_pdf = _try_import_pdfplumber()
    have_docx = _try_import_docx()
    counter = 0
    files = sorted(sources_dir.rglob("*"))
    for f in files:
        if not f.is_file() or f.name.startswith("."):
            continue
        counter += 1
        src_id = f"src_{counter:04d}"
        suffix = f.suffix.lower()
        try:
            if suffix == ".pdf":
                if not have_pdf:
                    sys.stderr.write(
                        f"Skipping {f}: pdfplumber not installed. "
                        "Install with: pip install pdfplumber\n"
                    )
                    continue
                yield ingest_pdf(f, src_id)
            elif suffix == ".docx":
                if not have_docx:
                    sys.stderr.write(
                        f"Skipping {f}: python-docx not installed.\n"
                    )
                    continue
                yield ingest_docx(f, src_id)
            elif suffix in (".vtt", ".srt"):
                yield ingest_subtitle(f, src_id)
            elif suffix in (".txt", ".md"):
                if f.name.lower() == "urls.txt":
                    yield from ingest_url_list(f, src_id_base=src_id)
                else:
                    yield ingest_text(f, src_id)
            else:
                # Skip silently; not all files are sources.
                continue
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"Failed to ingest {f}: {e}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sources_dir", help="Directory of source materials")
    ap.add_argument("--out", help="Output JSON path (default: stdout)")
    args = ap.parse_args()
    src_dir = Path(args.sources_dir)
    if not src_dir.is_dir():
        sys.stderr.write(f"Sources dir not found or not a directory: {src_dir}\n")
        return 1
    sources = list(walk(src_dir))
    payload = {
        "sources_dir": str(src_dir),
        "n_sources": len(sources),
        "n_segments": sum(len(s["segments"]) for s in sources),
        "sources": sources,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        sys.stderr.write(f"Wrote {args.out}\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
