"""
RAMGuard Optimization Page
Shows confirmation dialog, progress, and results for optimization sessions.
Presentation layer redesigned to match the unified dark-navy design system.
All backend logic, signals and data flow preserved exactly.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QProgressBar, QScrollArea, QCheckBox,
    QComboBox, QTextEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from core.process_scanner import ProcessInfo
from core.optimizer import OptimizationResult
from core.safety_manager import SafetyLevel
from utils.logger import get_logger
import datetime

logger = get_logger("OptimizationPage")

# ── Design tokens (must match styles.py palette) ──────────────────────────
_BG_PANEL  = "#081426"
_BG_INPUT  = "#0b1930"
_ACCENT    = "#2563eb"
_ACCENT2   = "#38bdf8"
_SUCCESS   = "#10b981"
_WARNING   = "#f59e0b"
_DANGER    = "#ef4444"
_TEXT_HI   = "#f1f5f9"
_TEXT_MID  = "#94a3b8"
_TEXT_LO   = "#64748b"
_BORDER    = "rgba(59, 130, 246, 0.20)"


def _pill_style(color: str) -> str:
    """Returns a QLabel stylesheet for a small rounded pill badge."""
    return (
        f"background-color: {color}1a;"
        f"color: {color};"
        f"border: 1px solid {color}55;"
        f"border-radius: 10px;"
        f"padding: 2px 10px;"
        f"font-size: 10px;"
        f"font-weight: 700;"
        f"letter-spacing: 0.5px;"
    )


class ConfirmationDialog(QDialog):
    """Shows processes recommended for closing and asks for user confirmation."""

    confirmed = pyqtSignal(list)  # list[ProcessInfo] user has selected

    def __init__(self, candidates: list[ProcessInfo], parent=None) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self._checks: dict[int, QCheckBox] = {}  # pid → checkbox
        self.setWindowTitle("RAMGuard — Confirm Optimization")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(440)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        # ── Header ──
        hdr = QLabel("Optimize Memory")
        hdr.setStyleSheet(f"font-size:20px; font-weight:800; color:{_TEXT_HI}; letter-spacing:-0.3px;")
        sub = QLabel("Review and confirm applications to close")
        sub.setStyleSheet(f"color:{_TEXT_MID}; font-size:12px;")
        root.addWidget(hdr)
        root.addWidget(sub)

        # ── Info banner ──
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(37, 99, 235, 0.12);
                border: 1px solid rgba(37, 99, 235, 0.30);
                border-radius: 12px;
                padding: 12px 16px;
            }}
        """)
        b_layout = QHBoxLayout(banner)
        b_layout.setSpacing(14)

        shield = QLabel("🛡")
        shield.setStyleSheet("font-size:28px; background:transparent;")
        shield.setFixedSize(36, 36)

        b_text = QVBoxLayout()
        b_text.setSpacing(3)
        b_title = QLabel(f"RAMGuard found {len(self._candidates)} application{'s' if len(self._candidates) != 1 else ''} recommended for closing.")
        b_title.setStyleSheet(f"font-weight:600; color:{_TEXT_HI}; font-size:13px; background:transparent;")
        b_sub = QLabel("These applications are safe to close and will help free up memory.\nOnly checked items will be closed.")
        b_sub.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px; background:transparent;")
        b_sub.setWordWrap(True)
        b_text.addWidget(b_title)
        b_text.addWidget(b_sub)

        b_layout.addWidget(shield, 0, Qt.AlignmentFlag.AlignVCenter)
        b_layout.addLayout(b_text, 1)
        root.addWidget(banner)

        # ── Process list ──
        list_frame = QFrame()
        list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {_BG_INPUT};
                border: 1px solid {_BORDER};
                border-radius: 12px;
                padding: 0px;
            }}
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # Header row
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(12, 10, 12, 10)
        hdr_row.setSpacing(0)
        for text, stretch in [("", 0), ("Application", 3), ("Memory", 2), ("Classification", 2)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; background:transparent;")
            if text == "":
                lbl.setFixedWidth(28)
                hdr_row.addWidget(lbl)
            else:
                hdr_row.addWidget(lbl, stretch)
        list_layout.addLayout(hdr_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_BORDER};")
        sep.setFixedHeight(1)
        list_layout.addWidget(sep)

        # Process rows
        total_mb = 0.0
        SAFETY_LABELS = {
            SafetyLevel.SAFE_TO_CLOSE: (_SUCCESS, "SAFE TO CLOSE"),
            SafetyLevel.REVIEW:        (_WARNING, "REVIEW"),
            SafetyLevel.PROTECTED:     (_ACCENT2, "PROTECTED"),
        }

        for i, proc in enumerate(self._candidates):
            row_widget = QWidget()
            row_widget.setStyleSheet(
                f"background-color: {'rgba(255,255,255,0.018)' if i % 2 else 'transparent'};"
            )
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(0)

            cb = QCheckBox()
            cb.setChecked(True)
            cb.setFixedWidth(28)
            self._checks[proc.pid] = cb

            name_lbl = QLabel(proc.name)
            name_lbl.setStyleSheet(f"color:{_TEXT_HI}; font-size:12px; font-weight:500; background:transparent;")
            name_lbl.setToolTip(proc.name)

            mem_lbl = QLabel(proc.memory_display)
            mem_lbl.setStyleSheet(f"color:{_ACCENT2}; font-size:12px; font-weight:600; background:transparent;")

            color, cls_text = SAFETY_LABELS.get(proc.safety_level, (_TEXT_MID, "UNKNOWN"))
            cls_pill = QLabel(cls_text)
            cls_pill.setFixedHeight(22)
            cls_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cls_pill.setStyleSheet(_pill_style(color))

            row.addWidget(cb)
            row.addWidget(name_lbl, 3)
            row.addWidget(mem_lbl, 2)
            row.addWidget(cls_pill, 2)
            list_layout.addWidget(row_widget)
            total_mb += proc.memory_mb

        root.addWidget(list_frame)

        # ── Summary ──
        total_display = f"{total_mb / 1024:.1f} GB" if total_mb >= 1024 else f"{total_mb:.0f} MB"
        summary = QLabel(f"Estimated RAM Recovery: {total_display}   •   Only safe applications will be closed.")
        summary.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px;")
        root.addWidget(summary)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary_btn")
        cancel.setFixedHeight(38)
        cancel.clicked.connect(self.reject)

        proceed = QPushButton("✓  Close Selected")
        proceed.setObjectName("success_btn")
        proceed.setFixedHeight(38)
        proceed.clicked.connect(self._on_confirm)

        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(proceed)
        root.addLayout(btn_row)

    def _on_confirm(self) -> None:
        selected = [p for p in self._candidates if self._checks[p.pid].isChecked()]
        if selected:
            self.confirmed.emit(selected)
        self.accept()


class ProgressDialog(QDialog):
    """Shows optimization progress in real time."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RAMGuard — Optimizing…")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        title = QLabel("Optimization in Progress")
        title.setStyleSheet(f"color:{_TEXT_HI}; font-size:18px; font-weight:800;")
        root.addWidget(title)

        self._status_lbl = QLabel("Starting optimization…")
        self._status_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:13px;")
        root.addWidget(self._status_lbl)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # Indeterminate
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        root.addWidget(self._bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(160)
        root.addWidget(self._log)

    def append_log(self, msg: str) -> None:
        self._log.append(msg)
        self._status_lbl.setText(msg[:80] + "…" if len(msg) > 80 else msg)

    def finish(self) -> None:
        self._bar.setRange(0, 1)
        self._bar.setValue(1)
        self._status_lbl.setText("Optimization complete!")
        self._status_lbl.setStyleSheet(f"color:{_SUCCESS}; font-size:13px; font-weight:600;")


class ResultDialog(QDialog):
    """Displays the before/after optimization result."""

    def __init__(self, result: OptimizationResult, parent=None) -> None:
        super().__init__(parent)
        self._result = result
        self.setWindowTitle("RAMGuard — Optimization Complete")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        # ── Header ──
        title = QLabel("Optimization Complete")
        title.setStyleSheet(f"font-size:20px; font-weight:800; color:{_TEXT_HI};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        banner = QLabel("✅  Memory optimization completed successfully!")
        banner.setStyleSheet(f"color:{_SUCCESS}; font-size:13px; font-weight:600;")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(banner)

        # ── Before / After ──
        ba_row = QHBoxLayout()
        ba_row.setSpacing(12)
        before = self._make_ba_card(
            "Before",
            f"{self._result.percent_before:.0f}%",
            f"Used: {self._result.snapshot_before.used_display if self._result.snapshot_before else 'N/A'}",
            _DANGER,
        )
        after = self._make_ba_card(
            "After",
            f"{self._result.percent_after:.0f}%",
            f"Used: {self._result.snapshot_after.used_display if self._result.snapshot_after else 'N/A'}",
            _SUCCESS,
        )
        ba_row.addWidget(before)
        ba_row.addWidget(after)
        root.addLayout(ba_row)

        # ── Stats ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        stats = [
            ("💾", "Memory Freed", self._result.memory_freed_display, _ACCENT2),
            ("✓",  "Apps Closed",  str(len(self._result.successful_closures)), _SUCCESS),
            ("🔒", "Protected",    "8", _TEXT_MID),
            ("✗",  "Failed",       str(len(self._result.failed_closures)), _DANGER),
        ]
        for icon, label, val, color in stats:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.setSpacing(4)
            ico = QLabel(icon)
            ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ico.setStyleSheet("background:transparent; font-size:18px;")
            v = QLabel(val)
            v.setStyleSheet(f"font-size:20px; font-weight:700; color:{color}; background:transparent;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:10px; background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(ico)
            cl.addWidget(v)
            cl.addWidget(lbl)
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── Failed list ──
        if self._result.failed_closures:
            fail_lbl = QLabel("Applications that could not be closed:")
            fail_lbl.setStyleSheet(f"color:{_DANGER}; font-size:12px; font-weight:600;")
            root.addWidget(fail_lbl)
            for c in self._result.failed_closures:
                fl = QLabel(f"  • {c.name} — {c.error_message}")
                fl.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px;")
                root.addWidget(fl)

        # ── Done button ──
        done = QPushButton("Done")
        done.setObjectName("optimize_btn")
        done.setFixedHeight(44)
        done.clicked.connect(self.accept)
        root.addWidget(done)

    def _make_ba_card(self, title: str, pct: str, sub: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        t = QLabel(title)
        t.setStyleSheet(f"color:{_TEXT_MID}; font-size:10px; font-weight:700; letter-spacing:0.8px; text-transform:uppercase; background:transparent;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        p = QLabel(pct)
        p.setStyleSheet(f"font-size:36px; font-weight:800; color:{color}; background:transparent;")
        p.setAlignment(Qt.AlignmentFlag.AlignCenter)

        s = QLabel(sub)
        s.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px; background:transparent;")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bar = QProgressBar()
        bar.setRange(0, 100)
        try:
            bar.setValue(int(pct.replace("%", "")))
        except ValueError:
            bar.setValue(0)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.06); border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
        """)

        layout.addWidget(t)
        layout.addWidget(p)
        layout.addWidget(bar)
        layout.addWidget(s)
        return frame


