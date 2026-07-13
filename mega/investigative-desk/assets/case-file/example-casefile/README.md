# Case File — Education Lobbying (seed)

A worked example of the **Case File skill** structure, built from a coworker's
Methodology & Replication Guide. It shows how a reproducible analysis workflow populates a
durable, auditable, multi-session investigation state.

## What's here

| File | Role |
|---|---|
| `brief.md` | The investigation charter — question, scope, finding bar |
| `workflow.md` | **The spine.** The reproducible analysis procedure (adapted from the methodology guide) — scripts, filters, seeds, caveats |
| `entities.yaml` | Canonical entities referenced across threads/findings |
| `threads/` | Lines of inquiry with status + next action; each cites the workflow step that produced it |
| `findings.yaml` | Claims that graduated to "documented," each source-bound; includes legal flags |
| `journal.md` | Append-only session log |

## The two illustrative outcomes

- **A deep, near-confirmed story:** `threads/T-0001` + findings F-001/F-002/F-003 (the ECCA
  revolving-door and contribution trail).
- **A board of open leads:** `threads/T-0002`…`T-0007` (six landscape story leads).

Both came from the *same* `workflow.md`, which is the point: the methodology is the
reusable engine; the outcomes are where it happens to land.

## How to read it as the skill

Each thread/finding names its **workflow step + script** and its **source records**, and
open threads carry a **next action**. That triad — provenance, evidence, next step — is
what keeps the investigation reproducible and lets an editor audit it without re-doing the
work. See the skill's `SKILL.md` and `references/file_formats.md` for the full design.

## Note on fidelity

Every entity, figure, and record here traces to the coworker's three documents
(ECCA_Reporting_Memo, Education_Lobbying_Analysis, Methodology_Replication_Guide, June
2026). Member canonical IDs are placeholders pending the Member Resolver skill (they'd
become bioguide IDs). Nothing here is fabricated; unproven links are marked as such.
