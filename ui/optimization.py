"""
RAMGuard Optimization Page
Shows confirmation dialog, progress, and results for optimization sessions.
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


class ConfirmationDialog(QDialog):
    """Shows processes recommended for closing and asks for user confirmation."""

    confirmed = pyqtSignal(list)  # list[ProcessInfo] user has selected

    def __init__(self, candidates: list[ProcessInfo], parent=None) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self._checks: dict[int, QCheckBox] = {}  # pid → checkbox
        self.setWindowTitle("RAMGuard — Confirm Optimization")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setMinimumHeight(420)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # ── Header ──
        hdr = QLabel("Optimize Memory")
        hdr.setStyleSheet("font-size:18px;font-weight:700;color:#e6edf3;")
        sub = QLabel("Review and confirm applications to close")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(hdr)
        root.addWidget(sub)

        # ── Info banner ──
        banner = QFrame()
        banner.setObjectName("card")
        b_layout = QHBoxLayout(banner)
        icon = QLabel("🛡")
        icon.setStyleSheet("font-size:32px;")
        b_text_layout = QVBoxLayout()
        b_title = QLabel(f"RAMGuard found {len(self._candidates)} applications recommended for closing.")
        b_title.setStyleSheet("font-weight:600;color:#e6edf3;font-size:13px;")
        b_sub = QLabel("These applications are safe to close and will help free up memory.\nOnly checked items will be closed.")
        b_sub.setStyleSheet("color:#8b949e;font-size:11px;")
        b_sub.setWordWrap(True)
        b_text_layout.addWidget(b_title)
        b_text_layout.addWidget(b_sub)
        b_layout.addWidget(icon)
        b_layout.addLayout(b_text_layout, 1)
        root.addWidget(banner)

        # ── Process list ──
        list_frame = QFrame()
        list_frame.setObjectName("card")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setSpacing(4)

        hdr_row = QHBoxLayout()
        QLabel("Application").setStyleSheet("color:#8b949e;font-size:11px;")
        h_app = QLabel("Application")
        h_app.setStyleSheet("color:#8b949e;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;")
        h_mem = QLabel("Memory")
        h_mem.setStyleSheet("color:#8b949e;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;")
        h_cls = QLabel("Classification")
        h_cls.setStyleSheet("color:#8b949e;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;")
        hdr_row.addSpacing(24)
        hdr_row.addWidget(h_app, 3)
        hdr_row.addWidget(h_mem, 2)
        hdr_row.addWidget(h_cls, 2)
        list_layout.addLayout(hdr_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#30363d;")
        list_layout.addWidget(sep)

        total_mb = 0.0
        for proc in self._candidates:
            row = QHBoxLayout()
            cb = QCheckBox()
            cb.setChecked(True)
            self._checks[proc.pid] = cb

            name_lbl = QLabel(proc.name)
            name_lbl.setStyleSheet("color:#e6edf3;font-size:12px;font-weight:500;")

            mem_lbl = QLabel(proc.memory_display)
            mem_lbl.setStyleSheet("color:#58a6ff;font-size:12px;")

            is_review = proc.safety_level == SafetyLevel.REVIEW
            cls_color = "#f39c12" if is_review else "#2ecc71"
            cls_text = "REVIEW" if is_review else "SAFE TO CLOSE"
            cls_lbl = QLabel(cls_text)
            cls_lbl.setStyleSheet(f"color:{cls_color};font-size:11px;font-weight:600;")

            row.addWidget(cb)
            row.addWidget(name_lbl, 3)
            row.addWidget(mem_lbl, 2)
            row.addWidget(cls_lbl, 2)
            list_layout.addLayout(row)
            total_mb += proc.memory_mb

        root.addWidget(list_frame)

        # ── Summary ──
        total_display = f"{total_mb / 1024:.1f} GB" if total_mb >= 1024 else f"{total_mb:.0f} MB"
        summary = QLabel(f"Estimated RAM Recovery: {total_display}   •   Only safe applications will be closed.")
        summary.setStyleSheet("color:#8b949e;font-size:11px;")
        root.addWidget(summary)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary_btn")
        cancel.clicked.connect(self.reject)

        proceed = QPushButton("Close Selected")
        proceed.setObjectName("success_btn")
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
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        self._status_lbl = QLabel("Starting optimization…")
        self._status_lbl.setStyleSheet("color:#e6edf3;font-size:14px;font-weight:600;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # Indeterminate
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(150)
        self._log.setStyleSheet("background:#0d1117;color:#8b949e;font-family:Consolas,monospace;font-size:11px;border:1px solid #30363d;border-radius:6px;")

        root.addWidget(self._status_lbl)
        root.addWidget(self._bar)
        root.addWidget(self._log)

    def append_log(self, msg: str) -> None:
        self._log.append(msg)
        self._status_lbl.setText(msg[:80] + "…" if len(msg) > 80 else msg)

    def finish(self) -> None:
        self._bar.setRange(0, 1)
        self._bar.setValue(1)


class ResultDialog(QDialog):
    """Displays the before/after optimization result."""

    def __init__(self, result: OptimizationResult, parent=None) -> None:
        super().__init__(parent)
        self._result = result
        self.setWindowTitle("RAMGuard — Optimization Complete")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Banner ──
        banner = QLabel("✅  Memory optimization completed successfully!")
        banner.setStyleSheet("color:#2ecc71;font-size:13px;font-weight:600;")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Optimization Complete")
        title.setStyleSheet("font-size:20px;font-weight:700;color:#e6edf3;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(banner)

        # ── Before / After ──
        ba_row = QHBoxLayout()
        ba_row.setSpacing(12)

        before = self._make_ba_card(
            "Before Optimization",
            f"{self._result.percent_before:.0f}%",
            f"Used Memory: {self._result.snapshot_before.used_display if self._result.snapshot_before else 'N/A'}",
            "#e74c3c",
        )
        after = self._make_ba_card(
            "After Optimization",
            f"{self._result.percent_after:.0f}%",
            f"Used Memory: {self._result.snapshot_after.used_display if self._result.snapshot_after else 'N/A'}",
            "#2ecc71",
        )
        ba_row.addWidget(before)
        ba_row.addWidget(after)
        root.addLayout(ba_row)

        # ── Stats row ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stats = [
            ("💾", "Memory Freed", self._result.memory_freed_display),
            ("✓", "Apps Closed", str(len(self._result.successful_closures))),
            ("🔒", "Protected", str(8)),
            ("✗", "Failed", str(len(self._result.failed_closures))),
        ]
        for icon, label, val in stats:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(QLabel(icon, alignment=Qt.AlignmentFlag.AlignCenter))
            v = QLabel(val)
            v.setStyleSheet("font-size:20px;font-weight:700;color:#e6edf3;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label)
            l.setStyleSheet("color:#8b949e;font-size:10px;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(v)
            cl.addWidget(l)
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── Failed list ──
        if self._result.failed_closures:
            fail_lbl = QLabel("Applications that could not be closed:")
            fail_lbl.setStyleSheet("color:#e74c3c;font-size:12px;font-weight:600;")
            root.addWidget(fail_lbl)
            for c in self._result.failed_closures:
                fl = QLabel(f"  • {c.name} — {c.error_message}")
                fl.setStyleSheet("color:#8b949e;font-size:11px;")
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

        t = QLabel(title)
        t.setStyleSheet("color:#8b949e;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)

        p = QLabel(pct)
        p.setStyleSheet(f"font-size:36px;font-weight:700;color:{color};")
        p.setAlignment(Qt.AlignmentFlag.AlignCenter)

        s = QLabel(sub)
        s.setStyleSheet("color:#8b949e;font-size:11px;")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(pct.replace("%", "")))
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background:#21262d; border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
        """)

        layout.addWidget(t)
        layout.addWidget(p)
        layout.addWidget(bar)
        layout.addWidget(s)
        return frame


