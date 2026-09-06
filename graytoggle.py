#!/usr/bin/env python3
import errno
import os
import re
import signal
import subprocess
import sys
import time
from typing import Optional, Tuple


def pid_running(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError as e:
        return e.errno != errno.ESRCH


def fast_kill(pid: int) -> None:
    if pid <= 1:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    time.sleep(0.12)
    if pid_running(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def read_pidfile(path: str) -> Optional[int]:
    try:
        with open(path, "r", encoding="ascii") as f:
            raw = f.read().strip()
        if not raw:
            return None
        pid = int(raw, 10)
        if pid <= 1:
            return None
        return pid
    except (OSError, ValueError):
        return None


def write_pidfile(path: str, pid: int) -> bool:
    try:
        with open(path, "w", encoding="ascii") as f:
            f.write(f"{pid}\n")
        return True
    except OSError:
        return False


def remove_pidfile(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def file_exists(path: str) -> bool:
    return os.access(path, os.R_OK)


def read_proc_comm(pid: int) -> Optional[str]:
    try:
        with open(f"/proc/{pid}/comm", "r", encoding="ascii", errors="ignore") as f:
            name = f.read().strip()
        return name or None
    except OSError:
        return None


def read_env_from_pid(pid: int, key: str) -> Optional[str]:
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            data = f.read()
    except OSError:
        return None

    key_bytes = key.encode("ascii") + b"="
    for entry in data.split(b"\0"):
        if entry.startswith(key_bytes):
            return entry[len(key_bytes) :].decode("utf-8", errors="ignore")
    return None


def _run_capture(cmd: list) -> Optional[str]:
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        return res.stdout
    except OSError:
        return None


def xprop_get_cm_window() -> Optional[int]:
    out = _run_capture(["xprop", "-root", "-notype", "_NET_WM_CM_S0"])
    if not out:
        return None
    m = re.search(r" = (0x[0-9a-fA-F]+|\d+)", out)
    if not m:
        return None
    try:
        return int(m.group(1), 0)
    except ValueError:
        return None


def xprop_get_cm_pid() -> Optional[int]:
    win = xprop_get_cm_window()
    if not win:
        return None
    out = _run_capture(["xprop", "-id", f"0x{win:x}", "-notype", "_NET_WM_PID"])
    if not out:
        return None
    m = re.search(r" = (\d+)", out)
    if not m:
        return None
    try:
        pid = int(m.group(1), 10)
    except ValueError:
        return None
    return pid if pid > 1 else None


def log_contains(path: str, needle: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if needle in line:
                    return True
    except OSError:
        return False
    return False


def compositor_running() -> Optional[int]:
    return xprop_get_cm_pid()


def xfwm_set_compositing(enabled: bool) -> bool:
    val = "true" if enabled else "false"
    try:
        res = subprocess.run(
            [
                "xfconf-query",
                "-c",
                "xfwm4",
                "-p",
                "/general/use_compositing",
                "-s",
                val,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return res.returncode == 0
    except OSError:
        return False


def xfwm_replace_compositor_off() -> bool:
    try:
        subprocess.Popen(
            ["xfwm4", "--replace", "--compositor=off"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return False
    time.sleep(0.2)
    return True


def start_picom(shader_path: str, log_path: str) -> Optional[subprocess.Popen]:
    args = [
        "picom",
        "--backend",
        "glx",
        "--config",
        "/dev/null",
        "--vsync",
        "--xrender-sync-fence",
        "--fade-in-step",
        "0.05",
        "--fade-out-step",
        "0.05",
        "--fade-delta",
        "5",
        "--log-level",
        "warn",
        "--log-file",
        log_path,
        "--window-shader-fg",
        shader_path,
    ]
    try:
        return subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return None


def start_picom_checked(shader: str, log_path: str) -> Optional[int]:
    proc = start_picom(shader, log_path)
    if not proc:
        return None
    time.sleep(0.08)
    if not pid_running(proc.pid):
        return None
    if log_contains(log_path, "FATAL ERROR"):
        fast_kill(proc.pid)
        return None
    owner = xprop_get_cm_pid()
    if owner and owner != proc.pid:
        fast_kill(proc.pid)
        return None
    return proc.pid


def which(cmd: str) -> Optional[str]:
    for d in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(d, cmd)
        if os.access(candidate, os.X_OK) and not os.path.isdir(candidate):
            return candidate
    return None


REQUIRED_TOOLS = {
    "picom": "picom (the compositor that applies the shader)",
    "xfconf-query": "xfconf-query (part of xfce4, toggles xfwm4 compositing)",
    "xprop": "xprop (part of x11-utils/x11-xserver-utils, detects the running compositor)",
}

INSTALL_HINTS = [
    ("apt", "sudo apt install picom xfconf x11-utils"),
    ("dnf", "sudo dnf install picom xfconf x11-utils"),
    ("pacman", "sudo pacman -S picom xfconf xorg-xprop"),
    ("zypper", "sudo zypper install picom xfconf xorg-x11-utils"),
]


def missing_tools() -> list:
    return [name for name in REQUIRED_TOOLS if which(name) is None]


def print_install_help(missing: list) -> None:
    print("toggle: missing required tools:", file=sys.stderr)
    for name in missing:
        print(f"  - {REQUIRED_TOOLS[name]}", file=sys.stderr)
    print("", file=sys.stderr)
    print("install with whichever package manager you have, e.g.:", file=sys.stderr)
    detected = [cmd for mgr, cmd in INSTALL_HINTS if which(mgr)]
    for cmd in detected or [cmd for _mgr, cmd in INSTALL_HINTS]:
        print(f"  {cmd}", file=sys.stderr)


def main(argv: list) -> int:
    force = False
    for arg in argv[1:]:
        if arg in ("--force", "-f"):
            force = True
        else:
            print(f"usage: {argv[0]} [--force]", file=sys.stderr)
            return 1

    disp = os.environ.get("DISPLAY")
    if not disp:
        print("toggle: DISPLAY not set (run inside an X11 session)", file=sys.stderr)
        return 2

    missing = missing_tools()
    if missing:
        print_install_help(missing)
        return 3

    if which("xfwm4") is None:
        print(
            "toggle: xfwm4 not found -- this tool targets XFCE4's window manager",
            file=sys.stderr,
        )
        return 4

    bindir = os.path.dirname(os.path.realpath(__file__))
    shader = os.path.join(bindir, "shaders", "grayscale.glsl")
    pidfile = os.path.join(bindir, ".graytoggle_picom.pid")

    if not file_exists(shader):
        print(f"toggle: shader not found: {shader}", file=sys.stderr)
        print("toggle: reinstall or restore shaders/grayscale.glsl from the repo", file=sys.stderr)
        return 6

    existing = read_pidfile(pidfile)
    if existing and pid_running(existing):
        should_kill = False
        owner = xprop_get_cm_pid()
        if owner and owner == existing:
            should_kill = True
        else:
            name = read_proc_comm(existing)
            if name in ("picom", "compton"):
                should_kill = True
        if should_kill:
            fast_kill(existing)
            remove_pidfile(pidfile)
            xfwm_set_compositing(True)
            print("Grayscale OFF")
            return 0
        remove_pidfile(pidfile)
    elif existing:
        # Stale pidfile: if no compositor is running, restore WM compositing.
        if not compositor_running():
            xfwm_set_compositing(True)
        remove_pidfile(pidfile)

    cm_pid = compositor_running()

    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS") and cm_pid:
        dbus = read_env_from_pid(cm_pid, "DBUS_SESSION_BUS_ADDRESS")
        if dbus:
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = dbus

    if not xfwm_set_compositing(False):
        print("toggle: failed to disable xfwm compositing (xfconf-query)", file=sys.stderr)
        other_pid = cm_pid
        if other_pid:
            print("toggle: another compositor is running", file=sys.stderr)
            if force:
                name = read_proc_comm(other_pid) or ""
                if name in ("picom", "compton", "xcompmgr"):
                    fast_kill(other_pid)
                    time.sleep(0.12)
                    if compositor_running():
                        print("toggle: failed to stop compositor", file=sys.stderr)
                        return 7
                elif name == "xfwm4":
                    if not xfwm_replace_compositor_off() or compositor_running():
                        print("toggle: failed to disable xfwm4 compositing", file=sys.stderr)
                        return 7
                elif not name:
                    xfwm_replace_compositor_off()
                else:
                    print(
                        f"toggle: compositor is '{name or 'unknown'}' (not safe to kill)",
                        file=sys.stderr,
                    )
                    return 7
            else:
                print("toggle: disable compositing in your WM or use --force", file=sys.stderr)
                return 7

    log_path = os.path.join(bindir, ".graytoggle_picom.log")
    try:
        with open(log_path, "w", encoding="ascii"):
            pass
    except OSError:
        print("toggle: log path too long", file=sys.stderr)
        xfwm_set_compositing(True)
        return 7

    picom_pid = start_picom_checked(shader, log_path)
    if not picom_pid:
        if force:
            xfwm_replace_compositor_off()
            try:
                with open(log_path, "w", encoding="ascii"):
                    pass
            except OSError:
                pass
            picom_pid = start_picom_checked(shader, log_path)
        if not picom_pid:
            print("toggle: picom reported a fatal error (see log)", file=sys.stderr)
            xfwm_set_compositing(True)
            return 10

    write_pidfile(pidfile, picom_pid)
    print("Grayscale ON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
