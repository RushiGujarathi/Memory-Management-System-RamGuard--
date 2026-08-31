"""
RAMGuard Optimizer
Orchestrates the safe closing of user-selected processes.
SAFETY > OPTIMIZATION — always.
"""

import time
import os
from dataclasses import dataclass, field
from typing import Optional
import psutil
from core.process_scanner import ProcessInfo, ProcessScanner
from core.safety_manager import ProcessSafetyManager, SafetyLevel
from core.memory_monitor import MemoryMonitor, MemorySnapshot
from utils.logger import get_logger

logger = get_logger("Optimizer")


class OptimizationMode:
    SAFE = "SAFE"      # Only close explicitly user-selected processes
    SMART = "SMART"    # Recommend based on memory + safety classification
    CUSTOM = "CUSTOM"  # User manually selects from full list


@dataclass
class ClosureResult:
    pid: int
    name: str
    memory_mb: float
    success: bool
    error_message: str = ""
    method_used: str = ""


@dataclass
class OptimizationResult:
    mode: str
    started_at: float
    finished_at: float
    snapshot_before: Optional[MemorySnapshot]
    snapshot_after: Optional[MemorySnapshot]
    closures: list[ClosureResult] = field(default_factory=list)

    @property
    def successful_closures(self) -> list[ClosureResult]:
        return [c for c in self.closures if c.success]

    @property
    def failed_closures(self) -> list[ClosureResult]:
        return [c for c in self.closures if not c.success]

    @property
    def memory_freed_mb(self) -> float:
        if self.snapshot_before and self.snapshot_after:
            freed = self.snapshot_before.used_bytes - self.snapshot_after.used_bytes
            return max(freed / (1024 * 1024), 0.0)
        return sum(c.memory_mb for c in self.successful_closures)

    @property
    def memory_freed_display(self) -> str:
        mb = self.memory_freed_mb
        if mb >= 1024:
            return f"{mb / 1024:.1f} GB"
        return f"{mb:.0f} MB"

    @property
    def percent_before(self) -> float:
        return self.snapshot_before.percent if self.snapshot_before else 0.0

    @property
    def percent_after(self) -> float:
        return self.snapshot_after.percent if self.snapshot_after else 0.0

    @property
    def duration_seconds(self) -> float:
        return self.finished_at - self.started_at