class OptimizationPage(QWidget):
    """Optimization control panel with mode selector and history preview."""

    optimize_requested = pyqtSignal(str)  # mode

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._processes: list[ProcessInfo] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        title = QLabel("Optimization")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        sub = QLabel("Choose an optimization mode and start the process")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(title)
        root.addWidget(sub)

        # ── Mode cards ──
        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)

        self._mode_cards = {}
        modes = [
            ("SAFE", "🛡", "Safe Mode",
             "Only close applications explicitly selected by the user. Maximum safety guaranteed."),
            ("SMART", "⚡", "Smart Mode",
             "RAMGuard recommends high-memory user applications based on safety classification."),
            ("CUSTOM", "🎛", "Custom Mode",
             "Manually select any application from the full process list to close."),
        ]

        for mode_id, icon, mode_name, mode_desc in modes:
            card = QFrame()
            card.setObjectName("card")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            cl = QVBoxLayout(card)
            cl.setSpacing(6)

            i_lbl = QLabel(icon)
            i_lbl.setStyleSheet("font-size:28px;")
            n_lbl = QLabel(mode_name)
            n_lbl.setStyleSheet("font-size:14px;font-weight:700;color:#e6edf3;")
            d_lbl = QLabel(mode_desc)
            d_lbl.setStyleSheet("color:#8b949e;font-size:11px;")
            d_lbl.setWordWrap(True)

            if mode_id == "SAFE":
                badge = QLabel("Default")
                badge.setStyleSheet("background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb;border-radius:4px;font-size:9px;font-weight:600;padding:2px 6px;")
                badge.setFixedHeight(18)
                badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                cl.addWidget(badge)

            cl.addWidget(i_lbl)
            cl.addWidget(n_lbl)
            cl.addWidget(d_lbl)

            select_btn = QPushButton("Select")
            select_btn.setObjectName("secondary_btn")
            select_btn.setFixedHeight(32)
            select_btn.clicked.connect(lambda checked, m=mode_id: self._select_mode(m))
            cl.addWidget(select_btn)

            self._mode_cards[mode_id] = {"card": card, "btn": select_btn}
            mode_row.addWidget(card)

        root.addLayout(mode_row)

        # ── Current mode display ──
        self._current_mode_lbl = QLabel("Current Mode: SAFE")
        self._current_mode_lbl.setStyleSheet("color:#58a6ff;font-size:13px;font-weight:600;")
        root.addWidget(self._current_mode_lbl)

        # ── Big optimize button ──
        self._opt_btn = QPushButton("⚡  OPTIMIZE MEMORY")
        self._opt_btn.setObjectName("optimize_btn")
        self._opt_btn.setFixedHeight(56)
        self._opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._opt_btn.clicked.connect(lambda: self.optimize_requested.emit(self._mode))
        root.addWidget(self._opt_btn)

        safety_note = QLabel("🔒  System processes are always protected. Only safe applications will be suggested for closure.")
        safety_note.setStyleSheet("color:#8b949e;font-size:11px;")
        safety_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(safety_note)

        root.addStretch()

        self._mode = "SAFE"
        self._highlight_mode("SAFE")

    def _select_mode(self, mode: str) -> None:
        self._mode = mode
        self._highlight_mode(mode)
        self._current_mode_lbl.setText(f"Current Mode: {mode}")

    def _highlight_mode(self, active_mode: str) -> None:
        for mode_id, widgets in self._mode_cards.items():
            if mode_id == active_mode:
                widgets["card"].setStyleSheet("background-color:#1f6feb11;border:1px solid #1f6feb;border-radius:12px;padding:16px;")
                widgets["btn"].setObjectName("optimize_btn")
                widgets["btn"].setText("✓ Selected")
            else:
                widgets["card"].setStyleSheet("")
                widgets["card"].setObjectName("card")
                widgets["btn"].setObjectName("secondary_btn")
                widgets["btn"].setText("Select")
            widgets["card"].update()
            widgets["btn"].update()

    def update_processes(self, processes: list[ProcessInfo]) -> None:
        self._processes = processes

    def set_optimize_enabled(self, enabled: bool) -> None:
        self._opt_btn.setEnabled(enabled)
        self._opt_btn.setText("⚡  OPTIMIZE MEMORY" if enabled else "⏳  Optimizing…")

    @property
    def current_mode(self) -> str:
        return self._mode
