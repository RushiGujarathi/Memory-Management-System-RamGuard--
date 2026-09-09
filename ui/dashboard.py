"""
RAMGuard Dashboard Page
Pixel-accurate recreation of the reference dashboard design:
- Header: Title & subtitle
- Memory Overview: Donut ring gauge, legend, and 3 sleek breakdown bars
- Right Column: 4 Stat cards (CPU, Running Apps, Background Processes, System Status) with sparklines
- Middle: Full-width OPTIMIZE MEMORY gradient banner
- Bottom: 4 Quick action feature cards
- Footer: Timestamp & live monitoring status
"""

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from core.memory_monitor import MemorySnapshot, MemoryPressure
from ui.icon_helper import IconHelper
from ui.custom_widgets import (
    DonutGauge, StatCard, SystemStatusCard, ProgressBarRow, FeatureCard
)
from utils.logger import get_logger

logger = get_logger("Dashboard")


class DashboardPage(QWidget):
    """Main dashboard page."""

    navigate_requested = pyqtSignal(str)

    def __init__(self, on_optimize_clicked, on_navigate=None, parent=None) -> None:
        super().__init__(parent)
        self._on_optimize = on_optimize_clicked
        if on_navigate:
            self.navigate_requested.connect(on_navigate)
        self._build_ui()

    def _build_ui(self) -> None:
        # Wrap in scroll area to ensure perfect presentation on various resolutions
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        container.setObjectName("dashboard_container")
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # ── 1. Header ──
        hdr_layout = QVBoxLayout()
        hdr_layout.setSpacing(2)

        title = QLabel("Dashboard")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size:28px; font-weight:700; color:#ffffff; letter-spacing:-0.4px;")

        subtitle = QLabel("Real-time overview of your system")
        subtitle.setStyleSheet("color:#8c9eb5; font-size:12px;")

        hdr_layout.addWidget(title)
        hdr_layout.addWidget(subtitle)
        root.addLayout(hdr_layout)

        # ── 2. Top Section (Memory Overview + 4 Right Cards) ──
        top_section = QHBoxLayout()
        top_section.setSpacing(16)

        # ── Left: Memory Overview Card ──
        mem_card = QFrame()
        mem_card.setObjectName("card")
        mem_layout = QVBoxLayout(mem_card)
        mem_layout.setContentsMargins(20, 16, 20, 16)
        mem_layout.setSpacing(14)

        # Card Header
        mem_hdr = QHBoxLayout()
        mem_hdr.setSpacing(12)

        mem_icon = QLabel()
        mem_icon.setPixmap(IconHelper.create_chip_icon(34, color="#38bdf8", bg_color="#0d213f"))
        mem_icon.setFixedSize(34, 34)

        mem_title_col = QVBoxLayout()
        mem_title_col.setSpacing(2)
        mem_title = QLabel("Memory Overview")
        mem_title.setStyleSheet("font-size:16px; font-weight:700; color:#ffffff;")
        mem_sub = QLabel("Monitor and manage your RAM usage")
        mem_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        mem_title_col.addWidget(mem_title)
        mem_title_col.addWidget(mem_sub)

        live_pill = QLabel("● Live")
        live_pill.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
        """)

        mem_hdr.addWidget(mem_icon)
        mem_hdr.addLayout(mem_title_col)
        mem_hdr.addStretch()
        mem_hdr.addWidget(live_pill)
        mem_layout.addLayout(mem_hdr)

        # Gauge + Legend Row
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(24)
        gauge_row.setContentsMargins(10, 8, 10, 8)

        self._gauge = DonutGauge()
        gauge_row.addWidget(self._gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        # Legend column
        legend_col = QVBoxLayout()
        legend_col.setSpacing(16)
        legend_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Item 1: Used Memory (Orange)
        used_item = QHBoxLayout()
        used_dot = QLabel("●")
        used_dot.setStyleSheet("color:#f97316; font-size:14px;")
        used_text_col = QVBoxLayout()
        used_text_col.setSpacing(1)
        used_title = QLabel("Used Memory")
        used_title.setStyleSheet("color:#8c9eb5; font-size:11px;")
        self._legend_used_val = QLabel("0.0 GB")
        self._legend_used_val.setStyleSheet("color:#ffffff; font-size:14px; font-weight:700;")
        used_text_col.addWidget(used_title)
        used_text_col.addWidget(self._legend_used_val)
        used_item.addWidget(used_dot)
        used_item.addLayout(used_text_col)

        # Item 2: Available Memory (Mint Green)
        avail_item = QHBoxLayout()
        avail_dot = QLabel("●")
        avail_dot.setStyleSheet("color:#10b981; font-size:14px;")
        avail_text_col = QVBoxLayout()
        avail_text_col.setSpacing(1)
        avail_title = QLabel("Available Memory")
        avail_title.setStyleSheet("color:#8c9eb5; font-size:11px;")
        self._legend_avail_val = QLabel("0.0 GB")
        self._legend_avail_val.setStyleSheet("color:#ffffff; font-size:14px; font-weight:700;")
        avail_text_col.addWidget(avail_title)
        avail_text_col.addWidget(self._legend_avail_val)
        avail_item.addWidget(avail_dot)
        avail_item.addLayout(avail_text_col)

        legend_col.addLayout(used_item)
        legend_col.addLayout(avail_item)
        gauge_row.addLayout(legend_col)
        gauge_row.addStretch()

        mem_layout.addLayout(gauge_row)

        # 3 Breakdown Bars
        bars_layout = QVBoxLayout()
        bars_layout.setSpacing(10)
        bars_layout.setContentsMargins(4, 4, 4, 4)

        self._ram_bar = ProgressBarRow("RAM Usage", "#3b82f6")
        self._used_bar = ProgressBarRow("Used Memory", "#f97316")
        self._avail_bar = ProgressBarRow("Available Memory", "#10b981")

        bars_layout.addWidget(self._ram_bar)
        bars_layout.addWidget(self._used_bar)
        bars_layout.addWidget(self._avail_bar)
        mem_layout.addLayout(bars_layout)

        top_section.addWidget(mem_card, 55)

        # ── Right: 4 Stat Cards ──
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        # Card 1: CPU USAGE
        self._cpu_card = StatCard(
            title="CPU USAGE",
            icon_pixmap=IconHelper.create_chip_icon(30, color="#38bdf8", bg_color="#0e1f3d"),
            badge_text="↓ 12%",
            badge_color="#10b981",
            sparkline_color="#38bdf8",
        )

        # Card 2: RUNNING APPLICATIONS
        self._apps_card = StatCard(
            title="RUNNING APPLICATIONS",
            icon_pixmap=IconHelper.create_grid_icon(30, color="#a855f7"),
            badge_text="↑ 5%",
            badge_color="#c084fc",
            sparkline_color="#a855f7",
        )

        # Card 3: BACKGROUND PROCESSES
        self._bg_card = StatCard(
            title="BACKGROUND PROCESSES",
            icon_pixmap=IconHelper.create_gear_icon(30, color="#2dd4bf"),
            badge_text="↓ 8%",
            badge_color="#10b981",
            sparkline_color="#2dd4bf",
        )

        # Card 4: SYSTEM STATUS
        self._status_card = SystemStatusCard()
        self._status_card.clicked.connect(self._on_optimize)

        right_col.addWidget(self._cpu_card)
        right_col.addWidget(self._apps_card)
        right_col.addWidget(self._bg_card)
        right_col.addWidget(self._status_card)

        top_section.addLayout(right_col, 45)
        root.addLayout(top_section)

        # ── 3. Middle Banner: OPTIMIZE MEMORY ──
        banner = QFrame()
        banner.setObjectName("optimize_banner")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(20, 14, 20, 14)
        b_layout.setSpacing(16)

        # Left Icon
        opt_icon_box = QLabel()
        opt_icon_box.setPixmap(IconHelper.create_lightning_icon(32, color="#ffffff"))
        opt_icon_box.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            min-width: 44px;
            min-height: 44px;
            max-width: 44px;
            max-height: 44px;
            qproperty-alignment: AlignCenter;
        """)

        # Text
        opt_text_col = QVBoxLayout()
        opt_text_col.setSpacing(2)
        opt_title = QLabel("OPTIMIZE MEMORY")
        opt_title.setStyleSheet("font-size:15px; font-weight:800; color:#ffffff; letter-spacing:0.5px;")
        opt_sub = QLabel("Free up memory by closing unnecessary applications")
        opt_sub.setStyleSheet("font-size:12px; color:rgba(255, 255, 255, 0.85);")
        opt_text_col.addWidget(opt_title)
        opt_text_col.addWidget(opt_sub)

        # Button
        self._opt_btn = QPushButton("🚀  Start Optimization →")
        self._opt_btn.setObjectName("optimize_btn")
        self._opt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._opt_btn.setFixedHeight(42)
        self._opt_btn.clicked.connect(self._on_optimize)

        b_layout.addWidget(opt_icon_box)
        b_layout.addLayout(opt_text_col, 1)
        b_layout.addWidget(self._opt_btn)
        root.addWidget(banner)

        # ── 4. Bottom Row: 4 Feature Cards ──
        feat_row = QHBoxLayout()
        feat_row.setSpacing(12)

        feat_1 = FeatureCard(
            icon_pixmap=IconHelper.create_monitor_icon(30, color="#3b82f6", bg_color="#0c1f3d"),
            title="Real-time Monitoring",
            desc="Monitor RAM, CPU and system performance in real-time.",
            accent_color="#3b82f6",
        )
        feat_1.clicked.connect(lambda: self.navigate_requested.emit("dashboard"))

        feat_2 = FeatureCard(
            icon_pixmap=IconHelper.create_shield_small(30, color="#10b981", bg_color="#0d2b20"),
            title="Smart & Safe",
            desc="Intelligent classification ensures system safety at all times.",
            accent_color="#10b981",
        )
        feat_2.clicked.connect(lambda: self.navigate_requested.emit("applications"))

        feat_3 = FeatureCard(
            icon_pixmap=IconHelper.create_lightning_icon(30, color="#a855f7"),
            title="One-Click Optimize",
            desc="Free memory safely with a single click.",
            accent_color="#a855f7",
        )
        feat_3.clicked.connect(lambda: self.navigate_requested.emit("optimization"))

        feat_4 = FeatureCard(
            icon_pixmap=IconHelper.create_lock_icon(30, color="#f59e0b", bg_color="#2b1f0d"),
            title="System Protection",
            desc="Protected processes will never be closed by RAMGuard.",
            accent_color="#f59e0b",
        )
        feat_4.clicked.connect(lambda: self.navigate_requested.emit("settings"))

        feat_row.addWidget(feat_1)
        feat_row.addWidget(feat_2)
        feat_row.addWidget(feat_3)
        feat_row.addWidget(feat_4)
        root.addLayout(feat_row)

        # ── 5. Footer: Timestamp & Live Status ──
        footer_layout = QHBoxLayout()
        self._footer_lbl = QLabel("Initializing…")
        self._footer_lbl.setStyleSheet("color:#64748b; font-size:11px;")
        footer_layout.addStretch()
        footer_layout.addWidget(self._footer_lbl)
        root.addLayout(footer_layout)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def update_snapshot(self, snap: MemorySnapshot) -> None:
        """Update dashboard UI with new memory snapshot."""
        # 1. Donut Gauge
        self._gauge.set_value(snap.percent, snap.pressure)

        # 2. Legend Values
        self._legend_used_val.setText(snap.used_display)
        self._legend_avail_val.setText(snap.available_display)

        # 3. Progress Bars
        pct = snap.percent
        used_pct = (snap.used_bytes / snap.total_bytes * 100.0) if snap.total_bytes else 0.0
        avail_pct = (snap.available_bytes / snap.total_bytes * 100.0) if snap.total_bytes else 0.0

        self._ram_bar.set_data(pct, f"{pct:.0f}%")
        self._used_bar.set_data(used_pct, snap.used_display)
        self._avail_bar.set_data(avail_pct, snap.available_display)

        # 4. Right column stat cards
        self._cpu_card.update_value(f"{snap.cpu_percent:.0f}%", snap.cpu_percent)
        self._apps_card.update_value(str(snap.process_count), float(snap.process_count))
        bg_count = max(snap.process_count - 15, 0)
        self._bg_card.update_value(str(bg_count), float(bg_count))

        # 5. System Status Card
        status_map = {
            "NORMAL": ("System Healthy", "#10b981"),
            "MODERATE": ("Moderate Usage", "#f59e0b"),
            "HIGH": ("High Memory Usage", "#f97316"),
            "CRITICAL": ("Critical — Optimize Now!", "#ef4444"),
        }
        status_text, status_color = status_map.get(snap.pressure.value, ("System Healthy", "#10b981"))
        self._status_card.set_status(status_text, status_color)

        # 6. Footer
        now = datetime.datetime.now().strftime("%d %b %Y — %I:%M:%S %p")
        self._footer_lbl.setText(f"Last updated: {now}  •  ● Monitoring Active")

    def set_optimize_enabled(self, enabled: bool) -> None:
        self._opt_btn.setEnabled(enabled)
        self._opt_btn.setText("🚀  Start Optimization →" if enabled else "⏳  Optimizing…")
