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
    QComboBox, QLineEdit, QCheckBox, QMenu, QApplication, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.startup_manager import StartupManager
from ui.icon_helper import IconHelper
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

# Filter dropdown options
_FILTER_OPTIONS = ["All", "Enabled", "Disabled", "High Impact", "Medium Impact", "Low Impact"]

# Mode-specific action button label
_ACTION_COL_WIDTH = 130
_CHECK_COL_WIDTH = 52


def _styled_checkbox() -> QCheckBox:
    """Checkbox with an explicit custom-drawn indicator so it always renders
    as a complete, closed square regardless of the app's global QCheckBox
    styling.

    NOTE: The previous version used a fractional border width (1.5px) on
    QCheckBox::indicator combined with border-radius. Qt's stylesheet
    rasterizer can fail to paint the right/bottom edge cleanly at fractional
    widths, which produced a half-open "bracket" look instead of a full
    square. Using an integer border width and explicit subcontrol
    positioning fixes this reliably.
    """
    cb = QCheckBox()
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setFixedSize(26, 26)
    cb.setStyleSheet(f"""
        QCheckBox {{
            background: transparent;
            spacing: 0px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid {rgba(_ACCENT2, '88')};
            background-color: {_BG_INPUT};
            image: none;
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {_ACCENT2};
            background-color: rgba(56, 189, 248, 0.10);
        }}
        QCheckBox::indicator:checked {{
            background-color: {_ACCENT};
            border: 2px solid {_ACCENT};
            image: none;
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {_ACCENT2};
            border: 2px solid {_ACCENT2};
            image: none;
        }}
    """)
    return cb


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
    h.setContentsMargins(0, 0, 0, 0)
    h.setAlignment(Qt.AlignmentFlag.AlignCenter)
    h.addWidget(inner)
    return container


def _icon_box(emoji: str, color: str, size: int = 40) -> QFrame:
    """Small rounded square icon badge used in page headers."""
    box = QFrame()
    box.setFixedSize(size, size)
    box.setStyleSheet(
        f"background-color: {rgba(color, '1f')};"
        f"border: 1px solid {rgba(color, '55')};"
        f"border-radius: 10px;"
    )
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl = QLabel(emoji)
    lbl.setStyleSheet(f"font-size:18px; background:transparent; border:none; color:{color};")
    lay.addWidget(lbl)
    return box


