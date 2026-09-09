"""
RAMGuard Settings Page
User-configurable settings with persistence.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QFrame, QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from config.app_config import AppConfig
from utils.logger import get_logger

logger = get_logger("SettingsPage")


class SettingsPage(QWidget):
    """Application settings panel."""

    theme_changed = pyqtSignal(str)
    interval_changed = pyqtSignal(int)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        root = QVBoxLayout(container)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # Header
        title = QLabel("Settings & Preferences")
        title.setObjectName("section_title")
        sub = QLabel("Configure RAMGuard system monitoring thresholds, startup preferences and application defaults.")
        sub.setObjectName("section_sub")
        root.addWidget(title)
        root.addWidget(sub)

        # ── 1. General Settings Card ──
        gen_card = QFrame()
        gen_card.setObjectName("card")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(20, 18, 20, 18)
        gen_layout.setSpacing(14)

        gen_title = QLabel("General Settings")
        gen_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        gen_layout.addWidget(gen_title)

        gen_layout.addLayout(self._row_check(
            "Start RAMGuard with Windows",
            self._config.get("start_with_windows", False),
            "start_with_windows"
        ))
        gen_layout.addLayout(self._row_check(
            "Show desktop notifications when RAM usage is high",
            self._config.get("show_notifications", True),
            "show_notifications"
        ))
        root.addWidget(gen_card)

        # ── 2. Monitoring Thresholds Card ──
        mon_card = QFrame()
        mon_card.setObjectName("card")
        mon_layout = QVBoxLayout(mon_card)
        mon_layout.setContentsMargins(20, 18, 20, 18)
        mon_layout.setSpacing(14)

        mon_title = QLabel("Monitoring & Thresholds")
        mon_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        mon_layout.addWidget(mon_title)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 60)
        self._interval_spin.setValue(self._config.monitoring_interval)
        self._interval_spin.setSuffix(" seconds")
        self._interval_spin.setFixedWidth(140)
        self._interval_spin.valueChanged.connect(self._on_interval_changed)

        self._warn_spin = QSpinBox()
        self._warn_spin.setRange(50, 95)
        self._warn_spin.setValue(self._config.warning_threshold)
        self._warn_spin.setSuffix("%")
        self._warn_spin.setFixedWidth(140)

        self._crit_spin = QSpinBox()
        self._crit_spin.setRange(80, 99)
        self._crit_spin.setValue(self._config.critical_threshold)
        self._crit_spin.setSuffix("%")
        self._crit_spin.setFixedWidth(140)

        mon_layout.addLayout(self._form_row("Live Refresh Interval:", self._interval_spin))
        mon_layout.addLayout(self._form_row("Warning RAM Threshold:", self._warn_spin))
        mon_layout.addLayout(self._form_row("Critical RAM Threshold:", self._crit_spin))
        root.addWidget(mon_card)

        # ── 3. Appearance & Mode Card ──
        app_card = QFrame()
        app_card.setObjectName("card")
        app_layout = QVBoxLayout(app_card)
        app_layout.setContentsMargins(20, 18, 20, 18)
        app_layout.setSpacing(14)

        app_title = QLabel("Appearance & Optimization Defaults")
        app_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        app_layout.addWidget(app_title)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.setCurrentText(self._config.theme)
        self._theme_combo.setFixedWidth(140)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["SAFE", "SMART", "CUSTOM"])
        self._mode_combo.setCurrentText(self._config.default_mode)
        self._mode_combo.setFixedWidth(140)

        app_layout.addLayout(self._form_row("Application Theme:", self._theme_combo))
        app_layout.addLayout(self._form_row("Default Optimization Mode:", self._mode_combo))
        root.addWidget(app_card)

        # ── 4. Protected Processes Policy Card ──
        prot_card = QFrame()
        prot_card.setObjectName("card")
        prot_layout = QVBoxLayout(prot_card)
        prot_layout.setContentsMargins(20, 18, 20, 18)
        prot_layout.setSpacing(10)

        prot_title = QLabel("System Protection Guarantee")
        prot_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700;")
        prot_layout.addWidget(prot_title)

        prot_info = QLabel(
            "RAMGuard automatically protects critical OS components, system drivers, "
            "security software (Windows Defender, Antivirus), and essential background services.\n\n"
            "Safety Classification Policy: Protected processes can NEVER be terminated automatically "
            "or manually through RAMGuard, preventing system instability or blue screens."
        )
        prot_info.setStyleSheet("color: #8c9eb5; font-size: 12px; line-height: 1.4;")
        prot_info.setWordWrap(True)
        prot_layout.addWidget(prot_info)
        root.addWidget(prot_card)

        # ── Action Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setObjectName("secondary_btn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setFixedHeight(40)
        reset_btn.setFixedWidth(140)
        reset_btn.clicked.connect(self._reset)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("optimize_btn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFixedHeight(40)
        save_btn.setFixedWidth(150)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

        root.addStretch()
        scroll.setWidget(container)

    def _save(self) -> None:
        self._config.set("monitoring_interval_seconds", self._interval_spin.value())
        self._config.set("memory_warning_threshold_percent", self._warn_spin.value())
        self._config.set("memory_critical_threshold_percent", self._crit_spin.value())
        self._config.set("theme", self._theme_combo.currentText())
        self._config.set("default_optimization_mode", self._mode_combo.currentText())
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")

    def _reset(self) -> None:
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._interval_spin.setValue(3)
            self._warn_spin.setValue(80)
            self._crit_spin.setValue(90)
            self._theme_combo.setCurrentText("dark")
            self._mode_combo.setCurrentText("SAFE")
            self._save()

    def _on_theme_changed(self, theme: str) -> None:
        self.theme_changed.emit(theme)

    def _on_interval_changed(self, val: int) -> None:
        self.interval_changed.emit(val)

    def _row_check(self, label: str, value: bool, key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        cb = QCheckBox()
        cb.setChecked(value)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.stateChanged.connect(lambda state, k=key: self._config.set(k, bool(state)))
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(cb)
        return row

    def _form_row(self, label: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #8c9eb5; font-size: 13px; min-width: 220px;")
        row.addWidget(lbl)
        row.addWidget(widget)
        row.addStretch()
        return row

