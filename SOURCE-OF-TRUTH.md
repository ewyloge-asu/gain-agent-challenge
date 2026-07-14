# Source of truth — read before editing anything

**The GitHub repos are canonical.** Nothing lives only on one person's laptop.

The product is named **Agent of Record** (renamed from "Case Agent," July 2026). The
GitHub repo slugs (`case-agent`, `case-agent-for-newsrooms`) keep the old name for now —
renaming repos breaks the published Pages URLs, so that waits until after the deadline.

| What you want to change | Edit this file, in this repo |
|---|---|
| The submission website (judge-facing) | `docs/index.html` in **gain-agent-challenge** ← Shelby: this one |
| The skills, findings, traces, legal checks | `menu/…` and `submission/…` in **gain-agent-challenge** |
| The plain-repo README | `README.md` in **case-agent** |
| The newsroom website | `docs/index.html` in **case-agent-for-newsrooms** |
| The newsroom guides | `docs/*.md` in **case-agent-for-newsrooms** |

## The rules (they're what prevent version hell)

1. **Never copy a file to work on it.** No "index-shelby.html", no downloaded copies,
   no save-as. Edit the file in place; git keeps every version.
2. **Edit on GitHub directly** (open the file → pencil icon → commit). GitHub will turn
   your edit into a pull request automatically — Evan reviews it like tracked changes
   and merges. `main` is protected, so nothing goes live without that review.
3. **One change per pull request round.** Finish a round, let it merge, start the next.

## For Evan (keeping the mirrors in sync after merges)

The skills content is mirrored into `case-agent` and `case-agent-for-newsrooms` by
`sync_plain_repo.sh` / `sync_newsroom_repo.sh` (in this repo). After merging content
PRs here, run the sync scripts against clones of the other two repos and push. After
merging a site PR, also copy `docs/index.html` back over the local staging copy
(`combined-submission/build/site/index.html`) before doing any script-driven site work,
or the merge will be overwritten by the next sync.
