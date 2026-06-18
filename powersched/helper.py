#!/usr/bin/env python3
"""Privileged helper for PowerSched. Invoked as root via pkexec:

    pkexec python3 helper.py '<json-payload>'

Payload examples:
    {"action": "cpu", "governor": "performance", "epp": "balance_performance",
     "min_khz": 800000, "max_khz": 4500000, "boost": true}
    {"action": "scx_start", "name": "scx_lavd", "args": ["--performance"]}
    {"action": "scx_stop"}

Inputs are validated against sysfs/whitelists before any write.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys

CPUFREQ = "/sys/devices/system/cpu"
PIDFILE = "/run/powersched-scx.pid"
SCX_DEFAULT = "/etc/default/scx"


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def write(path: str, value: str) -> None:
    with open(path, "w") as f:
        f.write(value)


def policy_dirs() -> list[str]:
    return sorted(glob.glob(f"{CPUFREQ}/cpu[0-9]*/cpufreq"))


# ---------------------------------------------------------------- CPU


def apply_cpu(p: dict) -> None:
    dirs = policy_dirs()
    if not dirs:
        fail("no cpufreq policies found")

    gov = p.get("governor")
    if gov is not None:
        allowed = (read(f"{dirs[0]}/scaling_available_governors") or "").split()
        if gov not in allowed:
            fail(f"governor {gov!r} not in {allowed}")
        for d in dirs:
            write(f"{d}/scaling_governor", gov)

    epp = p.get("epp")
    if epp is not None:
        allowed = (
            read(f"{dirs[0]}/energy_performance_available_preferences") or ""
        ).split()
        if epp not in allowed:
            fail(f"EPP {epp!r} not in {allowed}")
        for d in dirs:
            try:
                write(f"{d}/energy_performance_preference", epp)
            except OSError as e:
                print(f"warn: EPP on {d}: {e}", file=sys.stderr)

    for key, attr in (("min_khz", "scaling_min_freq"), ("max_khz", "scaling_max_freq")):
        v = p.get(key)
        if v is None:
            continue
        if not isinstance(v, int) or not (100_000 <= v <= 10_000_000):
            fail(f"{key} out of range: {v!r}")
        for d in dirs:
            try:
                write(f"{d}/{attr}", str(v))
            except OSError as e:
                print(f"warn: {attr} on {d}: {e}", file=sys.stderr)

    boost = p.get("boost")
    if boost is not None:
        no_turbo = f"{CPUFREQ}/intel_pstate/no_turbo"
        cpufreq_boost = f"{CPUFREQ}/cpufreq/boost"
        if os.path.exists(no_turbo):
            write(no_turbo, "0" if boost else "1")
        elif os.path.exists(cpufreq_boost):
            write(cpufreq_boost, "1" if boost else "0")
        else:
            print("warn: boost control not available", file=sys.stderr)

    print("ok")


# ---------------------------------------------------------------- scx


def _validate_sched(name: str) -> str:
    if not re.fullmatch(r"scx_[a-z0-9_\-]+", name):
        fail(f"invalid scheduler name: {name!r}")
    path = shutil.which(name)
    if not path:
        fail(f"scheduler binary not found: {name}")
    return path


def _validate_args(args: list) -> list[str]:
    out = []
    for a in args:
        if not isinstance(a, str) or not re.fullmatch(r"[A-Za-z0-9_\-=.,:%]+", a):
            fail(f"invalid argument: {a!r}")
        out.append(a)
    return out


def _systemctl(*args: str) -> int:
    return subprocess.call(["systemctl", *args])


def _scx_service_exists() -> bool:
    return shutil.which("systemctl") is not None and any(
        os.path.exists(p)
        for p in (
            "/usr/lib/systemd/system/scx.service",
            "/etc/systemd/system/scx.service",
            "/lib/systemd/system/scx.service",
        )
    )


def _kill_pidfile() -> None:
    pid = read(PIDFILE)
    if pid and pid.isdigit():
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
    try:
        os.unlink(PIDFILE)
    except OSError:
        pass


def scx_start(p: dict) -> None:
    name = p.get("name", "")
    path = _validate_sched(name)
    args = _validate_args(p.get("args", []))

    if _scx_service_exists():
        # Persist choice and let the distro service manage it (CachyOS-style)
        flags = " ".join(args)
        write(SCX_DEFAULT, f'SCX_SCHEDULER={name}\nSCX_FLAGS="{flags}"\n')
        if _systemctl("restart", "scx.service") != 0:
            fail("systemctl restart scx.service failed")
        print(f"ok: {name} via scx.service")
        return

    _kill_pidfile()  # stop a previously launched one first
    proc = subprocess.Popen(
        [path, *args],
        stdout=open("/var/log/powersched-scx.log", "ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    write(PIDFILE, str(proc.pid))
    print(f"ok: {name} started (pid {proc.pid})")


def scx_stop(_p: dict) -> None:
    stopped = False
    if _scx_service_exists():
        if _systemctl("stop", "scx.service") == 0:
            stopped = True
    if read(PIDFILE):
        _kill_pidfile()
        stopped = True
    if not stopped:
        # last resort: terminate any running scx_* scheduler
        subprocess.call(["pkill", "-TERM", "-f", r"^/?\S*scx_[a-z]"])
    print("ok: stopped")


# ---------------------------------------------------------------- main


def main() -> None:
    if os.geteuid() != 0:
        fail("must run as root (via pkexec)")
    if len(sys.argv) != 2:
        fail("expected exactly one JSON argument")
    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        fail(f"bad JSON: {e}")

    action = payload.get("action")
    if action == "cpu":
        apply_cpu(payload)
    elif action == "scx_start":
        scx_start(payload)
    elif action == "scx_stop":
        scx_stop(payload)
    else:
        fail(f"unknown action: {action!r}")


if __name__ == "__main__":
    main()
