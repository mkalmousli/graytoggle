#!/usr/bin/env sh
set -eu

REPO="https://github.com/mkalmousli/graytoggle"
DEST="${GRAYTOGGLE_SRC:-$HOME/.local/share/graytoggle-src}"

if ! command -v git >/dev/null 2>&1; then
    echo "install: git is required" >&2
    exit 1
fi
if ! command -v make >/dev/null 2>&1; then
    echo "install: make is required" >&2
    exit 1
fi

rm -rf "$DEST"
git clone --depth 1 "$REPO" "$DEST"
make -C "$DEST" install "$@"
echo "Done. Run 'graytoggle' (make sure ~/.local/bin is on your PATH)."
