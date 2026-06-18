#!/usr/bin/env bash
# Remove PowerSched (keeps GUI dependencies and scx schedulers).
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo: sudo ./uninstall.sh"
    exit 1
fi
rm -rf /opt/powersched
rm -f /usr/local/bin/powersched
rm -f /usr/share/applications/io.github.powersched.PowerSched.desktop
rm -f /usr/share/polkit-1/actions/io.github.powersched.policy
command -v update-desktop-database >/dev/null \
    && update-desktop-database /usr/share/applications || true
echo "PowerSched removed."
