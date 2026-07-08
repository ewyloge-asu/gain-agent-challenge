#!/usr/bin/env python3
"""Minimal Agent Skills spec validator (per agentskills.io/specification.md).

Checks the SKILL.md frontmatter rules so the submission validates cleanly even
where the official `skills-ref validate` binary is unavailable. If skills-ref IS
installed, prefer it: `skills-ref validate ./lobbying-influence-mapper`.

Usage: python3 validate_skill.py lobbying-influence-mapper
"""
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def fail(msg):
    print(f"FAIL: {msg}"); sys.exit(1)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "lobbying-influence-mapper").resolve()
    skill = root / "SKILL.md"
    if not skill.exists():
        fail(f"no SKILL.md in {root}")
    text = skill.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail("missing YAML frontmatter delimited by ---")
    fm = m.group(1)

    # name
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    if not nm:
        fail("frontmatter missing required 'name'")
    name = nm.group(1).strip()
    if not (1 <= len(name) <= 64):
        fail("name must be 1-64 chars")
    if not NAME_RE.match(name):
        fail("name must be lowercase alphanumerics/hyphens, no leading/trailing/double hyphen")
    if name != root.name:
        fail(f"name '{name}' must match parent directory name '{root.name}'")

    # description (supports '>-' block scalar)
    dm = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", fm, re.S | re.M)
    if not dm:
        fail("frontmatter missing required 'description'")
    desc = re.sub(r"\s+", " ", dm.group(1).replace(">-", "")).strip()
    if not (1 <= len(desc) <= 1024):
        fail(f"description must be 1-1024 chars (got {len(desc)})")

    # body present
    body = text[m.end():].strip()
    if len(body) < 50:
        fail("SKILL.md body looks empty")

    # referenced relative files exist
    missing = [r for r in re.findall(r"\(((?:references|scripts|assets)/[^)]+)\)", body)
               if not (root / r).exists()]
    if missing:
        fail(f"referenced files not found: {missing}")

    print(f"OK: {name}")
    print(f"  description: {len(desc)} chars")
    print(f"  body: {len(body.splitlines())} lines")
    print(f"  scripts: {len(list((root/'scripts').glob('*.py')))} py")
    print(f"  references: {len(list((root/'references').glob('*.md')))} md")
    print(f"  assets: {len(list((root/'assets').glob('*')))} files")


if __name__ == "__main__":
    main()
