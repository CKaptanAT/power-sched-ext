# PowerSched — install/uninstall via standard FHS paths.
#
# Used by `install.sh` and by the distro packages (Arch/Debian/Fedora) so that
# every install method puts files in exactly the same place.
#
#   make install              # install into /usr (needs root)
#   make install PREFIX=/usr/local
#   make install DESTDIR=/tmp/pkg PREFIX=/usr   # staged build (packaging)
#   make uninstall

PREFIX  ?= /usr
DESTDIR ?=

BINDIR     = $(DESTDIR)$(PREFIX)/bin
LIBDIR     = $(DESTDIR)$(PREFIX)/lib/powersched
DATADIR    = $(DESTDIR)$(PREFIX)/share
APPDIR     = $(DATADIR)/applications
POLKITDIR  = $(DATADIR)/polkit-1/actions
METAINFODIR= $(DATADIR)/metainfo
DOCDIR     = $(DATADIR)/doc/powersched

APP_ID = io.github.powersched

.PHONY: all install uninstall check clean

all:
	@echo "Nothing to build. Run 'make install' (as root) or build a package."

install:
	# --- application package ---
	install -d $(LIBDIR)/powersched
	install -m 644 powersched/*.py $(LIBDIR)/powersched/
	# --- launcher (PREFIX is baked in, DESTDIR is not) ---
	install -d $(BINDIR)
	printf '#!/usr/bin/env bash\nexec env PYTHONPATH=$(PREFIX)/lib/powersched /usr/bin/python3 -m powersched "$$@"\n' \
		> $(BINDIR)/powersched
	chmod 755 $(BINDIR)/powersched
	# --- desktop entry (point Exec at the installed launcher) ---
	install -d $(APPDIR)
	sed 's|^Exec=.*|Exec=powersched|' \
		data/$(APP_ID).PowerSched.desktop > $(APPDIR)/$(APP_ID).PowerSched.desktop
	chmod 644 $(APPDIR)/$(APP_ID).PowerSched.desktop
	# --- polkit policy ---
	install -d $(POLKITDIR)
	install -m 644 data/$(APP_ID).policy $(POLKITDIR)/$(APP_ID).policy
	# --- AppStream metadata ---
	install -d $(METAINFODIR)
	install -m 644 data/$(APP_ID).metainfo.xml $(METAINFODIR)/$(APP_ID).metainfo.xml
	# --- docs ---
	install -d $(DOCDIR)
	install -m 644 README.md $(DOCDIR)/README.md
	@echo "Installed PowerSched to $(DESTDIR)$(PREFIX)."

uninstall:
	rm -rf $(LIBDIR)
	rm -f  $(BINDIR)/powersched
	rm -f  $(APPDIR)/$(APP_ID).PowerSched.desktop
	rm -f  $(POLKITDIR)/$(APP_ID).policy
	rm -f  $(METAINFODIR)/$(APP_ID).metainfo.xml
	rm -rf $(DOCDIR)
	@echo "Removed PowerSched from $(DESTDIR)$(PREFIX)."

check:
	python3 -m py_compile powersched/*.py
	@echo "Python sources compile cleanly."

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
