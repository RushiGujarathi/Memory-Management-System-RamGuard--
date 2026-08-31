"""
RAMGuard Main Window
MVC-style orchestrator: sidebar navigation + stacked page container.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QStatusBar, QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QFont

from core.memory_monitor import MemorySnapshot, MemoryPressure
from core.process_scanner import ProcessScanner, ProcessInfo
from core.safety_manager import ProcessSafetyManager
from core.optimizer import MemoryOptimizer, OptimizationMode
from core.startup_manager import StartupManager
from config.app_config import AppConfig
from database.database import save_optimization_result

from ui.styles import get_stylesheet
from ui.workers import MonitorWorker, ScanWorker, OptimizeWorker
from ui.dashboard import DashboardPage
from ui.applications import ApplicationsPage
from ui.optimization import (
    OptimizationPage, ConfirmationDialog, ProgressDialog, ResultDialog,
)
from ui.startup import StartupPage
from ui.history import HistoryPage
from ui.settings import SettingsPage

from utils.logger import get_logger

logger = get_logger("MainWindow")


NAV_ITEMS = [
    ("dashboard",    "📊", "Dashboard"),
    ("applications", "💻", "Applications"),
    ("optimization", "⚡", "Optimization"),
    ("startup",      "🚀", "Startup Manager"),
    ("history",      "📜", "History"),
    ("settings",     "⚙", "Settings"),
]


class MainWindow(QMainWindow):
    """
    RAMGuard main application window.
    Coordinates all pages, background workers, and the optimization workflow.
    """

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config

        # ── Core services ──
        self._safety = ProcessSafetyManager()
        self._scanner = ProcessScanner(self._safety)
        self._optimizer = MemoryOptimizer(self._safety)
        self._processes: list[ProcessInfo] = []
        self._current_page = "dashboard"

        # ── Window setup ──
        self.setWindowTitle("RAMGuard — Smart & Safe Windows Memory Optimization")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self._apply_theme(config.theme)
        self._build_ui()
        self._start_workers()

    # ═══════════════════════════════════════════════════════════════
    #  UI Construction
    # ═══════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_row = QHBoxLayout(central)
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(0)

        # ── Sidebar ──
        self._sidebar = self._build_sidebar()
        main_row.addWidget(self._sidebar)

        # ── Stacked pages ──
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")
        main_row.addWidget(self._stack, 1)

        # ── Build pages ──
        self._dash_page = DashboardPage(on_optimize_clicked=self._trigger_optimization)
        self._apps_page = ApplicationsPage()
        self._opt_page = OptimizationPage()
        self._startup_page = StartupPage()
        self._history_page = HistoryPage()
        self._settings_page = SettingsPage(self._config)

        self._pages = {
            "dashboard":    self._dash_page,
            "applications": self._apps_page,
            "optimization": self._opt_page,
            "startup":      self._startup_page,
            "history":      self._history_page,
            "settings":     self._settings_page,
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        # ── Wire signals ──
        self._apps_page.close_process_requested.connect(self._close_single_process)
        self._apps_page.connect_refresh(self._start_scan)
        self._opt_page.optimize_requested.connect(self._trigger_optimization_mode)
        self._settings_page.theme_changed.connect(self._apply_theme)
        self._settings_page.interval_changed.connect(self._update_monitor_interval)

        # ── Status bar ──
        self._status = QStatusBar()
        self._status.setFixedHeight(28)
        self.setStatusBar(self._status)
        self._status_label = QLabel("RAMGuard — Monitoring Active  •  System Protection Enabled")
        self._status_label.setStyleSheet("color:#8b949e;font-size:11px;padding-left:8px;")
        self._status.addWidget(self._status_label)

        self._nav_to("dashboard")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo ──
        logo_area = QWidget()
        logo_area.setStyleSheet("background-color:#0d1117;border-bottom:1px solid #30363d;")
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 16, 16, 12)
        logo_layout.setSpacing(2)

        logo_row = QHBoxLayout()
        shield = QLabel("🛡")
        shield.setStyleSheet("font-size:22px;")
        name = QLabel("RAMGuard")
        name.setObjectName("sidebar_logo")
        name.setStyleSheet("color:#58a6ff;font-size:17px;font-weight:700;")
        logo_row.addWidget(shield)
        logo_row.addWidget(name)
        logo_row.addStretch()

        tagline = QLabel("Smart & Safe Memory Optimization")
        tagline.setObjectName("sidebar_tagline")
        tagline.setStyleSheet("color:#8b949e;font-size:10px;")
        tagline.setWordWrap(True)

        logo_layout.addLayout(logo_row)
        logo_layout.addWidget(tagline)
        layout.addWidget(logo_area)

        # ── Nav buttons ──
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background-color:#161b22;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(2)

        self._nav_buttons: dict[str, QPushButton] = {}
        for page_id, icon, label in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(False)
            btn.setFixedHeight(40)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, pid=page_id: self._nav_to(pid))
            self._nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout.addWidget(nav_widget, 1)

        # ── System protection badge ──
        prot_widget = QWidget()
        prot_widget.setStyleSheet("background-color:#161b22;border-top:1px solid #30363d;")
        prot_layout = QVBoxLayout(prot_widget)
        prot_layout.setContentsMargins(12, 10, 12, 10)

        self._ram_mini = QLabel("RAM: Initializing…")
        self._ram_mini.setStyleSheet("color:#58a6ff;font-size:11px;font-weight:600;")

        prot_lbl = QLabel("🔒  System Protection Active")
        prot_lbl.setStyleSheet("color:#2ecc71;font-size:10px;font-weight:600;")

        prot_sub = QLabel("RAMGuard protects critical system processes.")
        prot_sub.setStyleSheet("color:#484f58;font-size:9px;")
        prot_sub.setWordWrap(True)

        prot_layout.addWidget(self._ram_mini)
        prot_layout.addWidget(prot_lbl)
        prot_layout.addWidget(prot_sub)
        layout.addWidget(prot_widget)

        return sidebar

    # ═══════════════════════════════════════════════════════════════
    #  Navigation
    # ═══════════════════════════════════════════════════════════════

    def _nav_to(self, page_id: str) -> None:
        self._current_page = page_id
        page = self._pages.get(page_id)
        if page:
            self._stack.setCurrentWidget(page)

        for pid, btn in self._nav_buttons.items():
            btn.setStyleSheet(self._nav_btn_style(pid == page_id))

        # Refresh history when navigating to it
        if page_id == "history":
            self._history_page.refresh()

    @staticmethod
    def _nav_btn_style(active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #1f6feb22;
                    color: #58a6ff;
                    border: none;
                    border-left: 3px solid #58a6ff;
                    border-radius: 8px;
                    padding: 10px 16px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #21262d;
                color: #e6edf3;
            }
        """

    # ═══════════════════════════════════════════════════════════════
    #  Background Workers
    # ═══════════════════════════════════════════════════════════════

    def _start_workers(self) -> None:
        # ── Memory monitor ──
        self._monitor_worker = MonitorWorker(self._config.monitoring_interval)
        self._monitor_worker.snapshot_ready.connect(self._on_snapshot)
        self._monitor_worker.start()

        # ── Initial process scan ──
        QTimer.singleShot(500, self._start_scan)

    def _start_scan(self) -> None:
        self._scan_worker = ScanWorker(self._scanner)
        self._scan_worker.scan_complete.connect(self._on_scan_complete)
        self._scan_worker.error_occurred.connect(lambda e: logger.error("Scan error: %s", e))
        self._scan_worker.start()

    def _update_monitor_interval(self, seconds: int) -> None:
        if hasattr(self, "_monitor_worker"):
            self._monitor_worker.set_interval(seconds)

    # ═══════════════════════════════════════════════════════════════
    #  Slots — data updates
    # ═══════════════════════════════════════════════════════════════

    @pyqtSlot(object)
    def _on_snapshot(self, snap: MemorySnapshot) -> None:
        self._dash_page.update_snapshot(snap)
        self._ram_mini.setText(f"RAM: {snap.percent:.0f}%  |  {snap.available_display} free")

        # Trigger memory pressure notification
        if snap.pressure == MemoryPressure.CRITICAL:
            self._status_label.setText(
                "⚠  CRITICAL memory pressure detected — consider optimizing now!"
            )
            self._status_label.setStyleSheet("color:#e74c3c;font-size:11px;padding-left:8px;font-weight:600;")
        elif snap.pressure == MemoryPressure.HIGH:
            self._status_label.setText("⚠  High memory usage detected.")
            self._status_label.setStyleSheet("color:#e67e22;font-size:11px;padding-left:8px;")
        else:
            self._status_label.setText("RAMGuard — Monitoring Active  •  System Protection Enabled")
            self._status_label.setStyleSheet("color:#8b949e;font-size:11px;padding-left:8px;")

    @pyqtSlot(list)
    def _on_scan_complete(self, processes: list[ProcessInfo]) -> None:
        self._processes = processes
        self._apps_page.update_processes(processes)
        self._opt_page.update_processes(processes)
        logger.debug("Process list updated: %d processes", len(processes))

        # Schedule next auto-refresh
        interval_ms = self._config.get("process_list_refresh_interval_seconds", 5) * 1000
        QTimer.singleShot(interval_ms, self._start_scan)

    # ═══════════════════════════════════════════════════════════════
    #  Optimization Workflow
    # ═══════════════════════════════════════════════════════════════

    def _trigger_optimization(self) -> None:
        """Called from Dashboard Optimize button — uses current default mode."""
        mode = self._config.default_mode
        self._run_optimization_workflow(mode)

    def _trigger_optimization_mode(self, mode: str) -> None:
        """Called from Optimization page."""
        self._run_optimization_workflow(mode)

    def _run_optimization_workflow(self, mode: str) -> None:
        if not self._processes:
            QMessageBox.information(self, "No Data", "Process scan has not completed yet. Please wait a moment.")
            return

        # Determine candidates
        if mode == OptimizationMode.SMART:
            candidates = [
                p for p in self._processes
                if p.is_safe_to_close and p.memory_mb >= self._config.min_recommend_mb
            ]
            if not candidates:
                candidates = [
                    p for p in self._processes
                    if not p.is_protected and p.memory_mb >= self._config.min_recommend_mb
                ]
        else:
            candidates = [
                p for p in self._processes
                if not p.is_protected and p.memory_mb >= self._config.min_recommend_mb
            ]

        if not candidates:
            QMessageBox.information(
                self,
                "No Candidates Found",
                "RAMGuard did not find any applications that are safe to recommend for closing.\n\n"
                "Your system processes and protected applications have been preserved.",
            )
            return

        # ── Step 1: Confirmation dialog ──
        confirm_dlg = ConfirmationDialog(candidates, self)
        confirm_dlg.confirmed.connect(self._start_optimization)
        confirm_dlg.exec()

    @pyqtSlot(list)
    def _start_optimization(self, selected: list[ProcessInfo]) -> None:
        if not selected:
            return

        self._dash_page.set_optimize_enabled(False)
        self._opt_page.set_optimize_enabled(False)

        # ── Step 2: Progress dialog ──
        self._progress_dlg = ProgressDialog(self)
        self._progress_dlg.show()

        # ── Step 3: Run optimization in background ──
        mode = self._opt_page.current_mode
        self._opt_worker = OptimizeWorker(self._optimizer, selected, mode)
        self._opt_worker.progress.connect(self._progress_dlg.append_log)
        self._opt_worker.finished.connect(self._on_optimization_finished)
        self._opt_worker.error_occurred.connect(self._on_optimization_error)
        self._opt_worker.start()

    @pyqtSlot(object)
    def _on_optimization_finished(self, result) -> None:
        self._progress_dlg.finish()
        self._progress_dlg.close()

        # Save to DB
        try:
            save_optimization_result(result)
        except Exception as e:
            logger.error("Could not save optimization result: %s", e)

        # Re-enable optimize button
        self._dash_page.set_optimize_enabled(True)
        self._opt_page.set_optimize_enabled(True)

        # Refresh scan
        self._start_scan()

        # Show result dialog
        result_dlg = ResultDialog(result, self)
        result_dlg.exec()

    @pyqtSlot(str)
    def _on_optimization_error(self, error: str) -> None:
        self._progress_dlg.close()
        self._dash_page.set_optimize_enabled(True)
        self._opt_page.set_optimize_enabled(True)
        QMessageBox.critical(
            self, "Optimization Error",
            f"An error occurred during optimization:\n\n{error}\n\n"
            "RAMGuard has stopped the optimization to ensure system safety.",
        )

    def _close_single_process(self, proc: ProcessInfo) -> None:
        """Close a single process from the Applications page."""
        if proc.is_protected:
            QMessageBox.warning(
                self, "Protected Process",
                f"'{proc.name}' is a protected process and cannot be closed by RAMGuard.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Close",
            f"Close '{proc.name}' (PID {proc.pid}) — {proc.memory_display}?\n\n"
            "Make sure you have saved any open work.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._start_optimization([proc])

    # ═══════════════════════════════════════════════════════════════
    #  Theme
    # ═══════════════════════════════════════════════════════════════

    def _apply_theme(self, theme: str) -> None:
        self.setStyleSheet(get_stylesheet(theme))

    # ═══════════════════════════════════════════════════════════════
    #  Window lifecycle
    # ═══════════════════════════════════════════════════════════════

    def closeEvent(self, event) -> None:
        logger.info("RAMGuard shutting down…")
        if hasattr(self, "_monitor_worker"):
            self._monitor_worker.stop()
        event.accept()
