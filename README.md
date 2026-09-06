# graytoggle

**Instant grayscale mode for Linux, built for the XFCE4 desktop.**

One command turns your entire screen black-and-white — and one command turns
it back. No hardware, no monitor color settings, no "night light" gimmicks.
It's 100% software: a real-time GLSL shader running through your compositor.

Grayscale mode is one of the best-known tricks for cutting phone/screen
addiction and doomscrolling — iOS and Android have shipped it for years.
Linux desktops, and XFCE4 in particular, never got one. `graytoggle` is that
missing feature.

![off vs on](assets/example.png)

## Why this exists

XFCE4 has no built-in grayscale mode — unlike GNOME or KDE, there's no
setting to flip. Building one meant taking over xfwm4's compositor, swapping
in `picom` on the fly without breaking shadows/transparency, running a
per-window fragment shader, and handing compositing cleanly back to xfwm4 the
moment you're done — all without leaving orphan processes or a broken desktop
if any step fails. `graytoggle` is the result of solving that, wrapped in a
single command.

## What it does

Running `graytoggle` will:
1. Turn off xfwm4's built-in compositor.
2. Start `picom` with a grayscale window shader.
3. On the next run, stop `picom` and hand compositing back to xfwm4.

The shader computes real luminance (`0.2126R + 0.7152G + 0.0722B`) per pixel,
per window, live. Nothing about your display, monitor, or graphics driver is
touched — it's a pure compositing-layer effect that turns off as cleanly as
it turns on.

## Requirements

Linux with an X11 session running XFCE4:

- XFCE4 (`xfwm4`)
- [`picom`](https://github.com/yshui/picom)
- `xfconf-query` (ships with xfce4)
- `xprop` (ships with x11-utils / x11-xserver-utils)

Missing something? Just run `graytoggle` — it detects exactly what's missing
and prints the install command for your package manager (apt, dnf, pacman,
zypper).

## Install

One-liner (clones the repo and runs `make install`):

```sh
curl -fsSL https://raw.githubusercontent.com/mkalmousli/graytoggle/master/install.sh | sh
```

Or manually:

```sh
git clone https://github.com/mkalmousli/graytoggle
cd graytoggle
make install
```

Installs to `~/.local/bin/graytoggle` by default. Make sure `~/.local/bin` is
on your `PATH`.

Install elsewhere with:

```sh
make install PREFIX=/usr/local
```

## Uninstall

```sh
make uninstall
```

## Usage

```sh
graytoggle          # toggle grayscale on/off
graytoggle --force  # take over from another running compositor if needed
```

Bind it to a keyboard shortcut in XFCE's Keyboard settings for a one-key
grayscale toggle — the fastest way to make your desktop as boring (and as
easy to put down) as a black-and-white phone.

## License

[GPL-3.0](LICENSE)
