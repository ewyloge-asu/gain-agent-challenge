#!/usr/bin/env python3
"""
extract_claims.py — Extract factual claims from a draft .docx.

Usage:
    python extract_claims.py <draft.docx> [--out claims.json]

Reads a .docx, segments it into paragraphs and sentences, classifies each
sentence as either needing a footnote or not, and emits a JSON list of
claim records that downstream scripts can use.

This script does NOT use an LLM. It uses heuristics that the agent loop
can refine in step 4 of the workflow. The goal is high recall — flag
anything that might need a footnote — and let the agent prune in review.

The contract with the agent:
    Each claim record has the shape documented in
    references/claim_extraction_rules.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    from docx import Document
except ImportError:
    sys.stderr.write(
        "python-docx is required. Install with: pip install python-docx\n"
    )
    sys.exit(1)


# ---------- Sentence segmentation -----------------------------------------
# A pragmatic sentence splitter. Not perfect; aim is recall.
# Splits on sentence-final . ! ? followed by whitespace + capital,
# while protecting common abbreviations and decimal numbers.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "rev", "fr", "sr", "jr", "st", "mt", "ft",
    "no", "vs", "etc", "ie", "eg", "approx", "est", "incl", "vol", "inc",
    "co", "corp", "ltd", "llc", "llp", "pty",
    "u.s", "u.k", "u.n", "e.u", "d.c", "ph.d", "m.d", "j.d", "b.a", "m.a",
    "sen", "rep", "gov", "pres", "sec", "asst", "atty",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}

_SENT_END = re.compile(r'([.!?])(\s+)(?=[A-Z"“])')


def _protect_decimals(text: str) -> str:
    return re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", text)


def _restore_decimals(text: str) -> str:
    return text.replace("<DOT>", ".")


def split_sentences(paragraph: str) -> list[str]:
    if not paragraph.strip():
        return []
    work = _protect_decimals(paragraph)
    out, last = [], 0
    for m in _SENT_END.finditer(work):
        # Don't split after a known abbreviation.
        prev_word = re.search(r"(\S+)$", work[: m.start()])
        if prev_word and prev_word.group(1).rstrip(".").lower() in _ABBREVIATIONS:
            continue
        end = m.end(1)  # include the punctuation
        out.append(_restore_decimals(work[last:end]).strip())
        last = m.end(2)
    tail = _restore_decimals(work[last:]).strip()
    if tail:
        out.append(tail)
    return [s for s in out if s]


# ---------- Heuristic classifiers -----------------------------------------
_NUMBER_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s*(?:%|percent|percentage|million|billion|trillion|"
    r"thousand|hundred)?\b",
    re.IGNORECASE,
)
_DOLLAR_RE = re.compile(r"\$\d[\d,]*(?:\.\d+)?(?:\s*(?:million|billion|trillion|thousand|k|m|bn))?", re.IGNORECASE)
_PERCENT_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*%")
_DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}\b",
)
_QUOTE_RE = re.compile(r'["“”][^"“”]{6,}["“”]')
_ATTRIBUTION_RE = re.compile(
    r"\b(?:said|told|argued|wrote|stated|reported|testified|claimed|"
    r"alleged|noted|warned|announced|denied|acknowledged|conceded|"
    r"according to|in a statement|in an interview)\b",
    re.IGNORECASE,
)
_SUPERLATIVE_RE = re.compile(
    r"\b(?:first|last|only|biggest|largest|smallest|fastest|slowest|"
    r"highest|lowest|most|least|best|worst|unprecedented|record(?:-breaking)?|"
    r"more than (?:any|all)|less than (?:any|all))\b",
    re.IGNORECASE,
)
_NAMED_ENTITY_RE = re.compile(
    r"\b(?:[A-Z][a-z]+\s+){1,4}(?:Inc|Corp|LLC|LLP|Ltd|Co|Company|"
    r"Foundation|Association|Council|Committee|Agency|Bureau|Department|"
    r"Office|Commission|Authority|Administration|Organization|Society|"
    r"University|Institute|Court)\b",
)
_TITLE_RE = re.compile(
    r"\b(?:Sen(?:ator)?|Rep(?:resentative)?|Gov(?:ernor)?|Pres(?:ident)?|"
    r"CEO|CFO|CTO|COO|Director|Secretary|Chairman|Chairwoman|Spokesperson|"
    r"Attorney General|Mayor|Judge|Justice|Officer|Detective|Commissioner|"
    r"Professor|Dr\.|Rev\.)\b",
)

# A short list of "narrative scaffolding" lead-ins that, on their own, don't
# carry verifiable factual content.
_NARRATIVE_LEADINS = re.compile(
    r"^(?:Here(?:'s| is) (?:what|why|how)|This is|That was|Now,?|Then,?|"
    r"Meanwhile,?|At first,?|Later,?)\b",
    re.IGNORECASE,
)


def classify_sentence(text: str) -> dict:
    """Return a dict describing whether and why this sentence needs a footnote."""
    distinctive_terms: list[str] = []
    flags: list[str] = []

    if _DOLLAR_RE.search(text):
        flags.append("dollar_amount")
        distinctive_terms.extend(_DOLLAR_RE.findall(text))
    if _PERCENT_RE.search(text):
        flags.append("percentage")
        distinctive_terms.extend(_PERCENT_RE.findall(text))
    # Generic numbers (not part of a date)
    for m in _NUMBER_RE.finditer(text):
        token = m.group(0)
        if not _DATE_RE.fullmatch(token.strip()):
            distinctive_terms.append(token)
    if _DATE_RE.search(text):
        flags.append("date")
        distinctive_terms.extend(_DATE_RE.findall(text))
    if _QUOTE_RE.search(text):
        flags.append("direct_quote")
    if _ATTRIBUTION_RE.search(text):
        flags.append("attribution")
    if _SUPERLATIVE_RE.search(text):
        flags.append("superlative")
        distinctive_terms.extend(
            m.group(0) for m in _SUPERLATIVE_RE.finditer(text)
        )
    if _NAMED_ENTITY_RE.search(text):
        flags.append("named_organization")
        distinctive_terms.extend(
            m.group(0) for m in _NAMED_ENTITY_RE.finditer(text)
        )
    if _TITLE_RE.search(text):
        flags.append("named_title")

    # Pick the primary claim_type
    if "direct_quote" in flags:
        claim_type = "quote"
    elif "attribution" in flags:
        claim_type = "attribution"
    elif "dollar_amount" in flags or "percentage" in flags:
        claim_type = "statistic"
    elif "date" in flags and ("named_organization" in flags or "named_title" in flags):
        claim_type = "date_event"
    elif "superlative" in flags:
        claim_type = "comparison_or_superlative"
    elif flags:
        claim_type = "named_fact"
    else:
        claim_type = "general_assertion"

    is_narrative = bool(_NARRATIVE_LEADINS.match(text)) and not flags
    needs_footnote = bool(flags) and not is_narrative

    # Dedupe and clean distinctive terms.
    seen = set()
    uniq_terms = []
    for t in distinctive_terms:
        t = t.strip()
        if t and t.lower() not in seen:
            uniq_terms.append(t)
            seen.add(t.lower())

    rationale = (
        ", ".join(flags) if flags
        else ("narrative scaffolding" if is_narrative else "no verifiable assertion detected")
    )

    return {
        "claim_type": claim_type,
        "distinctive_terms": uniq_terms[:12],
        "flags": flags,
        "needs_footnote": needs_footnote,
        "rationale": rationale,
    }


# ---------- Multi-claim detection -----------------------------------------
def detect_multi_claim(text: str) -> bool:
    """Sentences containing both a primary statistic and a comparative
    reference (e.g. 'more than triple') typically pack multiple distinct
    claims and should be split."""
    has_stat = bool(_DOLLAR_RE.search(text) or _PERCENT_RE.search(text) or _NUMBER_RE.search(text))
    has_comparison = bool(re.search(
        r"\b(?:more|less|greater|fewer|higher|lower|double|triple|quadruple|"
        r"half|quarter|compared to|versus|vs\.|than (?:any|in))\b",
        text, re.IGNORECASE,
    ))
    return has_stat and has_comparison


# ---------- Main pipeline -------------------------------------------------
def extract_from_docx(path: Path) -> Iterable[dict]:
    doc = Document(str(path))
    cursor = 0
    claim_n = 0
    for para_idx, para in enumerate(doc.paragraphs):
        text = para.text
        sentences = split_sentences(text)
        for sent_idx, sentence in enumerate(sentences):
            start = text.find(sentence, 0)
            span = (cursor + max(start, 0), cursor + max(start, 0) + len(sentence))
            cls = classify_sentence(sentence)
            claim_n += 1
            yield {
                "id": f"claim_{claim_n:04d}",
                "paragraph_index": para_idx,
                "sentence_index": sent_idx,
                "char_span": list(span),
                "sentence_text": sentence,
                "claim_type": cls["claim_type"],
                "distinctive_terms": cls["distinctive_terms"],
                "flags": cls["flags"],
                "multi_claim": detect_multi_claim(sentence),
                "needs_footnote": cls["needs_footnote"],
                "rationale": cls["rationale"],
            }
        cursor += len(text) + 1  # +1 for paragraph break


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("draft", help="Path to a .docx draft article")
    ap.add_argument("--out", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        sys.stderr.write(f"Draft not found: {draft_path}\n")
        return 1

    claims = list(extract_from_docx(draft_path))

    output = {
        "draft_path": str(draft_path),
        "n_claims_extracted": len(claims),
        "n_needing_footnote": sum(1 for c in claims if c["needs_footnote"]),
        "claims": claims,
    }

    payload = json.dumps(output, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        sys.stderr.write(f"Wrote {args.out}\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
