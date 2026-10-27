#!/usr/bin/env bash
# Adds a new lab's files to your repo without touching your existing work.
# Run from your Codespace terminal:
#   curl -fsSL https://raw.githubusercontent.com/esbee1/data-infra-ai-course/main/get_lab.sh | bash -s 2
set -euo pipefail
LAB="${1:-}"
BASE="${COURSE_BASE:-https://raw.githubusercontent.com/esbee1/data-infra-ai-course/main}"

case "$LAB" in
  2) FILES="notebooks/lab2_joins.ipynb data/species_lookup.csv labs/lab2.md" ;;
  *) echo "Usage: ... | bash -s <lab number>   (available: 2)"; exit 1 ;;
esac

if [ ! -d data ] || [ ! -d notebooks ]; then
  echo "Run this from the top folder of your course repo (the one with data/ and notebooks/)."
  exit 1
fi

for f in $FILES; do
  if [ -e "$f" ]; then
    echo "  already have  $f  (left unchanged)"
  else
    mkdir -p "$(dirname "$f")"
    curl -fsSL "$BASE/$f" -o "$f"
    echo "  added         $f"
  fi
done
echo "Lab $LAB files are ready. Open notebooks/ in the file list on the left."
