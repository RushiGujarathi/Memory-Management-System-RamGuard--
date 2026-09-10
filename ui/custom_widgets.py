"""
RAMGuard Custom UI Widgets
Pixel-accurate components matching the reference design:
- DonutGauge: circular gradient ring with center percentage
- SparklineWidget: animated wave area graph with smooth spline & gradient fill
- StatCard: stat metric card with icon, title, trend badge, value, and sparkline
- SystemStatusCard: status card with warning icon, severity text, and chevron
- ProgressBarWidget: smooth antialiased pill progress bar with optional gradient
- ProgressBarRow: sleek horizontal progress bar with label and value
- FeatureCard: bottom action card with colored border, icon, and arrow
"""

from collections import deque
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPainterPath, QPen, QColor, QBrush, QFont,
    QLinearGradient, QConicalGradient
)
from core.memory_monitor import MemoryPressure
from ui.icon_helper import IconHelper
from ui.styles import rgba


class DonutGauge(QWidget):
    """Circular donut RAM gauge with smooth gradient arc and center text."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._percent = 0.0
        self._pressure = MemoryPressure.NORMAL
        self.setFixedSize(180, 180)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_value(self, percent: float, pressure: MemoryPressure = MemoryPressure.NORMAL) -> None:
        self._percent = max(0.0, min(100.0, percent))
        self._pressure = pressure
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        center = QPointF(w / 2, h / 2)
        radius = min(w, h) / 2 - 16
        thickness = 16.0

        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        # ── Background track ──
        track_pen = QPen(QColor("#132038"), thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        start_angle = 225
        total_span = -270
        painter.drawArc(rect, int(start_angle * 16), int(total_span * 16))

        # ── Value arc with gradient ──
        if self._percent > 0:
            val_span = int(total_span * 16 * (self._percent / 100.0))

            grad = QConicalGradient(center, 225)
            grad.setColorAt(0.0, QColor("#00d2ff"))
            grad.setColorAt(0.35, QColor("#2563eb"))
            grad.setColorAt(0.75, QColor("#9333ea"))
            grad.setColorAt(1.0, QColor("#a855f7"))

            val_pen = QPen(QBrush(grad), thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(val_pen)
            painter.drawArc(rect, int(start_angle * 16), val_span)

        # ── Center Text ──
        painter.setPen(QColor("#ffffff"))
        val_font = QFont("Segoe UI", 26, QFont.Weight.Bold)
        painter.setFont(val_font)
        painter.drawText(
            QRectF(0, h / 2 - 28, w, 36),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._percent:.0f}%",
        )

        sub_font = QFont("Segoe UI", 9, QFont.Weight.Medium)
        painter.setFont(sub_font)
        painter.setPen(QColor("#8c9eb5"))
        painter.drawText(
            QRectF(0, h / 2 + 10, w, 20),
            Qt.AlignmentFlag.AlignCenter,
            "RAM Usage",
        )

        painter.end()


class SparklineWidget(QWidget):
    """
    Smooth bezier wave area chart with vertical gradient fill underneath.
    Maintains a sliding buffer of recent values.
    """

    def __init__(self, color_hex: str = "#38bdf8", parent=None) -> None:
        super().__init__(parent)
        self._color_hex = color_hex
        self._buffer = deque(maxlen=16)
        seed_pattern = [28, 32, 30, 36, 34, 40, 38, 44, 42, 39, 45, 42, 48, 44, 46, 45]
        for val in seed_pattern:
            self._buffer.append(float(val))

        self.setFixedHeight(34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_point(self, value: float) -> None:
        self._buffer.append(float(value))
        self.update()

    def set_color(self, color_hex: str) -> None:
        self._color_hex = color_hex
        self.update()

    def paintEvent(self, event) -> None:
        if len(self._buffer) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        pad_top = 4.0
        pad_bottom = 3.0
        avail_h = h - pad_top - pad_bottom

        min_val = min(self._buffer)
        max_val = max(self._buffer)
        val_range = max_val - min_val if max_val > min_val else 1.0

        pts: list[QPointF] = []
        n = len(self._buffer)
        dx = w / (n - 1) if n > 1 else w

        for i, val in enumerate(self._buffer):
            x = i * dx
            norm = (val - min_val) / val_range
            clamped = 0.2 + norm * 0.65
            y = pad_top + (1.0 - clamped) * avail_h
            pts.append(QPointF(x, y))

        curve_path = QPainterPath()
        curve_path.moveTo(pts[0])

        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            cx1 = p0.x() + (p1.x() - p0.x()) / 2
            cy1 = p0.y()
            cx2 = cx1
            cy2 = p1.y()
            curve_path.cubicTo(QPointF(cx1, cy1), QPointF(cx2, cy2), p1)

        area_path = QPainterPath(curve_path)
        area_path.lineTo(w, h)
        area_path.lineTo(0, h)
        area_path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        c_top = QColor(self._color_hex)
        c_top.setAlpha(95)
        c_mid = QColor(self._color_hex)
        c_mid.setAlpha(35)
        c_bot = QColor(self._color_hex)
        c_bot.setAlpha(0)

        grad.setColorAt(0.0, c_top)
        grad.setColorAt(0.6, c_mid)
        grad.setColorAt(1.0, c_bot)

        painter.fillPath(area_path, grad)

        pen = QPen(QColor(self._color_hex), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(curve_path)

        painter.end()


class ProgressBarWidget(QWidget):
    """Smooth antialiased pill progress bar with optional linear gradient fill."""

    def __init__(
        self,
        color_hex: str = "#3b82f6",
        end_color_hex: str = "",
        height: int = 8,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color_hex)
        self._end_color = QColor(end_color_hex) if end_color_hex else None
        self._percent = 0.0
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_percent(self, pct: float) -> None:
        self._percent = max(0.0, min(100.0, pct))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        r = h / 2.0

        # Background track
        painter.setBrush(QColor("#132035"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        # Progress chunk
        if self._percent > 0:
            fill_w = max(h, w * (self._percent / 100.0))
            if self._end_color:
                grad = QLinearGradient(0, 0, w, 0)
                grad.setColorAt(0.0, self._color)
                grad.setColorAt(1.0, self._end_color)
                painter.setBrush(grad)
            else:
                painter.setBrush(self._color)

            painter.drawRoundedRect(QRectF(0, 0, min(w, fill_w), h), r, r)

        painter.end()


class StatCard(QFrame):
    """
    Stat metric card matching the right-column cards in the reference image:
    - Top row: Icon in styled box + uppercase title + trend badge (e.g. '↓ 12%')
    - Value row: Large bold value (e.g. '36%')
    - Bottom: Sparkline wave area chart
    """

    def __init__(
        self,
        title: str,
        icon_pixmap,
        badge_text: str = "",
        badge_color: str = "#10b981",
        sparkline_color: str = "#38bdf8",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setStyleSheet("""
            QFrame#stat_card {
                background-color: #0b1526;
                border: 1px solid rgba(59, 130, 246, 0.16);
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(icon_pixmap)
        self._icon_lbl.setFixedSize(30, 30)
        self._icon_lbl.setStyleSheet("border: none; background: transparent;")

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet("""
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            border: none;
        """)

        self._badge_lbl = QLabel(badge_text)
        self._badge_color = badge_color
        self._update_badge_style(badge_text, badge_color)

        top_row.addWidget(self._icon_lbl)
        top_row.addWidget(self._title_lbl)
        top_row.addStretch()
        top_row.addWidget(self._badge_lbl)
        layout.addLayout(top_row)

        # ── Row 2: Value on left, Sparkline on right ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        bottom_row.setContentsMargins(0, 0, 0, 0)

        self._val_lbl = QLabel("—")
        self._val_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 26px;
            font-weight: 800;
            min-width: 65px;
            border: none;
        """)
        bottom_row.addWidget(self._val_lbl)

        self._sparkline = SparklineWidget(sparkline_color)
        bottom_row.addWidget(self._sparkline, 1)

        layout.addLayout(bottom_row)

    def _update_badge_style(self, text: str, color: str) -> None:
        if not text:
            self._badge_lbl.setVisible(False)
            return
        self._badge_lbl.setText(text)
        self._badge_lbl.setVisible(True)
        self._badge_lbl.setStyleSheet(f"""
            background-color: {rgba(color, "25")};
            color: {color};
            border: 1px solid {rgba(color, "60")};
            border-radius: 9px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
        """)

    def update_value(self, value_text: str, numeric_val: float = None) -> None:
        self._val_lbl.setText(value_text)
        if numeric_val is not None:
            self._sparkline.add_point(numeric_val)

    def update_badge(self, text: str, color: str = "") -> None:
        if color:
            self._badge_color = color
        self._update_badge_style(text, self._badge_color)


class SystemStatusCard(QFrame):
    """
    SYSTEM STATUS card (4th card in the right column):
    - Left: Warning triangle inside glowing dark-coral box
    - Middle: 'SYSTEM STATUS' + 'Critical — Optimize Now!' / 'System Healthy'
    - Right: Chevron '>'
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("status_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#status_card {
                background-color: #0b1526;
                border: 1px solid rgba(239, 68, 68, 0.28);
                border-radius: 14px;
            }
            QFrame#status_card:hover {
                border-color: rgba(239, 68, 68, 0.55);
                background-color: #0e182c;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self._icon_lbl = QLabel()
        self._icon_lbl.setPixmap(IconHelper.create_warning_icon(32, color="#ef4444", bg_color="#2b1419"))
        self._icon_lbl.setFixedSize(32, 32)
        self._icon_lbl.setStyleSheet("border: none; background: transparent;")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self._title_lbl = QLabel("SYSTEM STATUS")
        self._title_lbl.setStyleSheet("color:#8c9eb5;font-size:10px;font-weight:700;letter-spacing:0.8px; border:none;")

        self._val_lbl = QLabel("System Healthy")
        self._val_lbl.setStyleSheet("color:#10b981;font-size:15px;font-weight:700; border:none;")

        text_col.addWidget(self._title_lbl)
        text_col.addWidget(self._val_lbl)

        chevron = QLabel("›")
        chevron.setStyleSheet("color:#64748b;font-size:22px;font-weight:300;padding-right:4px; border:none;")

        layout.addWidget(self._icon_lbl)
        layout.addLayout(text_col, 1)
        layout.addWidget(chevron)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_status(self, text: str, color: str, icon_color: str = "#ef4444") -> None:
        self._val_lbl.setText(text)
        self._val_lbl.setStyleSheet(f"color:{color};font-size:15px;font-weight:700;")

        is_critical = "critical" in text.lower() or "high" in text.lower()
        if is_critical:
            self._icon_lbl.setPixmap(IconHelper.create_warning_icon(32, color="#ef4444", bg_color="#381419"))
            self.setStyleSheet("""
                QFrame#status_card {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(239, 68, 68, 0.22), stop:1 #1c0e14);
                    border: 1.5px solid rgba(239, 68, 68, 0.6);
                    border-radius: 14px;
                }
                QFrame#status_card:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(239, 68, 68, 0.32), stop:1 #24111a);
                    border: 1.5px solid #ef4444;
                }
            """)
        else:
            self._icon_lbl.setPixmap(IconHelper.create_shield_small(32, color="#10b981", bg_color="#0d2b20"))
            self.setStyleSheet("""
                QFrame#status_card {
                    background-color: #0b1526;
                    border: 1px solid rgba(59, 130, 246, 0.2);
                    border-radius: 14px;
                }
                QFrame#status_card:hover {
                    border-color: #10b981;
                    background-color: #0e1c34;
                }
            """)


