"""
RAMGuard History Page
Displays past optimization sessions from the database.
Presentation redesigned to match the unified dark-navy design system.
All backend logic, database calls, and signals preserved exactly.
"""

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QDialog, QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.database import load_optimization_history, clear_optimization_history
from utils.logger import get_logger

logger = get_logger("HistoryPage")

# ── Design tokens ────────────────────────────────────────────────────────────
_BG_PANEL = "#081426"
_BG_INPUT = "#0b1930"
_ACCENT   = "#2563eb"
_ACCENT2  = "#38bdf8"
_SUCCESS  = "#10b981"
_WARNING  = "#f59e0b"
_DANGER   = "#ef4444"
_TEXT_HI  = "#f1f5f9"
_TEXT_MID = "#94a3b8"
_TEXT_LO  = "#64748b"
_BORDER   = "rgba(59, 130, 246, 0.20)"

_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: transparent;
        border: none;
        color: {_TEXT_HI};
        selection-background-color: rgba(37, 99, 235, 0.14);
        outline: none;
    }}
    QHeaderView {{
        background-color: {_BG_INPUT};
    }}
    QHeaderView::section {{
        background-color: {_BG_INPUT};
        color: {_TEXT_MID};
        border: none;
        border-bottom: 2px solid {_BORDER};
        border-right: 1px solid rgba(59,130,246,0.10);
        padding: 0px 14px;
        height: 42px;
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.9px;
    }}
    QTableWidget::item {{
        border: none;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        padding: 0px 14px;
    }}
    QTableWidget::item:selected {{
        background-color: rgba(37, 99, 235, 0.18);
    }}
    QTableWidget::item:hover {{
        background-color: rgba(37, 99, 235, 0.07);
    }}
    QScrollBar:vertical {{
        background: {_BG_PANEL};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(59, 130, 246, 0.30);
        border-radius: 4px;
        min-height: 28px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""


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


def _pct_color(pct: float) -> str:
    if pct >= 90:
        return _DANGER
    if pct >= 75:
        return _WARNING
    return _SUCCESS


def _center_btn(btn: QPushButton) -> QWidget:
    container = QWidget()
    container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    container.setStyleSheet("background: transparent;")
    h = QHBoxLayout(container)
    h.setContentsMargins(4, 0, 4, 0)
    h.setAlignment(Qt.AlignmentFlag.AlignCenter)
    h.addWidget(btn)
    return container


class SessionDetailDialog(QDialog):
    """Shows all processes closed in a single optimization session."""

    def __init__(self, session: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Optimization Session — {_fmt_ts(session['started_at'])}")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._build_ui(session)

    def _build_ui(self, s: dict) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        # Header
        title = QLabel(f"Session — {_fmt_ts(s['started_at'])}")
        title.setStyleSheet(f"font-size:18px; font-weight:800; color:{_TEXT_HI};")
        root.addWidget(title)

        # Stats card
        stats_card = QFrame()
        stats_card.setObjectName("card")
        sl = QHBoxLayout(stats_card)
        sl.setSpacing(0)

        stat_items = [
            ("Mode",   s.get("mode", "—"),                             _ACCENT2),
            ("Before", f"{s.get('percent_before', 0):.0f}%",           _DANGER),
            ("After",  f"{s.get('percent_after', 0):.0f}%",            _SUCCESS),
            ("Freed",  _fmt_mb(s.get("memory_freed_mb", 0)),           _ACCENT2),
            ("Closed", str(s.get("apps_closed", 0)),                   _TEXT_HI),
            ("Failed", str(s.get("apps_failed", 0)),                   _WARNING if s.get("apps_failed") else _TEXT_MID),
        ]

        for i, (label, val, color) in enumerate(stat_items):
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.setSpacing(4)
            v = QLabel(str(val))
            v.setStyleSheet(f"font-size:18px; font-weight:700; color:{color}; background:transparent;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label)
            l.setStyleSheet(f"color:{_TEXT_MID}; font-size:10px; letter-spacing:0.6px; background:transparent;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(v)
            col.addWidget(l)
            sl.addLayout(col)
            if i < len(stat_items) - 1:
                div = QFrame()
                div.setFrameShape(QFrame.Shape.VLine)
                div.setStyleSheet("color: rgba(59,130,246,0.15);")
                sl.addWidget(div)

        root.addWidget(stats_card)

        # Process list
        if s.get("processes"):
            proc_title = QLabel("Closed Applications")
            proc_title.setStyleSheet(f"font-weight:700; color:{_TEXT_HI}; font-size:14px;")
            root.addWidget(proc_title)

            for p in s["processes"]:
                row_w = QFrame()
                row_w.setStyleSheet(f"""
                    QFrame {{
                        background-color: {_BG_INPUT};
                        border: 1px solid {_BORDER};
                        border-radius: 8px;
                        padding: 6px 12px;
                    }}
                """)
                row = QHBoxLayout(row_w)
                row.setContentsMargins(0, 0, 0, 0)
                icon  = "✓" if p.get("success") else "✗"
                color = _SUCCESS if p.get("success") else _DANGER
                n = QLabel(f"{icon}  {p.get('name', '—')}")
                n.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600; background:transparent;")
                m = QLabel(_fmt_mb(p.get("memory_mb", 0)))
                m.setStyleSheet(f"color:{_ACCENT2}; font-size:12px; font-weight:600; background:transparent;")
                row.addWidget(n, 3)
                row.addWidget(m, 1)
                if p.get("error_message"):
                    e = QLabel(p["error_message"])
                    e.setStyleSheet(f"color:{_TEXT_LO}; font-size:10px; background:transparent;")
                    e.setWordWrap(True)
                    row.addWidget(e, 2)
                root.addWidget(row_w)

        close = QPushButton("Close")
        close.setObjectName("secondary_btn")
        close.setFixedHeight(36)
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
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Header ──
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title = QLabel("History")
        title.setObjectName("section_title")
        sub = QLabel("View your past optimization actions")
        sub.setObjectName("section_sub")
        title_col.addWidget(title)
        title_col.addWidget(sub)

        self._clear_btn = QPushButton("🗑  Clear History")
        self._clear_btn.setObjectName("danger_btn")
        self._clear_btn.setFixedHeight(38)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_history)

        hdr_row.addLayout(title_col, 1)
        hdr_row.addWidget(self._clear_btn, 0, Qt.AlignmentFlag.AlignBottom)
        root.addLayout(hdr_row)

        # ── Empty state label (hidden when data present) ──
        self._empty_lbl = QLabel("No optimization history yet.\nRun your first optimization to see results here.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:14px; line-height:1.8;")
        self._empty_lbl.setVisible(False)
        root.addWidget(self._empty_lbl)

        # ── Table card ──
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {_BG_PANEL};
                border: 1px solid {_BORDER};
                border-radius: 14px;
                padding: 0px;
            }}
        """)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

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
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setStyleSheet(_TABLE_STYLE)

        hv = self._table.horizontalHeader()
        hv.setFixedHeight(42)
        hv.setHighlightSections(False)
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self._table.verticalHeader().setDefaultSectionSize(48)
        self._table.verticalHeader().setMinimumSectionSize(48)

        tc_layout.addWidget(self._table)
        root.addWidget(table_card, 1)

        self.refresh()

    def refresh(self) -> None:
        self._sessions = load_optimization_history()
        self._populate_table()

    def _populate_table(self) -> None:
        has_data = bool(self._sessions)
        self._empty_lbl.setVisible(not has_data)

        self._table.setRowCount(len(self._sessions))
        self._table.blockSignals(True)

        for row, s in enumerate(self._sessions):
            self._table.setRowHeight(row, 48)

            pct_before = s.get("percent_before", 0)
            pct_after  = s.get("percent_after", 0)

            cols = [
                (0, _fmt_ts(s.get("started_at", 0)), _TEXT_HI),
                (1, s.get("mode", "—"),               _ACCENT2),
                (2, f"{pct_before:.0f}%",             _pct_color(pct_before)),
                (3, f"{pct_after:.0f}%",              _pct_color(pct_after)),
                (4, _fmt_mb(s.get("memory_freed_mb", 0)), _SUCCESS),
                (5, str(s.get("apps_closed", 0)),     _TEXT_HI),
            ]

            for col, text, color in cols:
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setData(Qt.ItemDataRole.UserRole, s)
                self._table.setItem(row, col, item)

            # Col 6: "View Details" button
            detail_btn = QPushButton("View Details")
            detail_btn.setObjectName("secondary_btn")
            detail_btn.setFixedHeight(30)
            detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            detail_btn.clicked.connect(lambda checked, sess=s: self._open_detail(sess))
            self._table.setCellWidget(row, 6, _center_btn(detail_btn))

        self._table.blockSignals(False)

    def _open_detail(self, session: dict) -> None:
        d = SessionDetailDialog(session, self)
        d.exec()

    def _show_detail(self, item: QTableWidgetItem) -> None:
        # Legacy: kept for double-click compatibility
        session = item.data(Qt.ItemDataRole.UserRole)
        if session:
            self._open_detail(session)

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
