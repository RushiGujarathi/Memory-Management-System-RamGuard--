"""
RAMGuard Configuration Manager
Loads and saves app configuration from config/config.json.
"""

import json
import os
from pathlib import Path
from typing import Any
from utils.logger import get_logger

logger = get_logger("Config")

CONFIG_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "config" / "config.json"

_DEFAULTS = {
    "app_name": "RAMGuard",
    "version": "1.0.0",
    "theme": "dark",
    "monitoring_interval_seconds": 3,
    "memory_warning_threshold_percent": 80,
    "memory_critical_threshold_percent": 90,
    "start_with_windows": False,
    "show_notifications": True,
    "default_optimization_mode": "SAFE",
    "min_memory_to_recommend_mb": 100,
    "max_history_entries": 100,
    "custom_protected_processes": [],
    "auto_refresh_process_list": True,
    "process_list_refresh_interval_seconds": 5,
}


class AppConfig:
    """Thread-safe configuration accessor backed by a JSON file."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._data = {**_DEFAULTS, **json.load(f)}
                logger.debug("Config loaded from %s", CONFIG_PATH)
                return
            except Exception as e:
                logger.warning("Could not load config, using defaults: %s", e)
        self._data = dict(_DEFAULTS)

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
            logger.debug("Config saved to %s", CONFIG_PATH)
        except Exception as e:
            logger.error("Could not save config: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    # Convenience properties
    @property
    def theme(self) -> str:
        return self.get("theme", "dark")

    @property
    def monitoring_interval(self) -> int:
        return int(self.get("monitoring_interval_seconds", 3))

    @property
    def warning_threshold(self) -> int:
        return int(self.get("memory_warning_threshold_percent", 80))

    @property
    def critical_threshold(self) -> int:
        return int(self.get("memory_critical_threshold_percent", 90))

    @property
    def default_mode(self) -> str:
        return self.get("default_optimization_mode", "SAFE")

    @property
    def min_recommend_mb(self) -> float:
        return float(self.get("min_memory_to_recommend_mb", 100))


# Module-level singleton
config = AppConfig()
