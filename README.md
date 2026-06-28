# PowerSched

A single GTK4/libadwaita app that combines what **cpupower-gui** and
**scx-manager** do — CPU power management and `sched_ext` (scx) scheduler
control in one window.

![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)
![Platform](https://img.shields.io/badge/platform-Linux-informational)
![Python](https://img.shields.io/badge/python-3.10%2B-green)

- **CPU Power page** — scaling governor, energy/performance preference (EPP),
  min/max frequency limits, turbo boost, plus a live per-core frequency monitor.
- **Scheduler page** — detects `sched_ext` kernel support, lists installed
  `scx_*` schedulers with descriptions, shows the active one, and starts/stops
  them with profile presets (Gaming, Low Latency, Power Save, Server).

Privileged changes use a small root helper invoked through **pkexec** (polkit
prompt). On systems with `scx.service` (e.g. CachyOS), scheduler choices are
written to `/etc/default/scx` and managed via systemd so they survive the app
closing; otherwise the scheduler is launched directly in the background.

> The scx schedulers themselves (`scx_rusty`, `scx_lavd`, `scx_bpfland`,
> `scx_flash`, …) are the Rust `sched_ext` schedulers from the
> [sched-ext/scx](https://github.com/sched-ext/scx) project. PowerSched
> detects, describes, and drives them — it does not bundle them.

---

## Installation

Pick the row for your distribution. All methods install the same files to
standard FHS locations (`/usr/lib/powersched`, `/usr/bin/powersched`, a menu
entry, and the polkit policy).

| Distro | Recommended method |
| --- | --- |
| **Arch / CachyOS / Manjaro** | build the bundled PKGBUILD with `makepkg` |
| **Debian / Ubuntu** | build & install a `.deb` |
| **Fedora** | build & install an `.rpm` (or COPR) |
| **Any distro** | `sudo ./install.sh` (portable fallback) |

### Arch / CachyOS / Manjaro

Build and install from the bundled PKGBUILD (clone the repo first):

```bash
git clone https://github.com/CKaptanAT/power-sched-ext.git
cd power-sched-ext/packaging/aur
makepkg -si
```

`makepkg` pulls in the build/runtime dependencies and installs the package with
pacman, so removal is clean (`sudo pacman -R powersched-git`).

Scheduler support: `sudo pacman -S scx-scheds` (the package recommends it as an
optional dependency).

> An AUR package (`powersched-git`) is planned so this becomes
> `yay -S powersched-git`. The PKGBUILD is already AUR-ready — see
> [Building packages](#building-packages).

### Debian / Ubuntu

Build a `.deb` from the source tree and install it:

```bash
sudo apt install dpkg-dev debhelper        # one-time build tooling
./packaging/build-deb.sh                    # produces ../powersched_0.1.0_all.deb
sudo apt install ../powersched_0.1.0_all.deb
```

`apt` pulls in the runtime dependencies (`python3-gi`, `gir1.2-gtk-4.0`,
`gir1.2-adw-1`, polkit) automatically. Scheduler support needs a
`sched_ext`-capable kernel (Ubuntu 25.04+ / 6.12+) and scx schedulers — see
[Schedulers](#schedulers).

### Fedora

Build an `.rpm` from the source tree:

```bash
sudo dnf install rpm-build rpmdevtools make libappstream-glib desktop-file-utils
./packaging/build-rpm.sh                    # produces ../powersched-0.1.0-1.*.noarch.rpm
sudo dnf install ../powersched-0.1.0-1.*.noarch.rpm
```

The spec (`packaging/fedora/powersched.spec`) is COPR-ready: point a COPR
build at it with a `powersched-0.1.0.tar.gz` source tarball, then users install
with `dnf copr enable <you>/powersched && dnf install powersched`. Scheduler
support: `sudo dnf copr enable bieszczaders/kernel-cachyos-addons && sudo dnf
install scx-scheds`.

### Any distro — portable installer

```bash
sudo ./install.sh              # app + GUI deps + menu entry for all users
sudo ./install.sh --with-scx   # also install scx schedulers if missing
sudo ./install.sh --no-deps    # skip distro package installation
```

`install.sh` installs the GUI runtime dependencies for apt/pacman/dnf/zypper,
then runs `make install`. `--with-scx` installs schedulers from your distro's
package where one exists, or builds the Rust schedulers from
[sched-ext/scx](https://github.com/sched-ext/scx) on Ubuntu (several minutes).

Remove everything with `sudo ./uninstall.sh`.

### Run without installing

```bash
./powersched-run
```

---

## Requirements

- Linux with cpufreq (`/sys/devices/system/cpu/.../cpufreq`)
- Python 3.10+, GTK 4, libadwaita ≥ 1.4, PyGObject, polkit (`pkexec`)
- For the Scheduler page: a `sched_ext`-enabled kernel (6.12+) and scx schedulers

GUI dependencies, if you are installing them by hand:

- Arch/CachyOS: `sudo pacman -S python-gobject gtk4 libadwaita polkit`
- Fedora: `sudo dnf install python3-gobject gtk4 libadwaita polkit`
- Ubuntu 24.04+: `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 policykit-1`

### Schedulers

The Scheduler page needs a `sched_ext`-enabled kernel and one or more `scx_*`
schedulers on `PATH`:

- Arch/CachyOS: `sudo pacman -S scx-scheds`
- Fedora: `sudo dnf copr enable bieszczaders/kernel-cachyos-addons && sudo dnf install scx-scheds`
- openSUSE: `sudo zypper install scx`
- Ubuntu / others: build from [sched-ext/scx](https://github.com/sched-ext/scx),
  or run `sudo ./install.sh --with-scx`

---

## Building packages

All three packages reuse the same `make install` target, so the install layout
is identical no matter how you install.

| Path | Purpose |
| --- | --- |
| `Makefile` | `make install PREFIX=/usr DESTDIR=…` — single source of truth |
| `packaging/aur/PKGBUILD` + `.SRCINFO` | Arch AUR package (`powersched-git`) |
| `packaging/debian/` | Debian source package (debhelper 13) |
| `packaging/fedora/powersched.spec` | RPM spec (Fedora / COPR) |
| `packaging/build-deb.sh` | one-shot `.deb` build |
| `packaging/build-rpm.sh` | one-shot `.rpm` build |

To publish to the AUR (once you have an AUR account — registration is sometimes
temporarily closed), push `packaging/aur/PKGBUILD` and a regenerated `.SRCINFO`
(`makepkg --printsrcinfo > .SRCINFO`) to the AUR git repo `powersched-git` over
SSH. Until then, Arch users build the PKGBUILD locally as shown above. After
tagging an upstream release you can switch from the `-git` build to a versioned
tarball source.

---

## Layout

```
.
├── Makefile                # install/uninstall (used by all packages)
├── install.sh              # portable installer (deps + make install)
├── uninstall.sh
├── powersched-run          # run from the source tree
├── powersched/
│   ├── main.py             # Adw.Application
│   ├── window.py           # window + view switcher
│   ├── cpu_page.py         # CPU Power UI
│   ├── scx_page.py         # Scheduler UI
│   ├── cpu_backend.py      # sysfs reads
│   ├── scx_backend.py      # scheduler detection, profiles
│   ├── privileged.py       # async pkexec runner
│   └── helper.py           # root helper (validated writes)
├── data/                   # .desktop, polkit policy, AppStream metainfo
└── packaging/              # aur/, debian/, fedora/ + build scripts
```

Profile flags live in `scx_backend.py` (`PROFILES`) — edit to taste; scheduler
flags vary between scx versions.

---

## Notes

- CPU settings revert on reboot (same as cpupower-gui without its service).
- "Active scheduler" is read from `/sys/kernel/sched_ext/root/ops`.
- The root helper validates every input (governor/EPP whitelists from sysfs,
  scheduler name pattern + PATH lookup, frequency bounds) before writing.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
