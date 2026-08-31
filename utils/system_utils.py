"""
RAMGuard System Utilities
Platform-specific helpers and general system utilities.
"""

import os
import sys
import platform
import subprocess
from typing import Optional
from utils.logger import get_logger

logger = get_logger("SystemUtils")


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return platform.system() == "Windows"


def get_windows_startup_folder() -> Optional[str]:
    """Return the user startup folder path on Windows."""
    if not is_windows():
        return None
    startup = os.path.expanduser(
        r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    )
    return startup if os.path.isdir(startup) else None


def human_readable_bytes(bytes_value: int, suffix: str = "B") -> str:
    """Convert a raw byte count to a human-readable string."""
    for unit in ("", "K", "M", "G", "T"):
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.1f} {unit}{suffix}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} P{suffix}"


def human_readable_mb(mb_value: float) -> str:
    """Convert MB value to human-readable string."""
    if mb_value >= 1024:
        return f"{mb_value / 1024:.1f} GB"
    return f"{mb_value:.0f} MB"


def get_python_pid() -> int:
    """Return the current Python process PID."""
    return os.getpid()


def is_elevated() -> bool:
    """Check whether the process is running with elevated privileges on Windows."""
    if not is_windows():
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def open_task_manager() -> None:
    """Open Windows Task Manager."""
    try:
        if is_windows():
            subprocess.Popen(["taskmgr.exe"])
    except Exception as e:
        logger.warning(f"Could not open Task Manager: {e}")


def get_startup_registry_entries() -> list[dict]:
    """
    Retrieve startup programs from Windows registry (HKCU run key).
    Returns a list of dicts with name, command, enabled fields.
    """
    entries = []
    if not is_windows():
        return entries
    try:
        import winreg
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in reg_paths:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries.append({
                            "name": name,
                            "command": value,
                            "enabled": True,
                            "source": "registry",
                            "hive": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                            "impact": _estimate_startup_impact(value),
                        })
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception as e:
                logger.debug(f"Could not read registry path {path}: {e}")
    except ImportError:
        logger.warning("winreg module not available")
    return entries


def disable_startup_registry_entry(name: str, hive_str: str = "HKCU") -> bool:
    """Disable a Windows registry startup entry by moving it to a disabled key."""
    if not is_windows():
        return False
    try:
        import winreg
        hive = winreg.HKEY_CURRENT_USER if hive_str == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        disabled_path = r"Software\Microsoft\Windows\CurrentVersion\Run-\Disabled"

        # Read existing value
        key = winreg.OpenKey(hive, run_path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        value, _ = winreg.QueryValueEx(key, name)

        # Write to disabled key
        try:
            disabled_key = winreg.CreateKey(hive, disabled_path)
            winreg.SetValueEx(disabled_key, name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(disabled_key)
        except Exception:
            pass

        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        logger.info(f"Disabled startup entry: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to disable startup entry '{name}': {e}")
        return False


def enable_startup_registry_entry(name: str, command: str, hive_str: str = "HKCU") -> bool:
    """Re-enable a previously disabled startup registry entry."""
    if not is_windows():
        return False
    try:
        import winreg
        hive = winreg.HKEY_CURRENT_USER if hive_str == "HKCU" else winreg.HKEY_LOCAL_MACHINE
        run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(hive, run_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        logger.info(f"Enabled startup entry: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable startup entry '{name}': {e}")
        return False


def _estimate_startup_impact(command: str) -> str:
    """Heuristically estimate startup impact based on executable name."""
    cmd_lower = command.lower()
    high_impact = ["chrome", "firefox", "edge", "teams", "zoom", "skype", "discord", "spotify"]
    medium_impact = ["onedrive", "dropbox", "googledrive", "steam", "epic"]
    for kw in high_impact:
        if kw in cmd_lower:
            return "High"
    for kw in medium_impact:
        if kw in cmd_lower:
            return "Medium"
    return "Low"
