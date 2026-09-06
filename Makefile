PREFIX  ?= $(HOME)/.local
BINDIR  := $(PREFIX)/bin
SHAREDIR := $(PREFIX)/share/graytoggle

.PHONY: install uninstall

install:
	install -d "$(BINDIR)" "$(SHAREDIR)/shaders"
	install -m 755 graytoggle.py "$(SHAREDIR)/graytoggle.py"
	install -m 644 shaders/grayscale.glsl "$(SHAREDIR)/shaders/grayscale.glsl"
	ln -sf "$(SHAREDIR)/graytoggle.py" "$(BINDIR)/graytoggle"
	@echo "Installed. Run 'graytoggle' (make sure $(BINDIR) is on your PATH)."

uninstall:
	rm -f "$(BINDIR)/graytoggle"
	rm -rf "$(SHAREDIR)"
	@echo "Uninstalled."