class MemoryOptimizer:
    """
    Safely closes a list of user-confirmed processes.
    
    Closure strategy (in order):
      1. Graceful (SIGTERM / WM_CLOSE via terminate())
      2. Wait up to GRACE_PERIOD_SECONDS
      3. If still alive and explicitly needed → kill()
    
    Protected processes are NEVER touched.
    """

    GRACE_PERIOD_SECONDS: float = 3.0
    POST_CLOSE_SETTLE_SECONDS: float = 1.5

    def __init__(
        self,
        safety_manager: Optional[ProcessSafetyManager] = None,
        monitor: Optional[MemoryMonitor] = None,
        scanner: Optional[ProcessScanner] = None,
    ) -> None:
        self._safety = safety_manager or ProcessSafetyManager()
        self._monitor = monitor or MemoryMonitor()
        self._scanner = scanner or ProcessScanner(self._safety)
        self._own_pid = os.getpid()

    def execute(
        self,
        processes: list[ProcessInfo],
        mode: str = OptimizationMode.SAFE,
        progress_callback=None,
    ) -> OptimizationResult:
        """
        Close the supplied list of processes safely.
        
        Args:
            processes:          User-confirmed list of ProcessInfo objects to close.
            mode:               Optimization mode label (SAFE / SMART / CUSTOM).
            progress_callback:  Optional callable(message: str) for UI progress updates.
        
        Returns:
            OptimizationResult with full details.
        """
        started_at = time.time()
        snapshot_before = self._monitor.take_snapshot()
        closures: list[ClosureResult] = []

        def emit(msg: str) -> None:
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        emit(f"Starting {mode} optimization for {len(processes)} process(es).")

        for proc_info in processes:
            result = self._close_process(proc_info, emit)
            closures.append(result)

        # Allow OS to reclaim memory
        emit(f"Waiting {self.POST_CLOSE_SETTLE_SECONDS}s for memory to settle…")
        time.sleep(self.POST_CLOSE_SETTLE_SECONDS)

        snapshot_after = self._monitor.take_snapshot()
        finished_at = time.time()

        opt_result = OptimizationResult(
            mode=mode,
            started_at=started_at,
            finished_at=finished_at,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
            closures=closures,
        )

        emit(
            f"Optimization complete: {len(opt_result.successful_closures)} closed, "
            f"{len(opt_result.failed_closures)} failed, "
            f"~{opt_result.memory_freed_display} freed."
        )
        return opt_result

    # ──────────────────────────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _close_process(self, proc_info: ProcessInfo, emit) -> ClosureResult:
        """Attempt to gracefully close a single process."""
        pid = proc_info.pid
        name = proc_info.name

        # ── Re-check safety immediately before touching the process ──
        try:
            live_proc = psutil.Process(pid)
            live_name = live_proc.name()
            live_exe: Optional[str] = None
            try:
                live_exe = live_proc.exe()
            except psutil.AccessDenied:
                pass

            assessment = self._safety.assess(pid, live_name, live_exe)
            if not assessment.can_terminate or assessment.level == SafetyLevel.PROTECTED:
                msg = f"Safety check blocked closure of '{name}' (PID {pid}): {assessment.reason}"
                logger.warning(msg)
                emit(f"⚠ Skipping '{name}' — {assessment.reason}")
                return ClosureResult(
                    pid=pid, name=name, memory_mb=proc_info.memory_mb,
                    success=False, error_message=assessment.reason,
                )
        except psutil.NoSuchProcess:
            # Process already gone — count as success
            emit(f"ℹ '{name}' (PID {pid}) already exited.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=True, method_used="already_exited",
            )
        except psutil.AccessDenied as e:
            msg = f"Access denied reading info for '{name}' (PID {pid}): {e}"
            logger.warning(msg)
            emit(f"⚠ Cannot access '{name}' — insufficient privileges.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=False, error_message="Access denied",
            )

        # ── Attempt graceful termination ──
        emit(f"Closing '{name}' (PID {pid}) gracefully…")
        try:
            live_proc.terminate()  # SIGTERM / WM_CLOSE on Windows
            method = "terminate"
        except psutil.AccessDenied:
            emit(f"⚠ Cannot close '{name}' — Windows denied access.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=False, error_message="Windows denied access (insufficient privileges).",
            )
        except psutil.NoSuchProcess:
            emit(f"ℹ '{name}' already exited during close attempt.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=True, method_used="already_exited",
            )

        # ── Wait for graceful exit ──
        try:
            live_proc.wait(timeout=self.GRACE_PERIOD_SECONDS)
            emit(f"✓ '{name}' closed successfully.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=True, method_used=method,
            )
        except psutil.TimeoutExpired:
            # Grace period expired — attempt forceful kill ONLY for non-critical processes
            emit(f"'{name}' did not respond to graceful shutdown. Attempting force close…")
            try:
                live_proc.kill()
                live_proc.wait(timeout=2.0)
                emit(f"✓ '{name}' force-closed.")
                return ClosureResult(
                    pid=pid, name=name, memory_mb=proc_info.memory_mb,
                    success=True, method_used="kill",
                )
            except psutil.NoSuchProcess:
                emit(f"✓ '{name}' exited during force-close.")
                return ClosureResult(
                    pid=pid, name=name, memory_mb=proc_info.memory_mb,
                    success=True, method_used="kill_no_such_process",
                )
            except (psutil.AccessDenied, psutil.TimeoutExpired) as e:
                msg = f"Could not close '{name}': {e}"
                logger.error(msg)
                emit(f"✗ '{name}' could not be closed: {e}")
                return ClosureResult(
                    pid=pid, name=name, memory_mb=proc_info.memory_mb,
                    success=False, error_message=str(e),
                )
        except psutil.NoSuchProcess:
            emit(f"✓ '{name}' exited during wait.")
            return ClosureResult(
                pid=pid, name=name, memory_mb=proc_info.memory_mb,
                success=True, method_used="no_such_process",
            )
