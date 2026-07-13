---
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
  author: Arizona State University team
  version: "0.1.0"
---

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