class ProgressBarRow(QWidget):
    """
    Sleek progress bar row with label, colored rounded progress bar, and value text.
    """

    def __init__(self, label: str, bar_color: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600; min-width: 110px;")

        self._bar = ProgressBarWidget(bar_color, height=12)

        self._val_lbl = QLabel("—")
        self._val_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 700; min-width: 55px;")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._lbl)
        layout.addWidget(self._bar, 1)
        layout.addWidget(self._val_lbl)

    def set_data(self, percent: float, display_text: str) -> None:
        self._val_lbl.setText(display_text)
        self._bar.set_percent(percent)


class FeatureCard(QFrame):
    """
    Bottom row feature card:
    - Glowing subtle border
    - Vector icon in colored rounded box
    - Bold title
    - Description text
    - Colored arrow in the bottom right corner
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        icon_pixmap,
        title: str,
        desc: str,
        accent_color: str = "#3b82f6",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("feature_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._accent = accent_color

        self.setStyleSheet(f"""
            QFrame#feature_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {rgba(accent_color, "18")}, stop:1 #0b1526);
                border: 1px solid {rgba(accent_color, "35")};
                border-radius: 14px;
            }}
            QFrame#feature_card:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {rgba(accent_color, "2a")}, stop:1 #0e1c34);
                border: 1px solid {rgba(accent_color, "88")};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self._icon = QLabel()
        self._icon.setPixmap(icon_pixmap)
        self._icon.setFixedSize(30, 30)
        self._icon.setStyleSheet("border: none; background: transparent;")

        self._title = QLabel(title)
        self._title.setStyleSheet("color:#ffffff; font-size:14px; font-weight:700; border:none;")

        self._desc = QLabel(desc)
        self._desc.setStyleSheet("color:#cbd5e1; font-size:11px; line-height:1.3; border:none;")
        self._desc.setWordWrap(True)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color:{accent_color}; font-size:16px; font-weight:700;")
        bottom_row.addWidget(arrow)

        layout.addWidget(self._icon)
        layout.addWidget(self._title)
        layout.addWidget(self._desc)
        layout.addStretch()
        layout.addLayout(bottom_row)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
