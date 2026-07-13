#!/usr/bin/env python3
"""Assemble the single 'mega' skill (investigative-desk) from the menu bundle's five
skills — ONE source of truth, so mega and menu never drift. Sub-skill scripts/references/
assets are namespaced under scripts/<skill>/, references/<skill>/, assets/<skill>/, and a
composed SKILL.md is generated from the orchestrator.

Usage: python3 assemble_mega.py            # reads menu/skills, writes mega/investigative-desk
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "menu", "skills")
OUT = os.path.join(HERE, "mega", "investigative-desk")
SUBSKILLS = ["lobbying-influence-mapper", "robodoig", "case-file",
             "checking-the-law", "howard-center-footnoter"]

FRONT_MATTER = """---
name: investigative-desk
description: >-
  All-in-one records-investigation skill for ANY dataset: scope the question with the
  user, open a durable case file, gather the given data plus relevant outside data
  (web-search for datasets/APIs included), profile it, surface and rank leads, verify
  against ground truth, check the law, and footnote every claim — every number traceable
  to a source, organized across sessions. Bundles the analysis engine, case file, legal
  checker, footnoter, and profiler behind one front door. Use to investigate a dataset,
  find stories in public records, triage leads, or run a reproducible investigation.
license: MIT
metadata:
  author: ASU / Howard Center team
  version: "0.1.0"
---
"""

BODY = """
# Investigative Desk (all-in-one)

This is the **menu bundle composed into one skill**. Same tools, one front door. The full
method, the S0 scope-framing loop, and the three-bucket assembly line are described in
`ASSEMBLY.md` (a copy of the `investigative-method` orchestrator). Paths differ only in that
each sub-skill's files are namespaced here:

- Analysis engine: `scripts/lobbying-influence-mapper/` (+ `references/`, `assets/`)
- Profiler + QA: `scripts/robodoig/`
- Case file (organizing spine): `scripts/case-file/`
- Legal checker: `references/checking-the-law/`
- Footnoter: `scripts/howard-center-footnoter/`
- Orchestrator tools (scope, find_data, fetch_source, build_dashboard): `tools/`

Shared setup lives at the bundle root: `setup_keys.py`, `credentials.env.example`,
`data-setup.md`. See `ASSEMBLY.md` for the step-by-step workflow and guardrails.

> Prefer the **menu** form (separate skills) if you want to reuse just one capability; use
> this **mega** form if you want the whole investigation behind a single skill.
"""


IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def copy_sub(kind, dst_root):
    for sk in SUBSKILLS:
        src = os.path.join(SRC, sk, kind)
        if os.path.isdir(src):
            dst = os.path.join(dst_root, kind, sk)
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    for kind in ("scripts", "references", "assets"):
        copy_sub(kind, OUT)
    # orchestrator tools
    tools_src = os.path.join(SRC, "investigative-method", "tools")
    shutil.copytree(tools_src, os.path.join(OUT, "tools"), dirs_exist_ok=True,
                    ignore=IGNORE)
    # ASSEMBLY.md = orchestrator SKILL.md (the method)
    shutil.copy(os.path.join(SRC, "investigative-method", "SKILL.md"),
                os.path.join(OUT, "ASSEMBLY.md"))
    with open(os.path.join(OUT, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(FRONT_MATTER + BODY)
    # count
    n = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"✓ assembled mega skill at {os.path.relpath(OUT, HERE)} ({n} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