class StartupPage(QWidget):
    """Displays and manages Windows startup applications."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._manager = StartupManager()
        self._entries: list[dict] = []
        self._filtered_entries: list[dict] = []
        self._row_checks: list[tuple[dict, QCheckBox]] = []
        self._build_ui()

    # ── UI construction ──────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Header ──
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_box = _icon_box("🚀", _ACCENT)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Startup Manager")
        title.setObjectName("section_title")
        sub = QLabel("Manage applications that start with Windows")
        sub.setObjectName("section_sub")
        title_col.addWidget(title)
        title_col.addWidget(sub)

        header_row.addWidget(icon_box, 0, Qt.AlignmentFlag.AlignTop)
        header_row.addLayout(title_col)
        header_row.addStretch()

        self._count_lbl = QLabel("Showing 0 of 0 startup entries")
        self._count_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:12px;")
        header_row.addWidget(self._count_lbl, 0, Qt.AlignmentFlag.AlignTop)

        root.addLayout(header_row)

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

        # ── Toolbar: Filter + Search + Refresh ──
        bar = QHBoxLayout()
        bar.setSpacing(10)

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:12px; font-weight:600;")

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(_FILTER_OPTIONS)
        self._filter_combo.setFixedHeight(36)
        self._filter_combo.setFixedWidth(160)
        self._filter_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {_BG_INPUT};
                color: {_TEXT_HI};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background-color: {_BG_INPUT};
                color: {_TEXT_HI};
                selection-background-color: rgba(37, 99, 235, 0.25);
                border: 1px solid {_BORDER};
                outline: none;
            }}
        """)
        self._filter_combo.currentIndexChanged.connect(self._apply_filters)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍   Search startup applications…")
        self._search_input.setFixedHeight(36)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_BG_INPUT};
                color: {_TEXT_HI};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {rgba(_ACCENT, '88')}; }}
        """)
        self._search_input.textChanged.connect(self._apply_filters)

        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("secondary_btn")
        self._refresh_btn.setFixedHeight(36)
        self._refresh_btn.setFixedWidth(110)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.load_entries)

        bar.addWidget(filter_lbl)
        bar.addWidget(self._filter_combo)
        bar.addWidget(self._search_input, 1)
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
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["", "Application", "Command", "Impact", "Status", "Action"])
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
        hv.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, _CHECK_COL_WIDTH)
        hv.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hv.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 100)
        hv.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 110)
        hv.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, _ACTION_COL_WIDTH)

        self._table.verticalHeader().setDefaultSectionSize(48)
        self._table.verticalHeader().setMinimumSectionSize(48)

        tc_layout.addWidget(self._table)
        root.addWidget(table_card, 1)

        # ── Bottom action bar ──
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self._view_details_btn = QPushButton("👁  View Details")
        self._view_details_btn.setObjectName("secondary_btn")
        self._view_details_btn.setFixedHeight(38)
        self._view_details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_details_btn.clicked.connect(self._on_view_selected)

        self._close_selected_btn = QPushButton("🗑  Close Selected")
        self._close_selected_btn.setObjectName("danger_btn")
        self._close_selected_btn.setFixedHeight(38)
        self._close_selected_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_selected_btn.clicked.connect(self._on_bulk_disable)

        bottom_bar.addStretch()
        bottom_bar.addWidget(self._view_details_btn)
        bottom_bar.addWidget(self._close_selected_btn)
        root.addLayout(bottom_bar)

        self.load_entries()

    # ── Data loading / filtering ─────────────────────────────────────────
    def load_entries(self) -> None:
        self._entries = self._manager.refresh()
        self._apply_filters()

    def _apply_filters(self) -> None:
        self._filtered_entries = self._filter_entries()
        self._populate_table()
        total = len(self._entries)
        shown = len(self._filtered_entries)
        self._count_lbl.setText(f"Showing {shown} of {total} startup entr{'y' if total == 1 else 'ies'}")

    def _filter_entries(self) -> list[dict]:
        text = self._search_input.text().strip().lower() if hasattr(self, "_search_input") else ""
        active_filter = self._filter_combo.currentText() if hasattr(self, "_filter_combo") else "All"

        result = []
        for entry in self._entries:
            name = entry.get("name", "").lower()
            command = entry.get("command", "").lower()
            if text and text not in name and text not in command:
                continue

            enabled = entry.get("enabled", True)
            impact = entry.get("impact", "Low")

            if active_filter == "Enabled" and not enabled:
                continue
            if active_filter == "Disabled" and enabled:
                continue
            if active_filter == "High Impact" and impact != "High":
                continue
            if active_filter == "Medium Impact" and impact != "Medium":
                continue
            if active_filter == "Low Impact" and impact != "Low":
                continue

            result.append(entry)
        return result

    # ── Table population ─────────────────────────────────────────────────
    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._filtered_entries))
        self._table.blockSignals(True)
        self._row_checks = []

        for row, entry in enumerate(self._filtered_entries):
            name    = entry.get("name", "Unknown")
            cmd     = entry.get("command", "")
            impact  = entry.get("impact", "Low")
            enabled = entry.get("enabled", True)
            hive    = entry.get("hive", "HKCU")

            self._table.setRowHeight(row, 48)

            # Col 0: Selection checkbox
            cb = _styled_checkbox()
            self._table.setCellWidget(row, 0, _center_widget(cb))
            self._row_checks.append((entry, cb))

            # Col 1: Application name (clean, professional text block)
            name_container = QWidget()
            name_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            name_container.setStyleSheet("background: transparent;")
            name_layout = QHBoxLayout(name_container)
            name_layout.setContentsMargins(18, 0, 8, 0)
            name_layout.setSpacing(10)
            name_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            app_icon = QLabel()
            app_icon.setPixmap(IconHelper.get_process_icon(name, 22))
            app_icon.setFixedSize(22, 22)
            app_icon.setStyleSheet("background: transparent;")

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                "color: #e2e8f0;"
                "font-size: 13px;"
                "font-weight: 600;"
                "background: transparent;"
            )
            name_lbl.setWordWrap(False)
            name_lbl.setToolTip(name)

            name_layout.addWidget(app_icon, 0, Qt.AlignmentFlag.AlignVCenter)
            name_layout.addWidget(name_lbl, 1, Qt.AlignmentFlag.AlignVCenter)
            self._table.setCellWidget(row, 1, name_container)

            # Col 2: Command (truncated)
            cmd_short = cmd[:80] + "…" if len(cmd) > 80 else cmd
            cmd_item = QTableWidgetItem(cmd_short)
            cmd_item.setForeground(QColor(_TEXT_LO))
            cmd_item.setToolTip(cmd)
            self._table.setItem(row, 2, cmd_item)

            # Col 3: Impact pill
            impact_color, impact_label = IMPACT_MAP.get(impact, (_TEXT_MID, impact))
            pill = _pill_lbl(impact_label, impact_color)
            self._table.setCellWidget(row, 3, _center_widget(pill))

            # Col 4: Status pill
            status_color  = _SUCCESS if enabled else _TEXT_LO
            status_text   = "Enabled"  if enabled else "Disabled"
            status_pill   = _pill_lbl(status_text, status_color)
            self._table.setCellWidget(row, 4, _center_widget(status_pill))

            # Col 5: Action cluster (Disable/Enable + kebab menu with Details/Copy)
            action_container = QWidget()
            action_container.setStyleSheet("background: transparent;")
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(6)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_text = "Disable" if enabled else "Enable"
            btn_obj  = "danger_btn" if enabled else "success_btn"
            toggle_btn = QPushButton(btn_text)
            toggle_btn.setObjectName(btn_obj)
            toggle_btn.setFixedHeight(30)
            toggle_btn.setMinimumWidth(76)
            toggle_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setStyleSheet("padding: 0px 10px; font-size: 11px;")
            toggle_btn.clicked.connect(
                lambda checked, n=name, h=hive, e=enabled, c=cmd:
                self._toggle_entry(n, h, e, c)
            )

            kebab_btn = QPushButton("⋮")
            kebab_btn.setObjectName("secondary_btn")
            kebab_btn.setFixedSize(30, 30)
            kebab_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            kebab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            kebab_btn.setStyleSheet("padding: 0px; font-size: 14px;")
            kebab_btn.clicked.connect(lambda checked, e=entry, b=kebab_btn: self._open_row_menu(e, b))

            action_layout.addWidget(toggle_btn)
            action_layout.addWidget(kebab_btn)

            self._table.setCellWidget(row, 5, action_container)

        self._table.blockSignals(False)

    # ── Row-level kebab menu ─────────────────────────────────────────────
    def _open_row_menu(self, entry: dict, anchor: QPushButton) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {_BG_INPUT};
                color: {_TEXT_HI};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background-color: rgba(37, 99, 235, 0.20);
            }}
        """)
        view_action = menu.addAction("View Details")
        copy_action = menu.addAction("Copy Command")
        chosen = menu.exec(anchor.mapToGlobal(anchor.rect().bottomRight()))
        if chosen == view_action:
            self._show_details([entry])
        elif chosen == copy_action:
            QApplication.clipboard().setText(entry.get("command", ""))

    # ── Details viewing ──────────────────────────────────────────────────
    def _show_details(self, entries: list[dict]) -> None:
        if not entries:
            QMessageBox.information(
                self, "No Selection",
                "Select at least one startup entry to view its details."
            )
            return

        blocks = []
        for e in entries:
            blocks.append(
                f"Application: {e.get('name', 'Unknown')}\n"
                f"Command: {e.get('command', '')}\n"
                f"Registry Hive: {e.get('hive', 'HKCU')}\n"
                f"Impact: {e.get('impact', 'Low')}\n"
                f"Status: {'Enabled' if e.get('enabled', True) else 'Disabled'}"
            )
        QMessageBox.information(self, "Startup Entry Details", "\n\n".join(blocks))

    def _on_view_selected(self) -> None:
        selected = [e for e, cb in self._row_checks if cb.isChecked()]
        self._show_details(selected)

    # ── Single toggle (unchanged backend behaviour) ──────────────────────
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

    # ── Bulk disable ("Close Selected") ──────────────────────────────────
    def _on_bulk_disable(self) -> None:
        selected = [e for e, cb in self._row_checks if cb.isChecked()]
        if not selected:
            QMessageBox.information(
                self, "No Selection",
                "Select at least one startup entry using the checkboxes first."
            )
            return

        to_disable = [e for e in selected if e.get("enabled", True)]
        if not to_disable:
            QMessageBox.information(
                self, "Nothing To Do",
                "All selected entries are already disabled."
            )
            return

        names = "\n".join(f"• {e.get('name', 'Unknown')}" for e in to_disable)
        reply = QMessageBox.question(
            self,
            "Confirm Bulk Disable",
            f"Disable {len(to_disable)} selected startup entr{'y' if len(to_disable) == 1 else 'ies'}?\n\n"
            f"{names}\n\n"
            "This will take effect on the next Windows restart.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        failed = []
        for e in to_disable:
            ok = self._manager.disable(e.get("name", "Unknown"), e.get("hive", "HKCU"))
            if not ok:
                failed.append(e.get("name", "Unknown"))

        if failed:
            QMessageBox.warning(
                self, "Some Entries Failed",
                "Could not disable:\n" + "\n".join(failed) +
                "\n\nThis may require administrator privileges. "
                "Try running RAMGuard as administrator."
            )
        else:
            QMessageBox.information(
                self, "Success",
                f"{len(to_disable)} startup entr{'y' if len(to_disable) == 1 else 'ies'} disabled successfully."
            )
        self.load_entries()