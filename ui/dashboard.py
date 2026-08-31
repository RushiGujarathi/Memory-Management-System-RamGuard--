"""
RAMGuard Dashboard Page
Real-time overview: RAM gauge, metric cards, and the Optimize button.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QConicalGradient, QRadialGradient, QBrush
from core.memory_monitor import MemorySnapshot, MemoryPressure
from utils.logger import get_logger

logger = get_logger("Dashboard")


class CircularGauge(QWidget):
    """Custom circular RAM usage gauge with animated fill."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._percent = 0.0
        self._pressure = MemoryPressure.NORMAL
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(200, 200)

    def set_value(self, percent: float, pressure: MemoryPressure) -> None:
        self._percent = percent
        self._pressure = pressure
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        center = QPointF(w / 2, h / 2)
        radius = min(w, h) / 2 - 14
        thickness = 16

        # ── Track (background arc) ──
        pen = QPen(QColor("#21262d"), thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # ── Value arc ──
        color_map = {
            MemoryPressure.NORMAL: ("#2ecc71", "#27ae60"),
            MemoryPressure.MODERATE: ("#f1c40f", "#f39c12"),
            MemoryPressure.HIGH: ("#e67e22", "#d35400"),
            MemoryPressure.CRITICAL: ("#e74c3c", "#c0392b"),
        }
        c1, c2 = color_map.get(self._pressure, ("#2ecc71", "#27ae60"))

        span = int(-270 * 16 * (self._percent / 100))
        grad = QConicalGradient(center, 225)
        grad.setColorAt(0.0, QColor(c1))
        grad.setColorAt(1.0, QColor(c2))
        pen = QPen(QBrush(grad), thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 225 * 16, span)

        # ── Center text ──
        painter.setPen(QColor("#e6edf3"))
        font = QFont("Segoe UI", 30, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, h / 2 - 30, w, 40),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._percent:.0f}%",
        )

        font2 = QFont("Segoe UI", 9)
        painter.setFont(font2)
        painter.setPen(QColor("#8b949e"))
        painter.drawText(
            QRectF(0, h / 2 + 14, w, 20),
            Qt.AlignmentFlag.AlignCenter,
            "RAM Usage",
        )


class MetricCard(QFrame):
    """Small stat card: title + value + optional sub-text."""

    def __init__(self, title: str, value: str = "—", sub: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(14, 12, 14, 12)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("card_title")
        self._title_lbl.setStyleSheet("font-size:10px;color:#8b949e;font-weight:600;letter-spacing:1px;text-transform:uppercase;")

        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("card_value")
        self._value_lbl.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")

        self._sub_lbl = QLabel(sub)
        self._sub_lbl.setObjectName("card_sub")
        self._sub_lbl.setStyleSheet("font-size:11px;color:#8b949e;")

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)
        if sub:
            layout.addWidget(self._sub_lbl)

    def update_value(self, value: str, sub: str = "") -> None:
        self._value_lbl.setText(value)
        if sub:
            self._sub_lbl.setText(sub)