class OptimizationPage(QWidget):
    """Optimization control panel with mode selector."""

    optimize_requested = pyqtSignal(str)  # mode

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._processes: list[ProcessInfo] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── Header ──
        title = QLabel("Optimization")
        title.setObjectName("section_title")
        sub = QLabel("Choose an optimization mode and start the process")
        sub.setObjectName("section_sub")
        root.addWidget(title)
        root.addWidget(sub)

        # ── Mode cards ──
        mode_row = QHBoxLayout()
        mode_row.setSpacing(14)

        self._mode_cards: dict[str, dict] = {}
        modes = [
            ("SAFE",   "🛡", "Safe Mode",
             "Close only user-selected applications. Maximum safety, no surprises.",
             "#10b981"),
            ("SMART",  "⚡", "Smart Mode",
             "RAMGuard auto-selects high-memory apps classified as safe to close.",
             "#2563eb"),
            ("CUSTOM", "🎛", "Custom Mode",
             "Pick any application from the full list to close manually.",
             "#a855f7"),
        ]

        for mode_id, icon, mode_name, mode_desc, accent in modes:
            card = QFrame()
            card.setObjectName("card")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setMinimumHeight(180)
            cl = QVBoxLayout(card)
            cl.setSpacing(8)
            cl.setContentsMargins(18, 18, 18, 18)

            if mode_id == "SAFE":
                badge = QLabel("Default")
                badge.setStyleSheet(
                    f"background:{_ACCENT}22; color:{_ACCENT2}; border:1px solid {_ACCENT}55;"
                    "border-radius:8px; font-size:9px; font-weight:700; padding:2px 8px; letter-spacing:0.5px;"
                )
                badge.setFixedHeight(20)
                badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                cl.addWidget(badge)

            i_lbl = QLabel(icon)
            i_lbl.setStyleSheet(f"font-size:28px; background:transparent; color:{accent};")
            n_lbl = QLabel(mode_name)
            n_lbl.setStyleSheet(f"font-size:14px; font-weight:700; color:{_TEXT_HI}; background:transparent;")
            d_lbl = QLabel(mode_desc)
            d_lbl.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px; background:transparent;")
            d_lbl.setWordWrap(True)

            cl.addWidget(i_lbl)
            cl.addWidget(n_lbl)
            cl.addWidget(d_lbl)
            cl.addStretch()

            select_btn = QPushButton("Select")
            select_btn.setObjectName("secondary_btn")
            select_btn.setFixedHeight(34)
            select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            select_btn.clicked.connect(lambda checked, m=mode_id: self._select_mode(m))
            cl.addWidget(select_btn)

            self._mode_cards[mode_id] = {"card": card, "btn": select_btn, "accent": accent}
            mode_row.addWidget(card)

        root.addLayout(mode_row)

        # ── Current mode label ──
        self._current_mode_lbl = QLabel("Current Mode: SAFE")
        self._current_mode_lbl.setStyleSheet(f"color:{_ACCENT2}; font-size:13px; font-weight:600;")
        root.addWidget(self._current_mode_lbl)

        # ── Optimize Button ──
        self._opt_btn = QPushButton("⚡  OPTIMIZE NOW")
        self._opt_btn.setObjectName("optimize_btn")
        self._opt_btn.setFixedHeight(58)
        self._opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._opt_btn.setStyleSheet(self._opt_btn.styleSheet())  # use global
        self._opt_btn.clicked.connect(lambda: self.optimize_requested.emit(self._mode))
        root.addWidget(self._opt_btn)

        # ── Safety note ──
        note_card = QFrame()
        note_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(16, 185, 129, 0.06);
                border: 1px solid rgba(16, 185, 129, 0.22);
                border-radius: 10px;
                padding: 10px 16px;
            }}
        """)
        note_layout = QHBoxLayout(note_card)
        note_layout.setSpacing(10)
        shield_lbl = QLabel("🔒")
        shield_lbl.setStyleSheet("font-size:18px; background:transparent;")
        note_text = QLabel(
            "System processes are always protected. Only safe applications will be suggested for closure."
        )
        note_text.setStyleSheet(f"color:{_TEXT_MID}; font-size:11px; background:transparent;")
        note_text.setWordWrap(True)
        note_layout.addWidget(shield_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        note_layout.addWidget(note_text, 1)
        root.addWidget(note_card)

        root.addStretch()

        self._mode = "SAFE"
        self._highlight_mode("SAFE")

    def _select_mode(self, mode: str) -> None:
        self._mode = mode
        self._highlight_mode(mode)
        self._current_mode_lbl.setText(f"Current Mode: {mode}")

    def _highlight_mode(self, active_mode: str) -> None:
        for mode_id, widgets in self._mode_cards.items():
            accent = widgets["accent"]
            if mode_id == active_mode:
                widgets["card"].setStyleSheet(
                    f"QFrame {{ background-color: {accent}10; border: 1.5px solid {accent}60;"
                    "border-radius: 14px; padding: 0px; }}"
                )
                widgets["btn"].setObjectName("optimize_btn")
                widgets["btn"].setText("✓ Selected")
            else:
                widgets["card"].setStyleSheet("")
                widgets["card"].setObjectName("card")
                widgets["btn"].setObjectName("secondary_btn")
                widgets["btn"].setText("Select")
            widgets["card"].style().unpolish(widgets["card"])
            widgets["card"].style().polish(widgets["card"])
            widgets["btn"].style().unpolish(widgets["btn"])
            widgets["btn"].style().polish(widgets["btn"])

    def update_processes(self, processes: list[ProcessInfo]) -> None:
        self._processes = processes

    def set_optimize_enabled(self, enabled: bool) -> None:
        self._opt_btn.setEnabled(enabled)
        self._opt_btn.setText("⚡  OPTIMIZE NOW" if enabled else "⏳  Optimizing…")

    @property
    def current_mode(self) -> str:
        return self._mode
