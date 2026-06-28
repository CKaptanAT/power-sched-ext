#!/usr/bin/env bash
# Build a PowerSched .rpm from this source tree.
#
#   ./packaging/build-rpm.sh
#
# Requires: rpm-build make libappstream-glib desktop-file-utils
#   sudo dnf install rpm-build rpmdevtools make libappstream-glib desktop-file-utils
# The finished .rpm is copied next to the project directory.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=0.1.0
NAME=powersched
TOP="$(mktemp -d)"
trap 'rm -rf "$TOP"' EXIT

mkdir -p "$TOP"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

# Stage a clean source tree as %{name}-%{version}/ and tar it up.
STAGE="$TOP/$NAME-$VERSION"
mkdir -p "$STAGE"
cp -r "$ROOT"/Makefile "$ROOT"/powersched "$ROOT"/data "$ROOT"/README.md \
      "$ROOT"/LICENSE "$ROOT"/powersched-run "$STAGE"/
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} +
( cd "$TOP" && tar czf "SOURCES/$NAME-$VERSION.tar.gz" "$NAME-$VERSION" )

cp "$ROOT/packaging/fedora/$NAME.spec" "$TOP/SPECS/"

echo "==> rpmbuild"
rpmbuild --define "_topdir $TOP" -ba "$TOP/SPECS/$NAME.spec"

OUT_DIR="$(dirname "$ROOT")"
find "$TOP/RPMS" -name '*.rpm' -exec cp {} "$OUT_DIR"/ \;
echo "==> Done. Package(s):"
ls -1 "$OUT_DIR"/$NAME-$VERSION*.rpm
echo "Install with:  sudo dnf install $OUT_DIR/$NAME-$VERSION-1.*.noarch.rpm"
