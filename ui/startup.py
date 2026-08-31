"""
RAMGuard Startup Page
Displays Windows startup programs with enable/disable controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from core.startup_manager import StartupManager
from utils.logger import get_logger

logger = get_logger("StartupPage")

IMPACT_COLORS = {
    "High": "#e74c3c",
    "Medium": "#f39c12",
    "Low": "#2ecc71",
}


class StartupPage(QWidget):
    """Displays and manages Windows startup applications."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._manager = StartupManager()
        self._entries: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Startup Manager")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        sub = QLabel("Manage applications that start with Windows")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(title)
        root.addWidget(sub)

        # ── Warning banner ──
        warn = QLabel("⚠  Changes to startup items require explicit user action. RAMGuard will not modify startup configuration automatically.")
        warn.setStyleSheet("background:#f39c1222;color:#f39c12;border:1px solid #f39c12;border-radius:8px;padding:10px 14px;font-size:11px;")
        warn.setWordWrap(True)
        root.addWidget(warn)

        # ── Toolbar ──
        bar = QHBoxLayout()
        self._refresh_btn = QPushButton("↻  Refresh")
        self._refresh_btn.setObjectName("secondary_btn")
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.clicked.connect(self.load_entries)

        self._count_lbl = QLabel("Loading…")
        self._count_lbl.setStyleSheet("color:#8b949e;font-size:12px;")

        bar.addWidget(self._refresh_btn)
        bar.addWidget(self._count_lbl)
        bar.addStretch()
        root.addLayout(bar)

        # ── Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Application", "Command", "Impact", "Status", "Action"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)

        hv = self._table.horizontalHeader()
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(self._table)

        self.load_entries()

    def load_entries(self) -> None:
        self._entries = self._manager.refresh()
        self._populate_table()
        self._count_lbl.setText(f"{len(self._entries)} startup entries found")

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            name = entry.get("name", "Unknown")
            cmd = entry.get("command", "")
            impact = entry.get("impact", "Low")
            enabled = entry.get("enabled", True)
            hive = entry.get("hive", "HKCU")

            items = [
                (0, name, "#e6edf3"),
                (1, cmd, "#8b949e"),
                (2, impact, IMPACT_COLORS.get(impact, "#8b949e")),
                (3, "Enabled" if enabled else "Disabled",
                 "#2ecc71" if enabled else "#8b949e"),
            ]

            for col, text, color in items:
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self._table.setItem(row, col, item)

            # Action button
            btn_text = "Disable" if enabled else "Enable"
            btn = QPushButton(btn_text)
            btn.setObjectName("secondary_btn" if enabled else "success_btn")
            btn.setFixedHeight(28)
            btn.setFixedWidth(80)
            btn.clicked.connect(lambda checked, n=name, h=hive, e=enabled, c=cmd:
                                 self._toggle_entry(n, h, e, c))
            self._table.setCellWidget(row, 4, btn)
            self._table.setRowHeight(row, 38)

    def _toggle_entry(self, name: str, hive: str, currently_enabled: bool, command: str) -> None:
        action = "disable" if currently_enabled else "enable"
        reply = QMessageBox.question(
            self,
            "Confirm Startup Change",
            f"Are you sure you want to {action} '{name}' from Windows startup?\n\n"
            "This will take effect on the next Windows restart.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if currently_enabled:
            ok = self._manager.disable(name, hive)
        else:
            ok = self._manager.enable(name, command, hive)

        if ok:
            QMessageBox.information(self, "Success", f"'{name}' startup entry {action}d successfully.")
            self.load_entries()
        else:
            QMessageBox.warning(
                self, "Failed",
                f"Could not {action} '{name}'.\n\n"
                "This may require administrator privileges. "
                "Try running RAMGuard as administrator.",
            )
