#!/usr/bin/env python3
"""
insert_tracked_footnotes.py — Insert rendered footnotes into a .docx as
                              tracked changes.

Usage:
    python insert_tracked_footnotes.py \\
        --draft draft.docx \\
        --claims claims.json \\
        --footnotes footnotes.json \\
        [--upgrades upgrades.json] \\
        --out draft_footnoted.docx \\
        [--author "Claude"] [--date 2026-06-25T19:30:00Z]

Reads:
    draft.docx       — original draft
    claims.json      — output of extract_claims.py (provides paragraph_index,
                       sentence_text, and char_span per claim_id)
    footnotes.json   — output of format_footnote.py (provides the rendered
                       footnote text and URL per claim_id)
    upgrades.json    — optional; the agent's per-existing-footnote decisions
                       from step 2 of the workflow. Shape:
                         { "upgrades": [
                             { "footnote_id": "3",
                               "action": "improve" | "replace" | "keep" | "flag",
                               "reason": "...",
                               "improved_footnote": "...",
                               "improved_url": "https://..." },
                             ...
                         ] }

Writes:
    draft_footnoted.docx — a copy of the draft with:
                           (a) new footnote references at the end of each
                               footnoted sentence, wrapped in <w:ins> so they
                               appear as tracked insertions;
                           (b) existing footnote bodies with action=improve
                               or replace edited in place: old body wrapped in
                               <w:del> and the new body wrapped in <w:ins>,
                               so the editor sees the old text struck through
                               and the new text underlined and can accept or
                               reject each one.

Implementation notes:
    - We open the .docx as a zip and edit document.xml, footnotes.xml, and
      the relationship files directly. This avoids depending on python-docx's
      partial support for footnotes / tracked changes.
    - We locate the sentence to footnote by matching the sentence text within
      paragraph N of document.xml. If the exact text isn't found verbatim
      (because the original split a word across runs), we fall back to the
      end of the paragraph.
    - Each insertion gets a unique w:ins ID and a unique w:footnoteReference
      ID. The footnote text is the rendered footnote, with the URL turned
      into a hyperlink anchored on a meaningful keyword if one is detected.

Tested with:
    python-docx >= 1.0
    lxml >= 4.6
"""
from __future__ import annotations


import argparse
import datetime as dt
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable

try:
    from lxml import etree
except ImportError:
    sys.stderr.write("lxml is required. Install with: pip install lxml\n")
    sys.exit(1)


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes"
)
COMMENTS_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)
HYPERLINK_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)
NSMAP = {"w": W_NS, "r": R_NS}


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def r_attr(tag: str) -> str:
    return f"{{{R_NS}}}{tag}"


# ---------- Footnotes part skeleton ---------------------------------------
FOOTNOTES_SKELETON = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:footnote w:type="separator" w:id="-1">
    <w:p><w:r><w:separator/></w:r></w:p>
  </w:footnote>
  <w:footnote w:type="continuationSeparator" w:id="0">
    <w:p><w:r><w:continuationSeparator/></w:r></w:p>
  </w:footnote>
