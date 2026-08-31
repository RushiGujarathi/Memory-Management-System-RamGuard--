"""
RAMGuard Startup Manager
Reads and manages Windows startup applications.
"""

from utils.system_utils import (
    get_startup_registry_entries,
    disable_startup_registry_entry,
    enable_startup_registry_entry,
)
from utils.logger import get_logger

logger = get_logger("StartupManager")


class StartupManager:
    """
    Manages Windows startup entries.
    All changes require explicit user action — nothing is modified automatically.
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def refresh(self) -> list[dict]:
        """Reload startup entries from the registry."""
        self._entries = get_startup_registry_entries()
        logger.info("Loaded %d startup entries", len(self._entries))
        return self._entries

    def get_entries(self) -> list[dict]:
        """Return cached startup entries (call refresh() first)."""
        return list(self._entries)

    def disable(self, name: str, hive: str = "HKCU") -> bool:
        """Disable a startup entry (requires user confirmation in UI)."""
        result = disable_startup_registry_entry(name, hive)
        if result:
            self.refresh()
        return result

    def enable(self, name: str, command: str, hive: str = "HKCU") -> bool:
        """Re-enable a previously disabled startup entry."""
        result = enable_startup_registry_entry(name, command, hive)
        if result:
            self.refresh()
        return result
