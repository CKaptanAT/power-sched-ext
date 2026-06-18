"""PowerSched application entry point."""

from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio  # noqa: E402

from . import APP_ID, __version__  # noqa: E402
from .window import PowerSchedWindow  # noqa: E402


class PowerSchedApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        about = Gio.SimpleAction.new("about", None)
        about.connect("activate", self._about)
        self.add_action(about)

    def do_activate(self):
        win = self.props.active_window or PowerSchedWindow(application=self)
        win.present()

    def _about(self, *_):
        dlg = Adw.AboutDialog(
            application_name="PowerSched",
            application_icon="power-profile-performance-symbolic",
            version=__version__,
            developer_name="Cengizhan",
            comments=(
                "CPU frequency scaling and sched_ext scheduler control "
                "in one place. Inspired by cpupower-gui and scx-manager."
            ),
        )
        dlg.present(self.props.active_window)


def main() -> int:
    app = PowerSchedApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
