"""
RAMGuard UI Styles
Single-source-of-truth dark-navy design system.

Token palette
─────────────
bg-deep    : #060d17   (page background)
bg-panel   : #081426   (card / panel)
bg-sidebar : #071020   (sidebar)
bg-input   : #0b1930   (inputs, combos, table header)
accent-1   : #2563eb   (primary blue)
accent-2   : #38bdf8   (sky / cyan highlight)
accent-3   : #a855f7   (purple)
success    : #10b981   (green)
warning    : #f59e0b   (amber)
danger     : #ef4444   (red)
text-hi    : #f1f5f9   (primary white)
text-mid   : #94a3b8   (secondary gray-blue)
text-lo    : #64748b   (muted / placeholder)
border     : rgba(59, 130, 246, 0.20)
"""

# ─── colour shortcuts used inline ───────────────────────────────────────────
_BG_DEEP    = "#060d17"
_BG_PANEL   = "#081426"
_BG_SIDEBAR = "#071020"
_BG_INPUT   = "#0b1930"
_ACCENT     = "#2563eb"
_ACCENT2    = "#38bdf8"
_SUCCESS    = "#10b981"
_WARNING    = "#f59e0b"
_DANGER     = "#ef4444"
_TEXT_HI    = "#f1f5f9"
_TEXT_MID   = "#94a3b8"
_TEXT_LO    = "#64748b"
_BORDER     = "rgba(59, 130, 246, 0.20)"


def rgba(hex_color: str, alpha_hex: str = "ff") -> str:
    """
    Build a Qt-safe 'rgba(r, g, b, a)' string from a base '#RRGGBB' color and a
    2-digit hex alpha suffix (e.g. rgba('#3b82f6', '1a') for ~10% opacity blue).

    Qt style sheets accept the rgba(r, g, b, a) form with an integer alpha
    channel in the range 0-255. We intentionally convert the provided hex alpha
    suffix into that integer form instead of producing a floating-point alpha
    value, because some Qt stylesheet parsers reject the float variant.
    """
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a = int(alpha_hex, 16)
    return f"rgba({r}, {g}, {b}, {a})"


