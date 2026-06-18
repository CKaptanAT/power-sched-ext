"""Detect sched_ext support, installed scx schedulers, and the active one.

Starting/stopping schedulers is done by helper.py (root via pkexec).
"""

from __future__ import annotations

import os
import shutil

SCHED_EXT = "/sys/kernel/sched_ext"

DESCRIPTIONS = {
    "scx_bpfland": "Interactive workloads — prioritizes tasks that yield often (gaming, desktop)",
    "scx_lavd": "Latency-criticality aware — great for gaming and low-latency desktop use",
    "scx_rusty": "General purpose multi-domain scheduler, solid default for most systems",
    "scx_flash": "EDF-based, predictable latency — audio/real-time-ish workloads",
    "scx_rustland": "Userspace scheduling playground — experimental",
    "scx_simple": "Minimal example scheduler — single-socket systems",
    "scx_nest": "Keeps tasks on warm cores — favors high frequency over spreading",
    "scx_layered": "Highly configurable multi-layer scheduler",
    "scx_central": "Central dispatch from one CPU — VM / low-jitter setups",
    "scx_flatcg": "Flattened cgroup hierarchy — container-heavy workloads",
    "scx_qmap": "Simple five-level priority queue demo",
    "scx_userland": "Fully userspace scheduler — experimental",
    "scx_p2dq": "Pick-two load balancing with per-LLC queues",
    "scx_tickless": "Reduces timer ticks — server / HPC experimentation",
}

# Profile -> per-scheduler extra flags (mirrors scx_loader modes)
PROFILES = {
    "Default": {},
    "Gaming / Performance": {
        "scx_bpfland": ["-m", "performance"],
        "scx_lavd": ["--performance"],
        "scx_flash": ["-m", "performance"],
        "scx_p2dq": [],
        "scx_rusty": [],
    },
    "Low Latency": {
        "scx_bpfland": ["-s", "5000", "-S", "500", "-l", "5000"],
        "scx_lavd": ["--performance"],
        "scx_flash": ["-m", "all"],
    },
    "Power Save": {
        "scx_bpfland": ["-m", "powersave"],
        "scx_lavd": ["--powersave"],
        "scx_flash": ["-m", "powersave"],
    },
    "Server": {
        "scx_bpfland": ["-c", "0"],
        "scx_lavd": ["--no-preemption"],
    },
}


def kernel_supported() -> bool:
    return os.path.isdir(SCHED_EXT)


def _read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def state() -> str:
    return _read(f"{SCHED_EXT}/state") or "unknown"


def active_scheduler() -> str | None:
    """Name of the running sched_ext scheduler, or None."""
    if state() != "enabled":
        return None
    ops = _read(f"{SCHED_EXT}/root/ops")
    if not ops:
        return None
    return ops if ops.startswith("scx_") else f"scx_{ops}"


def installed_schedulers() -> list[str]:
    found = set()
    for name in DESCRIPTIONS:
        if shutil.which(name):
            found.add(name)
    # also scan PATH for anything scx_* we don't know about
    for d in os.environ.get("PATH", "/usr/bin:/usr/local/bin").split(":"):
        try:
            for f in os.listdir(d):
                if f.startswith("scx_") and os.access(os.path.join(d, f), os.X_OK):
                    if f not in ("scx_loader",):
                        found.add(f)
        except OSError:
            pass
    return sorted(found)


def has_scx_service() -> bool:
    return any(
        os.path.exists(p)
        for p in (
            "/usr/lib/systemd/system/scx.service",
            "/etc/systemd/system/scx.service",
            "/lib/systemd/system/scx.service",
        )
    )
