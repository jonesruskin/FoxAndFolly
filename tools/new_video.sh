#!/usr/bin/env bash
# Scaffold a new episode:  tools/new_video.sh 003 the-strip-bark-pine
set -euo pipefail
num="$1"; slug="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/videos/${num}-${slug}"
[ -e "$dest" ] && { echo "exists: $dest"; exit 1; }
cp -r "$root/templates/video" "$dest"
mkdir -p "$dest/output" "$dest/build"
sed -i "s/NNN/${num}/g; s/slug/${slug}/g" "$dest/CLAUDE.md"
echo "created $dest"
echo "tip: copy build.py, src/render.py and src/music.py from the latest episode as a starting point."