class DashboardPage(QWidget):
    """Main dashboard page."""

    def __init__(self, on_optimize_clicked, parent=None) -> None:
        super().__init__(parent)
        self._on_optimize = on_optimize_clicked
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        sub = QLabel("Real-time overview of your system")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)
        root.addWidget(sub)

        # ── Main content row ──
        main_row = QHBoxLayout()
        main_row.setSpacing(20)

        # Left: Gauge + progress bars
        left = QVBoxLayout()
        left.setSpacing(16)

        gauge_frame = QFrame()
        gauge_frame.setObjectName("card")
        gf_layout = QVBoxLayout(gauge_frame)
        gf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gauge_title = QLabel("Memory Overview")
        gauge_title.setStyleSheet("font-size:14px;font-weight:600;color:#e6edf3;")
        gf_layout.addWidget(gauge_title, alignment=Qt.AlignmentFlag.AlignCenter)

        self._gauge = CircularGauge()
        gf_layout.addWidget(self._gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        # RAM bars
        bars_layout = QVBoxLayout()
        bars_layout.setSpacing(8)

        self._ram_bar = self._make_bar_row("RAM Usage", "#1f6feb")
        self._used_bar = self._make_bar_row("Used Memory", "#e67e22")
        self._avail_bar = self._make_bar_row("Available Memory", "#2ecc71")

        bars_layout.addLayout(self._ram_bar["layout"])
        bars_layout.addLayout(self._used_bar["layout"])
        bars_layout.addLayout(self._avail_bar["layout"])
        gf_layout.addLayout(bars_layout)

        left.addWidget(gauge_frame)

        # Optimize Button
        self._opt_btn = QPushButton("⚡  OPTIMIZE MEMORY")
        self._opt_btn.setObjectName("optimize_btn")
        self._opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._opt_btn.setFixedHeight(52)
        self._opt_btn.setToolTip("Scan and safely close recommended applications")
        self._opt_btn.clicked.connect(self._on_optimize)
        left.addWidget(self._opt_btn)

        sub_opt = QLabel("Free up memory by closing unnecessary applications")
        sub_opt.setStyleSheet("color:#8b949e;font-size:11px;")
        sub_opt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(sub_opt)

        main_row.addLayout(left, 5)

        # Right: Metric cards
        right = QVBoxLayout()
        right.setSpacing(12)

        self._cpu_card = MetricCard("CPU Usage", "—%")
        self._apps_card = MetricCard("Running Applications", "—")
        self._bg_card = MetricCard("Background Processes", "—")
        self._status_card = MetricCard("System Status", "Initializing…")

        for c in (self._cpu_card, self._apps_card, self._bg_card, self._status_card):
            right.addWidget(c)

        right.addStretch()
        main_row.addLayout(right, 4)
        root.addLayout(main_row)

        # ── Bottom info row ──
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        features = [
            ("📡", "Real-time Monitoring", "Monitor RAM, CPU and system performance in real-time."),
            ("🛡", "Smart & Safe", "Intelligent classification ensures system safety at all times."),
            ("⚡", "One-Click Optimize", "Free memory safely with a single click."),
            ("🔒", "System Protection", "Protected processes will never be closed by RAMGuard."),
        ]
        for icon, title, desc in features:
            feat_frame = QFrame()
            feat_frame.setObjectName("card")
            feat_layout = QVBoxLayout(feat_frame)
            feat_layout.setSpacing(4)
            feat_layout.setContentsMargins(12, 10, 12, 10)
            i_lbl = QLabel(icon)
            i_lbl.setStyleSheet("font-size:22px;")
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-weight:600;color:#e6edf3;font-size:12px;")
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color:#8b949e;font-size:10px;")
            d_lbl.setWordWrap(True)
            feat_layout.addWidget(i_lbl)
            feat_layout.addWidget(t_lbl)
            feat_layout.addWidget(d_lbl)
            info_row.addWidget(feat_frame)

        root.addLayout(info_row)

        # ── Status bar label ──
        self._last_update = QLabel("Initializing…")
        self._last_update.setStyleSheet("color:#484f58;font-size:10px;")
        self._last_update.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self._last_update)

    # ── Progress bar helper ──
    def _make_bar_row(self, label: str, color: str) -> dict:
        layout = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#8b949e;font-size:11px;min-width:110px;")
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{ background:#21262d; border:none; border-radius:3px; }}
            QProgressBar::chunk {{ background:{color}; border-radius:3px; }}
        """)
        val_lbl = QLabel("—")
        val_lbl.setStyleSheet("color:#e6edf3;font-size:11px;min-width:70px;text-align:right;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)
        layout.addWidget(bar)
        layout.addWidget(val_lbl)
        return {"layout": layout, "bar": bar, "label": val_lbl}

    # ── Public update method ──
    def update_snapshot(self, snap: MemorySnapshot) -> None:
        import datetime
        self._gauge.set_value(snap.percent, snap.pressure)

        pct = int(snap.percent)
        used_pct = int((snap.used_bytes / snap.total_bytes) * 100) if snap.total_bytes else 0
        avail_pct = int((snap.available_bytes / snap.total_bytes) * 100) if snap.total_bytes else 0

        self._ram_bar["bar"].setValue(pct)
        self._ram_bar["label"].setText(f"{pct}%")

        self._used_bar["bar"].setValue(used_pct)
        self._used_bar["label"].setText(snap.used_display)

        self._avail_bar["bar"].setValue(avail_pct)
        self._avail_bar["label"].setText(snap.available_display)

        self._cpu_card.update_value(f"{snap.cpu_percent:.0f}%")
        self._apps_card.update_value(str(snap.process_count))
        self._bg_card.update_value(str(max(snap.process_count - 15, 0)))

        status_map = {
            "NORMAL": ("System Healthy ✓", "#2ecc71"),
            "MODERATE": ("Moderate Usage", "#f39c12"),
            "HIGH": ("High Memory Usage ⚠", "#e67e22"),
            "CRITICAL": ("Critical — Optimize Now! 🔴", "#e74c3c"),
        }
        status_text, status_color = status_map.get(snap.pressure.value, ("Unknown", "#8b949e"))
        self._status_card._value_lbl.setText(status_text)
        self._status_card._value_lbl.setStyleSheet(f"font-size:14px;font-weight:700;color:{status_color};")

        now = datetime.datetime.now().strftime("%d %b %Y — %I:%M:%S %p")
        self._last_update.setText(f"Last updated: {now}  •  Monitoring Active")

    def set_optimize_enabled(self, enabled: bool) -> None:
        self._opt_btn.setEnabled(enabled)
        self._opt_btn.setText("⚡  OPTIMIZE MEMORY" if enabled else "⏳  Optimizing…")
