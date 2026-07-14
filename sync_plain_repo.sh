#!/bin/sh
# Populate the plain-repo edition (ewyloge-asu/case-agent) from this build folder —
# the same single source that feeds the website repo, so the two never drift.
# Usage:  sh sync_plain_repo.sh /path/to/case-agent-clone
set -e
DEST="${1:?usage: sh sync_plain_repo.sh /path/to/case-agent-clone}"
SRC="$(cd "$(dirname "$0")" && pwd)"

rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$SRC/menu/" "$DEST/menu/"
rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$SRC/mega/" "$DEST/mega/"
rsync -a --delete "$SRC/dist/" "$DEST/dist/"
rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' --exclude 'raw/' \
      "$SRC/submission/" "$DEST/submission/"
rsync -a --delete "$SRC/casefile/" "$DEST/casefile/"
cp "$SRC/validate_skills.py" "$SRC/assemble_mega.py" "$DEST/"
cp "$SRC/README_plain.md" "$DEST/README.md"
printf 'workdir/\ncredentials.env\n__pycache__/\n.DS_Store\n*.pyc\nsubmission/traces/raw/\n' > "$DEST/.gitignore"
echo "synced $SRC -> $DEST"