DARK_THEME = f"""
/* ═══════════════════════════════════════════════════════════════
   RAMGuard — Unified Dark Navy Design System
   ═══════════════════════════════════════════════════════════════ */

/* ── Root containers ── */
QMainWindow, QDialog {{
    background-color: {_BG_DEEP};
    color: {_TEXT_HI};
}}

QWidget {{
    background-color: transparent;
    color: {_TEXT_HI};
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}}

/* ── Custom Title Bar ── */
#title_bar {{
    background-color: #070e1a;
    border-bottom: 1px solid rgba(59, 130, 246, 0.12);
}}

#title_bar_btn {{
    background-color: transparent;
    color: {_TEXT_MID};
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    min-width: 36px;
    min-height: 28px;
    max-height: 28px;
}}

#title_bar_btn:hover {{
    background-color: rgba(255, 255, 255, 0.08);
    color: {_TEXT_HI};
}}

#title_bar_close_btn {{
    background-color: transparent;
    color: {_TEXT_MID};
    border: none;
    border-radius: 6px;
    font-size: 14px;
    min-width: 36px;
    min-height: 28px;
    max-height: 28px;
}}

#title_bar_close_btn:hover {{
    background-color: {_DANGER};
    color: {_TEXT_HI};
}}

/* ── Sidebar ── */
#sidebar {{
    background-color: {_BG_SIDEBAR};
    border-right: 1px solid rgba(59, 130, 246, 0.10);
    min-width: 230px;
    max-width: 230px;
}}

QPushButton#nav_btn {{
    background-color: transparent;
    color: {_TEXT_MID};
    border: none;
    border-radius: 10px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton#nav_btn:hover {{
    background-color: rgba(37, 99, 235, 0.12);
    color: {_TEXT_HI};
}}

QPushButton#nav_btn[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1d4ed8, stop:1 #2563eb);
    color: {_TEXT_HI};
    font-weight: 700;
}}

/* ── Content Area ── */
#content_area {{
    background-color: {_BG_DEEP};
}}

/* ── Cards ── */
#card {{
    background-color: {_BG_PANEL};
    border: 1px solid {_BORDER};
    border-radius: 14px;
    padding: 16px;
}}

#card_title {{
    color: {_TEXT_MID};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

#card_value {{
    color: {_TEXT_HI};
    font-size: 26px;
    font-weight: 700;
}}

#card_sub {{
    color: {_TEXT_MID};
    font-size: 11px;
}}

/* ── Settings section card (reused on settings & optimization) ── */
#settings_card {{
    background-color: {_BG_PANEL};
    border: 1px solid {_BORDER};
    border-radius: 14px;
}}

/* ── Optimize Banner ── */
#optimize_banner {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1e40af, stop:0.5 #1d4ed8, stop:1 #4f46e5);
    border: 1px solid rgba(147, 197, 253, 0.30);
    border-radius: 16px;
}}

/* ── Buttons ── */
QPushButton#optimize_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1d4ed8, stop:1 #2563eb);
    color: {_TEXT_HI};
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}

QPushButton#optimize_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2563eb, stop:1 #3b82f6);
    border-color: rgba(255, 255, 255, 0.35);
}}

QPushButton#optimize_btn:pressed {{
    background: #1e40af;
}}

QPushButton#optimize_btn:disabled {{
    background: #1e293b;
    color: {_TEXT_LO};
    border: none;
}}

QPushButton#primary_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1d4ed8, stop:1 #2563eb);
    color: {_TEXT_HI};
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}}

QPushButton#primary_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2563eb, stop:1 #3b82f6);
}}

QPushButton#danger_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #dc2626, stop:1 #ef4444);
    color: {_TEXT_HI};
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}}

QPushButton#danger_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #ef4444, stop:1 #f87171);
}}

QPushButton#success_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #059669, stop:1 #10b981);
    color: {_TEXT_HI};
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}}

QPushButton#success_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #10b981, stop:1 #34d399);
}}

QPushButton#secondary_btn {{
    background-color: {_BG_INPUT};
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
}}

QPushButton#secondary_btn:hover {{
    background-color: #12284c;
    color: {_TEXT_HI};
    border-color: rgba(59, 130, 246, 0.40);
}}

QPushButton#secondary_btn:pressed {{
    background-color: #0d1f3a;
}}

/* ── Tables ── */
QTableWidget {{
    background-color: {_BG_PANEL};
    border: 1px solid {_BORDER};
    border-radius: 12px;
    gridline-color: transparent;
    color: {_TEXT_HI};
    selection-background-color: rgba(37, 99, 235, 0.18);
    outline: none;
    alternate-background-color: rgba(255, 255, 255, 0.015);
}}

QTableWidget::item {{
    padding: 0px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}}

QTableWidget::item:selected {{
    background-color: rgba(37, 99, 235, 0.20);
    color: {_TEXT_HI};
}}

QTableWidget::item:hover {{
    background-color: rgba(37, 99, 235, 0.07);
}}

QHeaderView {{
    background-color: {_BG_INPUT};
}}

QHeaderView::section {{
    background-color: {_BG_INPUT};
    color: {_TEXT_MID};
    border: none;
    border-bottom: 2px solid rgba(59, 130, 246, 0.28);
    border-right: 1px solid rgba(59, 130, 246, 0.10);
    padding: 0px 14px;
    height: 42px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.9px;
}}

QHeaderView::section:last-child {{
    border-right: none;
}}

/* ── Search / Input fields ── */
QLineEdit {{
    background-color: {_BG_INPUT};
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    color: {_TEXT_HI};
    padding: 8px 14px;
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {_ACCENT};
    background-color: #0d1f3a;
}}

QLineEdit::placeholder {{
    color: {_TEXT_LO};
}}

/* ── ComboBox ── */
QComboBox {{
    background-color: {_BG_INPUT};
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    color: {_TEXT_HI};
    padding: 7px 14px;
    min-width: 120px;
    font-size: 13px;
}}

QComboBox:focus, QComboBox:on {{
    border-color: {_ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox QAbstractItemView {{
    background-color: #0d1f3a;
    border: 1px solid rgba(59, 130, 246, 0.30);
    border-radius: 8px;
    color: {_TEXT_HI};
    selection-background-color: {_ACCENT};
    padding: 4px;
    outline: none;
}}

/* ── SpinBox ── */
QSpinBox {{
    background-color: {_BG_INPUT};
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    color: {_TEXT_HI};
    padding: 7px 12px;
    font-size: 13px;
    min-width: 100px;
}}

QSpinBox:focus {{
    border-color: {_ACCENT};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: transparent;
    border: none;
    width: 18px;
}}

QSpinBox::up-arrow {{
    color: {_TEXT_MID};
}}

QSpinBox::down-arrow {{
    color: {_TEXT_MID};
}}

/* ── CheckBox ── */
QCheckBox {{
    color: {_TEXT_HI};
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid rgba(148, 163, 184, 0.35);
    border-radius: 0px;
    background-color: {_BG_INPUT};
    image: none;
}}

QCheckBox::indicator:hover {{
    border-color: {_ACCENT};
    background-color: rgba(37, 99, 235, 0.10);
}}

QCheckBox::indicator:checked {{
    background-color: {_ACCENT};
    border-color: {_ACCENT};
}}

/* ── GroupBox (removed; use QFrame#settings_card instead) ── */
QGroupBox {{
    color: {_TEXT_HI};
    border: 1px solid {_BORDER};
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 700;
    font-size: 13px;
    background-color: {_BG_PANEL};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: -1px;
    padding: 0 6px;
    color: {_TEXT_MID};
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

/* ── Progress Bar ── */
QProgressBar {{
    background-color: rgba(255, 255, 255, 0.06);
    border: none;
    border-radius: 4px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {_ACCENT}, stop:1 #38bdf8);
    border-radius: 4px;
}}

/* ── TextEdit (console/log) ── */
QTextEdit {{
    background-color: #050c16;
    color: {_TEXT_MID};
    border: 1px solid rgba(59, 130, 246, 0.18);
    border-radius: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    padding: 8px;
}}

/* ── Scroll Bars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: rgba(59, 130, 246, 0.30);
    border-radius: 4px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(59, 130, 246, 0.55);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(59, 130, 246, 0.30);
    border-radius: 4px;
    min-width: 28px;
}}

QScrollBar::handle:horizontal:hover {{
    background: rgba(59, 130, 246, 0.55);
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── ScrollArea ── */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

/* ── Label helpers ── */
QLabel#section_title {{
    color: {_TEXT_HI};
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.4px;
}}

QLabel#section_sub {{
    color: {_TEXT_MID};
    font-size: 12px;
    font-weight: 400;
}}

/* ── Dialogs ── */
QDialog {{
    background-color: #071020;
    border: 1px solid rgba(59, 130, 246, 0.22);
    border-radius: 16px;
}}

/* ── TabWidget ── */
QTabWidget::pane {{
    border: 1px solid {_BORDER};
    border-radius: 10px;
    background-color: {_BG_PANEL};
}}

QTabBar::tab {{
    background-color: {_BG_INPUT};
    color: {_TEXT_MID};
    border-radius: 6px;
    padding: 8px 18px;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {_ACCENT};
    color: {_TEXT_HI};
}}

/* ── Message Box ── */
QMessageBox {{
    background-color: #071020;
}}

QMessageBox QLabel {{
    color: {_TEXT_HI};
    font-size: 13px;
}}

QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 16px;
    border-radius: 6px;
    font-weight: 600;
}}
"""

LIGHT_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
    min-width: 230px;
    max-width: 230px;
}

#card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #64748b;
    border: none;
    border-radius: 10px;
    padding: 10px 16px;
    text-align: left;
}

QPushButton#nav_btn:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton#nav_btn[active="true"] {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 700;
}
"""


def get_stylesheet(theme: str = "dark") -> str:
    return DARK_THEME if theme == "dark" else LIGHT_THEME
