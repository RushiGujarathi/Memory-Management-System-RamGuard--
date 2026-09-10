"""
RAMGuard Applications Page
Pixel-accurate recreation matching the reference screenshot:
- Header: Applications icon + Title + Subtitle + "Showing X of Y processes"
- Filter + Search toolbar: "Filter:" dropdown, wide search input, and "Refresh" button
- Selection status: "Selected: X applications" + Estimated memory recovery
- Process Table:
  - Fixed 54px row height with perfect vertical centering
  - No text overlap: clean cell widgets with dedicated layouts
  - Checkbox (18x18px) completely separated from process icon
  - Recognizable 24px vector process icons with 12px gap to process name
  - PID, Status badge (● Running), Memory in cyan, CPU %, Classification pills (SAFE TO CLOSE, REVIEW, PROTECTED)
  - Action column: "Details" pill button + three-dot context menu ("⋮")
  - Column sorting on headers
- Bottom Action Area: "View Details" and "Close Selected" buttons
- Bottom Status Bar: Memory pressure notification + live monitoring timestamp
"""

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QDialog, QComboBox, QCheckBox, QAbstractItemView,
    QSizePolicy, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QIcon, QAction

from core.process_scanner import ProcessInfo
from core.safety_manager import SafetyLevel
from ui.icon_helper import IconHelper
from ui.styles import rgba
from utils.logger import get_logger

logger = get_logger("ApplicationsPage")

SAFETY_COLORS = {
    SafetyLevel.SAFE_TO_CLOSE: ("#10b981", "SAFE TO CLOSE"),
    SafetyLevel.REVIEW: ("#f59e0b", "REVIEW"),
    SafetyLevel.PROTECTED: ("#3b82f6", "PROTECTED"),
    SafetyLevel.UNKNOWN: ("#8c9eb5", "UNKNOWN"),
}


