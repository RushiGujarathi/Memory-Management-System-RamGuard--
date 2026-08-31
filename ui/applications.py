"""
RAMGuard Applications Page
Displays the running process table with filters, search, and process details.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QDialog, QDialogButtonBox, QScrollArea, QComboBox,
    QAbstractItemView, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from core.process_scanner import ProcessInfo
from core.safety_manager import SafetyLevel
from utils.logger import get_logger

logger = get_logger("ApplicationsPage")

SAFETY_COLORS = {
    SafetyLevel.SAFE_TO_CLOSE: ("#2ecc71", "SAFE TO CLOSE"),
    SafetyLevel.REVIEW: ("#f39c12", "REVIEW"),
    SafetyLevel.PROTECTED: ("#e74c3c", "PROTECTED"),
    SafetyLevel.UNKNOWN: ("#8b949e", "UNKNOWN"),
}


class ProcessDetailDialog(QDialog):
    """Modal dialog showing detailed info about a single process."""

    close_requested = pyqtSignal(object)  # ProcessInfo

    def __init__(self, proc: ProcessInfo, parent=None) -> None:
        super().__init__(parent)
        self._proc = proc
        self.setWindowTitle(f"Process Details — {proc.name}")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        color, label = SAFETY_COLORS.get(self._proc.safety_level, ("#8b949e", "UNKNOWN"))

        # ── Header ──
        h = QHBoxLayout()
        name_lbl = QLabel(self._proc.name)
        name_lbl.setStyleSheet("font-size:18px;font-weight:700;color:#e6edf3;")
        pid_lbl = QLabel(f"PID {self._proc.pid}")
        pid_lbl.setStyleSheet("color:#8b949e;font-size:12px;")
        h.addWidget(name_lbl)
        h.addStretch()
        h.addWidget(pid_lbl)
        layout.addLayout(h)

        # ── Classification badge ──
        badge = QLabel(f"  {label}  ")
        badge.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            border: 1px solid {color};
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
        """)
        badge.setFixedHeight(26)
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(badge)

        # ── Stats grid ──
        grid = QFrame()
        grid.setObjectName("card")
        grid_layout = QVBoxLayout(grid)
        grid_layout.setSpacing(10)

        rows = [
            ("Memory Usage", self._proc.memory_display),
            ("CPU Usage", f"{self._proc.cpu_percent:.1f}%"),
            ("Status", self._proc.status.capitalize()),
            ("Type", "Foreground App" if self._proc.is_foreground else "Background Process"),
            ("Threads", str(self._proc.num_threads)),
            ("User", self._proc.username or "N/A"),
            ("Executable", self._proc.exe or "N/A"),
        ]

        for key, val in rows:
            row_w = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet("color:#8b949e;font-size:12px;min-width:130px;")
            v = QLabel(val)
            v.setStyleSheet("color:#e6edf3;font-size:12px;")
            v.setWordWrap(True)
            v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row_w.addWidget(k)
            row_w.addWidget(v, 1)
            grid_layout.addLayout(row_w)

        layout.addWidget(grid)

        # ── Safety reason ──
        reason_frame = QFrame()
        reason_frame.setObjectName("card")
        r_layout = QVBoxLayout(reason_frame)
        r_title = QLabel("RAMGuard Classification Reason")
        r_title.setStyleSheet("color:#8b949e;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1px;")
        r_text = QLabel(self._proc.safety_reason)
        r_text.setStyleSheet("color:#e6edf3;font-size:12px;")
        r_text.setWordWrap(True)
        r_layout.addWidget(r_title)
        r_layout.addWidget(r_text)

        if self._proc.safety_assessment.warnings:
            w_text = QLabel("⚠ " + " | ".join(self._proc.safety_assessment.warnings))
            w_text.setStyleSheet("color:#f39c12;font-size:11px;")
            w_text.setWordWrap(True)
            r_layout.addWidget(w_text)

        layout.addWidget(reason_frame)

        # ── Buttons ──
        btn_box = QHBoxLayout()
        close_self = QPushButton("Close")
        close_self.setObjectName("secondary_btn")
        close_self.clicked.connect(self.accept)

        if self._proc.safety_assessment.can_terminate and not self._proc.is_protected:
            close_app = QPushButton("Close Application")
            close_app.setObjectName("danger_btn")
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
    """Process table with filter bar, search, and sort capabilities."""

    close_process_requested = pyqtSignal(object)  # ProcessInfo

    COLUMNS = ["Process Name", "PID", "Status", "Memory", "CPU", "Classification", "Action"]
    COL_NAME, COL_PID, COL_STATUS, COL_MEM, COL_CPU, COL_CLASS, COL_ACTION = range(7)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all_processes: list[ProcessInfo] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("Applications")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        self._count_lbl = QLabel("Loading…")
        self._count_lbl.setStyleSheet("color:#8b949e;font-size:12px;")
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self._count_lbl)
        root.addLayout(hdr)

        sub = QLabel("View and manage running applications")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(sub)

        # ── Filter + Search bar ──
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems([
            "All", "Applications", "Background",
            "High Memory (>200MB)", "Recommended", "Protected",
        ])
        self._filter_combo.currentTextChanged.connect(self._apply_filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search processes…")
        self._search.textChanged.connect(self._apply_filter)

        self._refresh_btn = QPushButton("↻  Refresh")
        self._refresh_btn.setObjectName("secondary_btn")
        self._refresh_btn.setFixedWidth(100)

        bar.addWidget(QLabel("Filter:"))
        bar.addWidget(self._filter_combo)
        bar.addWidget(self._search, 1)
        bar.addWidget(self._refresh_btn)
        root.addLayout(bar)

        # ── Selected summary ──
        self._selected_lbl = QLabel("Selected: 0 applications")
        self._selected_lbl.setStyleSheet("color:#8b949e;font-size:11px;")

        self._mem_recovery_lbl = QLabel("")
        self._mem_recovery_lbl.setStyleSheet("color:#2ecc71;font-size:11px;font-weight:600;")

        sel_row = QHBoxLayout()
        sel_row.addWidget(self._selected_lbl)
        sel_row.addStretch()
        sel_row.addWidget(self._mem_recovery_lbl)
        root.addLayout(sel_row)

        # ── Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)
        self._table.setWordWrap(False)
        self._table.itemDoubleClicked.connect(self._show_detail)
        self._table.itemSelectionChanged.connect(self._update_selection_label)

        hdr_view = self._table.horizontalHeader()
        hdr_view.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        hdr_view.setSectionResizeMode(self.COL_PID, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(self.COL_MEM, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(self.COL_CPU, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(self.COL_CLASS, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(self.COL_ACTION, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(self._table)

        # ── Footer ──
        footer = QHBoxLayout()
        self._detail_btn = QPushButton("View Details")
        self._detail_btn.setObjectName("secondary_btn")
        self._detail_btn.clicked.connect(self._show_selected_detail)

        self._close_sel_btn = QPushButton("🗕  Close Selected")
        self._close_sel_btn.setObjectName("danger_btn")
        self._close_sel_btn.clicked.connect(self._close_selected)

        footer.addStretch()
        footer.addWidget(self._detail_btn)
        footer.addWidget(self._close_sel_btn)
        root.addLayout(footer)

    # ── Public ──

    def update_processes(self, processes: list[ProcessInfo]) -> None:
        self._all_processes = processes
        self._apply_filter()

    def connect_refresh(self, slot) -> None:
        self._refresh_btn.clicked.connect(slot)

    # ── Private ──

    def _apply_filter(self) -> None:
        filter_text = self._filter_combo.currentText()
        search = self._search.text().lower()

        filtered = []
        for p in self._all_processes:
            # Filter
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
            # Search
            if search and search not in p.name.lower():
                continue
            filtered.append(p)

        self._populate_table(filtered)
        self._count_lbl.setText(f"Showing {len(filtered)} of {len(self._all_processes)} processes")

    def _populate_table(self, processes: list[ProcessInfo]) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            color, label = SAFETY_COLORS.get(proc.safety_level, ("#8b949e", "UNKNOWN"))

            items = [
                (self.COL_NAME,   proc.name),
                (self.COL_PID,    str(proc.pid)),
                (self.COL_STATUS, proc.status.capitalize()),
                (self.COL_MEM,    proc.memory_display),
                (self.COL_CPU,    f"{proc.cpu_percent:.1f}%"),
                (self.COL_CLASS,  label),
                (self.COL_ACTION, "Details"),
            ]

            for col, text in items:
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, proc)

                if col == self.COL_CLASS:
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                elif col == self.COL_MEM:
                    item.setForeground(QColor("#58a6ff"))
                elif col == self.COL_ACTION:
                    item.setForeground(QColor("#8b949e"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if proc.is_protected:
                    item.setForeground(QColor("#484f58"))

                self._table.setItem(row, col, item)

            self._table.setRowHeight(row, 36)

        self._table.setSortingEnabled(True)

    def _show_detail(self, item: QTableWidgetItem) -> None:
        proc: ProcessInfo = item.data(Qt.ItemDataRole.UserRole)
        if proc:
            dialog = ProcessDetailDialog(proc, self)
            dialog.close_requested.connect(lambda p: self.close_process_requested.emit(p))
            dialog.exec()

    def _show_selected_detail(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        item = self._table.item(rows[0].row(), 0)
        if item:
            self._show_detail(item)

    def _close_selected(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        for idx in rows:
            item = self._table.item(idx.row(), 0)
            if item:
                proc: ProcessInfo = item.data(Qt.ItemDataRole.UserRole)
                if proc and not proc.is_protected:
                    self.close_process_requested.emit(proc)

    def _update_selection_label(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        count = len(rows)
        total_mb = sum(
            self._table.item(r.row(), 0).data(Qt.ItemDataRole.UserRole).memory_mb
            for r in rows
            if self._table.item(r.row(), 0)
               and self._table.item(r.row(), 0).data(Qt.ItemDataRole.UserRole)
        )
        self._selected_lbl.setText(f"Selected: {count} application{'s' if count != 1 else ''}")
        if total_mb > 0:
            display = f"{total_mb / 1024:.1f} GB" if total_mb >= 1024 else f"{total_mb:.0f} MB"
            self._mem_recovery_lbl.setText(f"Estimated Memory Recovery: {display}")
        else:
            self._mem_recovery_lbl.setText("")
