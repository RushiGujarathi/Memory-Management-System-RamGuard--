"""
RAMGuard Startup Manager Page
Displays Windows startup programs with enable/disable controls.
Presentation redesigned to match the unified dark-navy design system.
All backend logic and signals preserved exactly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QHeaderView, QMessageBox,
    QAbstractItemView, QFrame, QTableWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.startup_manager import StartupManager
from utils.logger import get_logger
from ui.styles import rgba

logger = get_logger("StartupPage")

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

# Impact level → (accent color, label)
IMPACT_MAP = {
    "High":   (_DANGER,  "High"),
    "Medium": (_WARNING, "Medium"),
    "Low":    (_SUCCESS, "Low"),
}


def _pill_lbl(text: str, color: str) -> QLabel:
    """Returns a compact styled pill QLabel."""
    lbl = QLabel(text)
    lbl.setFixedHeight(22)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {rgba(color, '1a')};"
        f"color: {color};"
        f"border: 1px solid {rgba(color, '55')};"
        f"border-radius: 9px;"
        f"padding: 0px 10px;"
        f"font-size: 10px;"
        f"font-weight: 700;"
        f"letter-spacing: 0.5px;"
    )
    return lbl


def _center_widget(inner: QWidget) -> QWidget:
    """Wraps a widget in a transparent container for centered table placement."""
    container = QWidget()
    container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    container.setStyleSheet("background: transparent;")
    h = QHBoxLayout(container)
    h.setContentsMargins(4, 0, 4, 0)
    h.setAlignment(Qt.AlignmentFlag.AlignCenter)
    h.addWidget(inner)
    return container


class StartupPage(QWidget):
    """Displays and manages Windows startup applications."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._manager = StartupManager()
        self._entries: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Header ──
        title = QLabel("Startup Manager")
        title.setObjectName("section_title")
        sub = QLabel("Manage applications that start with Windows")
        sub.setObjectName("section_sub")
        root.addWidget(title)
        root.addWidget(sub)

        # ── Warning banner ──
        warn_card = QFrame()
        warn_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(245, 158, 11, 0.08);
                border: 1px solid rgba(245, 158, 11, 0.30);
                border-radius: 10px;
                padding: 10px 16px;
            }}
        """)
        warn_layout = QHBoxLayout(warn_card)
        warn_layout.setSpacing(12)
        warn_icon = QLabel("⚠")
        warn_icon.setStyleSheet(f"color:{_WARNING}; font-size:18px; background:transparent;")
        warn_text = QLabel(
            "Changes to startup items require explicit user action. "
            "RAMGuard will not modify startup configuration automatically."
        )
        warn_text.setStyleSheet(f"color:{_WARNING}; font-size:11px; font-weight:500; background:transparent;")
        warn_text.setWordWrap(True)
        warn_layout.addWidget(warn_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        warn_layout.addWidget(warn_text, 1)
        root.addWidget(warn_card)

        # ── Toolbar ──
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self._count_lbl = QLabel("Loading…")
        self._count_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:12px;")

        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("secondary_btn")
        self._refresh_btn.setFixedHeight(36)
        self._refresh_btn.setFixedWidth(110)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.load_entries)

        bar.addWidget(self._count_lbl)
        bar.addStretch()
        bar.addWidget(self._refresh_btn)
        root.addLayout(bar)

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
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Application", "Command", "Impact", "Status", "Action"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setStyleSheet(f"""
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
        """)

        hv = self._table.horizontalHeader()
        hv.setFixedHeight(42)
        hv.setHighlightSections(False)
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 100)
        hv.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 110)
        hv.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 110)

        self._table.verticalHeader().setDefaultSectionSize(48)
        self._table.verticalHeader().setMinimumSectionSize(48)

        tc_layout.addWidget(self._table)
        root.addWidget(table_card, 1)

        self.load_entries()

    def load_entries(self) -> None:
        self._entries = self._manager.refresh()
        self._populate_table()
        count = len(self._entries)
        self._count_lbl.setText(f"{count} startup entr{'y' if count == 1 else 'ies'} found")

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._entries))
        self._table.blockSignals(True)

        for row, entry in enumerate(self._entries):
            name    = entry.get("name", "Unknown")
            cmd     = entry.get("command", "")
            impact  = entry.get("impact", "Low")
            enabled = entry.get("enabled", True)
            hive    = entry.get("hive", "HKCU")

            self._table.setRowHeight(row, 48)

            # Col 0: Application name
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor(_TEXT_HI))
            self._table.setItem(row, 0, name_item)

            # Col 1: Command (truncated)
            cmd_short = cmd[:60] + "…" if len(cmd) > 60 else cmd
            cmd_item = QTableWidgetItem(cmd_short)
            cmd_item.setForeground(QColor(_TEXT_LO))
            cmd_item.setToolTip(cmd)
            self._table.setItem(row, 1, cmd_item)

            # Col 2: Impact pill
            impact_color, impact_label = IMPACT_MAP.get(impact, (_TEXT_MID, impact))
            pill = _pill_lbl(impact_label, impact_color)
            self._table.setCellWidget(row, 2, _center_widget(pill))

            # Col 3: Status pill
            status_color  = _SUCCESS if enabled else _TEXT_LO
            status_text   = "Enabled"  if enabled else "Disabled"
            status_pill   = _pill_lbl(status_text, status_color)
            self._table.setCellWidget(row, 3, _center_widget(status_pill))

            # Col 4: Action button
            btn_text = "Disable" if enabled else "Enable"
            btn_obj  = "danger_btn" if enabled else "success_btn"
            btn = QPushButton(btn_text)
            btn.setObjectName(btn_obj)
            btn.setFixedHeight(30)
            btn.setFixedWidth(80)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(
                lambda checked, n=name, h=hive, e=enabled, c=cmd:
                self._toggle_entry(n, h, e, c)
            )
            self._table.setCellWidget(row, 4, _center_widget(btn))

        self._table.blockSignals(False)

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
