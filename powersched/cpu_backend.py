"""Read-only CPU frequency / cpufreq information from sysfs.

All writes go through helper.py (run as root via pkexec).
"""

from __future__ import annotations

import glob
import os
import re

CPUFREQ = "/sys/devices/system/cpu"


def _read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def cpu_model() -> str:
    txt = _read("/proc/cpuinfo") or ""
    m = re.search(r"^model name\s*:\s*(.+)$", txt, re.M)
    return m.group(1) if m else "Unknown CPU"


def online_cpus() -> list[int]:
    cpus = []
    for d in glob.glob(f"{CPUFREQ}/cpu[0-9]*"):
        m = re.match(r".*/cpu(\d+)$", d)
        if not m:
            continue
        n = int(m.group(1))
        online = _read(f"{d}/online")
        if online is None or online == "1":
            if os.path.isdir(f"{d}/cpufreq"):
                cpus.append(n)
    return sorted(cpus)


def _cpu0(attr: str) -> str | None:
    return _read(f"{CPUFREQ}/cpu0/cpufreq/{attr}")


def driver() -> str:
    return _cpu0("scaling_driver") or "unknown"


def available_governors() -> list[str]:
    v = _cpu0("scaling_available_governors")
    return v.split() if v else []


def current_governor() -> str | None:
    return _cpu0("scaling_governor")


def available_epp() -> list[str]:
    v = _cpu0("energy_performance_available_preferences")
    return v.split() if v else []


def current_epp() -> str | None:
    return _cpu0("energy_performance_preference")


def hw_freq_limits_khz() -> tuple[int, int]:
    lo = _cpu0("cpuinfo_min_freq")
    hi = _cpu0("cpuinfo_max_freq")
    return (int(lo) if lo else 0, int(hi) if hi else 0)


def scaling_limits_khz() -> tuple[int, int]:
    lo = _cpu0("scaling_min_freq")
    hi = _cpu0("scaling_max_freq")
    return (int(lo) if lo else 0, int(hi) if hi else 0)


def current_freqs_khz() -> dict[int, int]:
    out = {}
    for n in online_cpus():
        v = _read(f"{CPUFREQ}/cpu{n}/cpufreq/scaling_cur_freq")
        if v:
            out[n] = int(v)
    return out


def boost_supported() -> bool:
    return (
        os.path.exists(f"{CPUFREQ}/intel_pstate/no_turbo")
        or os.path.exists(f"{CPUFREQ}/cpufreq/boost")
    )


def boost_enabled() -> bool | None:
    v = _read(f"{CPUFREQ}/intel_pstate/no_turbo")
    if v is not None:
        return v == "0"
    v = _read(f"{CPUFREQ}/cpufreq/boost")
    if v is not None:
        return v == "1"
    return None
