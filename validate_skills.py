#!/usr/bin/env python3
"""Validate skills against the Agent Skills spec (agentskills.io): each skill is a
directory with a SKILL.md whose YAML front-matter has a valid `name` and `description`.
Lightweight, stdlib-only. Exit 0 = all valid.

Usage: python3 validate_skills.py menu/skills
"""
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_front_matter(text):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta = {}
    key = None
    for line in parts[1].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key = m.group(1)
            meta[key] = m.group(2).strip()
        elif key and line.startswith(" "):
            meta[key] = (meta.get(key, "") + " " + line.strip()).strip()
    return meta


def validate(skills_dir):
    problems, ok = [], []
    for name in sorted(os.listdir(skills_dir)):
        d = os.path.join(skills_dir, name)
        if not os.path.isdir(d):
            continue
        sp = os.path.join(d, "SKILL.md")
        if not os.path.isfile(sp):
            problems.append(f"{name}: no SKILL.md")
            continue
        meta = parse_front_matter(open(sp, encoding="utf-8").read())
        if meta is None:
            problems.append(f"{name}: missing/blank YAML front-matter")
            continue
        nm = (meta.get("name") or "").strip().strip('"\'')
        desc = (meta.get("description") or "").strip()
        if not nm:
            problems.append(f"{name}: front-matter missing `name`")
        elif not NAME_RE.match(nm):
            problems.append(f"{name}: name {nm!r} not [a-z0-9-] form")
        if not desc:
            problems.append(f"{name}: front-matter missing `description`")
        elif len(desc) > 1024:
            problems.append(f"{name}: description {len(desc)} chars (>1024 recommended max)")
        if nm and NAME_RE.match(nm) and desc and len(desc) <= 1024:
            ok.append(f"{name}: name={nm!r} desc={len(desc)}c")
    return ok, problems


def main():
    skills_dir = sys.argv[1] if len(sys.argv) > 1 else "menu/skills"
    ok, problems = validate(skills_dir)
    print(f"Validating skills in {skills_dir}\n")
    for o in ok:
        print("  OK  " + o)
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  !!  " + p)
        return 1
    print(f"\n✓ all {len(ok)} skills valid against the Agent Skills spec.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
