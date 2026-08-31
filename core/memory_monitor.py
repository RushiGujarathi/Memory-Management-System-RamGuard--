"""
RAMGuard Memory Monitor
Continuously tracks system memory and CPU metrics.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import psutil
from utils.logger import get_logger

logger = get_logger("MemoryMonitor")


class MemoryPressure(Enum):
    NORMAL = "NORMAL"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_percent(cls, pct: float) -> "MemoryPressure":
        if pct >= 90:
            return cls.CRITICAL
        if pct >= 80:
            return cls.HIGH
        if pct >= 60:
            return cls.MODERATE
        return cls.NORMAL

    @property
    def color_name(self) -> str:
        colors = {
            "NORMAL": "#2ecc71",
            "MODERATE": "#f39c12",
            "HIGH": "#e67e22",
            "CRITICAL": "#e74c3c",
        }
        return colors.get(self.value, "#ffffff")

    @property
    def display_label(self) -> str:
        labels = {
            "NORMAL": "System Healthy",
            "MODERATE": "Moderate Usage",
            "HIGH": "High Memory Usage",
            "CRITICAL": "Critical — Optimize Now",
        }
        return labels.get(self.value, self.value)


@dataclass
class MemorySnapshot:
    timestamp: float
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float
    cpu_percent: float
    process_count: int
    pressure: MemoryPressure

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024 ** 3)

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024 ** 3)

    @property
    def total_display(self) -> str:
        return f"{self.total_gb:.1f} GB"

    @property
    def used_display(self) -> str:
        return f"{self.used_gb:.1f} GB"

    @property
    def available_display(self) -> str:
        return f"{self.available_gb:.1f} GB"

    @property
    def percent_display(self) -> str:
        return f"{self.percent:.0f}%"


class MemoryMonitor:
    """
    Provides real-time system memory and CPU snapshots.
    Designed to be called from a background QThread.
    """

    def __init__(self) -> None:
        # Prime the CPU measurement (first call always returns 0.0)
        psutil.cpu_percent(interval=None)
        self._last_snapshot: Optional[MemorySnapshot] = None
        logger.info("MemoryMonitor initialised")

    def take_snapshot(self) -> MemorySnapshot:
        """Capture a fresh snapshot of memory and CPU metrics."""
        vm = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        proc_count = len(psutil.pids())
        pressure = MemoryPressure.from_percent(vm.percent)

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_bytes=vm.total,
            used_bytes=vm.used,
            available_bytes=vm.available,
            percent=vm.percent,
            cpu_percent=cpu,
            process_count=proc_count,
            pressure=pressure,
        )
        self._last_snapshot = snapshot
        return snapshot

    @property
    def last_snapshot(self) -> Optional[MemorySnapshot]:
        """Return the most recent snapshot without triggering a new scan."""
        return self._last_snapshot

    def get_available_mb(self) -> float:
        """Quick helper — available RAM in megabytes."""
        return psutil.virtual_memory().available / (1024 * 1024)

    def get_used_percent(self) -> float:
        """Quick helper — current RAM usage as a percentage."""
        return psutil.virtual_memory().percent