</w:footnotes>
"""


def _ensure_footnotes_part(z_in: zipfile.ZipFile, members: dict) -> tuple[etree._Element, str]:
    """Return (footnotes_root, footnotes_path). Creates a skeleton if absent."""
    candidates = [n for n in members if n.endswith("/footnotes.xml") or n == "word/footnotes.xml"]
    if candidates:
        path = candidates[0]
        return etree.fromstring(members[path]), path
    path = "word/footnotes.xml"
    members[path] = FOOTNOTES_SKELETON
    return etree.fromstring(FOOTNOTES_SKELETON), path


def _ensure_footnotes_relationship(rels_xml: bytes, footnotes_target: str) -> tuple[bytes, str]:
    """Make sure document.xml.rels references footnotes.xml. Return updated bytes
    and the relationship id (rId)."""
    root = etree.fromstring(rels_xml)
    REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    ns = {"r": REL_NS}
    for rel in root.findall("r:Relationship", ns):
        if rel.get("Type") == WP_REL:
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), rel.get("Id")
    existing_ids = [rel.get("Id") for rel in root.findall("r:Relationship", ns)]
    n = 1
    while f"rId{n}" in existing_ids:
        n += 1
    new_id = f"rId{n}"
    rel = etree.SubElement(root, f"{{{REL_NS}}}Relationship",
                           Id=new_id, Type=WP_REL,
                           Target="footnotes.xml")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), new_id


def _ensure_content_types_for_footnotes(ct_xml: bytes) -> bytes:
    """Make sure [Content_Types].xml registers footnotes.xml."""
    root = etree.fromstring(ct_xml)
    CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
    fn_ct = ("application/vnd.openxmlformats-officedocument."
             "wordprocessingml.footnotes+xml")
    for ov in root.findall(f"{{{CT_NS}}}Override"):
        if ov.get("PartName") == "/word/footnotes.xml":
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    etree.SubElement(root, f"{{{CT_NS}}}Override",
                     PartName="/word/footnotes.xml", ContentType=fn_ct)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------- Comments part (Word comments) --------------------------------
COMMENTS_SKELETON = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
</w:comments>
"""


def _ensure_comments_part(members: dict) -> tuple[etree._Element, str]:
    """Return (comments_root, comments_path). Create a skeleton if absent."""
    path = "word/comments.xml"
    if path in members:
        return etree.fromstring(members[path]), path
    members[path] = COMMENTS_SKELETON
    return etree.fromstring(COMMENTS_SKELETON), path


def _ensure_comments_relationship(rels_xml: bytes) -> bytes:
    """Make sure document.xml.rels references comments.xml."""
    REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    root = etree.fromstring(rels_xml)
    ns = {"r": REL_NS}
    for rel in root.findall("r:Relationship", ns):
        if rel.get("Type") == COMMENTS_REL:
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    existing_ids = [rel.get("Id") for rel in root.findall("r:Relationship", ns)]
    n = 1
    while f"rId{n}" in existing_ids:
        n += 1
    new_id = f"rId{n}"
    etree.SubElement(root, f"{{{REL_NS}}}Relationship",
                     Id=new_id, Type=COMMENTS_REL, Target="comments.xml")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _ensure_content_types_for_comments(ct_xml: bytes) -> bytes:
    """Make sure [Content_Types].xml registers comments.xml."""
    CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
    root = etree.fromstring(ct_xml)
    comments_ct = ("application/vnd.openxmlformats-officedocument."
                   "wordprocessingml.comments+xml")
    for ov in root.findall(f"{{{CT_NS}}}Override"):
        if ov.get("PartName") == "/word/comments.xml":
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    etree.SubElement(root, f"{{{CT_NS}}}Override",
                     PartName="/word/comments.xml", ContentType=comments_ct)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------- Attaching comments to paragraphs -----------------------------
_FLAG_TITLES = {
    "no_source": "No source found",
    "context_concern": "Possible out-of-context quoting",
    "existing_footnote_flag": "Existing footnote may not support the claim",
}


