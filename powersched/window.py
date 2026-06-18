"""Main window — view switcher between CPU Power and Scheduler pages."""

from __future__ import annotations

from gi.repository import Adw, Gtk

from .cpu_page import CpuPage
from .scx_page import ScxPage


class PowerSchedWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("PowerSched")
        self.set_default_size(720, 760)

        self.toasts = Adw.ToastOverlay()

        stack = Adw.ViewStack()
        stack.add_titled_with_icon(
            CpuPage(self.toasts), "cpu", "CPU Power",
            "power-profile-performance-symbolic",
        )
        stack.add_titled_with_icon(
            ScxPage(self.toasts), "scx", "Scheduler", "emblem-system-symbolic"
        )

        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(
            stack=stack, policy=Adw.ViewSwitcherPolicy.WIDE
        )
        header.set_title_widget(switcher)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_btn.set_menu_model(self._menu())
        header.pack_end(menu_btn)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(stack)

        bottom = Adw.ViewSwitcherBar(stack=stack)
        breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 550sp")
        )
        breakpoint.add_setter(bottom, "reveal", True)
        breakpoint.add_setter(header, "title-widget", None)
        self.add_breakpoint(breakpoint)
        toolbar.add_bottom_bar(bottom)

        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)

    @staticmethod
    def _menu():
        from gi.repository import Gio

        menu = Gio.Menu()
        menu.append("About PowerSched", "app.about")
        return menu
