"""
RAMGuard Vector Icon System
Renders crisp, high-DPI custom vector icons using QPainter and QPainterPath.
Matches the modern dark glassmorphic UI design perfectly.
"""

from PyQt6.QtGui import (
    QPixmap, QPainter, QPainterPath, QPen, QColor, QBrush, QLinearGradient, QFont
)
from PyQt6.QtCore import Qt, QPointF, QRectF


class IconHelper:
    """Helper to render pixel-perfect vector icons as QPixmap or QIcon."""

    @staticmethod
    def create_shield_icon(size: int = 40, glowing: bool = True) -> QPixmap:
        """Shield with glowing outer rim and inner memory circuit design."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pad = s * 0.08
        w = s - 2 * pad
        h = s - 2 * pad

        # Shield path
        path = QPainterPath()
        top_left = QPointF(pad, pad + h * 0.15)
        top_center = QPointF(pad + w * 0.5, pad)
        top_right = QPointF(pad + w, pad + h * 0.15)
        bottom_center = QPointF(pad + w * 0.5, pad + h)

        path.moveTo(top_left)
        path.quadTo(pad + w * 0.25, pad, top_center.x(), top_center.y())
        path.quadTo(pad + w * 0.75, pad, top_right.x(), top_right.y())
        path.cubicTo(pad + w, pad + h * 0.6, pad + w * 0.75, pad + h * 0.85, bottom_center.x(), bottom_center.y())
        path.cubicTo(pad + w * 0.25, pad + h * 0.85, pad, pad + h * 0.6, top_left.x(), top_left.y())
        path.closeSubpath()

        # Fill background gradient
        grad = QLinearGradient(0, pad, 0, pad + h)
        grad.setColorAt(0.0, QColor("#1e40af"))
        grad.setColorAt(1.0, QColor("#0f214d"))
        painter.fillPath(path, grad)

        # Border
        pen = QPen(QColor("#60a5fa"), max(1.5, s * 0.04))
        painter.setPen(pen)
        painter.drawPath(path)

        # Inner emblem: Memory chip / Lock
        cx = s * 0.5
        cy = s * 0.52
        rw = s * 0.28
        rh = s * 0.32

        # Draw chip body
        chip_rect = QRectF(cx - rw / 2, cy - rh / 2, rw, rh)
        painter.setBrush(QColor("#3b82f6"))
        painter.setPen(QPen(QColor("#93c5fd"), max(1.0, s * 0.03)))
        painter.drawRoundedRect(chip_rect, s * 0.05, s * 0.05)

        # Draw pins / circuits
        painter.setPen(QPen(QColor("#bfdbfe"), max(1.0, s * 0.035)))
        # Left/Right pins
        for i in range(-1, 2):
            py = cy + i * (rh * 0.3)
            painter.drawLine(QPointF(cx - rw / 2 - s * 0.05, py), QPointF(cx - rw / 2, py))
            painter.drawLine(QPointF(cx + rw / 2, py), QPointF(cx + rw / 2 + s * 0.05, py))

        # Inner dot
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), s * 0.04, s * 0.04)

        painter.end()
        return pixmap

    @staticmethod
    def create_home_icon(size: int = 24, color: str = "#ffffff") -> QPixmap:
        """Dashboard home icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pad = s * 0.15
        w = s - 2 * pad
        h = s - 2 * pad

        path = QPainterPath()
        path.moveTo(pad + w * 0.5, pad)
        path.lineTo(pad + w, pad + h * 0.45)
        path.lineTo(pad + w * 0.85, pad + h * 0.45)
        path.lineTo(pad + w * 0.85, pad + h)
        path.lineTo(pad + w * 0.15, pad + h)
        path.lineTo(pad + w * 0.15, pad + h * 0.45)
        path.lineTo(pad, pad + h * 0.45)
        path.closeSubpath()

        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(path, QColor(color))

        # Door cutout
        door = QRectF(pad + w * 0.4, pad + h * 0.6, w * 0.2, h * 0.4)
        painter.setBrush(QColor("#0a1220"))
        painter.drawRoundedRect(door, 2, 2)

        painter.end()
        return pixmap

    @staticmethod
    def create_grid_icon(size: int = 24, color: str = "#8c9eb5") -> QPixmap:
        """Applications 4-square grid icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        gap = s * 0.14
        box_size = (s - gap * 3) / 2
        radius = box_size * 0.3

        painter.setPen(QPen(QColor(color), max(1.5, s * 0.07)))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        coords = [
            (gap, gap),
            (gap * 2 + box_size, gap),
            (gap, gap * 2 + box_size),
            (gap * 2 + box_size, gap * 2 + box_size),
        ]
        for x, y in coords:
            painter.drawRoundedRect(QRectF(x, y, box_size, box_size), radius, radius)

        painter.end()
        return pixmap

    @staticmethod
    def create_lightning_icon(size: int = 24, color: str = "#38bdf8") -> QPixmap:
        """Optimization lightning bolt icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        path = QPainterPath()
        path.moveTo(s * 0.58, s * 0.1)
        path.lineTo(s * 0.22, s * 0.52)
        path.lineTo(s * 0.48, s * 0.52)
        path.lineTo(s * 0.38, s * 0.9)
        path.lineTo(s * 0.78, s * 0.44)
        path.lineTo(s * 0.52, s * 0.44)
        path.closeSubpath()

        painter.fillPath(path, QColor(color))
        painter.end()
        return pixmap

    @staticmethod
    def create_rocket_icon(size: int = 24, color: str = "#8c9eb5") -> QPixmap:
        """Startup Manager rocket icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pen = QPen(QColor(color), max(1.5, s * 0.07))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Simplified sleek rocket body
        path = QPainterPath()
        path.moveTo(s * 0.8, s * 0.2)
        path.cubicTo(s * 0.75, s * 0.4, s * 0.65, s * 0.6, s * 0.35, s * 0.65)
        path.lineTo(s * 0.25, s * 0.75)
        path.lineTo(s * 0.35, s * 0.85)
        path.lineTo(s * 0.45, s * 0.75)
        path.cubicTo(s * 0.5, s * 0.45, s * 0.7, s * 0.35, s * 0.8, s * 0.2)
        painter.drawPath(path)

        # Wings
        painter.drawLine(QPointF(s * 0.38, s * 0.58), QPointF(s * 0.2, s * 0.58))
        painter.drawLine(QPointF(s * 0.52, s * 0.44), QPointF(s * 0.52, s * 0.26))

        # Jet fire
        painter.drawLine(QPointF(s * 0.22, s * 0.78), QPointF(s * 0.12, s * 0.88))

        painter.end()
        return pixmap

    @staticmethod
    def create_clock_icon(size: int = 24, color: str = "#8c9eb5") -> QPixmap:
        """History clock icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pad = s * 0.15
        pen = QPen(QColor(color), max(1.5, s * 0.07))
        painter.setPen(pen)

        painter.drawEllipse(QRectF(pad, pad, s - 2 * pad, s - 2 * pad))
        cx, cy = s * 0.5, s * 0.5
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - s * 0.22))
        painter.drawLine(QPointF(cx, cy), QPointF(cx + s * 0.18, cy))

        painter.end()
        return pixmap

    @staticmethod
    def create_gear_icon(size: int = 24, color: str = "#8c9eb5") -> QPixmap:
        """Settings gear icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pen = QPen(QColor(color), max(1.5, s * 0.07))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = s * 0.5, s * 0.5
        r_outer = s * 0.36
        r_inner = s * 0.18

        # Draw circle and teeth
        painter.drawEllipse(QPointF(cx, cy), r_outer, r_outer)
        painter.drawEllipse(QPointF(cx, cy), r_inner, r_inner)

        # Teeth lines
        import math
        for i in range(8):
            angle = i * (math.pi / 4)
            x1 = cx + math.cos(angle) * (r_outer - 1)
            y1 = cy + math.sin(angle) * (r_outer - 1)
            x2 = cx + math.cos(angle) * (r_outer + s * 0.08)
            y2 = cy + math.sin(angle) * (r_outer + s * 0.08)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.end()
        return pixmap

    @staticmethod
    def create_chip_icon(size: int = 28, color: str = "#38bdf8", bg_color: str = "#0d213f") -> QPixmap:
        """CPU / Memory chip badge icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        # Background rounded box
        if bg_color:
            painter.setBrush(QColor(bg_color))
            painter.setPen(QPen(QColor(color).lighter(120), 1))
            painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.22, s * 0.22)

        cx, cy = s * 0.5, s * 0.5
        cw = s * 0.44
        ch = s * 0.44

        # Chip core
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(cx - cw / 2, cy - ch / 2, cw, ch), s * 0.08, s * 0.08)

        # Pins
        painter.setPen(QPen(QColor(color), max(1.2, s * 0.05)))
        for offset in [-cw * 0.28, 0, cw * 0.28]:
            # Top/Bottom
            painter.drawLine(QPointF(cx + offset, cy - ch / 2), QPointF(cx + offset, cy - ch / 2 - s * 0.09))
            painter.drawLine(QPointF(cx + offset, cy + ch / 2), QPointF(cx + offset, cy + ch / 2 + s * 0.09))
            # Left/Right
            painter.drawLine(QPointF(cx - cw / 2, cy + offset), QPointF(cx - cw / 2 - s * 0.09, cy + offset))
            painter.drawLine(QPointF(cx + cw / 2, cy + offset), QPointF(cx + cw / 2 + s * 0.09, cy + offset))

        # Inner core point
        painter.setBrush(QColor("#0a1220"))
        painter.drawRect(QRectF(cx - s * 0.08, cy - s * 0.08, s * 0.16, s * 0.16))

        painter.end()
        return pixmap

    @staticmethod
    def create_warning_icon(size: int = 28, color: str = "#ef4444", bg_color: str = "#381419") -> QPixmap:
        """System Status Warning triangle icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        if bg_color:
            painter.setBrush(QColor(bg_color))
            painter.setPen(QPen(QColor(color).darker(110), 1))
            painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.22, s * 0.22)

        path = QPainterPath()
        path.moveTo(s * 0.5, s * 0.22)
        path.lineTo(s * 0.78, s * 0.75)
        path.lineTo(s * 0.22, s * 0.75)
        path.closeSubpath()

        painter.fillPath(path, QColor(color))

        # Exclamation mark
        painter.setPen(QPen(QColor("#ffffff"), max(1.5, s * 0.06), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(s * 0.5, s * 0.42), QPointF(s * 0.5, s * 0.57))
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(s * 0.5, s * 0.67), s * 0.035, s * 0.035)

        painter.end()
        return pixmap

    @staticmethod
    def create_monitor_icon(size: int = 28, color: str = "#3b82f6", bg_color: str = "#0d1f3b") -> QPixmap:
        """Real-time monitoring icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        if bg_color:
            painter.setBrush(QColor(bg_color))
            painter.setPen(QPen(QColor(color).lighter(120), 1))
            painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.22, s * 0.22)

        # Monitor screen
        pen = QPen(QColor(color), max(1.2, s * 0.05))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.22, s * 0.6, s * 0.42), 2, 2)

        # Stand
        painter.drawLine(QPointF(s * 0.5, s * 0.64), QPointF(s * 0.5, s * 0.74))
        painter.drawLine(QPointF(s * 0.35, s * 0.74), QPointF(s * 0.65, s * 0.74))

        # Wave line inside
        path = QPainterPath()
        path.moveTo(s * 0.26, s * 0.46)
        path.lineTo(s * 0.38, s * 0.46)
        path.lineTo(s * 0.45, s * 0.32)
        path.lineTo(s * 0.54, s * 0.54)
        path.lineTo(s * 0.62, s * 0.46)
        path.lineTo(s * 0.74, s * 0.46)
        painter.drawPath(path)

        painter.end()
        return pixmap

    @staticmethod
    def create_shield_small(size: int = 28, color: str = "#10b981", bg_color: str = "#0d2b20") -> QPixmap:
        """Shield icon for Smart & Safe / Protection."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        if bg_color:
            painter.setBrush(QColor(bg_color))
            painter.setPen(QPen(QColor(color).lighter(120), 1))
            painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.22, s * 0.22)

        path = QPainterPath()
        path.moveTo(s * 0.26, s * 0.3)
        path.lineTo(s * 0.5, s * 0.22)
        path.lineTo(s * 0.74, s * 0.3)
        path.cubicTo(s * 0.74, s * 0.56, s * 0.6, s * 0.72, s * 0.5, s * 0.78)
        path.cubicTo(s * 0.4, s * 0.72, s * 0.26, s * 0.56, s * 0.26, s * 0.3)
        path.closeSubpath()

        painter.fillPath(path, QColor(color))

        # Inner checkmark
        pen = QPen(QColor("#0a1220"), max(1.5, s * 0.06), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(s * 0.4, s * 0.5), QPointF(s * 0.47, s * 0.58))
        painter.drawLine(QPointF(s * 0.47, s * 0.58), QPointF(s * 0.62, s * 0.42))

        painter.end()
        return pixmap

    @staticmethod
    def create_lock_icon(size: int = 28, color: str = "#f59e0b", bg_color: str = "#30220e") -> QPixmap:
        """Lock icon for System Protection."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        if bg_color:
            painter.setBrush(QColor(bg_color))
            painter.setPen(QPen(QColor(color).lighter(120), 1))
            painter.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.22, s * 0.22)

        # Shackle
        pen = QPen(QColor(color), max(1.3, s * 0.055))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(s * 0.34, s * 0.22, s * 0.32, s * 0.35), 0, 180 * 16)

        # Body
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(s * 0.28, s * 0.44, s * 0.44, s * 0.34), 3, 3)

        # Keyhole
        painter.setBrush(QColor("#0a1220"))
        painter.drawEllipse(QPointF(s * 0.5, s * 0.57), s * 0.05, s * 0.05)
        painter.drawRect(QRectF(s * 0.48, s * 0.58, s * 0.04, s * 0.09))

        painter.end()
        return pixmap

    @staticmethod
    def create_chrome_icon(size: int = 24) -> QPixmap:
        """Google Chrome multi-colored vector logo."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        cx, cy = s * 0.5, s * 0.5
        r = s * 0.44

        # Red sector
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ea4335"))
        painter.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), 60 * 16, 120 * 16)

        # Green sector
        painter.setBrush(QColor("#34a853"))
        painter.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), 180 * 16, 120 * 16)

        # Yellow sector
        painter.setBrush(QColor("#fbbc05"))
        painter.drawPie(QRectF(cx - r, cy - r, r * 2, r * 2), 300 * 16, 120 * 16)

        # White inner ring
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QPointF(cx, cy), r * 0.48, r * 0.48)

        # Blue core
        painter.setBrush(QColor("#4285f4"))
        painter.drawEllipse(QPointF(cx, cy), r * 0.38, r * 0.38)

        painter.end()
        return pixmap

    @staticmethod
    def create_antigravity_icon(size: int = 24) -> QPixmap:
        """Antigravity IDE electric cyan code/atom icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        cx, cy = s * 0.5, s * 0.5

        pen = QPen(QColor("#00d2ff"), max(1.8, s * 0.08), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw crossed loop / chevron brackets
        path = QPainterPath()
        path.moveTo(s * 0.22, s * 0.25)
        path.lineTo(s * 0.44, s * 0.5)
        path.lineTo(s * 0.22, s * 0.75)
        painter.drawPath(path)

        path2 = QPainterPath()
        path2.moveTo(s * 0.78, s * 0.25)
        path2.lineTo(s * 0.56, s * 0.5)
        path2.lineTo(s * 0.78, s * 0.75)
        painter.drawPath(path2)

        # Center dot
        painter.setBrush(QColor("#38bdf8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), s * 0.08, s * 0.08)

        painter.end()
        return pixmap

    @staticmethod
    def create_defender_icon(size: int = 24) -> QPixmap:
        """Windows Defender (MsMpEng) security shield icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        cx, cy = s * 0.5, s * 0.5

        # Shield star/gear shape
        painter.setBrush(QColor("#38bdf8"))
        painter.setPen(QPen(QColor("#60a5fa"), 1))
        painter.drawRoundedRect(QRectF(s * 0.15, s * 0.15, s * 0.7, s * 0.7), 4, 4)

        # Inner cross
        painter.setPen(QPen(QColor("#0b1930"), max(1.8, s * 0.08), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(cx, s * 0.3), QPointF(cx, s * 0.7))
        painter.drawLine(QPointF(s * 0.3, cy), QPointF(s * 0.7, cy))

        painter.end()
        return pixmap

    @staticmethod
    def create_memcompression_icon(size: int = 24) -> QPixmap:
        """MemCompression orange memory layer icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        painter.setBrush(QColor("#f97316"))
        painter.setPen(Qt.PenStyle.NoPen)

        # Three stacked layers
        for i in range(3):
            y = s * 0.22 + i * (s * 0.22)
            painter.drawRoundedRect(QRectF(s * 0.15, y, s * 0.7, s * 0.15), 3, 3)

        painter.end()
        return pixmap

    @staticmethod
    def create_folder_icon(size: int = 24) -> QPixmap:
        """Windows Explorer folder icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        # Tab
        painter.setBrush(QColor("#eab308"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(s * 0.15, s * 0.2, s * 0.35, s * 0.2), 2, 2)
        # Body
        painter.setBrush(QColor("#facc15"))
        painter.drawRoundedRect(QRectF(s * 0.15, s * 0.3, s * 0.7, s * 0.48), 3, 3)

        painter.end()
        return pixmap

    @staticmethod
    def create_python_icon(size: int = 24) -> QPixmap:
        """Python / pyrefly development badge icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        # Terminal dark box with green text
        painter.setBrush(QColor("#1e293b"))
        painter.setPen(QPen(QColor("#10b981"), 1.2))
        painter.drawRoundedRect(QRectF(s * 0.12, s * 0.12, s * 0.76, s * 0.76), 4, 4)

        # Code prompt '>_'
        painter.setPen(QPen(QColor("#10b981"), max(1.5, s * 0.07), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(s * 0.26, s * 0.38), QPointF(s * 0.44, s * 0.5))
        painter.drawLine(QPointF(s * 0.44, s * 0.5), QPointF(s * 0.26, s * 0.62))
        painter.drawLine(QPointF(s * 0.52, s * 0.62), QPointF(s * 0.72, s * 0.62))

        painter.end()
        return pixmap

    @staticmethod
    def create_generic_app_icon(size: int = 24) -> QPixmap:
        """Clean generic application window vector icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        # Window frame
        painter.setBrush(QColor("#0d2242"))
        painter.setPen(QPen(QColor("#38bdf8"), 1))
        painter.drawRoundedRect(QRectF(s * 0.12, s * 0.12, s * 0.76, s * 0.76), 4, 4)

        # Titlebar line
        painter.drawLine(QPointF(s * 0.12, s * 0.34), QPointF(s * 0.88, s * 0.34))

        # Dot buttons
        painter.setBrush(QColor("#38bdf8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(s * 0.26, s * 0.23), s * 0.04, s * 0.04)
        painter.drawEllipse(QPointF(s * 0.38, s * 0.23), s * 0.04, s * 0.04)

        painter.end()
        return pixmap

    @classmethod
    def get_process_icon(cls, process_name: str, size: int = 24) -> QPixmap:
        """Selects a matching high-DPI vector icon based on the process name."""
        name = process_name.lower()
        if "chrome" in name:
            return cls.create_chrome_icon(size)
        elif "antigravity" in name:
            return cls.create_antigravity_icon(size)
        elif "msmpeng" in name or "defender" in name:
            return cls.create_defender_icon(size)
        elif "memcompression" in name:
            return cls.create_memcompression_icon(size)
        elif "explorer" in name:
            return cls.create_folder_icon(size)
        elif "python" in name or "pyrefly" in name:
            return cls.create_python_icon(size)
        elif "language_server" in name or "host" in name or "service" in name:
            return cls.create_gear_icon(size, color="#2dd4bf")
        else:
            return cls.create_generic_app_icon(size)

    @staticmethod
    def create_funnel_icon(size: int = 18, color: str = "#8c9eb5") -> QPixmap:
        """Funnel/filter icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        path = QPainterPath()
        path.moveTo(s * 0.15, s * 0.2)
        path.lineTo(s * 0.85, s * 0.2)
        path.lineTo(s * 0.58, s * 0.55)
        path.lineTo(s * 0.58, s * 0.82)
        path.lineTo(s * 0.42, s * 0.72)
        path.lineTo(s * 0.42, s * 0.55)
        path.closeSubpath()

        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(path, QColor(color))

        painter.end()
        return pixmap

    @staticmethod
    def create_search_icon(size: int = 18, color: str = "#8c9eb5") -> QPixmap:
        """Search magnifying glass icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pen = QPen(QColor(color), max(1.5, s * 0.09))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        r = s * 0.28
        cx, cy = s * 0.42, s * 0.42
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(s * 0.82, s * 0.82))

        painter.end()
        return pixmap

    @staticmethod
    def create_refresh_icon(size: int = 18, color: str = "#38bdf8") -> QPixmap:
        """Circular refresh arrows icon."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pen = QPen(QColor(color), max(1.5, s * 0.09), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        r = s * 0.32
        cx, cy = s * 0.5, s * 0.5
        painter.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 45 * 16, 270 * 16)

        # Arrow head
        path = QPainterPath()
        path.moveTo(s * 0.66, s * 0.18)
        path.lineTo(s * 0.82, s * 0.26)
        path.lineTo(s * 0.72, s * 0.42)
        path.closeSubpath()
        painter.setBrush(QColor(color))
        painter.drawPath(path)

        painter.end()
        return pixmap

    @staticmethod
    def create_eye_icon(size: int = 18, color: str = "#ffffff") -> QPixmap:
        """Eye icon for View Details button."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        cx, cy = s * 0.5, s * 0.5

        path = QPainterPath()
        path.moveTo(s * 0.15, cy)
        path.quadTo(cx, s * 0.18, s * 0.85, cy)
        path.quadTo(cx, s * 0.82, s * 0.15, cy)

        pen = QPen(QColor(color), max(1.4, s * 0.08))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), s * 0.14, s * 0.14)

        painter.end()
        return pixmap

    @staticmethod
    def create_trash_icon(size: int = 18, color: str = "#ffffff") -> QPixmap:
        """Trash/close icon for Close Selected button."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(size)
        pen = QPen(QColor(color), max(1.4, s * 0.08), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Lid
        painter.drawLine(QPointF(s * 0.25, s * 0.3), QPointF(s * 0.75, s * 0.3))
        painter.drawLine(QPointF(s * 0.4, s * 0.2), QPointF(s * 0.6, s * 0.2))

        # Can body
        path = QPainterPath()
        path.moveTo(s * 0.3, s * 0.3)
        path.lineTo(s * 0.34, s * 0.82)
        path.lineTo(s * 0.66, s * 0.82)
        path.lineTo(s * 0.7, s * 0.3)
        painter.drawPath(path)

        # Vertical ribs
        painter.drawLine(QPointF(s * 0.44, s * 0.4), QPointF(s * 0.44, s * 0.72))
        painter.drawLine(QPointF(s * 0.56, s * 0.4), QPointF(s * 0.56, s * 0.72))

        painter.end()
        return pixmap

