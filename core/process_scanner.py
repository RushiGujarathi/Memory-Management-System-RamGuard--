"""
RAMGuard Process Scanner
Retrieves and structures information about running processes.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional
import psutil
from core.safety_manager import ProcessSafetyManager, SafetyLevel, SafetyAssessment
from utils.logger import get_logger

logger = get_logger("ProcessScanner")


@dataclass
class ProcessInfo:
    pid: int
    name: str
    exe: Optional[str]
    memory_mb: float
    memory_bytes: int
    cpu_percent: float
    status: str
    is_foreground: bool
    safety_level: SafetyLevel
    safety_reason: str
    safety_assessment: SafetyAssessment
    create_time: float = 0.0
    username: str = ""
    num_threads: int = 0
    cmdline: str = ""

    @property
    def memory_display(self) -> str:
        """Human-readable memory string."""
        if self.memory_mb >= 1024:
            return f"{self.memory_mb / 1024:.1f} GB"
        return f"{self.memory_mb:.0f} MB"

    @property
    def is_safe_to_close(self) -> bool:
        return self.safety_level == SafetyLevel.SAFE_TO_CLOSE

    @property
    def is_protected(self) -> bool:
        return self.safety_level == SafetyLevel.PROTECTED

    @property
    def is_review(self) -> bool:
        return self.safety_level == SafetyLevel.REVIEW


class ProcessScanner:
    """
    Scans the system for running processes and enriches each entry
    with safety classification data.
    """

    # Minimum memory (MB) to include a process in results
    MIN_MEMORY_MB: float = 0.5

    def __init__(self, safety_manager: Optional[ProcessSafetyManager] = None) -> None:
        self._safety = safety_manager or ProcessSafetyManager()
        self._own_pid = os.getpid()

    def scan(self, min_memory_mb: float = 0.0) -> list[ProcessInfo]:
        """
        Scan all running processes and return enriched ProcessInfo list,
        sorted by memory consumption (descending).
        
        Args:
            min_memory_mb: Only include processes using at least this many MB.
        
        Returns:
            Sorted list of ProcessInfo objects.
        """
        results: list[ProcessInfo] = []
        threshold = max(min_memory_mb, self.MIN_MEMORY_MB)

        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "memory_info",
                                                "status", "create_time", "username",
                                                "num_threads", "cmdline"]):
            info = self._build_process_info(proc, threshold)
            if info is not None:
                results.append(info)

        results.sort(key=lambda p: p.memory_bytes, reverse=True)
        logger.debug("Scanned %d processes (threshold=%.1f MB)", len(results), threshold)
        return results

    def get_process_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Retrieve fresh information for a single process by PID."""
        try:
            proc = psutil.Process(pid)
            return self._build_process_info(proc, min_memory_mb=0.0)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def get_recommended_to_close(self, min_memory_mb: float = 100.0) -> list[ProcessInfo]:
        """
        Return processes that are SAFE_TO_CLOSE and consuming
        at least min_memory_mb.
        """
        all_procs = self.scan()
        return [
            p for p in all_procs
            if p.is_safe_to_close and p.memory_mb >= min_memory_mb
        ]

    # ──────────────────────────────────────────────────────────────
    #  Private helpers
    # ──────────────────────────────────────────────────────────────

    def _build_process_info(
        self, proc: psutil.Process, min_memory_mb: float
    ) -> Optional[ProcessInfo]:
        """Build a ProcessInfo for a single psutil.Process, or None on failure."""
        try:
            info = proc.as_dict(attrs=[
                "pid", "name", "exe", "memory_info", "status",
                "create_time", "username", "num_threads", "cmdline",
            ])

            pid: int = info.get("pid", 0)
            name: str = info.get("name") or "Unknown"
            exe: Optional[str] = info.get("exe")
            mem_info = info.get("memory_info")
            memory_bytes: int = mem_info.rss if mem_info else 0
            memory_mb: float = memory_bytes / (1024 * 1024)

            if memory_mb < min_memory_mb:
                return None

            # CPU percent — non-blocking (may return 0.0 on first call)
            try:
                cpu = proc.cpu_percent(interval=None)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cpu = 0.0

            status: str = info.get("status", "unknown")
            create_time: float = info.get("create_time") or 0.0
            username: str = info.get("username") or ""
            num_threads: int = info.get("num_threads") or 0
            cmdline_list = info.get("cmdline") or []
            cmdline: str = " ".join(cmdline_list) if isinstance(cmdline_list, list) else ""

            # Safety assessment
            assessment = self._safety.assess(pid, name, exe)

            # Foreground heuristic: has exe outside system32/syswow64 and is not a service
            is_fg = self._is_foreground(name, exe, status)

            return ProcessInfo(
                pid=pid,
                name=name,
                exe=exe,
                memory_mb=memory_mb,
                memory_bytes=memory_bytes,
                cpu_percent=cpu,
                status=status,
                is_foreground=is_fg,
                safety_level=assessment.level,
                safety_reason=assessment.reason,
                safety_assessment=assessment,
                create_time=create_time,
                username=username,
                num_threads=num_threads,
                cmdline=cmdline,
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            logger.debug("Unexpected error scanning process: %s", e)
            return None

    @staticmethod
    def _is_foreground(name: str, exe: Optional[str], status: str) -> bool:
        """Heuristically determine if a process is user-facing."""
        if not name:
            return False
        name_lower = name.lower()
        # Obvious background indicators
        if any(kw in name_lower for kw in ("svc", "service", "helper", "daemon", "agent")):
            return False
        # Obvious foreground indicators
        if any(kw in name_lower for kw in ("chrome", "firefox", "discord", "spotify",
                                             "notepad", "code", "explorer", "vlc",
                                             "teams", "zoom", "slack", "steam")):
            return True
        # If exe is in user's AppData / Program Files it's likely foreground
        if exe:
            exe_lower = exe.lower()
            if any(kw in exe_lower for kw in (r"appdata\local", r"program files", r"users")):
                return True
        return False
