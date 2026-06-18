"""CPU Power page — governor, EPP, frequency limits, boost, live core monitor."""

from __future__ import annotations

from gi.repository import Adw, GLib, Gtk

from . import cpu_backend as cpu
from .privileged import run_helper


def _mhz(khz: int) -> str:
    return f"{khz / 1000:.0f} MHz"


class CpuPage(Adw.PreferencesPage):
    def __init__(self, toast_overlay: Adw.ToastOverlay):
        super().__init__(
            title="CPU Power", icon_name="power-profile-performance-symbolic"
        )
        self.toasts = toast_overlay
        self.hw_min, self.hw_max = cpu.hw_freq_limits_khz()

        self._build_info_group()
        self._build_tuning_group()
        self._build_limits_group()
        self._build_apply_group()
        self._build_cores_group()

        GLib.timeout_add(1500, self._tick)

    # ------------------------------------------------------------ groups

    def _build_info_group(self) -> None:
        g = Adw.PreferencesGroup(title="System")
        self.add(g)

        row = Adw.ActionRow(title=cpu.cpu_model())
        row.set_subtitle(
            f"{len(cpu.online_cpus())} threads · driver: {cpu.driver()}"
        )
        row.add_prefix(Gtk.Image.new_from_icon_name("computer-symbolic"))
        self.avg_label = Gtk.Label(css_classes=["title-3", "accent"])
        row.add_suffix(self.avg_label)
        g.add(row)

    def _build_tuning_group(self) -> None:
        g = Adw.PreferencesGroup(
            title="Performance Tuning",
            description="Applied to all cores when you press Apply",
        )
        self.add(g)

        govs = cpu.available_governors()
        self.gov_row = Adw.ComboRow(
            title="Scaling governor",
            subtitle="How aggressively the CPU scales frequency",
            model=Gtk.StringList.new(govs),
        )
        cur = cpu.current_governor()
        if cur in govs:
            self.gov_row.set_selected(govs.index(cur))
        g.add(self.gov_row)

        epps = cpu.available_epp()
        self.epp_row = None
        if epps:
            self.epp_row = Adw.ComboRow(
                title="Energy / performance preference",
                subtitle="Hint to the hardware (EPP)",
                model=Gtk.StringList.new(epps),
            )
            cur = cpu.current_epp()
            if cur in epps:
                self.epp_row.set_selected(epps.index(cur))
            g.add(self.epp_row)

        self.boost_row = None
        if cpu.boost_supported():
            self.boost_row = Adw.SwitchRow(
                title="Turbo boost",
                subtitle="Allow cores to exceed base frequency",
            )
            self.boost_row.set_active(bool(cpu.boost_enabled()))
            g.add(self.boost_row)

    def _build_limits_group(self) -> None:
        g = Adw.PreferencesGroup(
            title="Frequency Limits",
            description=f"Hardware range: {_mhz(self.hw_min)} – {_mhz(self.hw_max)}",
        )
        self.add(g)

        cur_min, cur_max = cpu.scaling_limits_khz()
        lo, hi = self.hw_min // 1000, self.hw_max // 1000

        self.min_row = Adw.SpinRow(
            title="Minimum frequency",
            subtitle="MHz",
            adjustment=Gtk.Adjustment(
                lower=lo, upper=hi, step_increment=100, page_increment=500,
                value=cur_min // 1000,
            ),
        )
        self.max_row = Adw.SpinRow(
            title="Maximum frequency",
            subtitle="MHz",
            adjustment=Gtk.Adjustment(
                lower=lo, upper=hi, step_increment=100, page_increment=500,
                value=cur_max // 1000,
            ),
        )
        g.add(self.min_row)
        g.add(self.max_row)

    def _build_apply_group(self) -> None:
        g = Adw.PreferencesGroup()
        self.add(g)
        btn = Gtk.Button(
            label="Apply CPU Settings",
            halign=Gtk.Align.CENTER,
            css_classes=["suggested-action", "pill"],
        )
        btn.connect("clicked", self._on_apply)
        g.add(btn)

    def _build_cores_group(self) -> None:
        g = Adw.PreferencesGroup(title="Live Core Frequencies")
        self.add(g)
        self.core_rows: dict[int, tuple[Gtk.Label, Gtk.LevelBar]] = {}
        for n in cpu.online_cpus():
            row = Adw.ActionRow(title=f"Core {n}")
            bar = Gtk.LevelBar(
                min_value=self.hw_min or 0,
                max_value=self.hw_max or 1,
                valign=Gtk.Align.CENTER,
                hexpand=True,
            )
            bar.set_size_request(140, -1)
            label = Gtk.Label(width_chars=9, xalign=1, css_classes=["numeric", "dim-label"])
            row.add_suffix(bar)
            row.add_suffix(label)
            g.add(row)
            self.core_rows[n] = (label, bar)

    # ------------------------------------------------------------ logic

    def _tick(self) -> bool:
        freqs = cpu.current_freqs_khz()
        if freqs:
            self.avg_label.set_label(_mhz(sum(freqs.values()) // len(freqs)))
        for n, (label, bar) in self.core_rows.items():
            khz = freqs.get(n)
            if khz is not None:
                label.set_label(_mhz(khz))
                bar.set_value(min(max(khz, bar.get_min_value()), bar.get_max_value()))
        return True  # keep ticking

    def _on_apply(self, _btn) -> None:
        payload: dict = {"action": "cpu"}

        item = self.gov_row.get_selected_item()
        if item:
            payload["governor"] = item.get_string()
        if self.epp_row:
            item = self.epp_row.get_selected_item()
            if item:
                payload["epp"] = item.get_string()
        if self.boost_row:
            payload["boost"] = self.boost_row.get_active()

        min_mhz = int(self.min_row.get_value())
        max_mhz = int(self.max_row.get_value())
        if min_mhz > max_mhz:
            self._toast("Minimum frequency is above maximum")
            return
        payload["min_khz"] = min_mhz * 1000
        payload["max_khz"] = max_mhz * 1000

        run_helper(payload, self._on_applied)

    def _on_applied(self, ok: bool, msg: str) -> None:
        self._toast("CPU settings applied" if ok else f"Failed: {msg}")

    def _toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))