class ProcessDetailDialog(QDialog):
    """Modal dialog showing detailed info about a single process."""

    close_requested = pyqtSignal(object)  # ProcessInfo

    def __init__(self, proc: ProcessInfo, parent=None) -> None:
        super().__init__(parent)
        self._proc = proc
        self.setWindowTitle(f"Process Details — {proc.name}")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #071426;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 14px;
            }
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        color, label = SAFETY_COLORS.get(self._proc.safety_level, ("#8c9eb5", "UNKNOWN"))

        # Header with Process Icon
        h = QHBoxLayout()
        h.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(IconHelper.get_process_icon(self._proc.name, 32))
        icon_lbl.setFixedSize(32, 32)

        name_col = QVBoxLayout()
        name_col.setSpacing(1)
        name_lbl = QLabel(self._proc.name)
        name_lbl.setStyleSheet("font-size:17px; font-weight:700; color:#ffffff;")
        pid_lbl = QLabel(f"PID {self._proc.pid}")
        pid_lbl.setStyleSheet("color:#8c9eb5; font-size:12px;")
        name_col.addWidget(name_lbl)
        name_col.addWidget(pid_lbl)

        badge = QLabel(f"  {label}  ")
        badge.setStyleSheet(f"""
            background-color: {rgba(color, "20")};
            color: {color};
            border: 1px solid {rgba(color, "55")};
            border-radius: 11px;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
        """)

        h.addWidget(icon_lbl)
        h.addLayout(name_col)
        h.addStretch()
        h.addWidget(badge)
        layout.addLayout(h)

        # Stats grid
        grid = QFrame()
        grid.setObjectName("card")
        grid.setStyleSheet("""
            QFrame#card {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.18);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        grid_layout = QVBoxLayout(grid)
        grid_layout.setSpacing(8)

        rows = [
            ("Memory Usage", self._proc.memory_display),
            ("CPU Usage", f"{self._proc.cpu_percent:.1f}%"),
            ("Status", self._proc.status.capitalize()),
            ("Type", "Foreground Application" if self._proc.is_foreground else "Background Process"),
            ("Threads", str(self._proc.num_threads)),
            ("User", self._proc.username or "N/A"),
            ("Executable", self._proc.exe or "N/A"),
        ]

        for key, val in rows:
            row_w = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet("color:#8c9eb5; font-size:12px; min-width:130px;")
            v = QLabel(val)
            v.setStyleSheet("color:#ffffff; font-size:12px; font-weight:500;")
            v.setWordWrap(True)
            v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row_w.addWidget(k)
            row_w.addWidget(v, 1)
            grid_layout.addLayout(row_w)

        layout.addWidget(grid)

        # Safety reason
        reason_frame = QFrame()
        reason_frame.setStyleSheet("""
            QFrame {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.18);
                border-radius: 12px;
                padding: 12px;
            }
        """)
        r_layout = QVBoxLayout(reason_frame)
        r_layout.setSpacing(4)
        r_title = QLabel("RAMGUARD CLASSIFICATION REASON")
        r_title.setStyleSheet("color:#8c9eb5; font-size:10px; font-weight:700; letter-spacing:0.8px;")
        r_text = QLabel(self._proc.safety_reason)
        r_text.setStyleSheet("color:#ffffff; font-size:12px;")
        r_text.setWordWrap(True)
        r_layout.addWidget(r_title)
        r_layout.addWidget(r_text)

        if self._proc.safety_assessment.warnings:
            w_text = QLabel("⚠ " + " | ".join(self._proc.safety_assessment.warnings))
            w_text.setStyleSheet("color:#f59e0b; font-size:11px; padding-top:4px;")
            w_text.setWordWrap(True)
            r_layout.addWidget(w_text)

        layout.addWidget(reason_frame)

        # Buttons
        btn_box = QHBoxLayout()
        close_self = QPushButton("Close")
        close_self.setObjectName("secondary_btn")
        close_self.setFixedHeight(34)
        close_self.clicked.connect(self.accept)

        if self._proc.safety_assessment.can_terminate and not self._proc.is_protected:
            close_app = QPushButton("Close Application")
            close_app.setObjectName("danger_btn")
            close_app.setFixedHeight(34)
            close_app.setToolTip("Attempt to gracefully close this application")
            close_app.clicked.connect(self._request_close)
            btn_box.addWidget(close_app)

        btn_box.addStretch()
        btn_box.addWidget(close_self)
        layout.addLayout(btn_box)

    def _request_close(self) -> None:
        self.close_requested.emit(self._proc)
        self.accept()


class ApplicationsPage(QWidget):
    """
    Process table with filter bar, search, sorting, and row actions
    matching the reference screenshot design.
    """

    close_process_requested = pyqtSignal(object)  # ProcessInfo

    COL_CHECK = 0
    COL_NAME = 1
    COL_PID = 2
    COL_STATUS = 3
    COL_MEM = 4
    COL_CPU = 5
    COL_CLASS = 6
    COL_ACTION = 7

    COLUMNS = [
        "☑",
        "PROCESS NAME ⇅",
        "PID ⇅",
        "STATUS ⇅",
        "MEMORY ⇅",
        "CPU ⇅",
        "CLASSIFICATION ⇅",
        "ACTION",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all_processes: list[ProcessInfo] = []
        self._filtered_processes: list[ProcessInfo] = []
        self._row_checkboxes: dict[int, QCheckBox] = {}  # pid -> QCheckBox
        self._sort_col = self.COL_MEM
        self._sort_reverse = True  # Highest memory first by default
        self._all_checked = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 14)
        root.setSpacing(14)

        # ── 1. Header ──
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        # Grid Icon Container
        icon_box = QLabel()
        icon_box.setPixmap(IconHelper.create_grid_icon(24, color="#38bdf8"))
        icon_box.setStyleSheet("""
            background-color: #0b1930;
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 10px;
            min-width: 38px;
            min-height: 38px;
            max-width: 38px;
            max-height: 38px;
            qproperty-alignment: AlignCenter;
        """)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        title = QLabel("Applications")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size:26px; font-weight:800; color:#ffffff; letter-spacing:-0.3px;")

        sub = QLabel("View and manage running applications")
        sub.setStyleSheet("color:#8c9eb5; font-size:12px;")

        title_col.addWidget(title)
        title_col.addWidget(sub)

        self._count_lbl = QLabel("Loading…")
        self._count_lbl.setStyleSheet("color:#8c9eb5; font-size:12px; font-weight:500;")

        hdr.addWidget(icon_box)
        hdr.addLayout(title_col)
        hdr.addStretch()
        hdr.addWidget(self._count_lbl)
        root.addLayout(hdr)

        # ── 2. Filter + Search Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        # Filter box
        filter_container = QFrame()
        filter_container.setStyleSheet("""
            QFrame {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 8px;
            }
        """)
        f_layout = QHBoxLayout(filter_container)
        f_layout.setContentsMargins(10, 2, 10, 2)
        f_layout.setSpacing(8)

        funnel_lbl = QLabel()
        funnel_lbl.setPixmap(IconHelper.create_funnel_icon(16, color="#38bdf8"))
        funnel_lbl.setFixedSize(16, 16)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color:#8c9eb5; font-size:12px; font-weight:600; border:none; background:transparent;")

        self._filter_combo = QComboBox()
        self._filter_combo.addItems([
            "All",
            "Applications",
            "Background",
            "High Memory (>200MB)",
            "Recommended",
            "Protected",
        ])
        self._filter_combo.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding-left: 2px;
                padding-right: 18px;
                min-width: 140px;
                height: 32px;
            }
            QComboBox QAbstractItemView {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.35);
                color: #ffffff;
                selection-background-color: #0066ff;
            }
        """)
        self._filter_combo.currentTextChanged.connect(self._apply_filter)

        f_layout.addWidget(funnel_lbl)
        f_layout.addWidget(filter_label)
        f_layout.addWidget(self._filter_combo)
        toolbar.addWidget(filter_container)

        # Search box
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 8px;
            }
        """)
        s_layout = QHBoxLayout(search_container)
        s_layout.setContentsMargins(12, 2, 12, 2)
        s_layout.setSpacing(8)

        search_icon = QLabel()
        search_icon.setPixmap(IconHelper.create_search_icon(16, color="#8c9eb5"))
        search_icon.setFixedSize(16, 16)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search processes...")
        self._search.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 13px;
                padding: 0;
                height: 32px;
            }
            QLineEdit::placeholder { color: #64748b; }
        """)
        self._search.textChanged.connect(self._apply_filter)

        s_layout.addWidget(search_icon)
        s_layout.addWidget(self._search, 1)
        toolbar.addWidget(search_container, 1)

        # Refresh button
        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setIcon(QIcon(IconHelper.create_refresh_icon(16, "#ffffff")))
        self._refresh_btn.setIconSize(IconHelper.create_refresh_icon(16).size())
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b1930;
                color: #ffffff;
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 600;
                height: 20px;
            }
            QPushButton:hover {
                background-color: #12284c;
                border-color: #38bdf8;
            }
        """)
        toolbar.addWidget(self._refresh_btn)
        root.addLayout(toolbar)

        # ── 3. Selected summary row ──
        sel_row = QHBoxLayout()
        self._selected_lbl = QLabel("Selected: 0 applications")
        self._selected_lbl.setStyleSheet("color:#8c9eb5; font-size:12px; font-weight:500;")

        self._mem_recovery_lbl = QLabel("")
        self._mem_recovery_lbl.setStyleSheet("color:#10b981; font-size:12px; font-weight:600;")

        sel_row.addWidget(self._selected_lbl)
        sel_row.addStretch()
        sel_row.addWidget(self._mem_recovery_lbl)
        root.addLayout(sel_row)

        # ── 4. Process Table Card ──
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet("""
            QFrame#card {
                background-color: #081426;
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 14px;
                padding: 0px;
            }
        """)
        tc_layout = QVBoxLayout(table_card)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(False)  # We handle manual sort on header click
        self._table.setWordWrap(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.itemDoubleClicked.connect(self._on_table_double_click)

        # Custom header click sorting
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        # Fixed row height so cell widgets always have enough vertical space
        self._table.verticalHeader().setDefaultSectionSize(56)
        self._table.verticalHeader().setMinimumSectionSize(56)

        self._table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #ffffff;
                selection-background-color: rgba(59, 130, 246, 0.12);
                outline: none;
            }
            QHeaderView {
                background-color: #0c1b33;
            }
            QHeaderView::section {
                background-color: #0c1b33;
                color: #8c9eb5;
                border: none;
                border-bottom: 2px solid rgba(59, 130, 246, 0.30);
                border-right: 1px solid rgba(59, 130, 246, 0.12);
                padding: 0px 10px;
                height: 42px;
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QTableWidget::item {
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                padding: 0px;
            }
            QTableWidget::item:selected {
                background-color: rgba(59, 130, 246, 0.12);
            }
            QTableWidget::item:hover {
                background-color: rgba(59, 130, 246, 0.07);
            }
            QScrollBar:vertical {
                background: #081426;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(59, 130, 246, 0.35);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        hdr_view = self._table.horizontalHeader()
        hdr_view.setFixedHeight(42)
        hdr_view.setHighlightSections(False)

        # COL_CHECK — fixed 48 px
        hdr_view.setSectionResizeMode(self.COL_CHECK, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_CHECK, 48)

        # COL_NAME — stretches to fill remaining space
        hdr_view.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)

        # COL_PID — fixed 90 px
        hdr_view.setSectionResizeMode(self.COL_PID, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_PID, 90)

        # COL_STATUS — fixed 118 px
        hdr_view.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_STATUS, 118)

        # COL_MEM — fixed 108 px
        hdr_view.setSectionResizeMode(self.COL_MEM, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_MEM, 108)

        # COL_CPU — fixed 82 px
        hdr_view.setSectionResizeMode(self.COL_CPU, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_CPU, 82)

        # COL_CLASS — fixed 145 px
        hdr_view.setSectionResizeMode(self.COL_CLASS, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_CLASS, 185)

        # COL_ACTION — fixed 130 px
        hdr_view.setSectionResizeMode(self.COL_ACTION, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_ACTION, 130)

        tc_layout.addWidget(self._table)
        root.addWidget(table_card, 1)

        # ── 5. Bottom Action Area ──
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self._detail_btn = QPushButton("  View Details")
        self._detail_btn.setIcon(QIcon(IconHelper.create_eye_icon(16, "#ffffff")))
        self._detail_btn.setIconSize(IconHelper.create_eye_icon(16).size())
        self._detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #0b2246;
                color: #ffffff;
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 8px;
                padding: 9px 20px;
                font-size: 13px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #123060;
                border-color: #38bdf8;
            }
        """)
        self._detail_btn.clicked.connect(self._show_selected_detail)

        self._close_sel_btn = QPushButton("  Close Selected")
        self._close_sel_btn.setIcon(QIcon(IconHelper.create_trash_icon(16, "#ffffff")))
        self._close_sel_btn.setIconSize(IconHelper.create_trash_icon(16).size())
        self._close_sel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_sel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #dc2626, stop:1 #ef4444);
                color: #ffffff;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: 700;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #ef4444, stop:1 #f87171);
            }
        """)
        self._close_sel_btn.clicked.connect(self._close_selected)

        action_row.addStretch()
        action_row.addWidget(self._detail_btn)
        action_row.addWidget(self._close_sel_btn)
        root.addLayout(action_row)

        # ── 6. Bottom Status Bar ──
        status_bar_row = QHBoxLayout()
        status_bar_row.setSpacing(12)

        self._bottom_warn = QLabel("⚠  CRITICAL: Memory pressure detected — consider optimizing now!")
        self._bottom_warn.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.12);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)

        self._bottom_timestamp = QLabel("Initializing…")
        self._bottom_timestamp.setStyleSheet("color:#64748b; font-size:11px;")

        status_bar_row.addWidget(self._bottom_warn)
        status_bar_row.addStretch()
        status_bar_row.addWidget(self._bottom_timestamp)
        root.addLayout(status_bar_row)

    # ═══════════════════════════════════════════════════════════════
    #  Public API (Preserves all existing slots & methods)
    # ═══════════════════════════════════════════════════════════════

    def update_processes(self, processes: list[ProcessInfo]) -> None:
        self._all_processes = processes
        self._apply_filter()

        now = datetime.datetime.now().strftime("%d %b %Y — %I:%M:%S %p")
        self._bottom_timestamp.setText(f"Last updated: {now}  •  ● Monitoring Active")

    def update_pressure_status(self, pressure_val: str) -> None:
        if "CRITICAL" in pressure_val.upper():
            self._bottom_warn.setText("⚠  CRITICAL: Memory pressure detected — consider optimizing now!")
            self._bottom_warn.setStyleSheet("""
                background-color: rgba(239, 68, 68, 0.12);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
            self._bottom_warn.setVisible(True)
        elif "HIGH" in pressure_val.upper():
            self._bottom_warn.setText("⚠  HIGH memory usage detected — consider optimizing.")
            self._bottom_warn.setStyleSheet("""
                background-color: rgba(249, 115, 22, 0.12);
                color: #f97316;
                border: 1px solid rgba(249, 115, 22, 0.3);
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)
            self._bottom_warn.setVisible(True)
        else:
            self._bottom_warn.setVisible(False)

    def connect_refresh(self, slot) -> None:
        self._refresh_btn.clicked.connect(slot)

    # ═══════════════════════════════════════════════════════════════
    #  Filtering & Population
    # ═══════════════════════════════════════════════════════════════

    def _apply_filter(self) -> None:
        filter_text = self._filter_combo.currentText()
        search = self._search.text().lower().strip()

        filtered = []
        for p in self._all_processes:
            if filter_text == "Applications" and not p.is_foreground:
                continue
            if filter_text == "Background" and p.is_foreground:
                continue
            if filter_text == "High Memory (>200MB)" and p.memory_mb < 200:
                continue
            if filter_text == "Recommended" and not p.is_safe_to_close:
                continue
            if filter_text == "Protected" and not p.is_protected:
                continue
            if search and search not in p.name.lower() and search not in str(p.pid):
                continue
            filtered.append(p)

        self._filtered_processes = filtered
        self._sort_and_populate()
        self._count_lbl.setText(f"Showing {len(filtered)} of {len(self._all_processes)} processes")

    def _on_header_clicked(self, logical_index: int) -> None:
        if logical_index == self.COL_CHECK:
            # Toggle Select All
            self._all_checked = not self._all_checked
            for cb in self._row_checkboxes.values():
                cb.setChecked(self._all_checked)
            self._update_selection_label()
            return

        if self._sort_col == logical_index:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = logical_index
            self._sort_reverse = False

        self._sort_and_populate()

    def _sort_and_populate(self) -> None:
        key_map = {
            self.COL_NAME: lambda p: p.name.lower(),
            self.COL_PID: lambda p: p.pid,
            self.COL_STATUS: lambda p: p.status.lower(),
            self.COL_MEM: lambda p: p.memory_mb,
            self.COL_CPU: lambda p: p.cpu_percent,
            self.COL_CLASS: lambda p: p.safety_level.value,
        }
        sort_fn = key_map.get(self._sort_col, lambda p: p.memory_mb)
        self._filtered_processes.sort(key=sort_fn, reverse=self._sort_reverse)
        self._populate_table(self._filtered_processes)

    def _populate_table(self, processes: list[ProcessInfo]) -> None:
        self._table.setRowCount(len(processes))
        self._row_checkboxes.clear()

        # Block signals while repopulating to avoid spurious selection-label updates
        self._table.blockSignals(True)

        for row, proc in enumerate(processes):
            # Blank backing items (carry UserRole data for double-click / sort)
            for c in range(len(self.COLUMNS)):
                blank_item = QTableWidgetItem("")
                blank_item.setData(Qt.ItemDataRole.UserRole, proc)
                self._table.setItem(row, c, blank_item)

            # Enforce row height explicitly (also set via defaultSectionSize)
            self._table.setRowHeight(row, 56)

            # ────────────────────────────────────────────────────────
            # COL 0 · Checkbox — centered, 48 px wide, nothing else
            # ────────────────────────────────────────────────────────
            cb_container = QWidget()
            cb_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            cb_container.setStyleSheet("background: transparent;")
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setSpacing(0)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            cb = QCheckBox()
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setFixedSize(16, 16)
            cb.setStyleSheet("""
                QCheckBox {
                    background: transparent;
                    spacing: 0px;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border: 2px solid rgba(148, 163, 184, 0.40);
                    border-radius: 0px;
                    background-color: #0b1930;
                    image: none;
                }
                QCheckBox::indicator:hover {
                    border-color: #3b82f6;
                    background-color: rgba(59, 130, 246, 0.10);
                }
                QCheckBox::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                    image: none;
                }
            """)
            cb.stateChanged.connect(self._update_selection_label)
            cb_layout.addWidget(cb)
            self._row_checkboxes[proc.pid] = cb
            self._table.setCellWidget(row, self.COL_CHECK, cb_container)

            # ────────────────────────────────────────────────────────
            # COL 1 · Process Name — icon (24×24) + 12px gap + text
            # ────────────────────────────────────────────────────────
            name_container = QWidget()
            name_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            name_container.setStyleSheet("background: transparent;")
            name_layout = QHBoxLayout(name_container)
            # slightly push the process name text to the right within the column
            name_layout.setContentsMargins(0, 20, 28, 20)
            name_layout.setSpacing(0)   # controlled manually below
            name_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(IconHelper.get_process_icon(proc.name, 24))
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setScaledContents(False)
            icon_lbl.setStyleSheet("background: transparent; margin: 0px; padding: 0px;")

            # 14 px spacer between icon and text
            spacer_lbl = QLabel()
            spacer_lbl.setFixedWidth(14)
            spacer_lbl.setStyleSheet("background: transparent;")

            name_lbl = QLabel(proc.name)
            name_lbl.setStyleSheet(
                "color: #e2e8f0;"
                "font-size: 13px;"
                "font-weight: 500;"
                "background: transparent;"
                "letter-spacing: 0.1px;"
            )
            name_lbl.setToolTip(f"{proc.name}  (PID: {proc.pid})")
            name_lbl.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )

            name_layout.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            name_layout.addWidget(spacer_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
            name_layout.addWidget(name_lbl, 1, Qt.AlignmentFlag.AlignVCenter)
            self._table.setCellWidget(row, self.COL_NAME, name_container)

            # ────────────────────────────────────────────────────────
            # COL 2 · PID
            # ────────────────────────────────────────────────────────
            pid_container = QWidget()
            pid_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            pid_container.setStyleSheet("background: transparent;")
            pid_layout = QHBoxLayout(pid_container)
            pid_layout.setContentsMargins(0, 0, 0, 0)
            pid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pid_lbl = QLabel(str(proc.pid))
            pid_lbl.setStyleSheet(
                "color: #94a3b8; font-size: 13px; font-weight: 500; background: transparent;"
            )
            pid_layout.addWidget(pid_lbl)
            self._table.setCellWidget(row, self.COL_PID, pid_container)

            # ────────────────────────────────────────────────────────
            # COL 3 · Status Badge
            # ────────────────────────────────────────────────────────
            status_container = QWidget()
            status_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            status_container.setStyleSheet("background: transparent;")
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(4, 0, 4, 0)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            status_pill = QLabel("● Running")
            status_pill.setFixedHeight(24)
            status_pill.setStyleSheet("""
                QLabel {
                    background-color: rgba(16, 185, 129, 0.14);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.40);
                    border-radius: 10px;
                    padding: 0px 11px;
                    font-size: 11px;
                    font-weight: 700;
                }
            """)
            status_layout.addWidget(status_pill)
            self._table.setCellWidget(row, self.COL_STATUS, status_container)

            # ────────────────────────────────────────────────────────
            # COL 4 · Memory
            # ────────────────────────────────────────────────────────
            mem_container = QWidget()
            mem_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            mem_container.setStyleSheet("background: transparent;")
            mem_layout = QHBoxLayout(mem_container)
            mem_layout.setContentsMargins(0, 0, 0, 0)
            mem_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mem_lbl = QLabel(proc.memory_display)
            mem_lbl.setStyleSheet(
                "color: #38bdf8; font-size: 13px; font-weight: 600; background: transparent;"
            )
            mem_layout.addWidget(mem_lbl)
            self._table.setCellWidget(row, self.COL_MEM, mem_container)

            # ────────────────────────────────────────────────────────
            # COL 5 · CPU
            # ────────────────────────────────────────────────────────
            cpu_container = QWidget()
            cpu_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            cpu_container.setStyleSheet("background: transparent;")
            cpu_layout = QHBoxLayout(cpu_container)
            cpu_layout.setContentsMargins(0, 0, 0, 0)
            cpu_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_lbl = QLabel(f"{proc.cpu_percent:.1f}%")
            cpu_lbl.setStyleSheet(
                "color: #cbd5e1; font-size: 13px; font-weight: 500; background: transparent;"
            )
            cpu_layout.addWidget(cpu_lbl)
            self._table.setCellWidget(row, self.COL_CPU, cpu_container)

            # ────────────────────────────────────────────────────────
            # COL 6 · Classification Badge
            # ────────────────────────────────────────────────────────
            color, label = SAFETY_COLORS.get(proc.safety_level, ("#8c9eb5", "UNKNOWN"))
            class_container = QWidget()
            class_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            class_container.setStyleSheet("background: transparent;")
            class_layout = QHBoxLayout(class_container)
            class_layout.setContentsMargins(6, 0, 6, 0)
            class_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            class_pill = QLabel(label)
            class_pill.setFixedHeight(24)
            class_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            class_pill.setStyleSheet(f"""
                QLabel {{
                    background-color: {rgba(color, "1a")};
                    color: {color};
                    border: 1px solid {rgba(color, "55")};
                    border-radius: 10px;
                    padding: 0px 10px;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }}
            """)
            class_layout.addWidget(class_pill)
            self._table.setCellWidget(row, self.COL_CLASS, class_container)

            # ────────────────────────────────────────────────────────
            # COL 7 · Action — "Details" pill + "⋮" icon button
            # ────────────────────────────────────────────────────────
            act_container = QWidget()
            act_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            act_container.setStyleSheet("background: transparent;")
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(6, 0, 8, 0)
            act_layout.setSpacing(6)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            det_btn = QPushButton("Details")
            det_btn.setFixedHeight(28)
            det_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            det_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0d2242;
                    color: #93c5fd;
                    border: 1px solid rgba(59, 130, 246, 0.40);
                    border-radius: 6px;
                    padding: 0px 14px;
                    font-size: 11px;
                    font-weight: 600;
                    min-width: 64px;
                }
                QPushButton:hover {
                    background-color: #1a3a70;
                    color: #ffffff;
                    border-color: #38bdf8;
                }
                QPushButton:pressed {
                    background-color: #112e5a;
                }
            """)
            det_btn.clicked.connect(lambda _, p=proc: self._open_detail_for_proc(p))

            menu_btn = QPushButton("⋮")
            menu_btn.setFixedSize(28, 28)
            menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            menu_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #64748b;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #e2e8f0;
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255, 255, 255, 0.12);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.05);
                }
            """)
            menu_btn.clicked.connect(lambda _, p=proc, b=menu_btn: self._show_proc_menu(p, b))

            act_layout.addWidget(det_btn)
            act_layout.addWidget(menu_btn)
            self._table.setCellWidget(row, self.COL_ACTION, act_container)

        self._table.blockSignals(False)

    # ═══════════════════════════════════════════════════════════════
    #  Row Actions & Context Menu
    # ═══════════════════════════════════════════════════════════════

    def _show_proc_menu(self, proc: ProcessInfo, button: QPushButton) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0b1930;
                border: 1px solid rgba(59, 130, 246, 0.35);
                border-radius: 8px;
                padding: 4px;
                color: #ffffff;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0066ff;
            }
            QMenu::item:disabled {
                color: #64748b;
            }
        """)

        act_detail = QAction("View Details", self)
        act_detail.triggered.connect(lambda: self._open_detail_for_proc(proc))
        menu.addAction(act_detail)

        act_close = QAction("Close Process", self)
        if proc.is_protected:
            act_close.setEnabled(False)
            act_close.setText("Protected (Cannot Close)")
        else:
            act_close.triggered.connect(lambda: self.close_process_requested.emit(proc))
        menu.addAction(act_close)

        menu.exec(button.mapToGlobal(QPoint(0, button.height())))

    def _on_table_double_click(self, item: QTableWidgetItem) -> None:
        row = item.row()
        backing_item = self._table.item(row, self.COL_NAME)
        if backing_item:
            proc = backing_item.data(Qt.ItemDataRole.UserRole)
            if proc:
                self._open_detail_for_proc(proc)

    def _open_detail_for_proc(self, proc: ProcessInfo) -> None:
        dialog = ProcessDetailDialog(proc, self)
        dialog.close_requested.connect(lambda p: self.close_process_requested.emit(p))
        dialog.exec()

    def _show_selected_detail(self) -> None:
        checked_procs = self._get_checked_processes()
        if checked_procs:
            self._open_detail_for_proc(checked_procs[0])
            return

        rows = self._table.selectionModel().selectedRows()
        if rows:
            backing_item = self._table.item(rows[0].row(), self.COL_NAME)
            if backing_item:
                proc = backing_item.data(Qt.ItemDataRole.UserRole)
                if proc:
                    self._open_detail_for_proc(proc)

    def _close_selected(self) -> None:
        targets = self._get_checked_processes()
        if not targets:
            # Fallback to selected rows
            for idx in self._table.selectionModel().selectedRows():
                item = self._table.item(idx.row(), self.COL_NAME)
                if item:
                    proc = item.data(Qt.ItemDataRole.UserRole)
                    if proc and not proc.is_protected:
                        targets.append(proc)

        for proc in targets:
            if not proc.is_protected:
                self.close_process_requested.emit(proc)

    def _get_checked_processes(self) -> list[ProcessInfo]:
        targets = []
        for pid, cb in self._row_checkboxes.items():
            if cb.isChecked():
                for p in self._all_processes:
                    if p.pid == pid:
                        targets.append(p)
                        break
        return targets

    def _update_selection_label(self) -> None:
        checked_procs = self._get_checked_processes()
        count = len(checked_procs)
        total_mb = sum(p.memory_mb for p in checked_procs)

        self._selected_lbl.setText(f"Selected: {count} application{'s' if count != 1 else ''}")
        if total_mb > 0:
            display = f"{total_mb / 1024:.1f} GB" if total_mb >= 1024 else f"{total_mb:.0f} MB"
            self._mem_recovery_lbl.setText(f"Estimated Memory Recovery: {display}")
        else:
            self._mem_recovery_lbl.setText("")
