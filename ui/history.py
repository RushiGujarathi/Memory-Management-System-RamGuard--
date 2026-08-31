"""
RAMGuard History Page
Displays past optimization sessions from the database.
"""

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QDialog, QScrollArea, QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.database import load_optimization_history, clear_optimization_history
from utils.logger import get_logger

logger = get_logger("HistoryPage")


def _fmt_ts(ts: float) -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%d %b %Y  %I:%M %p")
    except Exception:
        return "—"


def _fmt_mb(mb: float) -> str:
    if not mb:
        return "—"
    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb:.0f} MB"


class SessionDetailDialog(QDialog):
    """Shows all processes closed in a single optimization session."""

    def __init__(self, session: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Optimization Session — {_fmt_ts(session['started_at'])}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._build_ui(session)

    def _build_ui(self, s: dict) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel(f"Session — {_fmt_ts(s['started_at'])}")
        title.setStyleSheet("font-size:16px;font-weight:700;color:#e6edf3;")
        root.addWidget(title)

        stats = QFrame()
        stats.setObjectName("card")
        sl = QHBoxLayout(stats)
        for label, val in [
            ("Mode", s.get("mode", "—")),
            ("Before", f"{s.get('percent_before', 0):.0f}%"),
            ("After", f"{s.get('percent_after', 0):.0f}%"),
            ("Freed", _fmt_mb(s.get("memory_freed_mb", 0))),
            ("Closed", str(s.get("apps_closed", 0))),
            ("Failed", str(s.get("apps_failed", 0))),
        ]:
            card = QVBoxLayout()
            v = QLabel(str(val))
            v.setStyleSheet("font-size:16px;font-weight:700;color:#e6edf3;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label)
            l.setStyleSheet("color:#8b949e;font-size:10px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card.addWidget(v)
            card.addWidget(l)
            sl.addLayout(card)
        root.addWidget(stats)

        if s.get("processes"):
            proc_title = QLabel("Closed Applications")
            proc_title.setStyleSheet("font-weight:600;color:#e6edf3;font-size:13px;")
            root.addWidget(proc_title)

            for p in s["processes"]:
                row = QHBoxLayout()
                icon = "✓" if p.get("success") else "✗"
                color = "#2ecc71" if p.get("success") else "#e74c3c"
                n = QLabel(f"{icon}  {p.get('name', '—')}")
                n.setStyleSheet(f"color:{color};font-size:12px;")
                m = QLabel(_fmt_mb(p.get("memory_mb", 0)))
                m.setStyleSheet("color:#58a6ff;font-size:12px;")
                row.addWidget(n, 3)
                row.addWidget(m, 1)
                if p.get("error_message"):
                    e = QLabel(p["error_message"])
                    e.setStyleSheet("color:#8b949e;font-size:10px;")
                    row.addWidget(e, 2)
                root.addLayout(row)

        close = QPushButton("Close")
        close.setObjectName("secondary_btn")
        close.clicked.connect(self.accept)
        root.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class HistoryPage(QWidget):
    """Optimization history page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._sessions: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("Optimization History")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        hdr.addWidget(title)
        hdr.addStretch()

        self._clear_btn = QPushButton("🗑  Clear History")
        self._clear_btn.setObjectName("danger_btn")
        self._clear_btn.clicked.connect(self._clear_history)
        hdr.addWidget(self._clear_btn)

        root.addLayout(hdr)

        sub = QLabel("View your past optimization actions")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(sub)

        # ── Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Date & Time", "Mode", "Before", "After",
            "Memory Freed", "Apps Closed", "Details",
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.itemDoubleClicked.connect(self._show_detail)

        hv = self._table.horizontalHeader()
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        root.addWidget(self._table)
        self.refresh()

    def refresh(self) -> None:
        self._sessions = load_optimization_history()
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._sessions))
        for row, s in enumerate(self._sessions):
            cols = [
                (0, _fmt_ts(s.get("started_at", 0)), "#e6edf3"),
                (1, s.get("mode", "—"), "#58a6ff"),
                (2, f"{s.get('percent_before', 0):.0f}%", "#e74c3c"),
                (3, f"{s.get('percent_after', 0):.0f}%", "#2ecc71"),
                (4, _fmt_mb(s.get("memory_freed_mb", 0)), "#2ecc71"),
                (5, str(s.get("apps_closed", 0)), "#e6edf3"),
                (6, "View Details", "#8b949e"),
            ]
            for col, text, color in cols:
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setData(Qt.ItemDataRole.UserRole, s)
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 38)

    def _show_detail(self, item: QTableWidgetItem) -> None:
        session = item.data(Qt.ItemDataRole.UserRole)
        if session:
            d = SessionDetailDialog(session, self)
            d.exec()

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to delete all optimization history?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_optimization_history()
            self.refresh()
            QMessageBox.information(self, "History Cleared", "Optimization history has been cleared.")
