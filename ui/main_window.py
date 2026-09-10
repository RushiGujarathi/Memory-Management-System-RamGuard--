"""
RAMGuard Main Window
MVC-style orchestrator with custom frameless titlebar, glowing sidebar,
and stacked page container matching the reference UI design.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QMessageBox, QSizePolicy,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

from core.memory_monitor import MemorySnapshot, MemoryPressure
from core.process_scanner import ProcessScanner, ProcessInfo
from core.safety_manager import ProcessSafetyManager
from core.optimizer import MemoryOptimizer, OptimizationMode
from config.app_config import AppConfig
from database.database import save_optimization_result

from ui.styles import get_stylesheet
from ui.icon_helper import IconHelper
from ui.custom_widgets import ProgressBarWidget
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


class TitleBar(QWidget):
    """Custom frameless dark title bar with RAMGuard branding and controls."""

    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__(parent_window)
        self._window = parent_window
        self._drag_pos = QPoint()
        self.setObjectName("title_bar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 16, 8)
        layout.setSpacing(14)

        # ── Left: Brand Shield & Title ──
        self._shield_lbl = QLabel()
        self._shield_lbl.setPixmap(IconHelper.create_shield_icon(36))
        self._shield_lbl.setFixedSize(36, 36)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)

        brand_title = QLabel("RAMGuard")
        brand_title.setStyleSheet("font-size:16px; font-weight:800; color:#ffffff; letter-spacing:0.2px;")

        brand_sub = QLabel("Smart & Safe Memory Optimization")
        brand_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")

        brand_col.addWidget(brand_title)
        brand_col.addWidget(brand_sub)

        layout.addWidget(self._shield_lbl)
        layout.addLayout(brand_col)
        layout.addStretch()

        # ── Right: System Status Pill Badge ──
        self._status_pill = QLabel("● System Healthy")
        self._status_pill.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 13px;
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 700;
        """)
        layout.addWidget(self._status_pill)
        layout.addSpacing(10)

        # ── Window Control Buttons ──
        btn_box = QHBoxLayout()
        btn_box.setSpacing(4)

        min_btn = QPushButton("─")
        min_btn.setObjectName("title_bar_btn")
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(self._window.showMinimized)

        self._max_btn = QPushButton("◻")
        self._max_btn.setObjectName("title_bar_btn")
        self._max_btn.setToolTip("Maximize / Restore")
        self._max_btn.clicked.connect(self._toggle_max_restore)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("title_bar_close_btn")
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._window.close)

        btn_box.addWidget(min_btn)
        btn_box.addWidget(self._max_btn)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def _toggle_max_restore(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
            self._max_btn.setText("◻")
        else:
            self._window.showMaximized()
            self._max_btn.setText("❐")

    def set_status(self, text: str, color: str, bg_alpha: str = "15", border_alpha: str = "35") -> None:
        self._status_pill.setText(f"● {text}")
        self._status_pill.setStyleSheet(f"""
            background-color: {color}{bg_alpha};
            color: {color};
            border: 1px solid {color}{border_alpha};
            border-radius: 13px;
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 700;
        """)

    # ── Mouse Dragging for Frameless Window ──
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self._window.isMaximized():
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_max_restore()
            event.accept()


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

        # ── Frameless Window Flags & Sizing ──
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle("RAMGuard — Smart & Safe Memory Optimization")
        self.setMinimumSize(1150, 750)
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
        root_col = QVBoxLayout(central)
        root_col.setContentsMargins(0, 0, 0, 0)
        root_col.setSpacing(0)

        # ── Top Titlebar ──
        self._title_bar = TitleBar(self)
        root_col.addWidget(self._title_bar)

        # ── Main Content Split (Sidebar + Stack) ──
        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)

        # Sidebar
        self._sidebar = self._build_sidebar()
        body_row.addWidget(self._sidebar)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")
        body_row.addWidget(self._stack, 1)
        root_col.addLayout(body_row, 1)

        # ── Build pages ──
        self._dash_page = DashboardPage(
            on_optimize_clicked=self._show_applications_page,
            on_navigate=self._nav_to,
            on_one_click_optimize_clicked=self._trigger_optimization,
        )
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

        self._nav_to("dashboard")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)

        # ── Nav buttons list ──
        nav_items = [
            ("dashboard",    "Dashboard",       IconHelper.create_home_icon(20, "#ffffff")),
            ("applications", "Applications",    IconHelper.create_grid_icon(20, "#8c9eb5")),
            ("startup",      "Startup Manager", IconHelper.create_rocket_icon(20, "#8c9eb5")),
            ("history",      "History",         IconHelper.create_clock_icon(20, "#8c9eb5")),
            ("settings",     "Settings",        IconHelper.create_gear_icon(20, "#8c9eb5")),
        ]

        self._nav_buttons: dict[str, QPushButton] = {}
        for page_id, label, icon_px in nav_items:
            btn = QPushButton(f"   {label}")
            btn.setObjectName("nav_btn")
            btn.setIcon(QIcon(icon_px))
            btn.setIconSize(icon_px.size())
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, pid=page_id: self._nav_to(pid))
            self._nav_buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # ── Bottom RAM Mini Card ──
        ram_card = QFrame()
        ram_card.setObjectName("card")
        ram_card.setStyleSheet("""
            QFrame#card {
                background-color: #0b1526;
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 14px;
            }
        """)
        rc_layout = QVBoxLayout(ram_card)
        rc_layout.setContentsMargins(12, 10, 12, 10)
        rc_layout.setSpacing(6)

        # Top row: chip icon + "RAM Usage" / "96%"
        rc_top = QHBoxLayout()
        rc_top.setSpacing(8)

        chip_icon = QLabel()
        chip_icon.setPixmap(IconHelper.create_chip_icon(26, color="#38bdf8", bg_color="#0e1f3d"))
        chip_icon.setFixedSize(26, 26)

        rc_text_col = QVBoxLayout()
        rc_text_col.setSpacing(0)
        rc_title = QLabel("RAM Usage")
        rc_title.setStyleSheet("color:#8c9eb5; font-size:10px;")
        self._ram_mini_pct = QLabel("0%")
        self._ram_mini_pct.setStyleSheet("color:#ffffff; font-size:16px; font-weight:700;")
        rc_text_col.addWidget(rc_title)
        rc_text_col.addWidget(self._ram_mini_pct)

        rc_top.addWidget(chip_icon)
        rc_top.addLayout(rc_text_col)
        rc_top.addStretch()
        rc_layout.addLayout(rc_top)

        # Mini Gradient Progress Bar (Cyan to Purple)
        self._ram_mini_bar = ProgressBarWidget("#00d2ff", end_color_hex="#a855f7", height=6)
        rc_layout.addWidget(self._ram_mini_bar)

        # Free / Used subtext
        self._ram_mini_sub = QLabel("0.0 GB Free / 0.0 GB Used")
        self._ram_mini_sub.setStyleSheet("color:#8c9eb5; font-size:10px;")
        rc_layout.addWidget(self._ram_mini_sub)

        layout.addWidget(ram_card)
        layout.addSpacing(6)

        # ── Bottom Shield Protection Card ──
        prot_card = QFrame()
        prot_layout = QHBoxLayout(prot_card)
        prot_layout.setContentsMargins(4, 4, 4, 4)
        prot_layout.setSpacing(8)

        prot_icon = QLabel()
        prot_icon.setPixmap(IconHelper.create_shield_small(24, color="#10b981", bg_color="#0d2b20"))
        prot_icon.setFixedSize(24, 24)

        prot_text_col = QVBoxLayout()
        prot_text_col.setSpacing(1)
        prot_title = QLabel("System Protection Active")
        prot_title.setStyleSheet("color:#10b981; font-size:11px; font-weight:700;")
        prot_desc = QLabel("Your system is safe and optimized.")
        prot_desc.setStyleSheet("color:#64748b; font-size:9px;")
        prot_desc.setWordWrap(True)

        prot_text_col.addWidget(prot_title)
        prot_text_col.addWidget(prot_desc)

        prot_layout.addWidget(prot_icon)
        prot_layout.addLayout(prot_text_col, 1)
        layout.addWidget(prot_card)

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
            is_active = (pid == page_id)
            btn.setProperty("active", "true" if is_active else "false")
            # Update icons for active vs inactive
            color = "#ffffff" if is_active else "#8c9eb5"
            icon_map = {
                "dashboard":    IconHelper.create_home_icon(20, color),
                "applications": IconHelper.create_grid_icon(20, color),
                "optimization": IconHelper.create_lightning_icon(20, color),
                "startup":      IconHelper.create_rocket_icon(20, color),
                "history":      IconHelper.create_clock_icon(20, color),
                "settings":     IconHelper.create_gear_icon(20, color),
            }
            if pid in icon_map:
                px = icon_map[pid]
                btn.setIcon(QIcon(px))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if page_id == "history":
            self._history_page.refresh()

    # ═══════════════════════════════════════════════════════════════
    #  Background Workers
    # ═══════════════════════════════════════════════════════════════

    def _start_workers(self) -> None:
        self._monitor_worker = MonitorWorker(self._config.monitoring_interval)
        self._monitor_worker.snapshot_ready.connect(self._on_snapshot)
        self._monitor_worker.start()

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
        self._apps_page.update_pressure_status(snap.pressure.value)

        # Update sidebar mini card
        self._ram_mini_pct.setText(f"{snap.percent:.0f}%")
        self._ram_mini_bar.set_percent(snap.percent)
        self._ram_mini_sub.setText(f"{snap.available_display} Free / {snap.used_display} Used")

        # Update top title bar status pill
        status_map = {
            "NORMAL": ("System Healthy", "#10b981"),
            "MODERATE": ("System Healthy", "#10b981"),
            "HIGH": ("High Memory Usage", "#f97316"),
            "CRITICAL": ("Critical — Optimize Now!", "#ef4444"),
        }
        status_text, status_color = status_map.get(snap.pressure.value, ("System Healthy", "#10b981"))
        self._title_bar.set_status(status_text, status_color)

    @pyqtSlot(list)
    def _on_scan_complete(self, processes: list[ProcessInfo]) -> None:
        self._processes = processes
        self._apps_page.update_processes(processes)
        self._opt_page.update_processes(processes)
        logger.debug("Process list updated: %d processes", len(processes))

        interval_ms = self._config.get("process_list_refresh_interval_seconds", 5) * 1000
        QTimer.singleShot(interval_ms, self._start_scan)

    # ═══════════════════════════════════════════════════════════════
    #  Optimization Workflow
    # ═══════════════════════════════════════════════════════════════

    def _show_applications_page(self) -> None:
        self._nav_to("applications")

    def _trigger_optimization(self) -> None:
        mode = self._config.default_mode
        self._run_optimization_workflow(mode)

    def _trigger_optimization_mode(self, mode: str) -> None:
        self._run_optimization_workflow(mode)

    def _run_optimization_workflow(self, mode: str) -> None:
        if not self._processes:
            QMessageBox.information(self, "No Data", "Process scan has not completed yet. Please wait a moment.")
            return

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

        confirm_dlg = ConfirmationDialog(candidates, self)
        confirm_dlg.confirmed.connect(self._start_optimization)
        confirm_dlg.exec()

    @pyqtSlot(list)
    def _start_optimization(self, selected: list[ProcessInfo]) -> None:
        if not selected:
            return

        self._dash_page.set_optimize_enabled(False)
        self._opt_page.set_optimize_enabled(False)

        self._progress_dlg = ProgressDialog(self)
        self._progress_dlg.show()

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

        try:
            save_optimization_result(result)
        except Exception as e:
            logger.error("Could not save optimization result: %s", e)

        self._dash_page.set_optimize_enabled(True)
        self._opt_page.set_optimize_enabled(True)

        self._start_scan()

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
