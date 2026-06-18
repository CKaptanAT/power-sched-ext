"""Run the root helper via pkexec, asynchronously, from the GTK app."""

from __future__ import annotations

import json
import os
import sys

from gi.repository import Gio

HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "helper.py")


def run_helper(payload: dict, callback) -> None:
    """Run pkexec helper with *payload*; callback(ok: bool, message: str)."""
    argv = ["pkexec", sys.executable or "python3", HELPER, json.dumps(payload)]
    try:
        proc = Gio.Subprocess.new(
            argv,
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
        )
    except Exception as e:  # pkexec missing, etc.
        callback(False, str(e))
        return

    def done(p, result):
        try:
            _, stdout, stderr = p.communicate_utf8_finish(result)
        except Exception as e:
            callback(False, str(e))
            return
        if p.get_exit_status() == 0:
            callback(True, (stdout or "ok").strip())
        elif p.get_exit_status() in (126, 127):
            callback(False, "Authorization was cancelled")
        else:
            callback(False, (stderr or stdout or "helper failed").strip())

    proc.communicate_utf8_async(None, None, done)
