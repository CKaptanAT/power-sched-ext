Name:           powersched
Version:        0.1.0
Release:        1%{?dist}
Summary:        CPU frequency and sched_ext scheduler control center

License:        GPL-3.0-or-later
URL:            https://github.com/CKaptanAT/power-sched-ext
# For COPR/Koji, attach a tarball of the source tree named %{name}-%{version}.tar.gz
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  make
BuildRequires:  libappstream-glib
BuildRequires:  desktop-file-utils

Requires:       python3 >= 3.10
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       polkit
Recommends:     scx-scheds

%description
PowerSched is a GTK4/libadwaita application that combines what cpupower-gui
and scx-manager do in a single window.

The CPU Power page exposes the scaling governor, energy/performance preference
(EPP), minimum and maximum frequency limits, turbo boost, and a live per-core
frequency monitor. The Scheduler page detects sched_ext kernel support, lists
installed scx_* schedulers, shows the active one, and starts/stops them with
profile presets (Gaming, Low Latency, Power Save, Server).

Privileged changes go through a small, input-validating root helper invoked
via pkexec (polkit).

%prep
%autosetup

%build
# Pure-Python application; nothing to compile.

%install
%make_install PREFIX=%{_prefix}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/io.github.powersched.PowerSched.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/io.github.powersched.metainfo.xml

%files
%license LICENSE
%{_bindir}/powersched
%{_prefix}/lib/powersched/
%{_datadir}/applications/io.github.powersched.PowerSched.desktop
%{_datadir}/polkit-1/actions/io.github.powersched.policy
%{_metainfodir}/io.github.powersched.metainfo.xml
%{_datadir}/doc/powersched/

%changelog
* Sun Jun 28 2026 CKaptanAT <linux.planet.ocean@gmail.com> - 0.1.0-1
- Initial Fedora packaging.
