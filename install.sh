#!/usr/bin/env bash
# PowerSched system-wide installer.
#
#   sudo ./install.sh              # install app + GUI dependencies + menu entry
#   sudo ./install.sh --with-scx   # also install scx schedulers if missing
#   sudo ./install.sh --no-deps    # skip package installation
#
# Installs (via the Makefile, PREFIX=/usr) to:
#   /usr/lib/powersched                      (application)
#   /usr/bin/powersched                      (launcher)
#   /usr/share/applications/...desktop       (menu entry, all users)
#   /usr/share/polkit-1/actions/...policy    (polkit prompt)
#   /usr/share/metainfo/...metainfo.xml      (AppStream metadata)
#
# Prefer a native package where available (see packaging/). This script is the
# portable fallback and also installs runtime dependencies for you.

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WITH_SCX=0
NO_DEPS=0
for a in "$@"; do
    case "$a" in
        --with-scx) WITH_SCX=1 ;;
        --no-deps)  NO_DEPS=1 ;;
        *) echo "unknown option: $a"; exit 1 ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo: sudo ./install.sh"
    exit 1
fi
# The user who invoked sudo (for cargo builds)
REAL_USER="${SUDO_USER:-root}"

msg()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*"; }

# ---------------------------------------------------------------- detect distro

PKG=""
command -v apt-get >/dev/null && PKG=apt
command -v pacman  >/dev/null && PKG=pacman
command -v dnf     >/dev/null && PKG=dnf
command -v zypper  >/dev/null && PKG=zypper

# ---------------------------------------------------------------- 1. GUI deps

if [ "$NO_DEPS" -eq 0 ]; then
    msg "Installing GUI dependencies ($PKG)..."
    case "$PKG" in
        apt)
            apt-get update -qq
            apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
                policykit-1 2>/dev/null \
            || apt-get install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
                polkitd pkexec
            ;;
        pacman)
            pacman -S --needed --noconfirm python-gobject gtk4 libadwaita polkit
            ;;
        dnf)
            dnf install -y python3-gobject gtk4 libadwaita polkit
            ;;
        zypper)
            zypper install -y python3-gobject typelib-1_0-Gtk-4_0 \
                typelib-1_0-Adw-1 polkit
            ;;
        *)
            warn "Unknown package manager — install GTK4/libadwaita/PyGObject/polkit manually."
            ;;
    esac
fi

# ---------------------------------------------------------------- 2. app files

msg "Installing application (make install, PREFIX=/usr) ..."
make -C "$SRC_DIR" install PREFIX=/usr

command -v update-desktop-database >/dev/null \
    && update-desktop-database /usr/share/applications || true

# ---------------------------------------------------------------- 3. scx schedulers

have_scx() { compgen -c | grep -q '^scx_' 2>/dev/null; }

install_scx_from_source() {
    msg "Building scx schedulers from source (this takes a while)..."
    case "$PKG" in
        apt)
            apt-get install -y build-essential cmake cargo rustc clang llvm \
                pkg-config libelf-dev protobuf-compiler libseccomp-dev \
                libbpf-dev pahole git
            ;;
        dnf)
            dnf install -y cargo rust clang llvm elfutils-libelf-devel \
                protobuf-compiler libseccomp-devel libbpf-devel dwarves git make
            ;;
        *)
            warn "Install rust/clang/libbpf dev packages manually, then re-run."
            return 1
            ;;
    esac

    local build=/tmp/powersched-scx-build
    rm -rf "$build"
    sudo -u "$REAL_USER" git clone --depth 1 \
        https://github.com/sched-ext/scx.git "$build"

    # Build the most useful Rust schedulers (add more with -p scx_<name>)
    sudo -u "$REAL_USER" bash -c \
        "cd '$build' && cargo build --release -p scx_rusty -p scx_lavd -p scx_bpfland -p scx_flash"

    install -m 755 "$build"/target/release/scx_{rusty,lavd,bpfland,flash} /usr/local/bin/
    rm -rf "$build"
    msg "Installed: scx_rusty scx_lavd scx_bpfland scx_flash -> /usr/local/bin"
}

if [ "$WITH_SCX" -eq 1 ]; then
    if have_scx; then
        msg "scx schedulers already installed — skipping."
    else
        case "$PKG" in
            pacman) pacman -S --needed --noconfirm scx-scheds ;;
            zypper) zypper install -y scx ;;
            dnf)
                dnf copr enable -y bieszczaders/kernel-cachyos-addons \
                    && dnf install -y scx-scheds \
                    || install_scx_from_source
                ;;
            apt)
                # No package in the Ubuntu archive — build from source
                install_scx_from_source
                ;;
            *) install_scx_from_source ;;
        esac
    fi

    if [ ! -d /sys/kernel/sched_ext ]; then
        warn "Your running kernel has no sched_ext support."
        warn "Ubuntu 25.04+ generic kernels (6.12+) support it — reboot into a recent kernel."
    fi
fi

# ---------------------------------------------------------------- done

echo
msg "Done! Launch 'PowerSched' from the application menu, or run: powersched"
[ "$WITH_SCX" -eq 0 ] && ! have_scx \
    && echo "    (no scx schedulers found — re-run with: sudo ./install.sh --with-scx)"
exit 0
