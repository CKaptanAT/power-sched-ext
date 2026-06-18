# PowerSched

One GTK4/libadwaita app that combines what **cpupower-gui** and **scx-manager** do:

- **CPU Power page** — scaling governor, energy/performance preference (EPP), min/max frequency limits, turbo boost, plus a live per-core frequency monitor.
- **Scheduler page** — detects sched_ext kernel support, lists installed `scx_*` schedulers with descriptions, shows the active one, and starts/stops them with profile presets (Gaming, Low Latency, Power Save, Server).

Privileged changes use a small root helper invoked through **pkexec** (polkit prompt). On systems with `scx.service` (e.g. CachyOS), scheduler choices are written to `/etc/default/scx` and managed via systemd so they survive the app closing; otherwise the scheduler is launched directly in the background.

## Requirements

- Linux with cpufreq (`/sys/devices/system/cpu/.../cpufreq`)
- Python 3.10+, GTK 4, libadwaita ≥ 1.4, PyGObject, polkit (`pkexec`)
- For the Scheduler page: a sched_ext-enabled kernel (6.12+) and scx schedulers
  - Arch/CachyOS: `sudo pacman -S scx-scheds`
  - Other distros: see https://github.com/sched-ext/scx

Install GUI deps:

- Arch/CachyOS: `sudo pacman -S python-gobject gtk4 libadwaita polkit`
- Fedora: `sudo dnf install python3-gobject gtk4 libadwaita polkit`
- Ubuntu 24.04+: `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 policykit-1`

## Install (recommended)

```bash
sudo ./install.sh              # app + GUI deps + menu entry for all users
sudo ./install.sh --with-scx   # also install scx schedulers if missing
```

The installer puts the app in `/opt/powersched`, a `powersched` command in
`/usr/local/bin`, a menu entry in `/usr/share/applications` (visible to every
user), and the polkit policy. `--with-scx` installs schedulers from your
distro's package (Arch/Fedora/openSUSE) or builds the Rust schedulers
(`scx_rusty`, `scx_lavd`, `scx_bpfland`, `scx_flash`) from
https://github.com/sched-ext/scx on Ubuntu — that build takes several minutes.

Remove everything with `sudo ./uninstall.sh`.

## Run without installing

```bash
./powersched-run
```

## Layout

```
powersched/
├── powersched-run          # launcher
├── powersched/
│   ├── main.py             # Adw.Application
│   ├── window.py           # window + view switcher
│   ├── cpu_page.py         # CPU Power UI
│   ├── scx_page.py         # Scheduler UI
│   ├── cpu_backend.py      # sysfs reads
│   ├── scx_backend.py      # scheduler detection, profiles
│   ├── privileged.py       # async pkexec runner
│   └── helper.py           # root helper (validated writes)
└── data/                   # .desktop + polkit policy
```

Profile flags live in `scx_backend.py` (`PROFILES`) — edit to taste; scheduler flags vary between scx versions.

## Notes

- CPU settings revert on reboot (same as cpupower-gui without its service).
- "Active scheduler" is read from `/sys/kernel/sched_ext/root/ops`.
- Helper validates every input (governor/EPP whitelists from sysfs, scheduler name pattern + PATH lookup, frequency bounds) before writing.
