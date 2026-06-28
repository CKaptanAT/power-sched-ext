#!/usr/bin/env bash
# Remove PowerSched (keeps GUI dependencies and scx schedulers).
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo: sudo ./uninstall.sh"
    exit 1
fi
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SRC_DIR/Makefile" ]; then
    make -C "$SRC_DIR" uninstall PREFIX=/usr
else
    rm -rf /usr/lib/powersched
    rm -f  /usr/bin/powersched
    rm -f  /usr/share/applications/io.github.powersched.PowerSched.desktop
    rm -f  /usr/share/polkit-1/actions/io.github.powersched.policy
    rm -f  /usr/share/metainfo/io.github.powersched.metainfo.xml
    rm -rf /usr/share/doc/powersched
fi

# Also clean up any legacy 0.x layout (/opt + /usr/local/bin).
rm -rf /opt/powersched
rm -f  /usr/local/bin/powersched

command -v update-desktop-database >/dev/null \
    && update-desktop-database /usr/share/applications || true
echo "PowerSched removed."
