#!/bin/sh
# Populate the newsroom edition (ewyloge-asu/case-agent-for-newsrooms) from this build
# folder — same single source as the website and plain-repo editions.
# The newsroom edition is THE TOOL ONLY: skills, newsroom docs, demo data, and its own
# site. No submission materials (findings, traces, legal checks, case files).
# Usage:  sh sync_newsroom_repo.sh /path/to/case-agent-for-newsrooms-clone
set -e
DEST="${1:?usage: sh sync_newsroom_repo.sh /path/to/clone}"
SRC="$(cd "$(dirname "$0")" && pwd)"

# skills + shared setup at root (mirrors the menu bundle's internal layout)
rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$SRC/menu/skills/" "$DEST/skills/"
cp "$SRC/menu/setup_keys.py" "$SRC/menu/credentials.env.example" "$SRC/menu/data-setup.md" "$DEST/"
rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$SRC/mega/" "$DEST/mega/"

# newsroom-facing README + guides + website (Pages serves docs/index.html;
# the markdown guides live alongside it in docs/)
cp "$SRC/newsroom/README.md" "$DEST/README.md"
mkdir -p "$DEST/docs"
cp "$SRC"/newsroom/docs/*.md "$DEST/docs/"
cp "$SRC/newsroom/site/index.html" "$DEST/docs/index.html"

# no examples/, no submission/ — this edition carries no competition artifacts
rm -rf "$DEST/examples" "$DEST/submission"

printf 'workdir/\ncredentials.env\n__pycache__/\n.DS_Store\n*.pyc\n' > "$DEST/.gitignore"
echo "synced $SRC -> $DEST (newsroom edition, tool only)"
