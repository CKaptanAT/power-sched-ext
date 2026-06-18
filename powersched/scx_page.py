"""Scheduler page — sched_ext status, launch options, installed scx schedulers."""

from __future__ import annotations

import shlex

from gi.repository import Adw, GLib, Gtk

from . import scx_backend as scx
from .privileged import run_helper


class ScxPage(Adw.PreferencesPage):
    def __init__(self, toast_overlay: Adw.ToastOverlay):
        super().__init__(title="Scheduler", icon_name="emblem-system-symbolic")
        self.toasts = toast_overlay
        self.busy = False

        self._build_status_group()
        self._build_options_group()
        self._build_schedulers_group()

        GLib.timeout_add(2000, self._tick)
        self._tick()

    # ------------------------------------------------------------ groups

    def _build_status_group(self) -> None:
        g = Adw.PreferencesGroup(title="sched_ext Status")
        self.add(g)

        supported = scx.kernel_supported()
        row = Adw.ActionRow(
            title="Kernel support",
            subtitle="/sys/kernel/sched_ext"
            if supported
            else "This kernel was not built with sched_ext (CONFIG_SCHED_CLASS_EXT)",
        )
        icon = Gtk.Image.new_from_icon_name(
            "emblem-ok-symbolic" if supported else "dialog-warning-symbolic"
        )
        icon.add_css_class("success" if supported else "warning")
        row.add_suffix(icon)
        g.add(row)

        self.active_row = Adw.ActionRow(title="Active scheduler")
        self.active_label = Gtk.Label(css_classes=["title-4"])
        self.active_row.add_suffix(self.active_label)

        self.stop_btn = Gtk.Button(
            label="Stop",
            valign=Gtk.Align.CENTER,
            css_classes=["destructive-action"],
        )
        self.stop_btn.connect("clicked", self._on_stop)
        self.active_row.add_suffix(self.stop_btn)
        g.add(self.active_row)

        if scx.has_scx_service():
            g.set_description(
                "Schedulers are managed through the system scx.service"
            )

    def _build_options_group(self) -> None:
        g = Adw.PreferencesGroup(
            title="Launch Options",
            description="Used when starting a scheduler below",
        )
        self.add(g)

        names = list(scx.PROFILES)
        self.profile_row = Adw.ComboRow(
            title="Profile",
            subtitle="Preset flags per scheduler (like scx-manager modes)",
            model=Gtk.StringList.new(names),
        )
        g.add(self.profile_row)

        self.args_row = Adw.EntryRow(title="Extra flags (optional)")
        g.add(self.args_row)

    def _build_schedulers_group(self) -> None:
        g = Adw.PreferencesGroup(title="Installed Schedulers")
        self.add(g)

        scheds = scx.installed_schedulers()
        self.start_btns: dict[str, Gtk.Button] = {}
        self.sched_rows: dict[str, Adw.ActionRow] = {}

        if not scheds:
            g.set_description(
                "No scx_* schedulers found in PATH. Install your distro's "
                "scx package (e.g. 'scx-scheds')."
            )
            return

        for name in scheds:
            row = Adw.ActionRow(
                title=name,
                subtitle=scx.DESCRIPTIONS.get(name, "sched_ext scheduler"),
            )
            row.add_prefix(Gtk.Image.new_from_icon_name("application-x-executable-symbolic"))
            btn = Gtk.Button(label="Start", valign=Gtk.Align.CENTER)
            btn.add_css_class("suggested-action")
            btn.connect("clicked", self._on_start, name)
            row.add_suffix(btn)
            g.add(row)
            self.start_btns[name] = btn
            self.sched_rows[name] = row

    # ------------------------------------------------------------ logic

    def _profile_args(self, name: str) -> list[str]:
        item = self.profile_row.get_selected_item()
        profile = item.get_string() if item else "Default"
        args = list(scx.PROFILES.get(profile, {}).get(name, []))
        extra = self.args_row.get_text().strip()
        if extra:
            args += shlex.split(extra)
        return args

    def _on_start(self, _btn, name: str) -> None:
        if self.busy:
            return
        self.busy = True
        run_helper(
            {"action": "scx_start", "name": name, "args": self._profile_args(name)},
            lambda ok, msg: self._done(ok, f"{name} started" if ok else msg),
        )

    def _on_stop(self, _btn) -> None:
        if self.busy:
            return
        self.busy = True
        run_helper(
            {"action": "scx_stop"},
            lambda ok, msg: self._done(ok, "Scheduler stopped" if ok else msg),
        )

    def _done(self, ok: bool, msg: str) -> None:
        self.busy = False
        self._toast(msg if ok else f"Failed: {msg}")
        GLib.timeout_add(800, lambda: (self._tick() and False))

    def _tick(self) -> bool:
        active = scx.active_scheduler()
        if active:
            self.active_label.set_label(active)
            self.active_label.remove_css_class("dim-label")
            self.active_label.add_css_class("accent")
            self.stop_btn.set_visible(True)
        else:
            self.active_label.set_label("none (default EEVDF)")
            self.active_label.add_css_class("dim-label")
            self.active_label.remove_css_class("accent")
            self.stop_btn.set_visible(False)

        for name, row in self.sched_rows.items():
            running = name == active
            btn = self.start_btns[name]
            btn.set_label("Running" if running else "Start")
            btn.set_sensitive(not running)
            if running:
                row.add_css_class("accent")
            else:
                row.remove_css_class("accent")
        return True

    def _toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))
