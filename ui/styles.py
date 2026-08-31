"""
RAMGuard UI Styles
Dark-themed, professional stylesheet for the entire application.
"""

DARK_THEME = """
/* ═══════════════════════════════════════════════════
   RAMGuard Dark Theme Stylesheet
   ═══════════════════════════════════════════════════ */

QMainWindow, QDialog {
    background-color: #0d1117;
    color: #e6edf3;
}

QWidget {
    background-color: transparent;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
    min-width: 220px;
    max-width: 220px;
}

#sidebar_logo {
    color: #58a6ff;
    font-size: 18px;
    font-weight: 700;
    padding: 20px 16px 8px 16px;
}

#sidebar_tagline {
    color: #8b949e;
    font-size: 10px;
    padding: 0 16px 16px 16px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #8b949e;
    border: none;
    border-radius: 8px;
    padding: 11px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_btn:hover {
    background-color: #21262d;
    color: #e6edf3;
}

QPushButton#nav_btn[active="true"] {
    background-color: #1f6feb22;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
}

/* ── Content Area ── */
#content_area {
    background-color: #0d1117;
}

/* ── Cards ── */
#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
}

#card_title {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

#card_value {
    color: #e6edf3;
    font-size: 28px;
    font-weight: 700;
}

#card_sub {
    color: #8b949e;
    font-size: 11px;
}

/* ── Optimize Button ── */
QPushButton#optimize_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1f6feb, stop:1 #388bfd);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton#optimize_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #388bfd, stop:1 #58a6ff);
}

QPushButton#optimize_btn:pressed {
    background: #1f6feb;
}

QPushButton#optimize_btn:disabled {
    background: #21262d;
    color: #484f58;
}

/* ── Action Buttons ── */
QPushButton#danger_btn {
    background-color: #da3633;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}

QPushButton#danger_btn:hover { background-color: #f85149; }

QPushButton#success_btn {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}

QPushButton#success_btn:hover { background-color: #2ea043; }

QPushButton#secondary_btn {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
}

QPushButton#secondary_btn:hover {
    background-color: #30363d;
    color: #e6edf3;
}

/* ── Tables ── */
QTableWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    gridline-color: #21262d;
    color: #e6edf3;
    selection-background-color: #1f6feb33;
    outline: none;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #21262d;
}

QTableWidget::item:selected {
    background-color: #1f6feb22;
    color: #e6edf3;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    border: none;
    border-bottom: 2px solid #30363d;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Search/Filter Bar ── */
QLineEdit {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #58a6ff;
    background-color: #161b22;
}

QLineEdit::placeholder { color: #484f58; }

/* ── Combo / Dropdowns ── */
QComboBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    padding: 7px 12px;
    min-width: 120px;
}

QComboBox:focus { border-color: #58a6ff; }

QComboBox::drop-down { border: none; width: 24px; }

QComboBox QAbstractItemView {
    background-color: #21262d;
    border: 1px solid #30363d;
    color: #e6edf3;
    selection-background-color: #1f6feb44;
}

/* ── Checkboxes ── */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #30363d;
    border-radius: 4px;
    background-color: #21262d;
}

QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}

/* ── Sliders ── */
QSlider::groove:horizontal {
    height: 4px;
    background: #30363d;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #58a6ff;
    border: none;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::sub-page:horizontal {
    background: #1f6feb;
    border-radius: 2px;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background: #161b22;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #161b22;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-width: 20px;
}

/* ── Labels ── */
QLabel#section_title {
    color: #e6edf3;
    font-size: 20px;
    font-weight: 700;
}

QLabel#section_sub {
    color: #8b949e;
    font-size: 12px;
}

QLabel#status_normal  { color: #2ecc71; font-weight: 600; }
QLabel#status_moderate { color: #f39c12; font-weight: 600; }
QLabel#status_high    { color: #e67e22; font-weight: 600; }
QLabel#status_critical { color: #e74c3c; font-weight: 600; font-size: 14px; }

/* ── Progress Bars ── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #1f6feb, stop:1 #58a6ff);
}

QProgressBar[pressure="MODERATE"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #f39c12, stop:1 #f1c40f);
}

QProgressBar[pressure="HIGH"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #e67e22, stop:1 #e74c3c);
}

QProgressBar[pressure="CRITICAL"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #e74c3c, stop:1 #c0392b);
}

/* ── Tooltips ── */
QToolTip {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Dialogs ── */
QDialog {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
}

/* ── Spin Boxes ── */
QSpinBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    padding: 6px 10px;
}

QSpinBox:focus { border-color: #58a6ff; }

/* ── Tab Widget ── */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 8px;
    background-color: #161b22;
}

QTabBar::tab {
    background-color: #21262d;
    color: #8b949e;
    border-radius: 6px;
    padding: 8px 18px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #1f6feb;
    color: #ffffff;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #161b22;
    color: #8b949e;
    border-top: 1px solid #30363d;
    font-size: 11px;
    padding: 4px 8px;
}

/* ── Separator ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #30363d;
}
"""

LIGHT_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #f6f8fa;
    color: #1f2328;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0d7de;
    min-width: 220px;
    max-width: 220px;
}

#card {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    padding: 16px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #57606a;
    border: none;
    border-radius: 8px;
    padding: 11px 16px;
    text-align: left;
}

QPushButton#nav_btn:hover { background-color: #f6f8fa; color: #1f2328; }

QPushButton#nav_btn[active="true"] {
    background-color: #ddf4ff;
    color: #0550ae;
    border-left: 3px solid #0550ae;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    color: #1f2328;
}

QHeaderView::section {
    background-color: #f6f8fa;
    color: #57606a;
    border-bottom: 2px solid #d0d7de;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    color: #1f2328;
    padding: 8px 12px;
}

QPushButton#optimize_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #0550ae, stop:1 #0969da);
    color: #ffffff;
    border-radius: 10px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: 700;
}
"""


def get_stylesheet(theme: str = "dark") -> str:
    return DARK_THEME if theme == "dark" else LIGHT_THEME
