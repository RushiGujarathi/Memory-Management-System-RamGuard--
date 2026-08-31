"""
RAMGuard Worker Threads
Background QThread workers for non-blocking operations.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from core.memory_monitor import MemoryMonitor, MemorySnapshot
from core.process_scanner import ProcessScanner, ProcessInfo
from core.optimizer import MemoryOptimizer, OptimizationResult
from utils.logger import get_logger
import time

logger = get_logger("Workers")


class MonitorWorker(QThread):
    """Emits fresh MemorySnapshot at a configurable interval."""
    snapshot_ready = pyqtSignal(object)  # MemorySnapshot

    def __init__(self, interval_seconds: int = 3) -> None:
        super().__init__()
        self._interval = interval_seconds
        self._monitor = MemoryMonitor()
        self._running = False

    def run(self) -> None:
        self._running = True
        logger.debug("MonitorWorker started (interval=%ds)", self._interval)
        while self._running:
            try:
                snap = self._monitor.take_snapshot()
                self.snapshot_ready.emit(snap)
            except Exception as e:
                logger.error("MonitorWorker error: %s", e)
            time.sleep(self._interval)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)

    def set_interval(self, seconds: int) -> None:
        self._interval = max(1, seconds)


class ScanWorker(QThread):
    """Scans all running processes in a background thread."""
    scan_complete = pyqtSignal(list)   # list[ProcessInfo]
    error_occurred = pyqtSignal(str)

    def __init__(self, scanner: ProcessScanner) -> None:
        super().__init__()
        self._scanner = scanner

    def run(self) -> None:
        try:
            processes = self._scanner.scan()
            self.scan_complete.emit(processes)
        except Exception as e:
            logger.error("ScanWorker error: %s", e)
            self.error_occurred.emit(str(e))


class OptimizeWorker(QThread):
    """Runs memory optimization in a background thread."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)   # OptimizationResult
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        optimizer: MemoryOptimizer,
        processes: list[ProcessInfo],
        mode: str,
    ) -> None:
        super().__init__()
        self._optimizer = optimizer
        self._processes = processes
        self._mode = mode

    def run(self) -> None:
        try:
            result = self._optimizer.execute(
                self._processes,
                mode=self._mode,
                progress_callback=self.progress.emit,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error("OptimizeWorker error: %s", e)
            self.error_occurred.emit(str(e))
