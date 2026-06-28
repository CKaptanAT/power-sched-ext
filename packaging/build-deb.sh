#!/usr/bin/env bash
# Build a PowerSched .deb from this source tree.
#
#   ./packaging/build-deb.sh
#
# Requires: dpkg-dev debhelper  (sudo apt install dpkg-dev debhelper)
# The finished .deb is written next to the project directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

SRC="$STAGE/powersched-0.1.0"
mkdir -p "$SRC"

# Copy the source tree (excluding VCS, caches and packaging metadata for
# other distros) into the staging dir, then drop debian/ at its root.
cp -r "$ROOT"/Makefile "$ROOT"/powersched "$ROOT"/data "$ROOT"/README.md \
      "$ROOT"/LICENSE "$ROOT"/powersched-run "$SRC"/
cp -r "$ROOT"/packaging/debian "$SRC"/debian
find "$SRC" -name '__pycache__' -type d -prune -exec rm -rf {} +

echo "==> Building .deb in $SRC"
( cd "$SRC" && dpkg-buildpackage -b -us -uc )

OUT_DIR="$(dirname "$ROOT")"
cp "$STAGE"/powersched_*.deb "$OUT_DIR"/
echo "==> Done. Package(s):"
ls -1 "$OUT_DIR"/powersched_*.deb
echo "Install with:  sudo apt install $OUT_DIR/powersched_0.1.0_all.deb"