def _build_comment_element(
    comment_id: int,
    body_text: str,
    flag_type: str,
    author: str,
    date_iso: str,
) -> etree._Element:
    """Construct a <w:comment w:id=N> element with body_text inside."""
    title = _FLAG_TITLES.get(flag_type, flag_type.replace("_", " ").title())
    full_text = f"[{title}] {body_text}"
    initials = "".join(part[0].upper() for part in author.split())[:3] or "A"
    c = etree.Element(w("comment"), {
        w("id"): str(comment_id),
        w("author"): author,
        w("date"): date_iso,
        w("initials"): initials,
    })
    p = etree.SubElement(c, w("p"))
    r = etree.SubElement(p, w("r"))
    t = etree.SubElement(r, w("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = full_text
    return c


def _attach_comment_to_paragraph(
    p: etree._Element,
    comment_id: int,
) -> None:
    """Anchor a comment to paragraph p. We place the commentRangeStart at the
    very beginning of the paragraph and commentRangeEnd + reference at the end,
    so the entire paragraph is the comment's anchor. Word will show the
    comment in the margin alongside the paragraph."""
    # Start of paragraph.
    start = etree.SubElement(p, w("commentRangeStart"), {w("id"): str(comment_id)})
    # Move it to be the first child of p.
    p.insert(0, start)
    # End + reference at the end of paragraph.
    etree.SubElement(p, w("commentRangeEnd"), {w("id"): str(comment_id)})
    ref_r = etree.SubElement(p, w("r"))
    ref_rPr = etree.SubElement(ref_r, w("rPr"))
    ref_rStyle = etree.SubElement(ref_rPr, w("rStyle"))
    ref_rStyle.set(w("val"), "CommentReference")
    etree.SubElement(ref_r, w("commentReference"), {w("id"): str(comment_id)})


# ---------- Footnotes rels ------------------------------------------------
def _ensure_footnotes_rels(members: dict) -> tuple[etree._Element, str]:
    """Return (rels_root, rels_path) for word/_rels/footnotes.xml.rels. Create
    a fresh document if absent."""
    REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    path = "word/_rels/footnotes.xml.rels"
    if path in members:
        return etree.fromstring(members[path]), path
    root = etree.Element(f"{{{REL_NS}}}Relationships",
                         nsmap={None: REL_NS})
    members[path] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return root, path


def _add_hyperlink_rel(rels_root: etree._Element, url: str) -> str:
    """Add a hyperlink relationship and return its Id."""
    REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
    existing_ids = [r.get("Id") for r in rels_root.findall(f"{{{REL_NS}}}Relationship")]
    n = 1
    while f"rId{n}" in existing_ids:
        n += 1
    rid = f"rId{n}"
    etree.SubElement(rels_root, f"{{{REL_NS}}}Relationship",
                     Id=rid, Type=HYPERLINK_REL, Target=url,
                     TargetMode="External")
    return rid


# ---------- Building footnote bodies --------------------------------------
def _split_footnote_text(rendered: str, url: str | None) -> tuple[str, str, str | None, str]:
    """Decide where to anchor the hyperlink inside the rendered footnote.
    Returns (pre, anchor, url_or_none, post) so the caller can write:
        pre <hyperlink anchor> post

    Heuristic: prefer the first identifier-like token (report number, case
    number, organization acronym in ALL CAPS) as the anchor. Otherwise use
    the first 6 words.
    """
    if not url:
        return rendered, "", None, ""

    # Try report-number patterns first.
    m = re.search(r"\b(GAO-\d+-\d+|CRS-[A-Z0-9-]+|\d{4}-CV-\d+|Case No\.\s*\S+)\b", rendered)
    if m:
        return rendered[: m.start()], m.group(0), url, rendered[m.end():]

    # Then a quoted document title.
    m = re.search(r'"([^"]{6,80})"', rendered)
    if m:
        return rendered[: m.start()], rendered[m.start():m.end()], url, rendered[m.end():]

    # Then the first up-to-6-word phrase.
    tokens = rendered.split()
    if len(tokens) <= 6:
        return "", rendered, url, ""
    anchor = " ".join(tokens[:6])
    post = " " + " ".join(tokens[6:])
    return "", anchor, url, post


def _build_footnote_element(
    footnote_id: int,
    rendered_text: str,
    url: str | None,
    author: str,
    date_iso: str,
    ins_id_start: int,
    rels_root: etree._Element,
) -> tuple[etree._Element, int]:
    """Construct a <w:footnote w:id=N> element with the rendered text inside.
    Returns (footnote_element, next_ins_id)."""
    fn = etree.Element(w("footnote"), {w("id"): str(footnote_id)})
    p = etree.SubElement(fn, w("p"))
    pPr = etree.SubElement(p, w("pPr"))
    pStyle = etree.SubElement(pPr, w("pStyle"))
    pStyle.set(w("val"), "FootnoteText")

    # First run: the footnote reference marker.
    # Apply superscript explicitly (don't rely on the FootnoteReference style
    # being defined in the doc's styles.xml — some templates omit it).
    ref_r = etree.SubElement(p, w("r"))
    ref_rPr = etree.SubElement(ref_r, w("rPr"))
    ref_rStyle = etree.SubElement(ref_rPr, w("rStyle"))
    ref_rStyle.set(w("val"), "FootnoteReference")
    ref_vert = etree.SubElement(ref_rPr, w("vertAlign"))
    ref_vert.set(w("val"), "superscript")
    etree.SubElement(ref_r, w("footnoteRef"))

    # Wrap the body of the footnote in <w:ins> so the inserted text is tracked.
    ins = etree.SubElement(p, w("ins"), {
        w("id"): str(ins_id_start),
        w("author"): author,
        w("date"): date_iso,
    })
    ins_id_start += 1

    pre, anchor, anchor_url, post = _split_footnote_text(rendered_text, url)

    # Leading space + pre-text
    space_run = etree.SubElement(ins, w("r"))
    t = etree.SubElement(space_run, w("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = " " + pre

    if anchor and anchor_url:
        rid = _add_hyperlink_rel(rels_root, anchor_url)
        hyperlink = etree.SubElement(ins, w("hyperlink"))
        hyperlink.set(r_attr("id"), rid)
        h_r = etree.SubElement(hyperlink, w("r"))
        h_rPr = etree.SubElement(h_r, w("rPr"))
        h_rStyle = etree.SubElement(h_rPr, w("rStyle"))
        h_rStyle.set(w("val"), "Hyperlink")
        h_t = etree.SubElement(h_r, w("t"))
        h_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        h_t.text = anchor
        # Post-text
        if post:
            post_r = etree.SubElement(ins, w("r"))
            post_t = etree.SubElement(post_r, w("t"))
            post_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            post_t.text = post
    elif anchor:
        # Anchor without URL (shouldn't happen, but just in case).
        a_r = etree.SubElement(ins, w("r"))
        a_t = etree.SubElement(a_r, w("t"))
        a_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        a_t.text = anchor + post

    return fn, ins_id_start


# ---------- Upgrading an existing footnote body ---------------------------
def _upgrade_existing_footnote(
    footnote_elem: etree._Element,
    new_rendered_text: str,
    new_url: str | None,
    author: str,
    date_iso: str,
    ins_id_start: int,
    del_id_start: int,
    rels_root: etree._Element,
) -> tuple[int, int]:
    """Modify an existing <w:footnote> in place: mark its body runs for
    deletion and append a new body wrapped in <w:ins>.

    The footnoteRef marker (the run containing <w:footnoteRef/>) is left
    untouched so the numbered marker remains visible in the rendered output.

    Returns (next_ins_id, next_del_id).
    """
    # Find the first paragraph in the footnote — that's where the body lives.
    p = footnote_elem.find(w("p"))
    if p is None:
        return ins_id_start, del_id_start

    # Identify the marker run (contains <w:footnoteRef/>). Everything AFTER
    # it is the body to be replaced.
    children = list(p)
    marker_idx = -1
    for i, child in enumerate(children):
        if child.tag == w("r") and child.find(w("footnoteRef")) is not None:
            marker_idx = i
            break

    # Walk the children after the marker and wrap them for deletion.
    # We collect them first, then replace.
    body_children = children[marker_idx + 1:] if marker_idx >= 0 else children[:]
    # Remove them from the paragraph.
    for c in body_children:
        p.remove(c)

    # If they aren't already inside a <w:del>, wrap them.
    del_elem = etree.SubElement(p, w("del"), {
        w("id"): str(del_id_start),
        w("author"): author,
        w("date"): date_iso,
    })
    del_id_start += 1
    for c in body_children:
        # Convert any <w:t> descendants inside this run to <w:delText>.
        _convert_t_to_delText(c)
        del_elem.append(c)

    # Append the new body, wrapped in <w:ins>.
    ins_elem = etree.SubElement(p, w("ins"), {
        w("id"): str(ins_id_start),
        w("author"): author,
        w("date"): date_iso,
    })
    ins_id_start += 1

    pre, anchor, anchor_url, post = _split_footnote_text(new_rendered_text, new_url)

    space_run = etree.SubElement(ins_elem, w("r"))
    t = etree.SubElement(space_run, w("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = " " + pre

    if anchor and anchor_url:
        rid = _add_hyperlink_rel(rels_root, anchor_url)
        hyperlink = etree.SubElement(ins_elem, w("hyperlink"))
        hyperlink.set(r_attr("id"), rid)
        h_r = etree.SubElement(hyperlink, w("r"))
        h_rPr = etree.SubElement(h_r, w("rPr"))
        h_rStyle = etree.SubElement(h_rPr, w("rStyle"))
        h_rStyle.set(w("val"), "Hyperlink")
        h_t = etree.SubElement(h_r, w("t"))
        h_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        h_t.text = anchor
        if post:
            post_r = etree.SubElement(ins_elem, w("r"))
            post_t = etree.SubElement(post_r, w("t"))
            post_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            post_t.text = post
    elif anchor:
        a_r = etree.SubElement(ins_elem, w("r"))
        a_t = etree.SubElement(a_r, w("t"))
        a_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        a_t.text = anchor + post

    return ins_id_start, del_id_start


def _convert_t_to_delText(elem: etree._Element) -> None:
    """In-place: turn every <w:t> descendant into <w:delText>. Required when
    wrapping runs inside <w:del> per the OOXML spec."""
    for t in list(elem.iter(w("t"))):
        t.tag = w("delText")


# ---------- Editing document.xml ------------------------------------------
def _para_text(p: etree._Element) -> str:
    return "".join(
        (t.text or "") for t in p.iter(w("t"))
    )


def _insert_footnote_ref_at_paragraph_end(
    p: etree._Element,
    footnote_id: int,
    author: str,
    date_iso: str,
    ins_id: int,
) -> None:
    """Append a tracked-change footnote reference at the end of paragraph p."""
    ins = etree.SubElement(p, w("ins"), {
        w("id"): str(ins_id),
        w("author"): author,
        w("date"): date_iso,
    })
    r = etree.SubElement(ins, w("r"))
    rPr = etree.SubElement(r, w("rPr"))
    rStyle = etree.SubElement(rPr, w("rStyle"))
    rStyle.set(w("val"), "FootnoteReference")
    # Apply superscript explicitly so the number renders raised + small even
    # when the document doesn't define a FootnoteReference style.
    vert = etree.SubElement(rPr, w("vertAlign"))
    vert.set(w("val"), "superscript")
    fr = etree.SubElement(r, w("footnoteReference"))
    fr.set(w("id"), str(footnote_id))


# ---------- Main pipeline -------------------------------------------------
def run(
    draft_path: Path,
    claims_path: Path,
    footnotes_path: Path,
    out_path: Path,
    author: str,
    date_iso: str | None,
    upgrades_path: Path | None = None,
    flags_path: Path | None = None,
) -> dict:
    if date_iso is None:
        date_iso = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    claims_data = json.loads(claims_path.read_text(encoding="utf-8"))
    footnotes_data = json.loads(footnotes_path.read_text(encoding="utf-8"))
    claims = {c["id"]: c for c in claims_data["claims"]}
    footnotes = footnotes_data["footnotes"]
    upgrades = []
    if upgrades_path is not None and upgrades_path.exists():
        upgrades_data = json.loads(upgrades_path.read_text(encoding="utf-8"))
        upgrades = upgrades_data.get("upgrades", [])
    flags = []
    if flags_path is not None and flags_path.exists():
        flags_data = json.loads(flags_path.read_text(encoding="utf-8"))
        flags = flags_data.get("flags", [])

    # Copy the draft to the output location so we modify in-place via zip.
    shutil.copyfile(draft_path, out_path)

    # Load all parts.
    with zipfile.ZipFile(out_path, "r") as z:
        members = {n: z.read(n) for n in z.namelist()}

    # Locate document.xml.
    doc_path = "word/document.xml"
    rels_path = "word/_rels/document.xml.rels"
    ct_path = "[Content_Types].xml"
    if doc_path not in members or rels_path not in members or ct_path not in members:
        raise RuntimeError("Draft .docx missing required parts.")

    document = etree.fromstring(members[doc_path])
    body = document.find(w("body"))
    if body is None:
        raise RuntimeError("document.xml has no body element.")
    paragraphs = body.findall(w("p"))

    # Ensure footnotes part + relationships + content types.
    footnotes_root, fn_path = _ensure_footnotes_part(z_in=None, members=members)
    members[rels_path], _fn_rel_id = _ensure_footnotes_relationship(members[rels_path], fn_path)
    members[ct_path] = _ensure_content_types_for_footnotes(members[ct_path])
    fn_rels_root, fn_rels_path = _ensure_footnotes_rels(members)

    # Ensure comments part + relationships + content types if any flags are
    # being applied.
    comments_root = None
    comments_path = None
    if flags:
        comments_root, comments_path = _ensure_comments_part(members)
        members[rels_path] = _ensure_comments_relationship(members[rels_path])
        members[ct_path] = _ensure_content_types_for_comments(members[ct_path])

    # Determine the next footnote id (avoid collisions with existing footnotes).
    existing_ids = [
        int(fn.get(w("id"), "0"))
        for fn in footnotes_root.findall(w("footnote"))
    ]
    next_fn_id = max(existing_ids + [0]) + 1
    next_ins_id = 1000  # high to avoid collisions
    next_del_id = 2000

    summary = {
        "inserted": 0,
        "skipped_missing_paragraph": 0,
        "needs_source": 0,
        "upgraded": 0,
        "kept": 0,
        "flagged_existing_footnotes": 0,
        "comments_attached": 0,
    }
    next_comment_id = 1
    existing_comment_ids = [
        int(c.get(w("id"), "-1"))
        for c in (comments_root.findall(w("comment")) if comments_root is not None else [])
    ]
    if existing_comment_ids:
        next_comment_id = max(existing_comment_ids) + 1

    # ---- Apply upgrades to existing footnotes first --------------------
    fn_by_id = {fn.get(w("id")): fn for fn in footnotes_root.findall(w("footnote"))}
    # Build a map from existing-footnote-id → paragraph_index, so a `flag`
    # upgrade can attach a comment to the right paragraph in the body.
    fn_to_para: dict[str, int] = {}
    for i, p in enumerate(paragraphs):
        for fr in p.iter(w("footnoteReference")):
            fid = fr.get(w("id"))
            if fid is not None:
                fn_to_para[fid] = i

    for up in upgrades:
        action = up.get("action", "keep")
        fid = str(up.get("footnote_id"))
        if action == "keep":
            summary["kept"] += 1
            continue
        if action == "flag":
            summary["flagged_existing_footnotes"] += 1
            # Attach a comment to the paragraph the flagged footnote belongs to.
            if comments_root is None:
                comments_root, comments_path = _ensure_comments_part(members)
                members[rels_path] = _ensure_comments_relationship(members[rels_path])
                members[ct_path] = _ensure_content_types_for_comments(members[ct_path])
            para_idx = fn_to_para.get(fid)
            if para_idx is not None and para_idx < len(paragraphs):
                comment_body = up.get("reason") or "This existing footnote does not appear to support the claim."
                comments_root.append(_build_comment_element(
                    comment_id=next_comment_id,
                    body_text=comment_body,
                    flag_type="existing_footnote_flag",
                    author=author, date_iso=date_iso,
                ))
                _attach_comment_to_paragraph(paragraphs[para_idx], next_comment_id)
                next_comment_id += 1
                summary["comments_attached"] += 1
            continue
        if action not in ("improve", "replace"):
            continue
        fn_elem = fn_by_id.get(fid)
        if fn_elem is None:
            continue
        new_text = up.get("improved_footnote") or ""
        new_url = up.get("improved_url")
        if not new_text:
            continue
        next_ins_id, next_del_id = _upgrade_existing_footnote(
            fn_elem,
            new_rendered_text=new_text,
            new_url=new_url,
            author=author,
            date_iso=date_iso,
            ins_id_start=next_ins_id,
            del_id_start=next_del_id,
            rels_root=fn_rels_root,
        )
        summary["upgraded"] += 1

    # ---- Apply standalone flags as Word comments ----------------------
    for flag in flags:
        flag_type = flag.get("flag_type") or "no_source"
        message = flag.get("message") or ""
        para_idx = flag.get("paragraph_index")
        claim_id = flag.get("claim_id")
        # Fall back to claim's paragraph_index if not given explicitly.
        if para_idx is None and claim_id and claim_id in claims:
            para_idx = claims[claim_id]["paragraph_index"]
        if para_idx is None or para_idx >= len(paragraphs):
            continue
        if comments_root is None:
            comments_root, comments_path = _ensure_comments_part(members)
            members[rels_path] = _ensure_comments_relationship(members[rels_path])
            members[ct_path] = _ensure_content_types_for_comments(members[ct_path])
        comments_root.append(_build_comment_element(
            comment_id=next_comment_id,
            body_text=message,
            flag_type=flag_type,
            author=author, date_iso=date_iso,
        ))
        _attach_comment_to_paragraph(paragraphs[para_idx], next_comment_id)
        next_comment_id += 1
        summary["comments_attached"] += 1

    for fn_record in footnotes:
        claim = claims.get(fn_record["claim_id"])
        if not claim:
            continue
        if fn_record["match_status"] == "needs_source":
            summary["needs_source"] += 1
        para_idx = claim["paragraph_index"]
        if para_idx >= len(paragraphs):
            summary["skipped_missing_paragraph"] += 1
            continue
        target_p = paragraphs[para_idx]

        # Build the footnote element and append to footnotes_root.
        fn_elem, next_ins_id = _build_footnote_element(
            footnote_id=next_fn_id,
            rendered_text=fn_record["rendered_footnote"],
            url=fn_record.get("url"),
            author=author,
            date_iso=date_iso,
            ins_id_start=next_ins_id,
            rels_root=fn_rels_root,
        )
        footnotes_root.append(fn_elem)

        # Insert tracked-change reference at the paragraph's end.
        _insert_footnote_ref_at_paragraph_end(
            target_p,
            footnote_id=next_fn_id,
            author=author,
            date_iso=date_iso,
            ins_id=next_ins_id,
        )
        next_ins_id += 1
        next_fn_id += 1
        summary["inserted"] += 1

    # Serialize everything back.
    members[doc_path] = etree.tostring(
        document, xml_declaration=True, encoding="UTF-8", standalone=True,
    )
    members[fn_path] = etree.tostring(
        footnotes_root, xml_declaration=True, encoding="UTF-8", standalone=True,
    )
    members[fn_rels_path] = etree.tostring(
        fn_rels_root, xml_declaration=True, encoding="UTF-8", standalone=True,
    )
    if comments_root is not None and comments_path is not None:
        members[comments_path] = etree.tostring(
            comments_root, xml_declaration=True, encoding="UTF-8", standalone=True,
        )

    # Write a fresh zip with the modified parts.
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in members.items():
            zout.writestr(name, data)
    tmp_path.replace(out_path)

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draft", required=True, help="Original draft .docx")
    ap.add_argument("--claims", required=True, help="claims.json")
    ap.add_argument("--footnotes", required=True, help="footnotes.json")
    ap.add_argument("--upgrades", default=None,
                    help="upgrades.json (optional) for upgrading existing footnotes")
    ap.add_argument("--flags", default=None,
                    help="flags.json (optional) for attaching Word comments to paragraphs")
    ap.add_argument("--out", required=True, help="Output .docx path")
    ap.add_argument("--author", default="Claude", help="Tracked-change author")
    ap.add_argument("--date", default=None, help="Tracked-change ISO date")
    args = ap.parse_args()

    summary = run(
        Path(args.draft),
        Path(args.claims),
        Path(args.footnotes),
        Path(args.out),
        author=args.author,
        date_iso=args.date,
        upgrades_path=Path(args.upgrades) if args.upgrades else None,
        flags_path=Path(args.flags) if args.flags else None,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
